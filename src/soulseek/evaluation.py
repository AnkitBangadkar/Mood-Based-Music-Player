from __future__ import annotations

import json
import math
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from soulseek.recommender import RecommendationService
from soulseek.storage import Store


@dataclass(frozen=True, slots=True)
class BenchmarkQuery:
    id: str
    prompt: str
    field: str
    value: str


def load_queries(path: Path) -> list[BenchmarkQuery]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("Benchmark query file must contain a non-empty JSON list")
    queries: list[BenchmarkQuery] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Every benchmark query must be an object")
        query = BenchmarkQuery(
            id=str(item.get("id", "")).strip(),
            prompt=str(item.get("prompt", "")).strip(),
            field=str(item.get("relevance", {}).get("field", "")).strip(),
            value=str(item.get("relevance", {}).get("equals", "")).strip(),
        )
        if not all((query.id, query.prompt, query.field, query.value)):
            raise ValueError(f"Incomplete benchmark query: {item!r}")
        queries.append(query)
    if len({query.id for query in queries}) != len(queries):
        raise ValueError("Benchmark query IDs must be unique")
    return queries


def ranking_metrics(hits: list[bool], relevant_total: int, k: int) -> dict[str, float]:
    top = hits[:k]
    hit_count = sum(top)
    precision = hit_count / k
    recall = hit_count / relevant_total if relevant_total else 0.0
    dcg = sum(float(hit) / math.log2(position + 2) for position, hit in enumerate(top))
    ideal_hits = min(k, relevant_total)
    ideal_dcg = sum(1 / math.log2(position + 2) for position in range(ideal_hits))
    return {
        f"precision@{k}": precision,
        f"recall@{k}": recall,
        f"ndcg@{k}": dcg / ideal_dcg if ideal_dcg else 0.0,
    }


def run_benchmark(
    recommender: RecommendationService,
    store: Store,
    manifest_path: Path,
    queries: list[BenchmarkQuery],
    *,
    k: int = 10,
    playlist_size: int = 20,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, list):
        raise ValueError("Corpus manifest must contain a JSON list")
    labels = {str(row["track_id"]): row for row in manifest}
    indexed_rows = store.retrieval_rows(recommender.encoder.encoder_id)
    if indexed_rows and all(
        str(row["artist"]).casefold() == "unknown artist" for row in indexed_rows
    ):
        raise RuntimeError(
            "Benchmark refused: corpus metadata is unresolved. Rescan the corpus root first."
        )
    details: list[dict[str, Any]] = []

    for query in queries:
        relevant_ids = {
            track_id
            for track_id, row in labels.items()
            if str(row.get(query.field, "")) == query.value
        }
        if not relevant_ids:
            raise ValueError(f"Query {query.id!r} has no relevant corpus tracks")

        started = time.perf_counter()
        _, selections = recommender.recommend(query.prompt, playlist_size)
        elapsed_ms = (time.perf_counter() - started) * 1000
        retrieved: list[tuple[str, str]] = []
        for selection in selections:
            track = store.get_track(selection.candidate.track_id)
            if track is None:
                continue
            retrieved.append((Path(track["path"]).stem, selection.candidate.artist))

        track_ids = [track_id for track_id, _ in retrieved]
        metrics = ranking_metrics(
            [track_id in relevant_ids for track_id in track_ids], len(relevant_ids), k
        )
        metrics.update(
            {
                "fill_rate": len(track_ids) / playlist_size,
                "artist_diversity": len({artist.casefold() for _, artist in retrieved})
                / max(1, len(retrieved)),
                "latency_ms": elapsed_ms,
            }
        )
        details.append(
            {
                "id": query.id,
                "prompt": query.prompt,
                "relevance": {"field": query.field, "equals": query.value},
                "relevant_tracks": len(relevant_ids),
                "returned_tracks": len(track_ids),
                "metrics": {key: round(value, 6) for key, value in metrics.items()},
                "top_track_ids": track_ids[:k],
            }
        )

    metric_names = list(details[0]["metrics"])
    aggregate = {
        name: round(statistics.fmean(item["metrics"][name] for item in details), 6)
        for name in metric_names
    }
    return {
        "benchmark": "soulseek-manifest-contrast-dev-v1",
        "judgment_source": (
            "Curated manifest contrast labels; development proxy only, not final human relevance"
        ),
        "encoder_id": recommender.encoder.encoder_id,
        "query_count": len(queries),
        "k": k,
        "playlist_size": playlist_size,
        "aggregate": aggregate,
        "queries": details,
    }

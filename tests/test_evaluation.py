import json
from pathlib import Path

import pytest

from soulseek.evaluation import BenchmarkQuery, load_queries, ranking_metrics, run_benchmark


def test_ranking_metrics_use_fixed_k_and_binary_ndcg():
    metrics = ranking_metrics([True, False, True], relevant_total=4, k=3)

    assert metrics["precision@3"] == pytest.approx(2 / 3)
    assert metrics["recall@3"] == pytest.approx(0.5)
    assert 0 < metrics["ndcg@3"] < 1


def test_load_queries_rejects_duplicate_ids(tmp_path: Path):
    path = tmp_path / "queries.json"
    item = {
        "id": "calm",
        "prompt": "calm evening",
        "relevance": {"field": "contrast_role", "equals": "Sad_vs_Calm:Calm"},
    }
    path.write_text(json.dumps([item, item]), encoding="utf-8")

    with pytest.raises(ValueError, match="unique"):
        load_queries(path)


def test_benchmark_refuses_unresolved_corpus_before_encoding(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps([{"track_id": "Q1_001", "contrast_role": "Romantic_vs_Happy:Happy"}]),
        encoding="utf-8",
    )

    class Encoder:
        encoder_id = "test-encoder"

    class Recommender:
        encoder = Encoder()

        def recommend(self, prompt, size):
            raise AssertionError("The encoder must not run for an invalid catalog")

    class Store:
        def retrieval_rows(self, encoder_id):
            return [{"artist": "Unknown artist"}]

    with pytest.raises(RuntimeError, match="Rescan the corpus root"):
        run_benchmark(
            Recommender(),
            Store(),
            manifest,
            [
                BenchmarkQuery(
                    "happy", "happy morning", "contrast_role", "Romantic_vs_Happy:Happy"
                )
            ],
        )

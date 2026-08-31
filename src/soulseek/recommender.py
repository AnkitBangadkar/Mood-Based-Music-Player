from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence

import numpy as np

from soulseek.domain import Candidate, PlaylistSelection, QueryIntent, TextEncoder
from soulseek.storage import Store

WORD_PATTERN = re.compile(r"[\w']+", re.UNICODE)
EXCLUSION_PATTERN = re.compile(
    r"(?:\bwithout\b|\bexcept\b|\bno\b|\bnot\b)\s+([^,;.]+)", re.IGNORECASE
)
STOP_WORDS = frozenset(
    {"a", "an", "and", "for", "from", "in", "me", "my", "of", "on", "some", "the", "to", "with"}
)


def _tokens(text: str) -> set[str]:
    return {token for token in WORD_PATTERN.findall(text.casefold()) if token not in STOP_WORDS}


class IntentParser:
    def parse(self, prompt: str) -> QueryIntent:
        normalized = " ".join(prompt.split()).strip()
        exclusions: list[str] = []
        for match in EXCLUSION_PATTERN.finditer(normalized):
            phrase = match.group(1).strip()
            if phrase:
                exclusions.append(phrase)
        desired = EXCLUSION_PATTERN.sub(" ", normalized)
        desired = re.sub(r"(?:,\s*)?\b(?:but|and)\b\s*$", " ", desired, flags=re.IGNORECASE)
        desired = re.sub(r"\s+", " ", desired).strip(" ,;.") or normalized
        return QueryIntent(normalized, desired, tuple(dict.fromkeys(exclusions)))


class RecommendationService:
    def __init__(
        self,
        store: Store,
        encoder: TextEncoder,
        *,
        retrieval_candidates: int = 120,
        max_tracks_per_artist: int = 2,
    ):
        self.store = store
        self.encoder = encoder
        self.intent_parser = IntentParser()
        self.retrieval_candidates = retrieval_candidates
        self.max_tracks_per_artist = max_tracks_per_artist

    def generate(self, prompt: str, size: int) -> tuple[str, QueryIntent, list[PlaylistSelection]]:
        intent, selections = self.recommend(prompt, size)
        persisted = [
            {
                "track_id": item.candidate.track_id,
                "position": item.position,
                "score": item.final_score,
                "reasons": list(item.reasons),
            }
            for item in selections
        ]
        run_id = self.store.save_playlist(
            prompt,
            {"desired_text": intent.desired_text, "exclusions": list(intent.exclusions)},
            self.encoder.encoder_id,
            persisted,
        )
        return run_id, intent, selections

    def recommend(self, prompt: str, size: int) -> tuple[QueryIntent, list[PlaylistSelection]]:
        """Rank a playlist without persisting a user-visible playlist run."""
        intent = self.intent_parser.parse(prompt)
        rows = self.store.retrieval_rows(self.encoder.encoder_id)
        if not rows:
            raise EmptyIndexError(self.encoder.encoder_id)

        query = self.encoder.encode_query(intent.desired_text)
        matrix = np.vstack([row["embedding"] for row in rows])
        if matrix.shape[1] != query.shape[0]:
            raise RuntimeError("Stored embedding dimensions do not match the active encoder")
        semantic_scores = matrix @ query
        desired_tokens = _tokens(intent.desired_text)
        exclusion_tokens = (
            set().union(*(_tokens(item) for item in intent.exclusions))
            if intent.exclusions
            else set()
        )

        candidates: list[Candidate] = []
        for row, semantic in zip(rows, semantic_scores, strict=True):
            document_tokens = _tokens(row["searchable_text"])
            lexical = len(desired_tokens & document_tokens) / max(1, len(desired_tokens))
            exclusion = len(exclusion_tokens & document_tokens) / max(1, len(exclusion_tokens))
            if exclusion > 0:
                continue
            rank_score = 0.88 * float(semantic) + 0.12 * lexical - exclusion
            candidates.append(
                Candidate(
                    track_id=row["id"],
                    title=row["title"],
                    artist=row["artist"],
                    searchable_text=row["searchable_text"],
                    embedding=row["embedding"],
                    semantic_score=float(semantic),
                    lexical_score=lexical,
                    exclusion_penalty=exclusion,
                    rank_score=rank_score,
                )
            )

        candidates.sort(key=lambda candidate: (-candidate.rank_score, candidate.track_id))
        broad = candidates[: max(self.retrieval_candidates, size * 8)]
        selections = self._diversify(broad, size)
        return intent, selections

    def _diversify(self, candidates: Sequence[Candidate], size: int) -> list[PlaylistSelection]:
        remaining = list(candidates)
        selected: list[PlaylistSelection] = []
        artist_counts: Counter[str] = Counter()

        while remaining and len(selected) < size:
            best: Candidate | None = None
            best_utility = -math.inf
            for candidate in remaining:
                artist_key = candidate.artist.casefold()
                if artist_counts[artist_key] >= self.max_tracks_per_artist:
                    continue
                redundancy = max(
                    (float(candidate.embedding @ item.candidate.embedding) for item in selected),
                    default=0.0,
                )
                same_artist_penalty = 0.10 if artist_counts[artist_key] else 0.0
                utility = (
                    0.82 * candidate.rank_score - 0.18 * max(0.0, redundancy) - same_artist_penalty
                )
                if utility > best_utility or (
                    math.isclose(utility, best_utility)
                    and best
                    and candidate.track_id < best.track_id
                ):
                    best = candidate
                    best_utility = utility
            if best is None:
                break

            reasons = ["Strong semantic match to the request"]
            if best.lexical_score > 0:
                reasons.append("Metadata directly overlaps the request")
            if selected:
                reasons.append("Adds variety while preserving playlist cohesion")
            selected.append(
                PlaylistSelection(
                    candidate=best,
                    position=len(selected) + 1,
                    final_score=best_utility,
                    reasons=tuple(reasons),
                )
            )
            artist_counts[best.artist.casefold()] += 1
            remaining.remove(best)
        return selected


class EmptyIndexError(RuntimeError):
    def __init__(self, encoder_id: str):
        self.encoder_id = encoder_id
        super().__init__("No tracks are indexed for the active encoder")

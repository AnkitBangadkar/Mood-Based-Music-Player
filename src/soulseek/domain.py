from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

FloatVector = NDArray[np.float32]


@dataclass(frozen=True, slots=True)
class TrackMetadata:
    path: Path
    modified_ns: int
    size_bytes: int
    title: str
    artist: str
    album: str = ""
    genre: str = ""
    year: int | None = None
    duration_seconds: float | None = None
    track_number: int | None = None
    disc_number: int | None = None
    descriptors: tuple[str, ...] = ()

    @property
    def searchable_text(self) -> str:
        fields = [
            f"track: {self.title}",
            f"artist: {self.artist}",
            f"album: {self.album}" if self.album else "",
            f"genre: {self.genre}" if self.genre else "",
            f"year: {self.year}" if self.year else "",
            f"descriptors: {', '.join(self.descriptors)}" if self.descriptors else "",
        ]
        return ". ".join(part for part in fields if part)


@dataclass(frozen=True, slots=True)
class QueryIntent:
    original: str
    desired_text: str
    exclusions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Candidate:
    track_id: str
    title: str
    artist: str
    searchable_text: str
    embedding: FloatVector
    semantic_score: float
    lexical_score: float
    exclusion_penalty: float
    rank_score: float


@dataclass(frozen=True, slots=True)
class PlaylistSelection:
    candidate: Candidate
    position: int
    final_score: float
    reasons: tuple[str, ...] = field(default_factory=tuple)


class TextEncoder(Protocol):
    @property
    def encoder_id(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    def encode_query(self, text: str) -> FloatVector: ...

    def encode_documents(self, texts: Sequence[str]) -> NDArray[np.float32]: ...


class CatalogProvider(Protocol):
    def discover(self, root: Path) -> list[Path]: ...

    def read(self, path: Path) -> TrackMetadata: ...


class CatalogProviderFactory(Protocol):
    def create(self, root: Path) -> CatalogProvider: ...

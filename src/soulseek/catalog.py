from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile

from soulseek.domain import TrackMetadata

AUDIO_EXTENSIONS = frozenset({".flac", ".mp3", ".m4a", ".mp4", ".ogg", ".opus", ".wav"})
NUMBER_PATTERN = re.compile(r"^(\d+)")


def _first(tags: Any, *keys: str) -> str:
    if not tags:
        return ""
    for key in keys:
        value = tags.get(key)
        if value is None:
            continue
        if isinstance(value, list | tuple):
            value = value[0] if value else ""
        text = str(value).strip()
        if text:
            return text
    return ""


def _number(value: str) -> int | None:
    match = NUMBER_PATTERN.match(value)
    return int(match.group(1)) if match else None


class FilesystemCatalogProvider:
    def discover(self, root: Path) -> list[Path]:
        resolved = root.expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(resolved)
        if not resolved.is_dir():
            raise NotADirectoryError(resolved)
        return sorted(
            path
            for path in resolved.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and path.suffix.casefold() in AUDIO_EXTENSIONS
        )

    def read(self, path: Path) -> TrackMetadata:
        stat = path.stat()
        audio = MutagenFile(path, easy=True)
        tags = getattr(audio, "tags", None)
        title = _first(tags, "title") or path.stem
        artist = _first(tags, "artist", "albumartist") or "Unknown artist"
        album = _first(tags, "album")
        genre = _first(tags, "genre")
        year = _number(_first(tags, "date", "year"))
        track_number = _number(_first(tags, "tracknumber"))
        disc_number = _number(_first(tags, "discnumber"))
        duration = getattr(getattr(audio, "info", None), "length", None)
        return TrackMetadata(
            path=path.resolve(),
            modified_ns=stat.st_mtime_ns,
            size_bytes=stat.st_size,
            title=title,
            artist=artist,
            album=album,
            genre=genre,
            year=year,
            duration_seconds=float(duration) if duration is not None else None,
            track_number=track_number,
            disc_number=disc_number,
        )


class ResearchCorpusCatalogProvider:
    """Reads the curated corpus manifest while keeping judgment labels out of retrieval text."""

    REQUIRED_FIELDS = frozenset({"track_id", "title", "artist"})
    DESCRIPTOR_FIELDS = (
        "genre_family",
        "subgenre",
        "tempo_class",
        "production_style",
        "vocal_type",
        "language",
        "decade",
    )

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.audio_root = self.root / "audio"
        manifest_path = self.root / "data" / "manifest.json"
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CorpusManifestError(f"Cannot read corpus manifest: {manifest_path}") from error
        if not isinstance(payload, list):
            raise CorpusManifestError("Corpus manifest must contain a JSON list")

        self.rows: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(payload):
            if not isinstance(item, dict) or not self.REQUIRED_FIELDS.issubset(item):
                raise CorpusManifestError(f"Invalid manifest entry at index {index}")
            track_id = str(item["track_id"]).strip()
            if not track_id or track_id.casefold() in self.rows:
                raise CorpusManifestError(f"Duplicate or empty track_id: {track_id!r}")
            self.rows[track_id.casefold()] = item

    def discover(self, root: Path) -> list[Path]:
        if root.resolve() != self.root:
            raise ValueError("Research corpus provider cannot be reused for another root")
        return sorted(
            path
            for path in self.audio_root.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and path.suffix.casefold() in AUDIO_EXTENSIONS
        )

    def read(self, path: Path) -> TrackMetadata:
        row = self.rows.get(path.stem.casefold())
        if row is None:
            return FilesystemCatalogProvider().read(path)

        stat = path.stat()
        audio = MutagenFile(path, easy=True)
        duration = getattr(getattr(audio, "info", None), "length", None)
        genre_parts = [str(row.get(key, "")).strip() for key in ("genre_family", "subgenre")]
        genre = " / ".join(dict.fromkeys(part for part in genre_parts if part))
        descriptors = tuple(
            dict.fromkeys(
                str(row.get(key, "")).strip()
                for key in self.DESCRIPTOR_FIELDS
                if str(row.get(key, "")).strip()
            )
        )
        return TrackMetadata(
            path=path.resolve(),
            modified_ns=stat.st_mtime_ns,
            size_bytes=stat.st_size,
            title=str(row["title"]).strip(),
            artist=str(row["artist"]).strip(),
            genre=genre,
            duration_seconds=float(duration) if duration is not None else None,
            descriptors=descriptors,
        )


class CatalogProviderRouter:
    def create(self, root: Path):
        resolved = root.resolve()
        if (resolved / "data" / "manifest.json").is_file() and (resolved / "audio").is_dir():
            return ResearchCorpusCatalogProvider(resolved)
        return FilesystemCatalogProvider()


class CorpusManifestError(ValueError):
    pass

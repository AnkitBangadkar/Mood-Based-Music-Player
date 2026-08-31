from __future__ import annotations

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

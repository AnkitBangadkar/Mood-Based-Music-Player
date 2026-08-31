from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile

from soulseek.catalog import AUDIO_EXTENSIONS


def _duplicate_groups(values: list[tuple[str, str]]) -> list[list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for key, track_id in values:
        groups[key].append(track_id)
    return sorted((ids for ids in groups.values() if len(ids) > 1), key=lambda ids: ids[0])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_research_corpus(root: Path, *, hashes: bool = False) -> dict[str, Any]:
    root = root.expanduser().resolve()
    manifest_path = root / "data" / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("manifest.json must contain a list")

    rows = [row for row in payload if isinstance(row, dict)]
    ids = [str(row.get("track_id", "")).strip() for row in rows]
    id_counts = Counter(ids)
    audio_paths = sorted(
        path
        for path in (root / "audio").rglob("*")
        if path.is_file() and path.suffix.casefold() in AUDIO_EXTENSIONS
    )
    audio_by_id = {path.stem: path for path in audio_paths}
    expected_ids = set(ids)
    actual_ids = set(audio_by_id)

    invalid_audio: list[dict[str, str]] = []
    long_tracks: list[dict[str, Any]] = []
    valid_audio = 0
    for track_id, path in audio_by_id.items():
        try:
            audio = MutagenFile(path)
            duration = float(audio.info.length)
            valid_audio += 1
            if duration > 600:
                long_tracks.append({"track_id": track_id, "duration_seconds": round(duration, 3)})
        except Exception as error:
            invalid_audio.append({"track_id": track_id, "message": str(error)})

    duplicate_hashes: list[list[str]] | None = None
    if hashes:
        duplicate_hashes = _duplicate_groups(
            [(_sha256(path), track_id) for track_id, path in audio_by_id.items()]
        )

    stale_database_paths = 0
    database_path = root / "data" / "corpus.db"
    if database_path.is_file():
        uri = f"file:{database_path}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            stored = [row[0] for row in connection.execute("SELECT file_path FROM tracks")]
        stale_database_paths = sum(not path or not Path(path).is_file() for path in stored)

    artist_title = [
        (
            f"{str(row.get('artist', '')).casefold()}\0{str(row.get('title', '')).casefold()}",
            str(row.get("track_id", "")),
        )
        for row in rows
    ]
    return {
        "root": str(root),
        "manifest_tracks": len(rows),
        "audio_files": len(audio_paths),
        "valid_audio_files": valid_audio,
        "missing_audio_ids": sorted(expected_ids - actual_ids),
        "unlisted_audio_ids": sorted(actual_ids - expected_ids),
        "duplicate_manifest_ids": sorted(key for key, count in id_counts.items() if count > 1),
        "duplicate_artist_title_groups": _duplicate_groups(artist_title),
        "duplicate_audio_hash_groups": duplicate_hashes,
        "invalid_audio": invalid_audio,
        "long_tracks": sorted(long_tracks, key=lambda item: -item["duration_seconds"]),
        "stale_database_paths": stale_database_paths,
        "unique_artists": len({str(row.get("artist", "")).casefold() for row in rows}),
        "label_counts": {
            field: dict(sorted(Counter(str(row.get(field, "")) for row in rows).items()))
            for field in ("quadrant", "primary_mood", "genre_family", "language", "decade")
        },
    }

import json
import sqlite3
from pathlib import Path

from conftest import make_wav

from soulseek.research import audit_research_corpus


def test_corpus_audit_finds_coverage_and_hygiene_issues(tmp_path: Path):
    root = tmp_path / "corpus"
    make_wav(root / "audio" / "A.wav")
    make_wav(root / "audio" / "EXTRA.wav")
    (root / "data").mkdir()
    rows = [
        {
            "track_id": "A",
            "title": "Same",
            "artist": "Artist",
            "quadrant": "Q1",
            "primary_mood": "joyful",
            "genre_family": "Pop",
            "language": "English",
            "decade": "2020s",
        },
        {
            "track_id": "MISSING",
            "title": "Same",
            "artist": "Artist",
            "quadrant": "Q2",
            "primary_mood": "angry",
            "genre_family": "Rock",
            "language": "English",
            "decade": "2020s",
        },
    ]
    (root / "data" / "manifest.json").write_text(json.dumps(rows), encoding="utf-8")
    with sqlite3.connect(root / "data" / "corpus.db") as connection:
        connection.execute("CREATE TABLE tracks(file_path TEXT)")
        connection.execute("INSERT INTO tracks VALUES (?)", ("/old/location/A.wav",))

    report = audit_research_corpus(root)

    assert report["manifest_tracks"] == 2
    assert report["audio_files"] == 2
    assert report["valid_audio_files"] == 2
    assert report["missing_audio_ids"] == ["MISSING"]
    assert report["unlisted_audio_ids"] == ["EXTRA"]
    assert report["duplicate_artist_title_groups"] == [["A", "MISSING"]]
    assert report["stale_database_paths"] == 1

from pathlib import Path

import numpy as np

from soulseek.domain import TrackMetadata


def metadata(path: Path, *, title: str = "Rain Drive", modified_ns: int = 1) -> TrackMetadata:
    return TrackMetadata(
        path=path,
        modified_ns=modified_ns,
        size_bytes=42,
        title=title,
        artist="Test Artist",
        album="Night Roads",
        genre="Ambient",
    )


def test_incremental_track_and_embedding_round_trip(services, tmp_path: Path):
    path = tmp_path / "music" / "track.mp3"
    root_id = services.store.ensure_root(path.parent)

    track_id, action = services.store.upsert_track(root_id, metadata(path))
    assert action == "added"
    same_id, action = services.store.upsert_track(root_id, metadata(path))
    assert (same_id, action) == (track_id, "unchanged")
    _, action = services.store.upsert_track(root_id, metadata(path, title="Changed", modified_ns=2))
    assert action == "updated"

    vector = np.arange(64, dtype=np.float32)
    vector /= np.linalg.norm(vector)
    services.store.upsert_embeddings(services.encoder.encoder_id, [(track_id, vector)])
    rows = services.store.retrieval_rows(services.encoder.encoder_id)
    assert len(rows) == 1
    np.testing.assert_allclose(rows[0]["embedding"], vector)


def test_missing_tracks_are_not_returned(services, tmp_path: Path):
    path = tmp_path / "music" / "gone.mp3"
    root_id = services.store.ensure_root(path.parent)
    services.store.upsert_track(root_id, metadata(path))

    assert services.store.finish_root_scan(root_id, set()) == 1
    assert services.store.list_tracks(1, 50, None)[1] == 0
    assert services.store.library_stats()["missing_count"] == 1

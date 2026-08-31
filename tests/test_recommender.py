from pathlib import Path

from soulseek.domain import TrackMetadata
from soulseek.recommender import IntentParser


def add_track(services, root_id: str, path: Path, title: str, artist: str, genre: str):
    item = TrackMetadata(
        path=path,
        modified_ns=1,
        size_bytes=100,
        title=title,
        artist=artist,
        genre=genre,
    )
    track_id, _ = services.store.upsert_track(root_id, item)
    vector = services.encoder.encode_documents([item.searchable_text])[0]
    services.store.upsert_embeddings(services.encoder.encoder_id, [(track_id, vector)])
    return track_id


def test_intent_parser_separates_exclusions():
    intent = IntentParser().parse("rainy evening drive, but not metal or aggressive music")
    assert intent.desired_text == "rainy evening drive"
    assert intent.exclusions == ("metal or aggressive music",)


def test_playlist_ranking_exclusions_and_artist_cap(services, tmp_path: Path):
    root_id = services.store.ensure_root(tmp_path / "music")
    add_track(services, root_id, tmp_path / "a.mp3", "Rainy Drive", "Artist A", "Ambient")
    add_track(services, root_id, tmp_path / "b.mp3", "Night Drive", "Artist A", "Ambient")
    add_track(services, root_id, tmp_path / "c.mp3", "Evening Roads", "Artist A", "Ambient")
    metal_id = add_track(
        services, root_id, tmp_path / "d.mp3", "Rainy Drive Metal", "Artist B", "Metal"
    )
    add_track(services, root_id, tmp_path / "e.mp3", "Evening Drive", "Artist C", "Electronic")

    _, intent, playlist = services.recommender.generate("rainy evening drive without metal", 4)

    assert intent.exclusions == ("metal",)
    assert metal_id not in [item.candidate.track_id for item in playlist]
    assert sum(item.candidate.artist == "Artist A" for item in playlist) <= 2
    assert [item.position for item in playlist] == [1, 2, 3]

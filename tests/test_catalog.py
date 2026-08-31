import json
from pathlib import Path

from conftest import make_wav

from soulseek.catalog import CatalogProviderRouter, ResearchCorpusCatalogProvider


def test_router_uses_manifest_metadata_without_judgment_leakage(tmp_path: Path):
    root = tmp_path / "corpus"
    audio_path = make_wav(root / "audio" / "Q4_001.wav")
    (root / "data").mkdir()
    (root / "data" / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "track_id": "Q4_001",
                    "title": "Quiet Road",
                    "artist": "Example Artist",
                    "genre_family": "Electronic/EDM",
                    "subgenre": "Ambient",
                    "tempo_class": "Slow (<80 BPM)",
                    "production_style": "Lo-Fi Bedroom",
                    "vocal_type": "100% Instrumental",
                    "language": "Instrumental",
                    "decade": "2020s",
                    "quadrant": "Q4_CALM_LOW_ENERGY",
                    "primary_mood": "peaceful",
                    "contrast_role": "Sad_vs_Calm:Calm",
                    "rationale": "A direct evaluation judgment that must not leak",
                    "valence": 0.8,
                    "arousal": 0.2,
                }
            ]
        ),
        encoding="utf-8",
    )

    provider = CatalogProviderRouter().create(root)
    assert isinstance(provider, ResearchCorpusCatalogProvider)
    item = provider.read(audio_path)

    assert item.title == "Quiet Road"
    assert item.artist == "Example Artist"
    assert item.genre == "Electronic/EDM / Ambient"
    assert "Lo-Fi Bedroom" in item.searchable_text
    for forbidden in ("peaceful", "Q4_CALM", "Sad_vs_Calm", "evaluation judgment"):
        assert forbidden not in item.searchable_text


def test_unlisted_audio_falls_back_to_embedded_metadata(tmp_path: Path):
    root = tmp_path / "corpus"
    audio_path = make_wav(root / "audio" / "UNKNOWN.wav")
    (root / "data").mkdir()
    (root / "data" / "manifest.json").write_text("[]", encoding="utf-8")

    item = CatalogProviderRouter().create(root).read(audio_path)

    assert item.title == "UNKNOWN"
    assert item.artist == "Unknown artist"

from __future__ import annotations

import wave
from pathlib import Path

import pytest

from soulseek.config import Settings
from soulseek.encoders import HashingTextEncoder
from soulseek.services import build_services


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path / "data",
        encoder_backend="hashing",
        encoder_dimensions=64,
        encoder_batch_size=4,
    )


@pytest.fixture
def services(settings: Settings):
    active = build_services(settings, HashingTextEncoder(settings.encoder_dimensions))
    active.store.initialize()
    yield active
    active.jobs.shutdown()


def make_wav(path: Path, seconds: float = 0.1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 8000
    frames = b"\x00\x00" * int(sample_rate * seconds)
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(frames)
    return path

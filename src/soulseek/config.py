from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SOULSEEK_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "SoulSeek"
    app_version: str = "0.1.0"
    environment: str = "development"
    data_dir: Path = Path("data")
    database_path: Path | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    encoder_backend: str = "sentence-transformers"
    encoder_model: str = "Qwen/Qwen3-Embedding-0.6B"
    encoder_dimensions: int = Field(default=512, ge=32, le=1024)
    encoder_batch_size: int = Field(default=16, ge=1, le=128)
    retrieval_candidates: int = Field(default=120, ge=20, le=1000)
    max_playlist_size: int = Field(default=50, ge=1, le=100)
    max_tracks_per_artist: int = Field(default=2, ge=1, le=10)

    @field_validator("data_dir", mode="before")
    @classmethod
    def expand_data_dir(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()

    @property
    def db_path(self) -> Path:
        if self.database_path is not None:
            return self.database_path.expanduser().resolve()
        return self.data_dir / "soulseek.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

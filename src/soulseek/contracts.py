from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(ContractModel):
    status: Literal["ok"]
    version: str
    database: Literal["ok"]
    encoder_id: str


class LibraryStatsResponse(ContractModel):
    track_count: int
    missing_count: int
    root_count: int
    encoder_id: str


class TrackResponse(ContractModel):
    id: str
    title: str
    artist: str
    album: str
    genre: str
    year: int | None
    duration_seconds: float | None
    audio_url: str


class TrackPageResponse(ContractModel):
    items: list[TrackResponse]
    page: int
    page_size: int
    total: int


class ScanRequest(ContractModel):
    root: str = Field(min_length=1, max_length=4096)


class JobAcceptedResponse(ContractModel):
    job_id: str
    status: Literal["queued"] = "queued"
    status_url: str


class JobResponse(ContractModel):
    id: str
    kind: str
    status: Literal["queued", "running", "succeeded", "failed"]
    phase: str
    progress: float = Field(ge=0, le=1)
    message: str
    result: dict[str, Any] | None
    error: dict[str, Any] | None
    created_at: str
    started_at: str | None
    finished_at: str | None


class PlaylistRequest(ContractModel):
    prompt: str = Field(min_length=2, max_length=500)
    size: int = Field(default=20, ge=1, le=50)

    @field_validator("prompt")
    @classmethod
    def prompt_must_have_content(cls, value: str) -> str:
        normalized = " ".join(value.split()).strip()
        if len(normalized) < 2:
            raise ValueError("prompt must contain at least two visible characters")
        return normalized


class ParsedIntentResponse(ContractModel):
    desired_text: str
    exclusions: list[str]


class PlaylistTrackResponse(TrackResponse):
    position: int
    score: float
    reasons: list[str]


class PlaylistResponse(ContractModel):
    playlist_id: str
    prompt: str
    intent: ParsedIntentResponse
    tracks: list[PlaylistTrackResponse]


class FeedbackRequest(ContractModel):
    playlist_id: str
    track_id: str | None = None
    value: Literal["like", "dislike", "skip"]


class FeedbackResponse(ContractModel):
    feedback_id: str
    accepted: Literal[True] = True


class ErrorBody(ContractModel):
    code: str
    message: str
    details: Any | None = None
    request_id: str


class ErrorResponse(ContractModel):
    error: ErrorBody

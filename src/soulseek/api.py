from __future__ import annotations

import logging
import mimetypes
import uuid
from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from soulseek.config import Settings, get_settings
from soulseek.contracts import (
    ErrorResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    JobAcceptedResponse,
    JobResponse,
    LibraryStatsResponse,
    ParsedIntentResponse,
    PlaylistRequest,
    PlaylistResponse,
    PlaylistTrackResponse,
    ScanRequest,
    TrackPageResponse,
    TrackResponse,
)
from soulseek.recommender import EmptyIndexError
from soulseek.services import Services, build_services
from soulseek.storage import ActiveJobError

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details=None, headers=None):
        self.status = status
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers or {}


def _services(request: Request) -> Services:
    return request.app.state.services


def _track_response(track: dict) -> TrackResponse:
    return TrackResponse(
        id=track["id"],
        title=track["title"],
        artist=track["artist"],
        album=track["album"],
        genre=track["genre"],
        year=track["year"],
        duration_seconds=track["duration_seconds"],
        audio_url=f"/api/v1/tracks/{track['id']}/audio",
    )


def _error_response(
    request: Request, status: int, code: str, message: str, details=None, headers=None
):
    request_id = getattr(request.state, "request_id", "unknown")
    body = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }
    return JSONResponse(status_code=status, content=jsonable_encoder(body), headers=headers)


def _parse_range(value: str, size: int) -> tuple[int, int]:
    if not value.startswith("bytes=") or "," in value:
        raise ValueError("Only one byte range is supported")
    start_text, separator, end_text = value.removeprefix("bytes=").partition("-")
    if not separator:
        raise ValueError("Malformed byte range")
    if not start_text:
        suffix = int(end_text)
        if suffix <= 0:
            raise ValueError("Invalid suffix range")
        return max(0, size - suffix), size - 1
    start = int(start_text)
    end = int(end_text) if end_text else size - 1
    if start < 0 or start >= size or end < start:
        raise ValueError("Range is outside the file")
    return start, min(end, size - 1)


def _file_chunks(
    path: Path, start: int, length: int, chunk_size: int = 1024 * 256
) -> Iterator[bytes]:
    remaining = length
    with path.open("rb") as handle:
        handle.seek(start)
        while remaining > 0:
            chunk = handle.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(request: Request) -> HealthResponse:
    services = _services(request)
    services.store.health()
    return HealthResponse(
        status="ok",
        version=services.settings.app_version,
        database="ok",
        encoder_id=services.encoder.encoder_id,
    )


@router.get("/library/stats", response_model=LibraryStatsResponse, tags=["library"])
def library_stats(request: Request) -> LibraryStatsResponse:
    services = _services(request)
    return LibraryStatsResponse(
        **services.store.library_stats(), encoder_id=services.encoder.encoder_id
    )


@router.get("/tracks", response_model=TrackPageResponse, tags=["library"])
def list_tracks(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> TrackPageResponse:
    rows, total = _services(request).store.list_tracks(page, page_size, search)
    return TrackPageResponse(
        items=[_track_response(row) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/library/scans",
    response_model=JobAcceptedResponse,
    status_code=202,
    responses={409: {"model": ErrorResponse}},
    tags=["library"],
)
def start_scan(payload: ScanRequest, request: Request) -> JobAcceptedResponse:
    root = Path(payload.root).expanduser().resolve()
    if not root.exists():
        raise ApiError(400, "scan_root_not_found", "The requested scan root does not exist")
    if not root.is_dir():
        raise ApiError(400, "scan_root_not_directory", "The requested scan root is not a directory")
    try:
        job_id = _services(request).jobs.submit_scan(root)
    except ActiveJobError as error:
        raise ApiError(
            409,
            "scan_already_running",
            "A library scan is already running",
            {"job_id": error.job_id},
        ) from error
    return JobAcceptedResponse(job_id=job_id, status_url=f"/api/v1/jobs/{job_id}")


@router.get("/jobs/{job_id}", response_model=JobResponse, tags=["jobs"])
def get_job(job_id: str, request: Request) -> JobResponse:
    job = _services(request).store.get_job(job_id)
    if not job:
        raise ApiError(404, "job_not_found", "Job not found")
    return JobResponse(**job)


@router.post(
    "/playlists",
    response_model=PlaylistResponse,
    responses={409: {"model": ErrorResponse}},
    tags=["recommendation"],
)
def generate_playlist(payload: PlaylistRequest, request: Request) -> PlaylistResponse:
    services = _services(request)
    size = min(payload.size, services.settings.max_playlist_size)
    try:
        playlist_id, intent, selections = services.recommender.generate(payload.prompt, size)
    except EmptyIndexError as error:
        raise ApiError(
            409,
            "library_not_indexed",
            "Scan the music library before generating a playlist",
            {"encoder_id": error.encoder_id},
        ) from error

    tracks: list[PlaylistTrackResponse] = []
    for item in selections:
        track = services.store.get_track(item.candidate.track_id)
        if not track:
            continue
        tracks.append(
            PlaylistTrackResponse(
                **_track_response(track).model_dump(),
                position=item.position,
                score=round(item.final_score, 6),
                reasons=list(item.reasons),
            )
        )
    return PlaylistResponse(
        playlist_id=playlist_id,
        prompt=payload.prompt,
        intent=ParsedIntentResponse(
            desired_text=intent.desired_text,
            exclusions=list(intent.exclusions),
        ),
        tracks=tracks,
    )


@router.post("/feedback", response_model=FeedbackResponse, status_code=202, tags=["recommendation"])
def feedback(payload: FeedbackRequest, request: Request) -> FeedbackResponse:
    try:
        feedback_id = _services(request).store.add_feedback(
            payload.playlist_id, payload.track_id, payload.value
        )
    except KeyError as error:
        raise ApiError(404, "playlist_not_found", "Playlist run not found") from error
    except ValueError as error:
        raise ApiError(400, "invalid_feedback_track", str(error)) from error
    return FeedbackResponse(feedback_id=feedback_id)


@router.get("/tracks/{track_id}/audio", tags=["playback"])
def stream_audio(track_id: str, request: Request):
    track = _services(request).store.get_track(track_id)
    if not track:
        raise ApiError(404, "track_not_found", "Track not found")
    path = Path(track["path"])
    if not path.is_file():
        raise ApiError(410, "audio_file_missing", "The audio file is no longer available")

    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    size = path.stat().st_size
    range_header = request.headers.get("range")
    if not range_header:
        return FileResponse(
            path,
            media_type=media_type,
            filename=path.name,
            content_disposition_type="inline",
            headers={"Accept-Ranges": "bytes"},
        )
    try:
        start, end = _parse_range(range_header, size)
    except (ValueError, TypeError):
        raise ApiError(
            416,
            "invalid_range",
            "The requested byte range cannot be served",
            headers={"Content-Range": f"bytes */{size}"},
        ) from None
    length = end - start + 1
    return StreamingResponse(
        _file_chunks(path, start, length),
        status_code=206,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{size}",
            "Content-Length": str(length),
        },
    )


def create_app(settings: Settings | None = None, services: Services | None = None) -> FastAPI:
    configured = settings or get_settings()
    supplied_services = services

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active_services = supplied_services or build_services(configured)
        active_services.store.initialize()
        active_services.store.fail_interrupted_jobs()
        app.state.services = active_services
        yield
        active_services.jobs.shutdown()

    app = FastAPI(
        title=configured.app_name,
        version=configured.app_version,
        description="Local-first natural-language playlist API",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Range", "X-Request-ID"],
        expose_headers=["Content-Length", "Content-Range", "Accept-Ranges", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, error: ApiError):
        return _error_response(
            request, error.status, error.code, error.message, error.details, error.headers
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, error: RequestValidationError):
        return _error_response(
            request, 422, "validation_error", "Request validation failed", error.errors()
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, error: HTTPException):
        return _error_response(
            request, error.status_code, "http_error", str(error.detail), headers=error.headers
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, error: Exception):
        logger.exception("Unhandled API error", exc_info=error)
        return _error_response(
            request,
            500,
            "internal_error",
            "An unexpected backend error occurred",
        )

    app.include_router(router)
    return app


app = create_app()

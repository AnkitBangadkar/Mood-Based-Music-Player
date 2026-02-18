from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn
import os
import mimetypes
import mutagen
import scanner
import database
import engine
from typing import List, Optional
from pathlib import Path

app = FastAPI(title="Mood Playlist Generator")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track scan status
scan_status = {
    "is_scanning": False,
    "current_file": "",
    "processed": 0,
    "total": 0,
    "current": 0,
    "stage": "idle",
    "start_time": None,
    "existing_count": 0,
    "indexed_songs": None,
    "errors": [],
}


class ScanRequest(BaseModel):
    path: str
    enable_audio: bool = True
    enable_lyrics: bool = False
    enable_online_lyrics: bool = False


class GenerateRequest(BaseModel):
    prompt: str
    limit: Optional[int] = 20


class SongResponse(BaseModel):
    id: int
    title: str
    artist: str
    album: str
    genre: str
    filepath: str
    bpm: Optional[float] = None
    energy: Optional[float] = None
    valence: Optional[float] = None
    arousal: Optional[float] = None
    duration: Optional[float] = None
    has_lyrics: Optional[bool] = None
    score: Optional[float] = None
    semantic_score: Optional[float] = None
    match_quality: Optional[str] = None


class PlaylistSaveRequest(BaseModel):
    name: str
    song_ids: List[int]


def _format_song_response(
    song,
    score: Optional[float] = None,
    semantic_score: Optional[float] = None,
    include_duration: bool = False,
) -> dict:
    """Helper to format song response consistently across endpoints."""
    # Convert sqlite3.Row to dict if needed
    if hasattr(song, "keys"):
        song = dict(song)

    # Determine match quality based on absolute score
    match_quality = "unknown"
    if score is not None:
        if score >= 60:
            match_quality = "high"
        elif score >= 35:
            match_quality = "medium"
        else:
            match_quality = "low"

    response = {
        "id": song["id"],
        "title": song.get("title") or "Unknown",
        "artist": song.get("artist") or "Unknown",
        "album": song.get("album") or "Unknown",
        "genre": song.get("genre") or "",
        "filepath": song["filepath"],
        "bpm": song.get("bpm"),
        "energy": song.get("energy"),
        "valence": song.get("valence"),
        "arousal": song.get("arousal"),
        "has_lyrics": bool(song.get("has_lyrics")),
        "score": float(score) if score is not None else None,
        "semantic_score": float(semantic_score) if semantic_score is not None else None,
        "match_quality": match_quality,
    }

    if include_duration:
        duration = 0
        try:
            audio = mutagen.File(song["filepath"])
            if audio:
                duration = getattr(audio.info, "length", 0)
        except Exception:
            pass
        response["duration"] = duration

    return response


# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def startup_event():
    # Create static directory if it doesn't exist
    static_dir.mkdir(exist_ok=True)
    # Initialize DB
    database.init_db()
    # Preload model
    print("Preloading model...")
    engine.get_engine().load_model()
    print("System ready.")


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    """Serve the frontend HTML"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse(
        content="""
    <html>
        <body style="background:#0a0a0a;color:#fafaf9;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;">
            <div style="text-align:center;">
                <h1 style="color:#f59e0b;">Mood Playlist Generator</h1>
                <p>Frontend not found. Place index.html in the static/ folder.</p>
                <p style="color:#666;">API is running at /docs</p>
            </div>
        </body>
    </html>
    """
    )


@app.get("/api/health")
def health_check():
    return {"status": "running", "message": "Mood Playlist Generator API"}


@app.post("/scan")
def scan_library_endpoint(request: ScanRequest, background_tasks: BackgroundTasks):
    global scan_status
    if not os.path.exists(request.path):
        raise HTTPException(status_code=400, detail="Path does not exist")

    scan_status["is_scanning"] = True
    scan_status["processed"] = 0
    scan_status["errors"] = []
    scan_status["start_time"] = None
    scan_status["existing_count"] = database.get_song_count()

    # Run scan in background so we don't block
    background_tasks.add_task(
        run_scan_with_status,
        request.path,
        request.enable_audio,
        request.enable_lyrics,
        request.enable_online_lyrics,
    )
    return {"status": "accepted", "message": f"Scanning started for {request.path}"}


def run_scan_with_status(
    path: str, enable_audio: bool, enable_lyrics: bool, enable_online_lyrics: bool
):
    """Wrapper to update scan status with progress"""
    global scan_status
    import time

    scan_status["start_time"] = time.time()

    def progress_callback(progress: dict):
        scan_status["current"] = progress.get("current", 0)
        scan_status["total"] = progress.get("total", 0)
        scan_status["current_file"] = progress.get("current_file", "")
        scan_status["stage"] = progress.get("stage", "scanning")
        scan_status["indexed_songs"] = progress.get(
            "indexed_songs", scan_status["existing_count"]
        )

    try:
        scanner.scan_library(
            path,
            enable_audio=enable_audio,
            enable_lyrics=enable_lyrics,
            enable_online_lyrics=enable_online_lyrics,
            progress_callback=progress_callback,
        )
    except Exception as e:
        scan_status["errors"].append(str(e))
    finally:
        scan_status["is_scanning"] = False
        scan_status["stage"] = "complete"


@app.get("/scan/status")
def get_scan_status():
    """Get current scan status with detailed progress"""
    song_count = len(database.get_all_songs())
    existing_count = scan_status.get("existing_count", 0)
    start_time = scan_status.get("start_time")

    # Calculate ETA
    eta_seconds = None
    elapsed = 0
    if start_time and scan_status.get("is_scanning"):
        import time

        elapsed = time.time() - start_time
        current = scan_status.get("current", 0)
        total = scan_status.get("total", 0)
        if current > 0 and total > 0:
            rate = current / elapsed
            remaining = total - current
            eta_seconds = remaining / rate if rate > 0 else None

    # Use indexed_songs from scan_status during scan, otherwise from database
    indexed_from_status = scan_status.get("indexed_songs")
    display_indexed = (
        indexed_from_status if indexed_from_status is not None else song_count
    )

    return {
        "is_scanning": scan_status["is_scanning"],
        "indexed_songs": display_indexed,
        "existing_songs": existing_count,
        "current": scan_status.get("current", 0),
        "total": scan_status.get("total", 0),
        "current_file": scan_status.get("current_file", ""),
        "stage": scan_status.get("stage", "idle"),
        "start_time": start_time,
        "elapsed_seconds": round(elapsed, 1),
        "eta_seconds": round(eta_seconds, 1) if eta_seconds else None,
        "errors": scan_status["errors"],
    }


@app.get("/scan/folders")
def get_scanned_folders():
    """Get list of all scanned folders with metadata"""
    folders = database.get_scanned_folders()
    return {"folders": folders}


@app.delete("/scan/folders/{folder_path:path}")
def remove_scanned_folder_endpoint(folder_path: str):
    """Remove a folder from the scanned folders tracking (does not delete songs)"""
    database.remove_scanned_folder(folder_path)
    return {
        "status": "success",
        "message": f"Removed {folder_path} from tracked folders",
    }


@app.post("/generate", response_model=List[SongResponse])
def generate_playlist(request: GenerateRequest):
    results = engine.search(request.prompt, limit=request.limit or 20)

    response = []
    for item in results:
        song_id, score, semantic_score = item
        song = database.get_song_by_id(song_id)
        if song:
            response.append(
                _format_song_response(
                    song,
                    score=score,
                    semantic_score=semantic_score,
                    include_duration=True,
                )
            )

    return response


@app.get("/songs", response_model=List[SongResponse])
def get_songs(limit: int = 500):
    all_songs = database.get_all_songs()
    result = []
    for s in all_songs[:limit]:
        result.append(_format_song_response(s, score=None, include_duration=False))
    return result


@app.get("/songs/{song_id}")
def get_song(song_id: int):
    """Get a single song by ID"""
    song = database.get_song_by_id(song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return _format_song_response(song, score=None, include_duration=False)


@app.get("/audio/{song_id}")
async def stream_audio(song_id: int, request: Request):
    """Stream audio file with range request support for seeking"""
    song = database.get_song_by_id(song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    filepath = song["filepath"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")

    file_size = os.path.getsize(filepath)

    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type:
        mime_type = "audio/mpeg"  # Default to mp3

    # Handle range requests for seeking
    range_header = request.headers.get("range")

    if range_header:
        # Parse range header
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1

        # Clamp values
        start = max(0, start)
        end = min(file_size - 1, end)
        content_length = end - start + 1

        def iter_file():
            with open(filepath, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        return StreamingResponse(
            iter_file(),
            status_code=206,
            media_type=mime_type,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            },
        )
    else:
        # Full file request
        def iter_full_file():
            with open(filepath, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk

        return StreamingResponse(
            iter_full_file(),
            media_type=mime_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            },
        )


@app.get("/lyrics/{song_id}")
def get_lyrics(song_id: int):
    """Get lyrics for a song if available"""
    song = database.get_song_by_id(song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # Check lyrics cache
    from pathlib import Path

    cache_dir = Path("lyrics_cache")

    # Try to find cached lyrics
    title = song["title"] or "Unknown"
    artist = song["artist"] or "Unknown"
    safe_name = f"{artist}_{title}".replace("/", "_").replace("\\", "_")[:100]

    lyrics_file = cache_dir / f"{safe_name}.txt"
    if lyrics_file.exists():
        return {"has_lyrics": True, "lyrics": lyrics_file.read_text(encoding="utf-8")}

    return {"has_lyrics": False, "lyrics": None}


@app.post("/library/flush")
def flush_library():
    """Clear all songs from the library and reset the index."""
    try:
        # Clear database
        database.clear_library()

        # Reset engine index
        eng = engine.get_engine()
        if hasattr(eng, "embeddings"):
            eng.embeddings = None
        if hasattr(eng, "ids"):
            eng.ids = None

        return {"status": "success", "message": "Library cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import (
    FileResponse,
    StreamingResponse,
    HTMLResponse,
    JSONResponse,
)
from pydantic import BaseModel
import uvicorn
import os
import glob as globmod
import mimetypes
import mutagen
import scanner
import database
import engine
import config
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
    "end_time": None,
    "existing_count": 0,
    "indexed_songs": None,
    "errors": [],
}

# Track background lyrics fetch status
lyrics_status = {
    "is_running": False,
    "current_song": "",
    "current": 0,
    "total": 0,
    "found": 0,
    "not_found": 0,
    "stage": "idle",
    "start_time": None,
    "end_time": None,
    "pending_reprocess": 0,
}


class ScanRequest(BaseModel):
    path: str
    enable_audio: bool = True
    enable_lyrics: bool = True
    enable_online_lyrics: Optional[bool] = None
    enable_async_lyrics: Optional[bool] = None
    force_rescan: bool = False


class GenerateRequest(BaseModel):
    prompt: str
    limit: Optional[int] = 20


class FlushRequest(BaseModel):
    folder: Optional[str] = None
    rescan_clap: Optional[bool] = False
    rescan_embeddings: Optional[bool] = False


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
frontend_dir = Path(__file__).parent / "frontend" / "dist"


@app.on_event("startup")
def startup_event():
    import subprocess
    import shutil

    # Create directories if they don't exist
    static_dir.mkdir(exist_ok=True)
    # Initialize DB
    database.init_db()
    # Preload model
    print("Preloading model...")
    engine.get_engine().load_model()

    # Check for React frontend - build if missing
    react_index = frontend_dir / "index.html"
    if not react_index.exists():
        frontend_src = Path(__file__).parent / "frontend"
        npm_path = shutil.which("npm")

        if npm_path and frontend_src.exists():
            print("Building React frontend...")
            try:
                subprocess.run(
                    ["npm", "run", "build"],
                    cwd=str(frontend_src),
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                print("React frontend built successfully!")
            except Exception as e:
                print(f"Frontend build failed: {e}")
                npm_path = None

        if not react_index.exists():
            if npm_path:
                print("Frontend build issue - falling back to static")
            else:
                print("npm not found - using static frontend")

    # Mount frontend assets
    if frontend_dir.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_dir / "assets")),
            name="assets",
        )
    else:
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Check for React frontend
    if frontend_dir.exists():
        print("React frontend detected - serving from /frontend/dist")
    else:
        print(
            "Using static frontend - place built React app in /frontend/dist for enhanced UI"
        )

    print("System ready.")


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    """Serve the frontend HTML - prioritize React frontend if built"""
    # Check for React frontend first
    react_index = frontend_dir / "index.html"
    if react_index.exists():
        return FileResponse(react_index)

    # Fall back to static frontend
    static_index = static_dir / "index.html"
    if static_index.exists():
        return FileResponse(static_index)

    return HTMLResponse(
        content="""
    <html>
        <body style="background:#0a0a0a;color:#fafaf9;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;">
            <div style="text-align:center;">
                <h1 style="color:#f59e0b;">Mood Playlist Generator</h1>
                <p>Frontend not found. Build the React frontend or place index.html in the static/ folder.</p>
                <p style="color:#666;">API is running at /docs</p>
            </div>
        </body>
    </html>
    """
    )


@app.get("/api/health")
def health_check():
    return {"status": "running", "message": "Mood Playlist Generator API"}


@app.get("/library/stats")
def library_stats():
    song_count = database.get_song_count()
    folders = database.get_scanned_folders()
    clap_count = 0
    try:
        clap_data = database.get_songs_with_clap_embeddings()
        clap_count = len(clap_data) if clap_data else 0
    except Exception:
        pass
    return {
        "song_count": song_count,
        "folder_count": len(folders),
        "clap_count": clap_count,
        "folders": folders,
        "is_empty": song_count == 0,
    }


@app.get("/scan/browse")
def browse_directories(path: str = "/"):
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="Path does not exist")
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Path is not a directory")
    try:
        entries = []
        for entry in sorted(
            os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())
        ):
            if entry.name.startswith("."):
                continue
            try:
                has_audio = False
                if entry.is_dir():
                    exts = {".mp3", ".flac", ".wav", ".m4a", ".ogg"}
                    try:
                        for root, _, files in os.walk(entry.path):
                            for f in files:
                                if os.path.splitext(f)[1].lower() in exts:
                                    has_audio = True
                                    break
                            if has_audio:
                                break
                    except PermissionError:
                        pass
                entries.append(
                    {
                        "name": entry.name,
                        "path": entry.path,
                        "is_dir": entry.is_dir(),
                        "has_audio": has_audio,
                    }
                )
            except (PermissionError, OSError):
                continue
        parent = str(Path(path).parent) if path != "/" else None
        return {"path": path, "parent": parent, "entries": entries}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        request.enable_async_lyrics,
        request.force_rescan,
    )
    return {"status": "accepted", "message": f"Scanning started for {request.path}"}


def run_scan_with_status(
    path: str,
    enable_audio: bool,
    enable_lyrics: bool,
    enable_online_lyrics: Optional[bool] = None,
    enable_async_lyrics: Optional[bool] = None,
    force_rescan: bool = False,
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
            enable_async_lyrics=enable_async_lyrics,
            progress_callback=progress_callback,
            force_rescan=force_rescan,
        )
    except Exception as e:
        scan_status["errors"].append(str(e))
    finally:
        scan_status["is_scanning"] = False
        scan_status["stage"] = "complete"
        scan_status["end_time"] = time.time()

        # If async lyrics enabled, start background lyrics fetch
        if enable_async_lyrics is not False and (
            enable_async_lyrics is True
            or (enable_async_lyrics is None and config.LYRICS_ASYNC_ENABLED)
        ):
            # Reset lyrics status before starting
            lyrics_status["is_running"] = True
            lyrics_status["stage"] = "fetching"
            lyrics_status["current"] = 0
            lyrics_status["found"] = 0
            lyrics_status["not_found"] = 0
            lyrics_status["current_song"] = ""
            lyrics_status["pending_reprocess"] = 0
            lyrics_status["start_time"] = time.time()
            lyrics_status["end_time"] = None
            _start_background_lyrics_fetch()


@app.get("/scan/status")
def get_scan_status():
    """Get current scan status with detailed progress"""
    import time

    song_count = len(database.get_all_songs())
    existing_count = scan_status.get("existing_count", 0)
    start_time = scan_status.get("start_time")
    end_time = scan_status.get("end_time")

    # Calculate ETA and elapsed time
    eta_seconds = None
    elapsed = 0
    if start_time and scan_status.get("is_scanning"):
        elapsed = time.time() - start_time
        current = scan_status.get("current", 0)
        total = scan_status.get("total", 0)
        if current > 0 and total > 0:
            rate = current / elapsed
            remaining = total - current
            eta_seconds = remaining / rate if rate > 0 else None
    elif end_time and start_time:
        elapsed = end_time - start_time

    # Calculate lyrics time
    lyrics_elapsed = 0
    if lyrics_status.get("start_time"):
        if lyrics_status.get("is_running"):
            lyrics_elapsed = time.time() - lyrics_status["start_time"]
        elif lyrics_status.get("end_time"):
            lyrics_elapsed = lyrics_status["end_time"] - lyrics_status["start_time"]

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
        "end_time": end_time,
        "elapsed_seconds": round(elapsed, 1),
        "eta_seconds": round(eta_seconds, 1) if eta_seconds else None,
        "errors": scan_status["errors"],
        "lyrics_async": {
            **lyrics_status,
            "elapsed_seconds": round(lyrics_elapsed, 1) if lyrics_elapsed else 0,
        },
    }


@app.get("/scan/progress")
def get_scan_progress():
    """Get detailed scan progress with audio vs lyrics breakdown."""
    import time

    songs = database.get_all_songs()
    # Convert sqlite3.Row objects to dicts for safe access
    songs = [dict(s) for s in songs]
    with_audio = sum(1 for s in songs if s.get("bpm") is not None)
    with_lyrics = sum(1 for s in songs if s.get("has_lyrics"))

    # Calculate audio processing time
    audio_elapsed = 0
    if scan_status.get("start_time"):
        if scan_status["is_scanning"]:
            audio_elapsed = time.time() - scan_status["start_time"]
        elif scan_status.get("end_time"):
            audio_elapsed = scan_status["end_time"] - scan_status["start_time"]

    # Calculate lyrics processing time
    lyrics_elapsed = 0
    if lyrics_status.get("start_time"):
        if lyrics_status["is_running"]:
            lyrics_elapsed = time.time() - lyrics_status["start_time"]
        elif lyrics_status.get("end_time"):
            lyrics_elapsed = lyrics_status["end_time"] - lyrics_status["start_time"]

    return {
        "is_scanning": scan_status["is_scanning"],
        "audio": {
            "total": scan_status.get("total", 0),
            "processed": scan_status.get("current", 0),
            "indexed": with_audio,
            "stage": scan_status.get("stage", "idle"),
            "current_file": scan_status.get("current_file", ""),
            "start_time": scan_status.get("start_time"),
            "end_time": scan_status.get("end_time"),
            "elapsed_seconds": round(audio_elapsed, 1),
        },
        "lyrics": {
            "is_running": lyrics_status.get("is_running", False),
            "total": lyrics_status.get("total", 0),
            "processed": lyrics_status.get("current", 0),
            "found": lyrics_status.get("found", 0),
            "not_found": lyrics_status.get("not_found", 0),
            "current_song": lyrics_status.get("current_song", ""),
            "stage": lyrics_status.get("stage", "idle"),
            "start_time": lyrics_status.get("start_time"),
            "end_time": lyrics_status.get("end_time"),
            "elapsed_seconds": round(lyrics_elapsed, 1),
        },
        "folders": database.get_scanned_folders(),
    }


def _start_background_lyrics_fetch():
    """Start background lyrics fetch in a separate thread."""
    import threading

    def _fetch_thread():
        global lyrics_status

        def progress_callback(progress: dict):
            lyrics_status["current"] = progress.get("current", 0)
            lyrics_status["total"] = progress.get(
                "total", lyrics_status.get("total", 0)
            )
            lyrics_status["current_song"] = progress.get("current_song", "")
            lyrics_status["found"] = progress.get("found", 0)
            lyrics_status["not_found"] = progress.get("not_found", 0)

        try:
            stats = scanner.fetch_lyrics_background(progress_callback=progress_callback)
            lyrics_status["found"] = stats["found"]
            lyrics_status["not_found"] = stats["not_found"]
            lyrics_status["total"] = stats.get("total", lyrics_status.get("total", 0))
        except Exception as e:
            lyrics_status["errors"] = lyrics_status.get("errors", []) + [str(e)]
        finally:
            import time

            lyrics_status["is_running"] = False
            lyrics_status["stage"] = "complete"
            lyrics_status["end_time"] = time.time()
            pending = len(database.get_songs_pending_reprocess())
            lyrics_status["pending_reprocess"] = pending

    thread = threading.Thread(target=_fetch_thread, daemon=True)
    thread.start()


@app.get("/lyrics/status")
def get_lyrics_status():
    """Get current background lyrics fetch status and pending reprocess count."""
    import time

    pending = 0
    if not lyrics_status.get("is_running"):
        try:
            pending = len(database.get_songs_pending_reprocess())
        except Exception:
            pass
        lyrics_status["pending_reprocess"] = pending

    # Calculate elapsed time
    elapsed = 0
    if lyrics_status.get("start_time"):
        if lyrics_status["is_running"]:
            elapsed = time.time() - lyrics_status["start_time"]
        elif lyrics_status.get("end_time"):
            elapsed = lyrics_status["end_time"] - lyrics_status["start_time"]

    return {
        **lyrics_status,
        "elapsed_seconds": round(elapsed, 1),
    }


@app.post("/lyrics/reprocess")
def reprocess_lyrics(background_tasks: BackgroundTasks):
    """Reprocess songs that have new lyrics but haven't had their mood_text/embeddings updated."""
    pending = database.get_songs_pending_reprocess()
    if not pending:
        return {"status": "success", "message": "No songs to reprocess", "count": 0}

    background_tasks.add_task(_run_reprocess)
    return {
        "status": "accepted",
        "message": f"Reprocessing {len(pending)} songs",
        "count": len(pending),
    }


def _run_reprocess():
    """Run lyrics reprocessing in a background thread."""
    global lyrics_status

    def progress_callback(progress: dict):
        lyrics_status["current"] = progress.get("current", 0)
        lyrics_status["total"] = progress.get("total", 0)
        lyrics_status["current_song"] = progress.get("current_song", "")

    try:
        lyrics_status["is_running"] = True
        lyrics_status["stage"] = "reprocessing"
        scanner.reprocess_pending_lyrics(progress_callback=progress_callback)
    except Exception as e:
        lyrics_status["errors"] = lyrics_status.get("errors", []) + [str(e)]
    finally:
        lyrics_status["is_running"] = False
        lyrics_status["stage"] = "complete"
        lyrics_status["pending_reprocess"] = 0


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
    """Get lyrics for a song if available.

    Priority:
    1. Database lyrics_text (from previous scan)
    2. Filesystem cache + sidecar + embedded tags
    3. Optional online fetch (if allow_online=True query param)
    """
    song = database.get_song_by_id(song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    from lyrics_extractor import get_lyrics_for_song

    allow_online = False
    lyrics = get_lyrics_for_song(song_id, allow_online=allow_online)

    if lyrics:
        return {"has_lyrics": True, "lyrics": lyrics}

    return {"has_lyrics": False, "lyrics": None}


@app.post("/library/flush")
def flush_library(request: FlushRequest = None):
    """Clear songs from the library. Supports selective flush by folder."""
    if request is None:
        request = FlushRequest()

    try:
        if request.folder:
            songs = database.get_all_songs()
            folder_path = request.folder
            ids_to_delete = [
                s["id"] for s in songs if s["filepath"].startswith(folder_path)
            ]
            if ids_to_delete:
                database.delete_songs_by_ids(ids_to_delete)
                database.remove_scanned_folder(folder_path)
            database.init_db()
            eng = engine.get_engine()
            if hasattr(eng, "embeddings"):
                eng.embeddings = None
            if hasattr(eng, "ids"):
                eng.ids = None
            return {
                "status": "success",
                "message": f"Removed {len(ids_to_delete)} songs from {folder_path}",
            }
        elif request.rescan_clap:
            database.clear_clap_embeddings()
            eng = engine.get_engine()
            if hasattr(eng, "clap_embeddings"):
                eng.clap_embeddings = None
                eng.clap_ids = None
            return {
                "status": "success",
                "message": "CLAP embeddings cleared. Rescan to regenerate.",
            }
        elif request.rescan_embeddings:
            database.clear_embeddings()
            eng = engine.get_engine()
            if hasattr(eng, "embeddings"):
                eng.embeddings = None
            if hasattr(eng, "ids"):
                eng.ids = None
            return {
                "status": "success",
                "message": "Embeddings cleared. Rescan to regenerate.",
            }
        else:
            database.clear_library()
            eng = engine.get_engine()
            if hasattr(eng, "embeddings"):
                eng.embeddings = None
            if hasattr(eng, "ids"):
                eng.ids = None
            if hasattr(eng, "clap_embeddings"):
                eng.clap_embeddings = None
                eng.clap_ids = None
            return {"status": "success", "message": "Library cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

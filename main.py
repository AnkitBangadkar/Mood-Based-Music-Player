from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import os
import scanner
import database
import engine
from typing import List, Optional

app = FastAPI(title="Mood Playlist Generator")

class ScanRequest(BaseModel):
    path: str
    enable_audio: bool = True
    enable_lyrics: bool = True
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
    has_lyrics: Optional[bool] = None
    score: Optional[float] = None

@app.on_event("startup")
def startup_event():
    # Initialize DB
    database.init_db()
    # Preload model
    print("Preloading model...")
    engine.get_engine().load_model()
    print("System ready.")

@app.get("/")
def read_root():
    return {"status": "running", "message": "Mood Playlist Generator API"}

@app.post("/scan")
def scan_library_endpoint(request: ScanRequest, background_tasks: BackgroundTasks):
    if not os.path.exists(request.path):
        raise HTTPException(status_code=400, detail="Path does not exist")
    
    # Run scan in background so we don't block
    background_tasks.add_task(
        scanner.scan_library, 
        request.path, 
        enable_audio=request.enable_audio, 
        enable_lyrics=request.enable_lyrics,
        enable_online_lyrics=request.enable_online_lyrics
    )
    return {"status": "accepted", "message": f"Scanning started for {request.path} (Audio: {request.enable_audio}, Lyrics: {request.enable_lyrics}, Online: {request.enable_online_lyrics})"}

@app.post("/generate", response_model=List[SongResponse])
def generate_playlist(request: GenerateRequest):
    results = engine.get_engine().search(request.prompt, limit=request.limit)
    
    response = []
    for song_id, score in results:
        song = database.get_song_by_id(song_id)
        if song:
            # song is a Row object, access by index or name
            response.append({
                "id": song['id'],
                "title": song['title'],
                "artist": song['artist'],
                "album": song['album'],
                "genre": song['genre'],
                "filepath": song['filepath'],
                "bpm": song['bpm'],
                "energy": song['energy'],
                "has_lyrics": bool(song['has_lyrics']),
                "score": float(score)
            })
            
    return response

@app.get("/songs", response_model=List[SongResponse])
def get_songs(limit: int = 100):
    all_songs = database.get_all_songs()
    # truncate
    return [dict(s) for s in all_songs[:limit]]

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

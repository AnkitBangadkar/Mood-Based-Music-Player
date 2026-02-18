import sqlite3
import threading
from logger import get_logger

log = get_logger("Database")

DB_PATH = "library.db"

# Thread-local storage for connection pooling
_local = threading.local()


def get_connection():
    """Get a thread-local database connection (connection pooling)."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


def close_connection():
    """Close the thread-local connection if it exists."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT UNIQUE NOT NULL,
            file_mtime REAL,
            title TEXT,
            artist TEXT,
            album TEXT,
            genre TEXT,
            bpm REAL,
            energy REAL,
            brightness REAL,
            valence REAL,
            arousal REAL,
            mode TEXT,
            sentiment REAL,
            has_lyrics INTEGER DEFAULT 0,
            rich_description TEXT,
            lyrics_vec BLOB,
            audio_vec BLOB,
            meta_vec BLOB,
            embedding BLOB
        )
    """)

    # Create scanned_folders table to track indexed directories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scanned_folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            last_scan_time REAL,
            song_count INTEGER DEFAULT 0,
            total_songs_in_db INTEGER DEFAULT 0
        )
    """)

    # Add new columns if they don't exist (migration for existing DBs)
    migrations = [
        "ALTER TABLE songs ADD COLUMN file_mtime REAL",
        "ALTER TABLE songs ADD COLUMN valence REAL",
        "ALTER TABLE songs ADD COLUMN arousal REAL",
        "ALTER TABLE songs ADD COLUMN mode TEXT",
        "ALTER TABLE songs ADD COLUMN lyrics_emotion TEXT",
        "ALTER TABLE songs ADD COLUMN lyrics_emotion_score REAL",
        "ALTER TABLE songs ADD COLUMN emotion_distribution TEXT",
        # Phase 1: new audio features
        "ALTER TABLE songs ADD COLUMN spectral_rolloff REAL",
        "ALTER TABLE songs ADD COLUMN spectral_bandwidth REAL",
        "ALTER TABLE songs ADD COLUMN dynamic_range REAL",
        "ALTER TABLE songs ADD COLUMN mfccs TEXT",  # JSON string of 13 floats
        # Embedding storage for incremental indexing
        "ALTER TABLE songs ADD COLUMN embedding BLOB",
    ]
    for migration in migrations:
        try:
            cursor.execute(migration)
        except sqlite3.OperationalError:
            pass  # Column already exists
    conn.commit()


def add_song(
    filepath,
    title,
    artist,
    album,
    genre,
    rich_description,
    bpm=0.0,
    energy=0.0,
    brightness=0.0,
    valence=0.0,
    arousal=0.0,
    mode="",
    sentiment=0.0,
    has_lyrics=False,
    lyrics_vec=None,
    audio_vec=None,
    meta_vec=None,
    file_mtime=None,
    lyrics_emotion=None,
    lyrics_emotion_score=0.0,
    emotion_distribution=None,
    spectral_rolloff=None,
    spectral_bandwidth=None,
    dynamic_range=None,
    mfccs=None,
):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO songs (
                filepath, file_mtime, title, artist, album, genre, rich_description, 
                bpm, energy, brightness, valence, arousal, mode, sentiment, has_lyrics,
                lyrics_vec, audio_vec, meta_vec, lyrics_emotion, lyrics_emotion_score,
                emotion_distribution, spectral_rolloff, spectral_bandwidth, dynamic_range, mfccs
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                filepath,
                file_mtime,
                title,
                artist,
                album,
                genre,
                rich_description,
                bpm,
                energy,
                brightness,
                valence,
                arousal,
                mode,
                sentiment,
                1 if has_lyrics else 0,
                lyrics_vec,
                audio_vec,
                meta_vec,
                lyrics_emotion,
                lyrics_emotion_score,
                emotion_distribution,
                spectral_rolloff,
                spectral_bandwidth,
                dynamic_range,
                mfccs,
            ),
        )
        song_id = cursor.lastrowid
        conn.commit()
        return song_id
    except sqlite3.Error as e:
        log.error(f"Error adding song {filepath}: {e}")
        return None


def get_all_songs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM songs")
    songs = cursor.fetchall()
    return songs


def get_song_by_id(song_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
    song = cursor.fetchone()
    return song


def get_songs_by_ids(song_ids):
    """Batch fetch multiple songs by their IDs (avoids N+1 queries)."""
    if not song_ids:
        return {}

    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(song_ids))
    cursor.execute(f"SELECT * FROM songs WHERE id IN ({placeholders})", song_ids)
    songs = cursor.fetchall()
    return {song["id"]: dict(song) for song in songs}


def get_existing_songs():
    """
    Returns a dict of filepath -> (id, file_mtime) for incremental scanning.
    This allows us to check which files are already indexed and their modification times.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filepath, file_mtime FROM songs")
    return {
        row["filepath"]: (row["id"], row["file_mtime"]) for row in cursor.fetchall()
    }


def get_song_by_filepath(filepath):
    """Get a single song by its filepath."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM songs WHERE filepath = ?", (filepath,))
    return cursor.fetchone()


def delete_songs_by_ids(song_ids):
    """Delete songs by their IDs (for removing files that no longer exist)."""
    if not song_ids:
        return
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(song_ids))
    cursor.execute(f"DELETE FROM songs WHERE id IN ({placeholders})", song_ids)
    conn.commit()
    log.info(f"Deleted {len(song_ids)} songs that no longer exist on disk.")


def clear_library():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM songs")
    conn.commit()


def get_song_count():
    """Returns the number of indexed songs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM songs")
    return cursor.fetchone()["count"]


def update_song_embedding(song_id, embedding):
    """Store the embedding vector for a song."""
    if embedding is None:
        return
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Convert numpy array to bytes
        embedding_bytes = (
            embedding.tobytes() if hasattr(embedding, "tobytes") else embedding
        )
        cursor.execute(
            "UPDATE songs SET embedding = ? WHERE id = ?", (embedding_bytes, song_id)
        )
        conn.commit()
    except sqlite3.Error as e:
        log.error(f"Error storing embedding for song {song_id}: {e}")


def get_songs_with_embeddings():
    """Get all songs that have embeddings stored."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, embedding FROM songs WHERE embedding IS NOT NULL")
    return cursor.fetchall()


def get_all_songs_with_embeddings():
    """Get all songs with their embeddings loaded."""
    import numpy as np

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM songs")
    songs = cursor.fetchall()

    result = []
    for song in songs:
        song_dict = dict(song)
        if song_dict.get("embedding"):
            # Convert bytes back to numpy array
            try:
                song_dict["embedding"] = np.frombuffer(
                    song_dict["embedding"], dtype=np.float32
                )
            except Exception as e:
                log.warning(f"Failed to load embedding for song {song_dict['id']}: {e}")
                song_dict["embedding"] = None
        result.append(song_dict)
    return result


# Scanned folders tracking
def add_or_update_scanned_folder(path, song_count=0):
    """Add or update a scanned folder entry."""
    import time

    conn = get_connection()
    cursor = conn.cursor()
    total_songs = get_song_count()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO scanned_folders (path, last_scan_time, song_count, total_songs_in_db)
            VALUES (?, ?, ?, ?)
            """,
            (path, time.time(), song_count, total_songs),
        )
        conn.commit()
    except sqlite3.Error as e:
        log.error(f"Error updating scanned folder {path}: {e}")


def get_scanned_folders():
    """Get list of all scanned folders with metadata."""
    import time

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT path, last_scan_time, song_count, total_songs_in_db FROM scanned_folders ORDER BY last_scan_time DESC"
    )
    folders = []
    for row in cursor.fetchall():
        folders.append(
            {
                "path": row["path"],
                "last_scan_time": row["last_scan_time"],
                "last_scan_formatted": time.strftime(
                    "%Y-%m-%d %H:%M", time.localtime(row["last_scan_time"])
                )
                if row["last_scan_time"]
                else "Unknown",
                "song_count": row["song_count"],
                "total_songs_in_db": row["total_songs_in_db"],
            }
        )
    return folders


def remove_scanned_folder(path):
    """Remove a folder from the scanned folders list."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM scanned_folders WHERE path = ?", (path,))
        conn.commit()
    except sqlite3.Error as e:
        log.error(f"Error removing scanned folder {path}: {e}")

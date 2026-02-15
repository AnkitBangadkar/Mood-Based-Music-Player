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
            meta_vec BLOB
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

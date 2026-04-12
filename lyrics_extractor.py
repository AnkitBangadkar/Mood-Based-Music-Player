"""
Lyrics Extractor with Caching.
Fetched lyrics are stored in a central cache folder to avoid re-fetching.
"""

import os
import hashlib
import mutagen
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from logger import get_logger
import lyrics_scraper
import config

log = get_logger("LyricsExtractor")


def _get_cache_path(filepath, title, artist):
    """Generate a unique cache file path for a song."""
    # Create a unique hash based on filepath (handles duplicates)
    unique_key = f"{filepath}|{title}|{artist}"
    hash_name = hashlib.md5(unique_key.encode("utf-8")).hexdigest()[:16]

    # Clean filename for cache
    safe_title = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in (title or "unknown")[:50]
    )
    safe_artist = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in (artist or "unknown")[:30]
    )

    cache_filename = f"{safe_artist} - {safe_title} [{hash_name}].txt"
    return os.path.join(config.LYRICS_CACHE_DIR, cache_filename)


def _ensure_cache_dir():
    """Create lyrics cache directory if it doesn't exist."""
    if not os.path.exists(config.LYRICS_CACHE_DIR):
        os.makedirs(config.LYRICS_CACHE_DIR)
        log.info(f"Created lyrics cache directory: {config.LYRICS_CACHE_DIR}")


def _get_cached_lyrics(cache_path):
    """Try to load lyrics from cache."""
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except Exception as e:
            log.warning(f"Failed to read cache {cache_path}: {e}")
    return None


def _save_to_cache(cache_path, lyrics):
    """Save lyrics to cache file."""
    try:
        _ensure_cache_dir()
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(lyrics)
    except Exception as e:
        log.warning(f"Failed to save cache {cache_path}: {e}")


def get_local_lyrics(filepath, title=None, artist=None):
    """
    Retrieve lyrics from local sources only (no online fetch).
    Used during async mode fast pass so scan isn't blocked by network.
    Priority:
    1. Local Sidecar File (.lrc, .txt next to audio file)
    2. Lyrics Cache (previously fetched online lyrics)
    3. Embedded Tags (ID3 USLT, FLAC LYRICS)

    Returns:
        str: Lyrics text or None if not found.
    """
    cache_path = _get_cache_path(filepath, title, artist)

    # 1. Check for Sidecar Files (user-provided local files)
    base_path = os.path.splitext(filepath)[0]
    for ext in [".lrc", ".txt"]:
        sidecar = base_path + ext
        if os.path.exists(sidecar):
            try:
                with open(sidecar, "r", encoding="utf-8") as f:
                    content = f.read()
                    if ext == ".lrc":
                        content = _clean_lrc(content)
                    if content and content.strip():
                        _save_to_cache(cache_path, content)
                    return content
            except Exception as e:
                log.error(f"Error reading sidecar lyrics {sidecar}: {e}")

    # 2. Check Lyrics Cache
    cached = _get_cached_lyrics(cache_path)
    if cached:
        return cached

    # 3. Check Embedded Tags
    try:
        file_ext = os.path.splitext(filepath)[1].lower()
        content = None
        if file_ext == ".mp3":
            content = _get_mp3_lyrics(filepath)
        elif file_ext == ".flac":
            content = _get_flac_lyrics(filepath)
        elif file_ext == ".m4a":
            content = _get_m4a_lyrics(filepath)

        if content:
            _save_to_cache(cache_path, content)
            return content
    except Exception as e:
        log.warning(f"Error reading embedded lyrics for {filepath}: {e}")

    return None


def get_lyrics(filepath, title=None, artist=None, allow_online=False):
    """
    Attempts to retrieve lyrics for a given audio file.
    Priority:
    1. Local Sidecar File (.lrc, .txt next to audio file)
    2. Lyrics Cache (previously fetched online lyrics)
    3. Embedded Tags (ID3 USLT, FLAC LYRICS)
    4. Online Fetch (Genius/OVH) - ONLY if allow_online=True

    Returns:
        str: Lyrics text or None if not found.
    """
    cache_path = _get_cache_path(filepath, title, artist)

    # 1. Check for Sidecar Files (user-provided local files)
    base_path = os.path.splitext(filepath)[0]
    for ext in [".lrc", ".txt"]:
        sidecar = base_path + ext
        if os.path.exists(sidecar):
            try:
                with open(sidecar, "r", encoding="utf-8") as f:
                    content = f.read()
                    if ext == ".lrc":
                        content = _clean_lrc(content)
                    # Cache sidecar lyrics for faster future retrieval
                    if content and content.strip():
                        _save_to_cache(cache_path, content)
                    return content
            except Exception as e:
                log.error(f"Error reading sidecar lyrics {sidecar}: {e}")

    # 2. Check Lyrics Cache (previously fetched from online or cached from sidecar)
    cached = _get_cached_lyrics(cache_path)
    if cached:
        return cached

    # 3. Check Embedded Tags
    try:
        file_ext = os.path.splitext(filepath)[1].lower()
        content = None
        if file_ext == ".mp3":
            content = _get_mp3_lyrics(filepath)
        elif file_ext == ".flac":
            content = _get_flac_lyrics(filepath)
        elif file_ext == ".m4a":
            content = _get_m4a_lyrics(filepath)

        if content:
            # Cache embedded lyrics too for consistency
            _save_to_cache(cache_path, content)
            return content
    except Exception as e:
        log.warning(f"Error reading embedded lyrics for {filepath}: {e}")

    # 4. Online Fetch (Optional) - only if not cached
    if allow_online and title and artist:
        from scanner import clean_title_for_embedding

        clean_title = clean_title_for_embedding(title)
        clean_artist = _clean_artist_for_lookup(artist)
        log.info(
            f"Local lyrics not found for '{clean_title}' by '{clean_artist}', attempting online fetch..."
        )
        online_lyrics = lyrics_scraper.fetch_lyrics(clean_title, clean_artist)
        if online_lyrics:
            _save_to_cache(cache_path, online_lyrics)
            return online_lyrics

    return None


def _clean_artist_for_lookup(artist):
    """Clean artist name for lyrics lookup.
    Remove common garbage like 'Topic', '- Topic', 'VEVO', etc.
    """
    if not artist:
        return ""
    import re

    artist = re.sub(r"\s*[-–]\s*Topic$", "", artist, flags=re.IGNORECASE)
    artist = re.sub(r"\s*Topic$", "", artist, flags=re.IGNORECASE)
    artist = re.sub(r"\s*VEVO$", "", artist, flags=re.IGNORECASE)
    artist = re.sub(r"\s*\(.*?\)\s*$", "", artist)
    artist = artist.strip()
    return artist


import re


def clean_lyrics_text(lyrics_text):
    """
    Clean raw lyrics by stripping section headers, timestamps,
    translations, and transliterations before analysis.
    This is the comprehensive version used across the application.
    """
    if not lyrics_text:
        return ""

    lines = lyrics_text.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Skip section headers like [Verse 1], [Chorus], [Hook], [Bridge], etc.
        if re.match(
            r"^\[(?:Verse|Chorus|Hook|Bridge|Intro|Outro|Pre-Chorus|Refrain|Interlude|Instrumental|Solo|Break|Skit|Spoken|Ad[- ]?lib)\s*\d*\]$",
            stripped,
            re.IGNORECASE,
        ):
            continue

        # Skip LRC timestamps like [00:32.14]
        stripped = re.sub(r"\[\d{1,2}:\d{2}(?:\.\d{2,3})?\]", "", stripped).strip()

        # Skip metadata lines like [ar:Artist], [ti:Title], etc.
        if re.match(r"^\[(?:ar|ti|al|by|offset):", stripped, re.IGNORECASE):
            continue

        # Skip translation markers
        if re.match(
            r"^\((?:Translation|Romanization|Romaji|English|Japanese)\s*:?\s*\)",
            stripped,
            re.IGNORECASE,
        ):
            continue

        # Skip lines that are just credits or metadata
        if re.match(
            r"^(?:Written by|Produced by|Lyrics by|Composed by|Music by)",
            stripped,
            re.IGNORECASE,
        ):
            continue

        # Skip very short lines (ad-libs, sound effects)
        if len(stripped) < 5:
            continue

        if stripped:
            cleaned.append(stripped)

    return "\n".join(cleaned)


def _clean_lrc(content):
    """Legacy alias for clean_lyrics_text - removes timestamps like [00:12.34] from LRC content."""
    return clean_lyrics_text(content)


def _get_mp3_lyrics(filepath):
    try:
        audio = ID3(filepath)
        uslt_keys = [key for key in audio.keys() if key.startswith("USLT")]
        if uslt_keys:
            return audio[uslt_keys[0]].text
    except mutagen.id3.ID3NoHeaderError:
        pass
    except Exception:
        pass
    return None


def _get_flac_lyrics(filepath):
    try:
        audio = FLAC(filepath)
        if "LYRICS" in audio:
            return audio["LYRICS"][0]
        if "UNSYNCEDLYRICS" in audio:
            return audio["UNSYNCEDLYRICS"][0]
    except Exception:
        pass
    return None


def _get_m4a_lyrics(filepath):
    try:
        audio = MP4(filepath)
        if "©lyr" in audio:
            return audio["©lyr"][0]
    except Exception:
        pass
    return None


def get_cache_stats():
    """Returns stats about the lyrics cache."""
    if not os.path.exists(config.LYRICS_CACHE_DIR):
        return {"count": 0, "size_mb": 0}

    files = [f for f in os.listdir(config.LYRICS_CACHE_DIR) if f.endswith(".txt")]
    total_size = sum(
        os.path.getsize(os.path.join(config.LYRICS_CACHE_DIR, f)) for f in files
    )

    return {"count": len(files), "size_mb": round(total_size / (1024 * 1024), 2)}


def get_lyrics_for_song(song_id, allow_online=False):
    """
    Retrieve lyrics for a song by its database ID.

    Priority:
    1. Database lyrics_text column (from previous scan)
    2. Filesystem cache + sidecar + embedded (via get_lyrics)

    Args:
        song_id: The database ID of the song.
        allow_online: Whether to fetch lyrics online if not found locally.

    Returns:
        str: Lyrics text or None if not found.
    """
    import database

    song = database.get_song_by_id(song_id)
    if song is None:
        return None

    lyrics_text = song["lyrics_text"] if "lyrics_text" in song.keys() else None
    if lyrics_text:
        return lyrics_text

    filepath = song["filepath"]
    title = song["title"] or "Unknown"
    artist = song["artist"] or "Unknown"

    lyrics = get_lyrics(filepath, title=title, artist=artist, allow_online=allow_online)

    if lyrics:
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE songs SET lyrics_text = ? WHERE id = ?",
                (lyrics, song_id),
            )
            conn.commit()
        except Exception:
            pass

    return lyrics

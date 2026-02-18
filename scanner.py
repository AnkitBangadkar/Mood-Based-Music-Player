"""
v8 Scanner - With incremental scanning and lyrics caching.
Only processes new/modified files, skips unchanged ones.
"""

import os
import json
import re
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
import database
import engine
import analyzer
import lyrics_extractor
from lyrics_extractor import clean_lyrics_text
import sentiment
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from logger import get_logger
import config

log = get_logger("Scanner")

SUPPORTED_EXTS = {".mp3", ".flac", ".wav", ".m4a", ".ogg"}


def clean_title_for_embedding(title):
    """
    Clean song title for embedding by removing noise while keeping useful info.

    Removes:
    - Leading track numbers (e.g., "01. ", "2 - ", "03 ")
    - Bracketed/parenthetical metadata (e.g., "(Live)", "[Remix]")
    - Common audio quality tags (e.g., "(Official Audio)", "[HQ]")

    Preserves:
    - Featured artists (feat./ft./featuring)
    - Version indicators that might affect mood (Acoustic, Remix sometimes)
    - Actual song title content
    """
    if not title:
        return ""

    import re

    # Remove leading track numbers (various formats)
    # Matches: "01. Title", "2 - Title", "03 Title", "1) Title"
    title = re.sub(r"^(\d+[\.\)\-\s]+)\s*", "", title.strip())

    # Remove common metadata tags in parentheses/brackets
    # These are usually audio quality/source indicators, not mood-relevant
    metadata_patterns = [
        r"\s*\(\s*(?:Official\s*)?(?:Audio|Video|Lyrics?|Visual|Visualizer)\s*\)",
        r"\s*\[\s*(?:Official\s*)?(?:Audio|Video|Lyrics?|Visual|Visualizer)\s*\]",
        r"\s*\(\s*(?:HD|HQ|High\s*Quality|4K|1080p)\s*\)",
        r"\s*\[\s*(?:HD|HQ|High\s*Quality|4K|1080p)\s*\]",
        r'\s*\(\s*(?:From\s+"[^"]+"|From\s+[^)]+)\s*\)',  # "(From Movie Name)"
        r'\s*\[\s*(?:From\s+"[^"]+"|From\s+[^\]]+)\s*\]',
    ]

    for pattern in metadata_patterns:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE)

    # Clean up multiple spaces
    title = re.sub(r"\s+", " ", title).strip()

    return title


def get_optimal_workers():
    """Calculate optimal workers based on logical CPU cores.

    Uses half the logical cores to leave headroom for:
    - Database operations
    - Embedding generation
    - Web server threads
    - OS background tasks
    """
    logical_cores = os.cpu_count() or 4
    workers = max(2, logical_cores // 2)
    return workers


def get_optimal_batch_size(workers):
    """Calculate batch size as 4x workers to keep workers fed."""
    return workers * 4


# Dynamic configuration based on hardware
MAX_WORKERS = get_optimal_workers()
BATCH_SIZE = get_optimal_batch_size(MAX_WORKERS)

log.info(
    f"Scanner configured: {MAX_WORKERS} workers, batch size {BATCH_SIZE} (detected {os.cpu_count()} logical cores)"
)


def get_metadata(filepath):
    """Extracts basic metadata."""
    title = None
    artist = None
    album = None
    genre = None

    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".mp3":
            try:
                audio = EasyID3(filepath)
            except mutagen.MutagenError:
                audio = mutagen.File(filepath, easy=True)
        else:
            audio = mutagen.File(filepath, easy=True)

        if audio:
            title = audio.get("title", [None])[0]
            artist = audio.get("artist", [None])[0]
            album = audio.get("album", [None])[0]
            genre = audio.get("genre", [None])[0]

    except Exception as e:
        log.warning(f"Metadata error for {filepath}: {e}")

    if not title:
        title = os.path.splitext(os.path.basename(filepath))[0]
    if not artist:
        artist = "Unknown Artist"
    if not album:
        album = "Unknown Album"
    if not genre:
        genre = ""

    return title, artist, album, genre


def extract_lyrics_snippet(lyrics_text, max_length=600):
    """
    Extract the most emotionally relevant portion of lyrics.
    Prefers repeated lines (likely chorus) and skips short ad-libs.
    Increased from 400 to 600 chars for better context.
    Weights lines by position (chorus is usually 40-60% into the song).
    """
    if not lyrics_text or len(lyrics_text.strip()) < 20:
        return ""

    # Clean lyrics first
    cleaned = clean_lyrics_text(lyrics_text)
    if not cleaned or len(cleaned.strip()) < 20:
        return ""

    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

    if not lines:
        return cleaned[:max_length]

    meaningful_lines = [l for l in lines if len(l) > 8]

    if meaningful_lines:
        line_counts = Counter(meaningful_lines)
        repeated = [line for line, count in line_counts.items() if count > 1]

        if repeated:
            # Prefer repeated lines from the middle of the song (chorus region)
            total_lines = len(meaningful_lines)

            def chorus_weight(line):
                """Weight lines by their position - favor middle of song."""
                positions = [i for i, l in enumerate(meaningful_lines) if l == line]
                # Average normalized position (0-1)
                avg_pos = sum(p / total_lines for p in positions) / len(positions)
                # Weight: highest at 0.4-0.6 (chorus region)
                center_dist = abs(avg_pos - 0.5)
                return 1.0 - center_dist

            repeated.sort(key=chorus_weight, reverse=True)
            snippet = " ".join(repeated[:5])
            if len(snippet) > max_length:
                snippet = snippet[:max_length]
            return snippet

    # Fall back to lines from the middle of the song (more likely chorus)
    mid = len(meaningful_lines) // 2
    start = max(0, mid - 2)
    end = min(len(meaningful_lines), mid + 3)
    return " ".join(meaningful_lines[start:end])[:max_length]


def build_mood_text(
    title,
    artist,
    genre,
    bpm,
    energy,
    brightness,
    valence,
    mode,
    arousal,
    lyrics_snippet,
    lyrics_emotion_result=None,
    key_confidence=0.5,
    harmonic_ratio=0.0,
    dynamic_range=0.0,
):
    """
    Creates a compact, keyword-dense mood description for embedding.
    Uses 2D valence-arousal quadrants for coherent mood keywords,
    preventing contradictory labels (e.g. "sad" + "upbeat" on same song).

    Quadrants:
      High arousal + High valence → energetic, upbeat, powerful
      High arousal + Low valence  → intense, dark, aggressive
      Low arousal  + High valence → calm, peaceful, gentle
      Low arousal  + Low valence  → sad, melancholic, somber
    """
    mood_words = []
    t = config.MOOD_THRESHOLDS

    # === 2D Valence-Arousal Quadrant System ===
    high_arousal = arousal > 0.55
    low_arousal = arousal < 0.45
    high_valence = valence > 0.1
    low_valence = valence < -0.1

    if high_arousal and high_valence:
        mood_words.extend(["energetic", "upbeat", "powerful", "lively"])
    elif high_arousal and low_valence:
        mood_words.extend(["intense", "dark", "aggressive", "fierce"])
    elif low_arousal and high_valence:
        mood_words.extend(["calm", "peaceful", "gentle", "serene"])
    elif low_arousal and low_valence:
        mood_words.extend(["sad", "melancholic", "somber", "mournful"])
    elif high_arousal:
        mood_words.extend(["driving", "energetic"])
    elif low_arousal:
        mood_words.extend(["relaxed", "mellow"])
    elif high_valence:
        mood_words.extend(["positive", "cheerful"])
    elif low_valence:
        mood_words.extend(["reflective", "contemplative"])
    else:
        mood_words.extend(["moderate", "steady"])

    # Dynamic range contribution (LOG-SCALED values): dramatic swells vs flat/ambient
    # log1p scale: ~0.7 = flat/compressed, ~2.8+ = dramatic swells
    if dynamic_range > 2.8:
        mood_words.extend(["dramatic", "cinematic", "epic"])
    elif dynamic_range < 1.2:
        mood_words.extend(["ambient", "steady", "uniform"])

    # Lyrics emotion words (additive, from sentiment analysis)
    if lyrics_emotion_result and lyrics_emotion_result.get("mood_words"):
        mood_words.extend(lyrics_emotion_result["mood_words"])

    # Mode contribution: only add bright/dark if key detection is confident
    if key_confidence >= 0.65:
        if mode == "major":
            mood_words.append("bright")
        elif mode == "minor":
            mood_words.append("dark")

    # Harmonic ratio: melodic vs percussive character
    if harmonic_ratio > 0.85:
        mood_words.extend(["melodic", "smooth"])
    elif harmonic_ratio < 0.55:
        mood_words.extend(["percussive", "rhythmic"])

    if bpm > 0:
        if bpm >= t["bpm_fast"]:
            mood_words.append("fast")
        elif bpm <= t["bpm_slow"]:
            mood_words.append("slow")

    if brightness > 0:
        if brightness >= t["brightness_bright"]:
            mood_words.append("sharp")
        elif brightness <= t["brightness_dark"]:
            mood_words.append("deep")

    unique_moods = list(dict.fromkeys(mood_words))[:10]
    mood_str = ", ".join(unique_moods) if unique_moods else "neutral"

    tempo_str = f"{bpm:.0f} BPM" if bpm > 0 else ""
    mode_str = f"{mode} key" if mode else ""
    features = [s for s in [tempo_str, mode_str] if s]
    feature_str = ". ".join(features) + "." if features else ""

    # Clean title for embedding (remove track numbers, metadata tags)
    # Use only title (not artist) to avoid false matches from artist names
    cleaned_title = clean_title_for_embedding(title)
    meta = cleaned_title

    lyrics_part = ""
    if lyrics_snippet and len(lyrics_snippet) > 20:
        clean = lyrics_snippet.replace("\n", " ").strip()[:400]
        lyrics_part = f" Lyrics: {clean}..."

    description = f"{mood_str}. {feature_str} {meta}{lyrics_part}"

    return description


def process_file(filepath, enable_audio, enable_lyrics, enable_online_lyrics):
    """Worker function to process a single file."""
    import logging

    thread_log = logging.getLogger("MoodPlaylist.Scanner.Worker")

    try:
        # Get file modification time for incremental scanning
        file_mtime = os.path.getmtime(filepath)

        # Metadata
        try:
            title, artist, album, genre = get_metadata(filepath)
        except Exception as e:
            thread_log.error(f"Failed at METADATA for {filepath}: {e}")
            return None

        # Audio Analysis (now with valence/mode/arousal)
        # Use 30s duration for faster processing - first 30s captures main theme/energy
        bpm = 0.0
        energy = 0.0
        brightness = 0.0
        valence = 0.0
        arousal = 0.0
        mode = ""
        key_confidence = 0.5
        harmonic_ratio = 0.0
        spectral_rolloff = 0.0
        spectral_bandwidth = 0.0
        dynamic_range = 0.0
        mfccs = None

        if enable_audio:
            try:
                audio_stats = analyzer.analyze_track(filepath, duration=60, offset=10)
                if audio_stats:
                    bpm = audio_stats["bpm"]
                    energy = audio_stats["energy"]
                    brightness = audio_stats["brightness"]
                    valence = audio_stats.get("valence", 0.0)
                    arousal = audio_stats.get("arousal", 0.0)
                    mode = audio_stats.get("mode", "")
                    key_confidence = audio_stats.get("key_confidence", 0.5)
                    harmonic_ratio = audio_stats.get("harmonic_ratio", 0.0)
                    spectral_rolloff = audio_stats.get("spectral_rolloff", 0.0)
                    spectral_bandwidth = audio_stats.get("spectral_bandwidth", 0.0)
                    dynamic_range = audio_stats.get("dynamic_range", 0.0)
                    mfccs = audio_stats.get("mfccs", None)
            except Exception as e:
                thread_log.error(f"Failed at AUDIO for {filepath}: {e}")

        # Lyrics (with caching and emotion analysis)
        lyrics_snippet = ""
        has_lyrics = False
        lyrics_emotion_result = None
        lyrics_emotion = None
        lyrics_emotion_score = 0.0

        if enable_lyrics:
            try:
                lyrics = lyrics_extractor.get_lyrics(
                    filepath,
                    title=title,
                    artist=artist,
                    allow_online=enable_online_lyrics,
                )
                if lyrics:
                    has_lyrics = True
                    # Clean lyrics before analysis
                    cleaned_lyrics = clean_lyrics_text(lyrics)
                    # Smart lyrics extraction with increased limit
                    lyrics_snippet = extract_lyrics_snippet(lyrics, max_length=600)
                    # Run emotion analysis on cleaned full lyrics
                    lyrics_emotion_result = sentiment.analyze_lyrics(
                        cleaned_lyrics or lyrics
                    )
                    if lyrics_emotion_result and lyrics_emotion_result.get("emotion"):
                        lyrics_emotion = lyrics_emotion_result["emotion"]
                        lyrics_emotion_score = lyrics_emotion_result.get("score", 0.0)
                        # Blend valence: audio + lyrics emotion (lyrics weighted more)
                        audio_valence = valence
                        emotion_valence = lyrics_emotion_result.get("valence", 0.0)
                        if emotion_valence != 0:
                            valence = 0.4 * audio_valence + 0.6 * emotion_valence
                            thread_log.info(
                                f"Blended valence: audio={audio_valence:.2f}, lyrics={emotion_valence:.2f} -> {valence:.2f}"
                            )
            except Exception as e:
                thread_log.error(f"Failed at LYRICS for {filepath}: {e}")

        # Build mood-aware text with valence/mode + lyrics emotion
        mood_text = build_mood_text(
            title,
            artist,
            genre,
            bpm,
            energy,
            brightness,
            valence,
            mode,
            arousal,
            lyrics_snippet,
            lyrics_emotion_result,
            key_confidence=key_confidence,
            harmonic_ratio=harmonic_ratio,
            dynamic_range=dynamic_range,
        )

        return {
            "filepath": filepath,
            "file_mtime": file_mtime,
            "title": title,
            "artist": artist,
            "album": album,
            "genre": genre,
            "mood_text": mood_text,
            "bpm": bpm,
            "energy": energy,
            "brightness": brightness,
            "valence": valence,
            "arousal": arousal,
            "mode": mode,
            "has_lyrics": has_lyrics,
            "lyrics_emotion": lyrics_emotion,
            "lyrics_emotion_score": lyrics_emotion_score,
            "emotion_distribution": json.dumps(
                lyrics_emotion_result.get("emotion_distribution", {})
            )
            if lyrics_emotion_result
            else None,
            "spectral_rolloff": spectral_rolloff,
            "spectral_bandwidth": spectral_bandwidth,
            "dynamic_range": dynamic_range,
            "mfccs": json.dumps(mfccs) if mfccs else None,
        }

    except Exception as e:
        thread_log.error(f"CRITICAL WORKER FAILURE: {e}")
        return None


def scan_library(
    directory_path,
    enable_audio=True,
    enable_lyrics=True,
    enable_online_lyrics=False,
    force_rescan=False,
    progress_callback=None,
    preserve_existing=True,
):
    """
    Incremental scan - only processes new or modified files.

    Args:
        force_rescan: If True, clears DB and rescans everything.
        progress_callback: Optional callback function called with progress dict:
            {
                "current": int,      # Current file number
                "total": int,       # Total files to process
                "current_file": str, # Current file name
                "stage": str,       # "scanning", "embedding", "clap", "complete"
            }
        preserve_existing: If True, don't delete songs from other folders when
                          scanning a different directory. Allows adding multiple
                          music folders without losing previous scans.
    """
    start_time = time.time()
    log.info(f"Starting scan: {directory_path}")

    database.init_db()

    # Get existing songs for incremental scanning
    existing_songs = {} if force_rescan else database.get_existing_songs()

    if force_rescan:
        database.clear_library()
        log.info("Force rescan: Cleared existing library.")

    # Find all audio files
    all_files = set()
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if os.path.splitext(file)[1].lower() in SUPPORTED_EXTS:
                all_files.add(os.path.join(root, file))

    # Determine which files need processing
    files_to_scan = []
    skipped = 0

    for filepath in all_files:
        if filepath in existing_songs:
            existing_id, existing_mtime = existing_songs[filepath]
            current_mtime = os.path.getmtime(filepath)

            # Skip if file hasn't been modified
            if existing_mtime and abs(current_mtime - existing_mtime) < 1.0:
                skipped += 1
                continue

        files_to_scan.append(filepath)

    # Find deleted files (in DB but not on disk)
    # Only delete files that were in the current directory scope
    deleted_ids = []
    if not preserve_existing:
        # Original behavior: delete anything not in current scan
        for filepath, (song_id, _) in existing_songs.items():
            if filepath not in all_files:
                deleted_ids.append(song_id)
    else:
        # New behavior: only delete files that were in this directory but are now gone
        # This allows scanning multiple different folders without losing data
        abs_directory = os.path.abspath(directory_path)
        for filepath, (song_id, _) in existing_songs.items():
            # Only consider deleting if file was in the current scan directory
            if filepath.startswith(abs_directory) and filepath not in all_files:
                deleted_ids.append(song_id)

    if deleted_ids:
        database.delete_songs_by_ids(deleted_ids)

    log.info(
        f"Found {len(all_files)} audio files. New/modified: {len(files_to_scan)}, Skipped: {skipped}, "
        f"Deleted: {len(deleted_ids)} (preserve_existing={preserve_existing})"
    )

    existing_song_count = database.get_song_count()

    # Report initial progress
    if progress_callback:
        progress_callback(
            {
                "current": 0,
                "total": len(files_to_scan),
                "current_file": "Starting scan...",
                "stage": "scanning",
                "indexed_songs": existing_song_count,
            }
        )

    if not files_to_scan:
        log.info("No new files to process. Scan complete.")
        # Just load the existing index - no need to rebuild
        eng = engine.get_engine()
        eng.load_index()
        return database.get_song_count()

    eng = engine.get_engine()
    all_ids = []
    all_embeddings = []

    batch_data = []
    count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                process_file, f, enable_audio, enable_lyrics, enable_online_lyrics
            ): f
            for f in files_to_scan
        }

        for future in as_completed(futures):
            res = future.result()
            if res:
                batch_data.append(res)

                if len(batch_data) >= BATCH_SIZE:
                    _process_batch(batch_data, all_ids, all_embeddings, eng)
                    count += len(batch_data)
                    log.info(f"Progress: {count}/{len(files_to_scan)} new files...")
                    if progress_callback:
                        current_indexed = existing_song_count + count
                        progress_callback(
                            {
                                "current": count,
                                "total": len(files_to_scan),
                                "current_file": res.get("filepath", "").split("/")[-1][
                                    :50
                                ],
                                "stage": "scanning",
                                "indexed_songs": current_indexed,
                            }
                        )
                    batch_data = []

    if batch_data:
        _process_batch(batch_data, all_ids, all_embeddings, eng)
        count += len(batch_data)

    # Rebuild the full index including existing songs
    if progress_callback:
        current_indexed = existing_song_count + count
        progress_callback(
            {
                "current": count,
                "total": len(files_to_scan),
                "current_file": "Rebuilding embeddings...",
                "stage": "embedding",
                "indexed_songs": current_indexed,
            }
        )
    _rebuild_index_from_db()

    elapsed_time = time.time() - start_time
    total_songs = database.get_song_count()
    log.info(
        f"Scan complete. {count} new songs processed, {total_songs} total indexed in {elapsed_time:.2f}s."
    )

    # Log lyrics cache stats
    cache_stats = lyrics_extractor.get_cache_stats()
    log.info(f"Lyrics cache: {cache_stats['count']} files, {cache_stats['size_mb']} MB")

    # Track this folder as scanned
    database.add_or_update_scanned_folder(directory_path, song_count=count)

    if progress_callback:
        progress_callback(
            {
                "current": total_songs,
                "total": total_songs,
                "current_file": "Scan complete!",
                "stage": "complete",
                "indexed_songs": total_songs,
            }
        )

    return total_songs


def _rebuild_index_from_db():
    """Rebuild the vector index from all songs in the database.

    Uses stored embeddings when available, only encodes new songs.
    This makes incremental scans much faster.
    """
    import numpy as np

    eng = engine.get_engine()

    # Get songs with embeddings from DB
    songs_with_embeddings = database.get_all_songs_with_embeddings()

    if not songs_with_embeddings:
        return

    ids = []
    embeddings_list = []
    songs_to_encode = []  # Songs without embeddings

    for song in songs_with_embeddings:
        ids.append(song["id"])
        if song.get("embedding") is not None:
            # Use stored embedding
            embeddings_list.append(song["embedding"])
        else:
            # Need to encode this song
            songs_to_encode.append(song)

    # Encode any songs that don't have stored embeddings
    if songs_to_encode:
        log.info(f"Encoding {len(songs_to_encode)} songs without stored embeddings...")
        texts = [s["rich_description"] for s in songs_to_encode]
        new_embeddings = eng.encode(texts, is_query=False)

        # Store new embeddings and add to list
        for i, song in enumerate(songs_to_encode):
            database.update_song_embedding(song["id"], new_embeddings[i])
            # Insert embedding at correct position
            idx = ids.index(song["id"])
            embeddings_list.insert(idx, new_embeddings[i])

    # Convert to numpy array
    embeddings = np.array(embeddings_list)

    # Set in-memory state BEFORE saving
    eng.embeddings = embeddings
    eng.ids = ids
    eng.save_index()


def _process_batch(batch, all_ids, all_embeddings, eng):
    """Process a batch of songs - embed and store."""
    texts = [d["mood_text"] for d in batch]
    embeddings = eng.encode(texts, is_query=False)

    for i, d in enumerate(batch):
        song_id = database.add_song(
            d["filepath"],
            d["title"],
            d["artist"],
            d["album"],
            d["genre"],
            d["mood_text"],
            bpm=d["bpm"],
            energy=d["energy"],
            brightness=d["brightness"],
            valence=d.get("valence", 0.0),
            arousal=d.get("arousal", 0.0),
            mode=d.get("mode", ""),
            sentiment=0.0,
            has_lyrics=d["has_lyrics"],
            lyrics_vec=None,
            audio_vec=None,
            meta_vec=None,
            file_mtime=d["file_mtime"],
            lyrics_emotion=d.get("lyrics_emotion"),
            lyrics_emotion_score=d.get("lyrics_emotion_score", 0.0),
            emotion_distribution=d.get("emotion_distribution"),
            spectral_rolloff=d.get("spectral_rolloff"),
            spectral_bandwidth=d.get("spectral_bandwidth"),
            dynamic_range=d.get("dynamic_range"),
            mfccs=d.get("mfccs"),
        )
        if song_id:
            all_ids.append(song_id)
            all_embeddings.append(embeddings[i])
            # Store embedding in database for incremental indexing
            database.update_song_embedding(song_id, embeddings[i])

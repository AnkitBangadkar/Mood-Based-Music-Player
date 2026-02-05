"""
v8 Scanner - With incremental scanning and lyrics caching.
Only processes new/modified files, skips unchanged ones.
"""
import os
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
import database
import engine
import analyzer
import lyrics_extractor
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from logger import get_logger
import config

log = get_logger("Scanner")

SUPPORTED_EXTS = {'.mp3', '.flac', '.wav', '.m4a', '.ogg'}
MAX_WORKERS = 8


def get_metadata(filepath):
    """Extracts basic metadata."""
    title = None
    artist = None
    album = None
    genre = None
    
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == '.mp3':
            try:
                audio = EasyID3(filepath)
            except mutagen.MutagenError:
                audio = mutagen.File(filepath, easy=True)
        else:
            audio = mutagen.File(filepath, easy=True)
            
        if audio:
            title = audio.get('title', [None])[0]
            artist = audio.get('artist', [None])[0]
            album = audio.get('album', [None])[0]
            genre = audio.get('genre', [None])[0]
            
    except Exception as e:
        log.warning(f"Metadata error for {filepath}: {e}")

    if not title: title = os.path.splitext(os.path.basename(filepath))[0]
    if not artist: artist = "Unknown Artist"
    if not album: album = "Unknown Album"
    if not genre: genre = ""
        
    return title, artist, album, genre


def build_mood_text(title, artist, genre, bpm, energy, brightness, valence, mode, arousal, lyrics_snippet):
    """
    Creates a rich, mood-aware description for embedding.
    Now uses valence and mode for more accurate mood representation.
    """
    parts = []
    mood_words = []
    
    # === VALENCE-BASED MOOD (Most Important!) ===
    if valence > 0.3:
        mood_words.extend(['happy', 'joyful', 'uplifting'])
    elif valence > 0.1:
        mood_words.extend(['positive', 'cheerful'])
    elif valence < -0.3:
        mood_words.extend(['sad', 'melancholic', 'somber'])
    elif valence < -0.1:
        mood_words.extend(['reflective', 'contemplative'])
    
    # === MODE (Major/Minor) ===
    if mode == 'major':
        mood_words.append('bright')
    elif mode == 'minor':
        mood_words.append('dark')
    
    # === AROUSAL/ENERGY ===
    if arousal > 0.7:
        mood_words.extend(['energetic', 'intense', 'powerful'])
    elif arousal > 0.5:
        mood_words.extend(['upbeat', 'driving'])
    elif arousal < 0.3:
        mood_words.extend(['calm', 'relaxed', 'peaceful'])
    
    # === TEMPO ===
    t = config.MOOD_THRESHOLDS
    if bpm > 0:
        if bpm >= t['bpm_fast']:
            mood_words.append('fast')
        elif bpm <= t['bpm_slow']:
            mood_words.append('slow')
    
    # === BRIGHTNESS ===
    if brightness > 0:
        if brightness >= t['brightness_bright']:
            mood_words.append('sharp')
        elif brightness <= t['brightness_dark']:
            mood_words.append('deep')
    
    # Build description
    if mood_words:
        unique_moods = list(dict.fromkeys(mood_words))[:5]  # Top 5 mood words
        parts.append(f"This is a {', '.join(unique_moods)} song")
    else:
        parts.append("This is a song")
    
    if bpm > 0:
        parts.append(f"with {bpm:.0f} BPM")
    
    if mode:
        parts.append(f"in {mode} key")
    
    if genre:
        parts.append(f"in the {genre} genre")
    
    parts.append(f"by {artist}")
    parts.append(f"called '{title}'")
    
    description = '. '.join([' '.join(parts)])
    
    if lyrics_snippet and len(lyrics_snippet) > 20:
        clean_lyrics = lyrics_snippet.replace('\n', ' ').strip()[:200]
        description += f". The lyrics include: {clean_lyrics}..."
    
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
        bpm = 0.0
        energy = 0.0
        brightness = 0.0
        valence = 0.0
        arousal = 0.0
        mode = ''
        
        if enable_audio:
            try:
                audio_stats = analyzer.analyze_track(filepath, duration=30) 
                if audio_stats:
                    bpm = audio_stats['bpm']
                    energy = audio_stats['energy']
                    brightness = audio_stats['brightness']
                    valence = audio_stats.get('valence', 0.0)
                    arousal = audio_stats.get('arousal', 0.0)
                    mode = audio_stats.get('mode', '')
            except Exception as e:
                thread_log.error(f"Failed at AUDIO for {filepath}: {e}")
        
        # Lyrics (with caching)
        lyrics_snippet = ""
        has_lyrics = False
        
        if enable_lyrics:
            try:
                lyrics = lyrics_extractor.get_lyrics(
                    filepath, 
                    title=title, 
                    artist=artist, 
                    allow_online=enable_online_lyrics
                )
                if lyrics:
                    has_lyrics = True
                    lyrics_snippet = lyrics[:500]
            except Exception as e:
                thread_log.error(f"Failed at LYRICS for {filepath}: {e}")

        # Build mood-aware text with valence/mode
        mood_text = build_mood_text(
            title, artist, genre, 
            bpm, energy, brightness,
            valence, mode, arousal,
            lyrics_snippet
        )
        
        return {
            'filepath': filepath,
            'file_mtime': file_mtime,
            'title': title,
            'artist': artist,
            'album': album,
            'genre': genre,
            'mood_text': mood_text,
            'bpm': bpm,
            'energy': energy,
            'brightness': brightness,
            'valence': valence,
            'arousal': arousal,
            'mode': mode,
            'has_lyrics': has_lyrics,
        }
    
    except Exception as e:
        thread_log.error(f"CRITICAL WORKER FAILURE: {e}")
        return None


def scan_library(directory_path, enable_audio=True, enable_lyrics=True, enable_online_lyrics=False, force_rescan=False):
    """
    Incremental scan - only processes new or modified files.
    
    Args:
        force_rescan: If True, clears DB and rescans everything.
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
    deleted_ids = []
    for filepath, (song_id, _) in existing_songs.items():
        if filepath not in all_files:
            deleted_ids.append(song_id)
    
    if deleted_ids:
        database.delete_songs_by_ids(deleted_ids)
    
    log.info(f"Found {len(all_files)} audio files. New/modified: {len(files_to_scan)}, Skipped: {skipped}, Deleted: {len(deleted_ids)}")
    
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
    BATCH_SIZE = 16
    count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_file, f, enable_audio, enable_lyrics, enable_online_lyrics): f 
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
                    batch_data = []

    if batch_data:
        _process_batch(batch_data, all_ids, all_embeddings, eng)
        count += len(batch_data)
    
    # Rebuild the full index including existing songs
    _rebuild_index_from_db()
        
    elapsed_time = time.time() - start_time
    total_songs = database.get_song_count()
    log.info(f"Scan complete. {count} new songs processed, {total_songs} total indexed in {elapsed_time:.2f}s.")
    
    # Log lyrics cache stats
    cache_stats = lyrics_extractor.get_cache_stats()
    log.info(f"Lyrics cache: {cache_stats['count']} files, {cache_stats['size_mb']} MB")
    
    return total_songs


def _rebuild_index_from_db():
    """Rebuild the vector index from all songs in the database."""
    eng = engine.get_engine()
    songs = database.get_all_songs()
    
    if not songs:
        return
    
    # Re-embed all songs (necessary because embeddings aren't stored in DB)
    texts = [s['rich_description'] for s in songs]
    embeddings = eng.encode(texts)
    ids = [s['id'] for s in songs]
    
    eng.save_index(ids, embeddings)
    
    # Update in-memory state so immediate queries work
    eng.embeddings = embeddings
    eng.ids = ids


def _process_batch(batch, all_ids, all_embeddings, eng):
    """Process a batch of songs - embed and store."""
    texts = [d['mood_text'] for d in batch]
    embeddings = eng.encode(texts)
    
    for i, d in enumerate(batch):
        song_id = database.add_song(
            d['filepath'], d['title'], d['artist'], d['album'], d['genre'],
            d['mood_text'],
            bpm=d['bpm'], energy=d['energy'], brightness=d['brightness'],
            valence=d.get('valence', 0.0), arousal=d.get('arousal', 0.0), mode=d.get('mode', ''),
            sentiment=0.0,
            has_lyrics=d['has_lyrics'],
            lyrics_vec=None, audio_vec=None, meta_vec=None,
            file_mtime=d['file_mtime']
        )
        if song_id:
            all_ids.append(song_id)
            all_embeddings.append(embeddings[i])

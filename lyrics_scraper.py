"""
Lyrics Scraper with multiple sources.
Priority: LRCLib (best for J-Pop) > Genius > OVH > Musixmatch
"""
import os
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from logger import get_logger

log = get_logger("LyricsScraper")

# API URLs
LRCLIB_API_URL = "https://lrclib.net/api/get"
GENIUS_SEARCH_URL = "https://genius.com/api/search/multi?q="
OVH_API_URL = "https://api.lyrics.ovh/v1/"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT = 10  # Longer timeout for reliability (LRCLib can be slow)

# Skip lyrics for these artist keywords (usually instrumental)
SKIP_ARTISTS = ['ost', 'soundtrack', 'instrumental', 'bgm', 'orchestra']


def fetch_lyrics(title, artist):
    """
    Attempts to fetch lyrics from multiple sources with fallback strategies.
    Returns None if lyrics can't be found or are low quality.
    """
    if not title:
        return None
    
    # Skip if artist suggests instrumental
    if artist and any(skip in artist.lower() for skip in SKIP_ARTISTS):
        log.info(f"Skipping lyrics for instrumental artist: {artist}")
        return None
    
    clean_title = _clean_text(title)
    clean_artist = _clean_text(artist) if artist else ""
    
    # Strategy 1: LRCLib (Best for J-Pop, Korean, multilingual)
    lyrics = _fetch_lrclib(clean_title, clean_artist)
    if lyrics and _is_valid_lyrics(lyrics):
        return lyrics

    # Strategy 2: Genius (Good for English, has some J-Pop)
    lyrics = _fetch_genius(clean_title, clean_artist)
    if lyrics and _is_valid_lyrics(lyrics):
        return lyrics

    # Strategy 3: OVH API (Fallback, often unreliable)
    lyrics = _fetch_ovh(clean_title, clean_artist)
    if lyrics and _is_valid_lyrics(lyrics):
        return lyrics

    # Strategy 4: Musixmatch API (Requires Key)
    lyrics = _fetch_musixmatch(clean_title, clean_artist)
    if lyrics and _is_valid_lyrics(lyrics):
        return lyrics

    # Strategy 5: Title Only (Genius) - for mislabeled artists
    if clean_artist:
        log.info(f"Retry: Searching with Title only: '{clean_title}'")
        lyrics = _fetch_genius(clean_title, "")
        if lyrics and _is_valid_lyrics(lyrics):
            return lyrics

    return None


def _is_valid_lyrics(text):
    """
    Basic quality filter to reject garbage lyrics.
    """
    if not text:
        return False
    
    # Too short - probably metadata or error
    if len(text) < 50:
        return False
    
    # Too few lines - probably not real lyrics
    lines = [l for l in text.split('\n') if l.strip()]
    if len(lines) < 3:
        return False
    
    # Check for garbage patterns (wrong song matches)
    garbage_patterns = [
        'lyrics not available',
        'we don\'t have the lyrics',
        'no lyrics found',
        'instrumental',
    ]
    text_lower = text.lower()[:200]
    if any(p in text_lower for p in garbage_patterns):
        return False
    
    return True


def _fetch_lrclib(title, artist):
    """
    LRCLib - Free, good for J-Pop, Korean, multilingual.
    Returns plain lyrics (strips LRC timestamps if present).
    """
    log.info(f"Searching LRCLib: '{title}' by '{artist}'")
    try:
        params = {
            'track_name': title,
            'artist_name': artist
        }
        response = requests.get(LRCLIB_API_URL, params=params, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            # Prefer plain lyrics over synced
            plain = data.get('plainLyrics', '')
            if plain and len(plain) > 20:
                return plain.strip()
            
            # Fall back to synced lyrics (strip timestamps)
            synced = data.get('syncedLyrics', '')
            if synced:
                return _strip_lrc_timestamps(synced)
                
    except Exception as e:
        log.warning(f"LRCLib fetch failed: {e}")
    
    return None


def _strip_lrc_timestamps(lrc_text):
    """Remove [00:12.34] timestamps from LRC format."""
    lines = []
    for line in lrc_text.split('\n'):
        # Skip metadata lines like [ar:Artist]
        if re.match(r'^\[(ar|ti|al|by|offset):.*\]', line, re.IGNORECASE):
            continue
        # Strip timestamp
        clean = re.sub(r'\[\d{2}:\d{2}\.\d{2,3}\]', '', line).strip()
        if clean:
            lines.append(clean)
    return '\n'.join(lines)


def _fetch_genius(title, artist):
    query = f"{title} {artist}".strip()
    log.info(f"Searching Genius: '{query}'")

    try:
        search_url = GENIUS_SEARCH_URL + urllib.parse.quote(query)
        headers = {"User-Agent": USER_AGENT}
        
        response = requests.get(search_url, headers=headers, timeout=TIMEOUT)
        if response.status_code != 200:
            return None
            
        data = response.json()
        
        hit_url = None
        for section in data.get('response', {}).get('sections', []):
            if section['type'] in ['top_hit', 'song']:
                for hit in section.get('hits', []):
                    if hit['type'] == 'song':
                        hit_url = hit['result']['path']
                        break
            if hit_url: break
        
        if not hit_url:
            return None
            
        full_url = "https://genius.com" + hit_url
        page_response = requests.get(full_url, headers=headers, timeout=TIMEOUT)
        soup = BeautifulSoup(page_response.text, 'html.parser')
        
        # Genius lyrics container
        lyrics_divs = soup.find_all("div", attrs={"data-lyrics-container": "true"})
        if lyrics_divs:
            return "\n".join([div.get_text(separator="\n") for div in lyrics_divs]).strip()
            
        # Old format fallback
        lyrics_div = soup.find("div", class_="lyrics")
        if lyrics_div:
            return lyrics_div.get_text(separator="\n").strip()
            
    except Exception as e:
        log.warning(f"Genius fetch failed for '{query}': {e}")
    
    return None


def _fetch_ovh(title, artist):
    if not artist:
        return None
    
    log.info(f"Searching OVH: '{title}' by '{artist}'")
    try:
        url = f"{OVH_API_URL}{urllib.parse.quote(artist)}/{urllib.parse.quote(title)}"
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if 'lyrics' in data and data['lyrics']:
                return data['lyrics'].strip()
    except Exception as e:
        log.warning(f"OVH fetch failed: {e}")
    
    return None


def _fetch_musixmatch(title, artist):
    api_key = os.getenv("MUSIXMATCH_API_KEY")
    if not api_key:
        return None
    
    log.info(f"Searching Musixmatch: '{title}' by '{artist}'")
    try:
        search_url = "https://api.musixmatch.com/ws/1.1/track.search"
        params = {
            "apikey": api_key,
            "q_track": title,
            "q_artist": artist,
            "page_size": 1,
            "s_track_rating": "desc"
        }
        response = requests.get(search_url, params=params, timeout=TIMEOUT)
        data = response.json()
        
        track_list = data.get("message", {}).get("body", {}).get("track_list", [])
        if not track_list:
            return None
            
        track_id = track_list[0]["track"]["track_id"]
        
        lyrics_url = "https://api.musixmatch.com/ws/1.1/track.lyrics.get"
        lyrics_params = {"apikey": api_key, "track_id": track_id}
        l_response = requests.get(lyrics_url, params=lyrics_params, timeout=TIMEOUT)
        l_data = l_response.json()
        
        lyrics_body = l_data.get("message", {}).get("body", {}).get("lyrics", {}).get("lyrics_body", "")
        if lyrics_body:
            # Remove the commercial use footer
            return lyrics_body.split("*******")[0].strip()
            
    except Exception as e:
        log.warning(f"Musixmatch fetch failed: {e}")
        
    return None


def _clean_text(text):
    """Aggressive cleaning of metadata."""
    if not text:
        return ""
    
    # Remove text in brackets
    text = re.sub(r'[\(\[].*?[\)\]]', '', text)
    
    # Remove specific keywords
    text = re.sub(r'(?i)\b(feat\.|ft\.|featuring|cv:|ost)\b.*', '', text)
    
    # Take first artist if multiple
    text = re.split(r'[;/&,]', text)[0]
    
    return text.strip()


if __name__ == "__main__":
    # Test with J-Pop
    print("Testing LRCLib (J-Pop):")
    print(fetch_lyrics("群青", "YOASOBI"))
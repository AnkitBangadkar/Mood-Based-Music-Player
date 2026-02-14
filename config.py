import os

# --- Hardware / Tier Configuration ---
SYSTEM_TIER = os.getenv("PBL_TIER", "normal")

# --- Model Settings ---
MODEL_EMBEDDING = "sentence-transformers/all-mpnet-base-v2"

# --- Feature Flags ---
ENABLE_QUERY_BOOSTING = True

# --- Lyrics Cache ---
# Store fetched lyrics in a separate folder to keep music folders clean
LYRICS_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "lyrics_cache"
)

# --- Mood Mapping Thresholds ---
MOOD_THRESHOLDS = {
    "bpm_slow": 85,
    "bpm_fast": 125,
    "energy_low": 0.12,
    "energy_high": 0.28,
    "brightness_dark": 1500,
    "brightness_bright": 3000,
}

# --- Query Boost Keywords ---
# Now includes valence and mode constraints for emotional matching
# Energy thresholds calibrated to actual range: min=0.054, mean=0.246, max=0.386
BOOST_KEYWORDS = {
    # === HAPPY / JOYFUL (Valence + BPM based — mode removed, 80% of GT happy songs are minor) ===
    "happy": {"min_valence": 0.0, "min_bpm": 100, "boost": 0.15},
    "joyful": {"min_valence": 0.0, "min_bpm": 105, "boost": 0.15},
    "cheerful": {"min_valence": 0.05, "boost": 0.12},
    "uplifting": {"min_valence": 0.0, "boost": 0.12},
    # === SAD / MELANCHOLIC (Valence + Mode based) ===
    "sad": {
        "max_valence": -0.1,
        "mode": "minor",
        "lyrics_emotion": "sadness",
        "boost": 0.15,
    },
    "melancholy": {"max_valence": -0.1, "mode": "minor", "max_bpm": 100, "boost": 0.15},
    "somber": {"max_valence": -0.15, "mode": "minor", "boost": 0.12},
    "heartbreak": {"max_valence": -0.1, "mode": "minor", "boost": 0.12},
    # === ENERGETIC / FAST ===
    "energetic": {"min_bpm": 120, "min_energy": 0.22, "boost": 0.12},
    "workout": {"min_bpm": 120, "min_energy": 0.22, "boost": 0.12},
    "fast": {"min_bpm": 120, "boost": 0.10},
    "upbeat": {"min_bpm": 110, "min_valence": 0.0, "boost": 0.10},
    "party": {"min_bpm": 115, "min_energy": 0.20, "min_valence": 0.0, "boost": 0.12},
    "dance": {"min_bpm": 115, "min_energy": 0.18, "boost": 0.10},
    "hype": {"min_bpm": 120, "min_energy": 0.25, "boost": 0.12},
    # === SLOW / CALM ===
    "slow": {"max_bpm": 90, "boost": 0.10},
    "calm": {"max_energy": 0.16, "max_bpm": 100, "boost": 0.10},
    "relaxing": {"max_bpm": 100, "max_energy": 0.16, "boost": 0.10},
    "chill": {"max_bpm": 105, "max_energy": 0.20, "boost": 0.10},
    "peaceful": {"max_bpm": 95, "max_energy": 0.14, "min_valence": -0.1, "boost": 0.12},
    "sleep": {"max_bpm": 80, "max_energy": 0.10, "boost": 0.12},
    "study": {"max_bpm": 100, "max_energy": 0.16, "boost": 0.10},
    # === EMOTIONAL (Various) ===
    "emotional": {"lyrics_emotion": "sadness", "boost": 0.10},
    "romantic": {"max_bpm": 115, "boost": 0.08},
    "love": {"max_bpm": 115, "boost": 0.05},
    "nostalgic": {"mode": "minor", "boost": 0.08},
    # === INTENSE / POWERFUL ===
    "intense": {"min_energy": 0.25, "lyrics_emotion": "anger", "boost": 0.10},
    "powerful": {"min_energy": 0.25, "boost": 0.10},
    "angry": {
        "min_energy": 0.22,
        "min_bpm": 110,
        "mode": "minor",
        "lyrics_emotion": "anger",
        "boost": 0.12,
    },
    "aggressive": {"min_energy": 0.25, "min_bpm": 120, "boost": 0.10},
    "epic": {"min_energy": 0.22, "boost": 0.10},
    # === DARK / MOODY ===
    "dark": {"mode": "minor", "max_brightness": 2000, "boost": 0.12},
    "moody": {"max_valence": 0.0, "max_brightness": 2200, "boost": 0.10},
    "mysterious": {"mode": "minor", "max_brightness": 2000, "boost": 0.10},
    # === BRIGHT / POSITIVE ===
    "bright": {"mode": "major", "min_brightness": 2500, "boost": 0.10},
    "positive": {"min_valence": 0.05, "mode": "major", "boost": 0.10},
    # === LYRICS EMOTION BOOSTS ===
    "joy": {"lyrics_emotion": "joy", "boost": 0.15},
    "fear": {"lyrics_emotion": "fear", "boost": 0.12},
}

# --- Paths ---
DB_PATH = "library.db"
EMBEDDINGS_PATH = "embeddings_v3.npy"
IDS_PATH = "ids_v3.json"

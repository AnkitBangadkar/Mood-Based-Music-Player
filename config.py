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
    "bpm_slow": 90,
    "bpm_fast": 120,
    "energy_low": 0.05,
    "energy_high": 0.12,
    "brightness_dark": 1500,
    "brightness_bright": 3000,
}

# --- Query Boost Keywords ---
# Now includes valence and mode constraints for emotional matching
BOOST_KEYWORDS = {
    # === HAPPY / JOYFUL (Valence + Mode based) ===
    "happy": {"min_valence": 0.1, "mode": "major", "min_bpm": 100, "boost": 0.15},
    "joyful": {"min_valence": 0.15, "mode": "major", "min_bpm": 105, "boost": 0.15},
    "cheerful": {"min_valence": 0.1, "mode": "major", "boost": 0.12},
    "uplifting": {"min_valence": 0.1, "mode": "major", "boost": 0.12},
    # === SAD / MELANCHOLIC (Valence + Mode based) ===
    "sad": {"max_valence": -0.1, "mode": "minor", "boost": 0.15},
    "melancholy": {"max_valence": -0.1, "mode": "minor", "max_bpm": 100, "boost": 0.15},
    "somber": {"max_valence": -0.15, "mode": "minor", "boost": 0.12},
    "heartbreak": {"max_valence": -0.1, "mode": "minor", "boost": 0.12},
    # === ENERGETIC / FAST ===
    "energetic": {"min_bpm": 120, "min_energy": 0.10, "boost": 0.12},
    "workout": {"min_bpm": 120, "min_energy": 0.10, "boost": 0.12},
    "fast": {"min_bpm": 120, "boost": 0.10},
    "upbeat": {"min_bpm": 110, "min_valence": 0.0, "boost": 0.10},
    "party": {"min_bpm": 115, "min_energy": 0.10, "min_valence": 0.0, "boost": 0.12},
    "dance": {"min_bpm": 115, "min_energy": 0.08, "boost": 0.10},
    "hype": {"min_bpm": 120, "min_energy": 0.12, "boost": 0.12},
    # === SLOW / CALM ===
    "slow": {"max_bpm": 90, "boost": 0.10},
    "calm": {"max_energy": 0.08, "max_bpm": 100, "boost": 0.10},
    "relaxing": {"max_bpm": 100, "max_energy": 0.08, "boost": 0.10},
    "chill": {"max_bpm": 105, "max_energy": 0.10, "boost": 0.10},
    "peaceful": {"max_bpm": 95, "max_energy": 0.07, "min_valence": -0.1, "boost": 0.12},
    "sleep": {"max_bpm": 80, "max_energy": 0.05, "boost": 0.12},
    "study": {"max_bpm": 100, "max_energy": 0.08, "boost": 0.10},
    # === EMOTIONAL (Various) ===
    "emotional": {"boost": 0.05},  # Very broad - rely on semantic
    "romantic": {"max_bpm": 115, "boost": 0.08},
    "love": {"max_bpm": 115, "boost": 0.05},
    "nostalgic": {"mode": "minor", "boost": 0.08},
    # === INTENSE / POWERFUL ===
    "intense": {"min_energy": 0.12, "boost": 0.10},
    "powerful": {"min_energy": 0.12, "boost": 0.10},
    "angry": {"min_energy": 0.10, "min_bpm": 110, "mode": "minor", "boost": 0.12},
    "aggressive": {"min_energy": 0.12, "min_bpm": 120, "boost": 0.10},
    "epic": {"min_energy": 0.10, "boost": 0.10},
    # === DARK / MOODY ===
    "dark": {"mode": "minor", "max_brightness": 2000, "boost": 0.12},
    "moody": {"max_valence": 0.0, "max_brightness": 2200, "boost": 0.10},
    "mysterious": {"mode": "minor", "max_brightness": 2000, "boost": 0.10},
    # === BRIGHT / POSITIVE ===
    "bright": {"mode": "major", "min_brightness": 2500, "boost": 0.10},
    "positive": {"min_valence": 0.05, "mode": "major", "boost": 0.10},
    # === LYRICS EMOTION BOOSTS ===
    "joy": {"lyrics_emotion": "joy", "boost": 0.15},
    "sad": {"lyrics_emotion": "sadness", "boost": 0.15},
    "angry": {"lyrics_emotion": "anger", "boost": 0.12},
    "fear": {"lyrics_emotion": "fear", "boost": 0.12},
    "intense": {"lyrics_emotion": "anger", "boost": 0.10},
    "emotional": {"lyrics_emotion": "sadness", "boost": 0.10},
}

# --- Paths ---
DB_PATH = "library.db"
EMBEDDINGS_PATH = "embeddings_v3.npy"
IDS_PATH = "ids_v3.json"

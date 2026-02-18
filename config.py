import os

# Base directory (where this script is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Hardware / Tier Configuration ---
SYSTEM_TIER = os.getenv("PBL_TIER", "normal")

# --- Model Settings ---
MODEL_EMBEDDING = "sentence-transformers/all-mpnet-base-v2"

# --- Lyrics Cache ---
LYRICS_CACHE_DIR = os.path.join(BASE_DIR, "lyrics_cache")

# --- Mood Mapping Thresholds ---
MOOD_THRESHOLDS = {
    "bpm_slow": 85,
    "bpm_fast": 125,
    "energy_low": 0.12,
    "energy_high": 0.28,
    "brightness_dark": 1500,
    "brightness_bright": 3000,
}

# --- Paths (absolute, relative to this script) ---
DB_PATH = os.path.join(BASE_DIR, "library.db")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "embeddings_v3.npy")
IDS_PATH = os.path.join(BASE_DIR, "ids_v3.json")

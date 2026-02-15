import os

# --- Hardware / Tier Configuration ---
SYSTEM_TIER = os.getenv("PBL_TIER", "normal")

# --- Model Settings ---
MODEL_EMBEDDING = "sentence-transformers/all-mpnet-base-v2"

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

# --- Paths ---
DB_PATH = "library.db"
EMBEDDINGS_PATH = "embeddings_v3.npy"
IDS_PATH = "ids_v3.json"

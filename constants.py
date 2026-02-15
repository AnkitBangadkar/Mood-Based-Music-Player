"""
Constants for the mood playlist engine.
All magic numbers and tuning parameters in one place.
"""

import numpy as np

# ──────────────────────────────────────────────────────────────────────
# WEIGHT CONFIGURATION
# ──────────────────────────────────────────────────────────────────────
W_SEMANTIC = 0.35  # Weight for semantic (embedding) similarity
W_FEATURES = 0.40  # Weight for audio feature matching
W_GENRE = 0.12  # Weight for genre matching
W_EMOTION = 0.13  # Weight for lyrics emotion matching

# ──────────────────────────────────────────────────────────────────────
# GAUSSIAN SIGMA VALUES (for feature matching)
# ──────────────────────────────────────────────────────────────────────
# Sigma controls how "picky" the matching is.
# Higher sigma = looser match, Lower sigma = stricter match

SIGMA_BPM = 25  # BPM matching strictness (BPM range ~60-200)
SIGMA_ENERGY = 0.12  # Energy matching (RMS range ~0.05-0.40)
SIGMA_BRIGHTNESS = 1000  # Spectral centroid matching (Hz range ~1000-4000)
SIGMA_AROUSAL = 0.25  # Arousal matching (0-1 range)
SIGMA_VALENCE = 0.5  # Valence matching (-1 to 1 scale)
SIGMA_DYNAMIC_RANGE = 1.0  # Dynamic range matching (log scale ~0.7-3.5)
SIGMA_SPECTRAL_ROLLOFF = 1500  # Spectral rolloff (Hz range ~1000-7500)
SIGMA_SPECTRAL_BANDWIDTH = 500  # Spectral bandwidth (Hz range ~800-3300)
SIGMA_MFCC = 20  # MFCC coefficient matching

# ──────────────────────────────────────────────────────────────────────
# SCORE THRESHOLDS & LIMITS
# ──────────────────────────────────────────────────────────────────────
MIN_SIMILARITY_THRESHOLD = 0.01  # Minimum similarity to consider
SCORE_NORMALIZATION_FLOOR = 0.05  # Floor for min-max normalization
NEGATION_PENALTY_SCALE = 0.15  # How much to penalize negated queries

# ──────────────────────────────────────────────────────────────────────
# AUDIO FEATURE RANGES (for reference/tuning)
# ──────────────────────────────────────────────────────────────────────
BPM_RANGE = (55, 200)  # Typical BPM range after octave correction
ENERGY_RANGE = (0.05, 0.40)  # RMS energy typical range
AROUSAL_RANGE = (0.0, 1.0)  # 0 = calm, 1 = excited
VALENCE_RANGE = (-1.0, 1.0)  # -1 = sad, +1 = happy
BRIGHTNESS_RANGE = (1000, 4000)  # Spectral centroid Hz
DYNAMIC_RANGE_LOG = (0.85, 3.5)  # Log-scaled dynamic range

# ──────────────────────────────────────────────────────────────────────
# KEY DETECTION
# ──────────────────────────────────────────────────────────────────────
KEY_CONFIDENCE_THRESHOLD = 0.65  # Minimum confidence to trust mode detection

# ──────────────────────────────────────────────────────────────────────
# SEMANTIC SEARCH
# ──────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-mpnet-base-v2"
COSINE_THRESHOLD = 0.3  # Minimum cosine similarity to consider relevant

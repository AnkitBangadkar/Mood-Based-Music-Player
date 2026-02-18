"""
Constants for the mood playlist engine.
All magic numbers and tuning parameters in one place.
"""

# ──────────────────────────────────────────────────────────────────────
# WEIGHT CONFIGURATION
# ──────────────────────────────────────────────────────────────────────
W_SEMANTIC = 0.35  # Weight for semantic (embedding) similarity
W_FEATURES = 0.40  # Weight for audio feature matching
W_GENRE = 0.12  # Weight for genre matching
W_EMOTION = 0.0  # Set to 0.0 since no lyrics in metadata - weight redistributes to semantic/features

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
TUNING_ESTIMATION_ENABLED = True  # Enable tuning estimation for non-A440 tracks
TUNING_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for tuning estimation

# ──────────────────────────────────────────────────────────────────────
# BPM & ENERGY THRESHOLDS (for octave correction and valence estimation)
# ──────────────────────────────────────────────────────────────────────
BPM_HIGH_THRESHOLD = 140  # BPM above this triggers octave-down correction
BPM_LOW_THRESHOLD = 55  # BPM below this triggers octave-up correction
ENERGY_OCTAVE_THRESHOLD = 0.22  # Energy threshold for BPM octave correction

# ──────────────────────────────────────────────────────────────────────
# VALENCE/AROUSAL ESTIMATION CONSTANTS
# ──────────────────────────────────────────────────────────────────────
VALENCE_MODE_MAX_WEIGHT = 0.3  # Maximum weight mode contributes to valence
VALENCE_TEMPO_REFERENCE = 100  # Reference BPM for tempo contribution
VALENCE_TEMPO_RANGE = 80  # BPM range for normalization
VALENCE_TEMPO_WEIGHT = 0.2  # Weight of tempo contribution
VALENCE_BRIGHTNESS_REFERENCE = 2000  # Hz reference for brightness
VALENCE_BRIGHTNESS_RANGE = 2000  # Hz range for normalization
VALENCE_BRIGHTNESS_WEIGHT = 0.15  # Weight of brightness contribution
VALENCE_CONTRAST_REFERENCE = 20  # Reference spectral contrast
VALENCE_CONTRAST_RANGE = 20  # Range for normalization
VALENCE_CONTRAST_WEIGHT = 0.1  # Weight of contrast contribution
VALENCE_ZCR_PENALTY_THRESHOLD = 0.15  # ZCR threshold for harshness penalty
VALENCE_ZCR_PENALTY = 0.05  # Penalty amount for high ZCR

AROUSAL_BPM_REFERENCE = 80  # Reference BPM for arousal (calm baseline)
AROUSAL_BPM_RANGE = 160  # BPM range for arousal calculation
AROUSAL_BPM_MIN_CLIP = -0.2  # Minimum arousal from BPM
AROUSAL_BPM_MAX_CLIP = 0.5  # Maximum arousal from BPM
AROUSAL_ENERGY_MIN = 0.05  # Minimum energy reference
AROUSAL_ENERGY_RANGE = 0.35  # Energy range for normalization
AROUSAL_ENERGY_WEIGHT = 0.3  # Weight of energy contribution

# ──────────────────────────────────────────────────────────────────────
# SEMANTIC SEARCH
# ──────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
COSINE_THRESHOLD = 0.3  # Minimum cosine similarity to consider relevant

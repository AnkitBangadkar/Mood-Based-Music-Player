"""
Constants for the mood playlist engine.
All magic numbers and tuning parameters in one place.

SIGMA TUNING PHILOSOPHY
========================
Sigma values control Gaussian similarity: closer = tighter match.

The previous sigmas were calibrated to feature *ranges* (e.g., BPM range
55-200, valence range -1 to 1), but that makes them far too permissive:
a song at valence +0.11 vs target -0.35 scored 65% match under sigma=0.5.

The correct approach is to calibrate sigma to the *perceptual JND* —
the smallest difference a human listener would actually notice:

  Feature          | Range     | JND    | Old σ  | Problem               | New σ
  -----------------|-----------|--------|--------|-----------------------|------
  Valence          | -1 to 1   | 0.15   | 0.50   | wrong-side matches    | 0.20
  Arousal          | 0 to 1    | 0.10   | 0.25   | 0.60 vs 0.82 = 0.68  | 0.14
  Energy (RMS)     | 0.05-0.40| 0.04   | 0.12   | 97% matches > 0.5   | 0.06
  BPM              | 55-200    | 10-15  | 25     | ±25 BPM is generous   | 15
  Brightness       | 1k-4k Hz  | 300 Hz | 1000   | timbre is discerning  | 400
  Dynamic Range    | 0.85-3.5  | 0.5    | 1.0    | 38% of range as 1σ    | 0.5
  Spectral Rolloff | 1k-7.5k   | 800 Hz | 1500   |                       | 800
  Spectral BW      | 800-3300  | 300 Hz | 500    |                       | 350
  MFCC             | coeff     | 5      | 20     | coefficients small    | 8

For Gaussian matching: at distance = 1σ, match = exp(-0.5) ≈ 0.61.
At distance = 2σ, match = exp(-2) ≈ 0.14. At 3σ, match ≈ 0.01.

With sigma=0.20 for valence:
  - Song valence +0.05 vs target -0.55 (opposite emotion): match = 0.01 ✓
  - Song valence -0.50 vs target -0.55 (close match):     match = 0.97 ✓
  - Song valence -0.30 vs target -0.55 (partial match):    match = 0.61 ✓

With sigma=0.14 for arousal:
  - Song arousal 0.40 vs target 0.82 (different energy):   match = 0.10 ✓
  - Song arousal 0.75 vs target 0.82 (close match):        match = 0.89 ✓
"""

# ──────────────────────────────────────────────────────────────────────
# SCORING WEIGHTS
# ──────────────────────────────────────────────────────────────────────
# Base weights for the ensemble scoring formula.
# Unused weights (e.g., genre/emotion inactive) are redistributed
# proportionally among active signals at query time.
W_SEMANTIC = 0.22  # BGE text-embedding cosine similarity
W_CLAP = 0.30  # CLAP audio-text alignment
W_FEATURES = 0.25  # Audio feature Gaussian profile matching
W_GENRE = 0.10  # Genre keyword matching
W_EMOTION = 0.13  # Lyrics emotion distribution matching

# ──────────────────────────────────────────────────────────────────────
# GAUSSIAN SIGMA VALUES
# ──────────────────────────────────────────────────────────────────────
# Calibrated to perceptual just-noticeable-differences (JND).
# See module docstring for the rationale behind each value.

SIGMA_BPM = 15  # ~10-15 BPM JND for casual listeners
SIGMA_ENERGY = 0.06  # RMS energy; stdev in pop library is ~0.047
SIGMA_BRIGHTNESS = 400  # Spectral centroid; timbral JND ~200-300 Hz
SIGMA_AROUSAL = 0.14  # Arousal 0-1; noticeable difference ~0.10
SIGMA_VALENCE = 0.20  # Valence -1 to 1; wrong-side must score ~0
SIGMA_DYNAMIC_RANGE = 0.5  # Log-scale dynamic range; JND ~0.5
SIGMA_SPECTRAL_ROLLOFF = 800  # Spectral rolloff in Hz; timbral discernment
SIGMA_SPECTRAL_BANDWIDTH = 350  # Spectral bandwidth in Hz
SIGMA_MFCC = 8  # MFCC coefficient matching; coeffs typically -10 to +10

# ──────────────────────────────────────────────────────────────────────────
# CONTRADICTION GATE
# ──────────────────────────────────────────────────────────────────────────
# When a song's feature value is on the WRONG SIDE of neutral from the
# target (e.g., positive valence for an "angry" query targeting negative
# valence), the Gaussian match is multiplied by this penalty factor.
# This prevents a song at valence +0.10 from scoring 65% match against
# a target of -0.55 — without it, generous sigmas make valence almost
# non-discriminative.
#
# Set to 1.0 to disable (pure Gaussian), 0.0 for hard rejection.
# 0.15 means wrong-side matches get only 15% of their Gaussian score.
VALENCE_CONTRADICTION_PENALTY = 0.15  # Wrong-side valence gets 15% of Gaussian score
AROUSAL_CONTRADICTION_PENALTY = 0.20  # Wrong-side arousal gets 20% of Gaussian score

# ──────────────────────────────────────────────────────────────────────
# SCORE THRESHOLDS & LIMITS
# ──────────────────────────────────────────────────────────────────────
MIN_SIMILARITY_THRESHOLD = 0.01  # Minimum similarity to consider
SCORE_NORMALIZATION_FLOOR = 0.08  # Floor for min-max normalization
NEGATION_PENALTY_SCALE = 0.20  # How much to penalize negated queries

# ──────────────────────────────────────────────────────────────────────
# AUDIO FEATURE RANGES (reference for tuning)
# ──────────────────────────────────────────────────────────────────────
BPM_RANGE = (55, 200)
ENERGY_RANGE = (0.05, 0.40)
AROUSAL_RANGE = (0.0, 1.0)
VALENCE_RANGE = (-1.0, 1.0)
BRIGHTNESS_RANGE = (1000, 4000)
DYNAMIC_RANGE_LOG = (0.85, 3.5)

# ──────────────────────────────────────────────────────────────────────
# KEY DETECTION
# ──────────────────────────────────────────────────────────────────────
KEY_CONFIDENCE_THRESHOLD = 0.65
TUNING_ESTIMATION_ENABLED = True
TUNING_CONFIDENCE_THRESHOLD = 0.5

# ──────────────────────────────────────────────────────────────────────
# BPM & ENERGY THRESHOLDS (octave correction)
# ──────────────────────────────────────────────────────────────────────
# BPM_HIGH_THRESHOLD: above this, if energy is LOW, the BPM is likely
# doubled by the detector and should be halved. 160 BPM is the threshold
# because many legitimate EDM/dance/pop songs are 128-155 BPM.
# Only genuinely extreme tempos (>160) with low energy should be corrected.
BPM_HIGH_THRESHOLD = 160
BPM_LOW_THRESHOLD = 55
ENERGY_OCTAVE_THRESHOLD = 0.18  # Lowered from 0.22 — pop library median is ~0.22

# ──────────────────────────────────────────────────────────────────────
# VALENCE / AROUSAL ESTIMATION
# ──────────────────────────────────────────────────────────────────────
# These constants govern how the analyzer converts raw audio features
# into valence and arousal values. They don't affect matching directly,
# but they determine the quality of the feature data.

VALENCE_MODE_MAX_WEIGHT = (
    0.30  # Mode contribution to valence (major=+0.30, minor=-0.30)
)
VALENCE_TEMPO_REFERENCE = 100  # Neutral BPM for valence estimation
VALENCE_TEMPO_RANGE = 100  # BPM range for valence normalization (widened from 80)
VALENCE_TEMPO_WEIGHT = 0.20  # Weight of tempo contribution to valence
VALENCE_BRIGHTNESS_REFERENCE = 2200  # Brightness midpoint (raised from 2000)
VALENCE_BRIGHTNESS_RANGE = 2000
VALENCE_BRIGHTNESS_WEIGHT = 0.15
VALENCE_CONTRAST_REFERENCE = 20
VALENCE_CONTRAST_RANGE = 20
VALENCE_CONTRAST_WEIGHT = 0.10
VALENCE_ZCR_PENALTY_THRESHOLD = 0.15
VALENCE_ZCR_PENALTY = 0.05

AROUSAL_BPM_REFERENCE = 80  # Calm baseline BPM for arousal estimation
AROUSAL_BPM_RANGE = 160  # BPM range for arousal normalization
AROUSAL_BPM_MIN_CLIP = -0.2  # Minimum arousal contribution from BPM
AROUSAL_BPM_MAX_CLIP = 0.5  # Maximum arousal contribution from BPM
AROUSAL_ENERGY_MIN = 0.05
AROUSAL_ENERGY_RANGE = 0.35
AROUSAL_ENERGY_WEIGHT = 0.30

# ──────────────────────────────────────────────────────────────────────
# SEMANTIC SEARCH
# ──────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
COSINE_THRESHOLD = 0.3

# ──────────────────────────────────────────────────────────────────────
# DYNAMIC WEIGHT BOOSTING
# ──────────────────────────────────────────────────────────────────────
# Emotion-dominant queries: boost emotion/CLAP weight, suppress features.
# Acoustic-dominant queries: boost feature weight, suppress emotion.
# Values are multipliers: 1.0 = no change, >1.0 = boost, <1.0 = suppress.
EMOTION_DOMINANT_QUERIES = {
    "angry",
    "sad",
    "happy",
    "romantic",
    "love",
    "heartbreak",
    "depressing",
    "melancholy",
    "moody",
    "bittersweet",
    "nostalgic",
}

ACOUSTIC_DOMINANT_QUERIES = {
    "epic",
    "cinematic",
    "dramatic",
    "bright",
    "calm",
    "chill",
    "relaxing",
    "intense",
    "sleep",
    "study",
}

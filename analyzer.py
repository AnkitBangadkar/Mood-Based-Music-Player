"""
Advanced Audio Analyzer - Music Theory Based Mood Detection

Implements research-backed audio feature extraction for mood/valence estimation.
All features are language-agnostic, working purely on audio signals.

Key references:
- Thayer's arousal-valence model of emotion
- Librosa audio feature extraction
- Musical mode theory (Major = happy tendency, Minor = sad tendency)
"""

import librosa
import numpy as np
import os
import warnings
from logger import get_logger
from constants import (
    KEY_CONFIDENCE_THRESHOLD,
    TUNING_ESTIMATION_ENABLED,
    TUNING_CONFIDENCE_THRESHOLD,
    BPM_HIGH_THRESHOLD,
    BPM_LOW_THRESHOLD,
    ENERGY_OCTAVE_THRESHOLD,
    VALENCE_MODE_MAX_WEIGHT,
    VALENCE_TEMPO_REFERENCE,
    VALENCE_TEMPO_RANGE,
    VALENCE_TEMPO_WEIGHT,
    VALENCE_BRIGHTNESS_REFERENCE,
    VALENCE_BRIGHTNESS_RANGE,
    VALENCE_BRIGHTNESS_WEIGHT,
    VALENCE_CONTRAST_REFERENCE,
    VALENCE_CONTRAST_RANGE,
    VALENCE_CONTRAST_WEIGHT,
    VALENCE_ZCR_PENALTY_THRESHOLD,
    VALENCE_ZCR_PENALTY,
    AROUSAL_BPM_REFERENCE,
    AROUSAL_BPM_RANGE,
    AROUSAL_BPM_MIN_CLIP,
    AROUSAL_BPM_MAX_CLIP,
    AROUSAL_ENERGY_MIN,
    AROUSAL_ENERGY_RANGE,
    AROUSAL_ENERGY_WEIGHT,
)

log = get_logger("Analyzer")

# Pitch class names for key detection
PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


# Krumhansl-Kessler key profiles (from music cognition research)
# These represent the "ideal" distribution of pitch classes for each key
MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)


def analyze_track(filepath, duration=90, offset=15):
    """
    Analyzes an audio file to extract semantic music theory data.

    Uses single-pass BPM estimation with octave correction (threshold 0.22).
    Loads 90s starting at offset 15s for better coverage.

    Args:
        filepath (str): Path to audio file.
        duration (int): How many seconds to analyze (default 90s).
        offset (int): Where to start (default 15s, skip intro).

    Returns:
        dict with audio features and mood descriptors.
    """
    try:
        # Load audio as mono - suppress only librosa UserWarnings about resampling
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            y, sr = librosa.load(
                filepath, sr=22050, mono=True, offset=offset, duration=duration
            )
    except (IOError, OSError) as e:
        log.error(f"Failed to load audio {filepath}: {e}")
        return None

    if len(y) == 0:
        return None

    # Normalize audio volume so RMS/energy is consistent across all files
    # This prevents quiet rips from being misclassified as low energy
    y = librosa.util.normalize(y)

    # === CORE FEATURES ===

    # 1. Tempo (BPM) - Single pass (multi-seg removed: 2.5x slower, no accuracy gain)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo) if not isinstance(tempo, np.ndarray) else float(tempo[0])
    except (RuntimeError, ValueError) as e:
        log.warning(f"Beat tracking failed: {e}")
        bpm = 0.0

    # 2. Energy (RMS)
    rms = librosa.feature.rms(y=y)
    energy = float(np.mean(rms))

    # 2b. BPM octave correction using energy as sanity check
    # Uses ENERGY_OCTAVE_THRESHOLD to fix misdetected high BPM on low-energy tracks
    if bpm > BPM_HIGH_THRESHOLD and energy < ENERGY_OCTAVE_THRESHOLD:
        bpm /= 2
    elif bpm < BPM_LOW_THRESHOLD:
        bpm *= 2

    # 3. Spectral Centroid (Brightness)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    brightness = float(np.mean(cent))

    # === ADVANCED FEATURES FOR MOOD ===

    # 4. Key and Mode Detection (Major/Minor)
    key, mode, key_confidence = detect_key(y, sr)

    # 5. Spectral Contrast (dynamic range across frequency bands)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    spectral_contrast = float(np.mean(contrast))

    # 6. Zero Crossing Rate (percussiveness/noisiness)
    zcr = librosa.feature.zero_crossing_rate(y)
    zero_crossing = float(np.mean(zcr))

    # 7. Harmonic-to-Noise Ratio (melodic vs noisy)
    harmonic, percussive = librosa.effects.hpss(y)
    harmonic_ratio = float(np.mean(np.abs(harmonic)) / (np.mean(np.abs(y)) + 1e-6))

    # === NEW PHASE 1 FEATURES ===

    # 9. MFCCs (13 coefficients) - THE most important music classification feature
    # Captures timbral texture/shape. Distinguishes songs with similar BPM/energy
    # but vastly different sound (e.g., Cruel Angel's Thesis vs death bed)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfccs = [round(float(np.mean(mfcc[i])), 4) for i in range(13)]

    # 10. Spectral Rolloff - frequency below which 85% of spectral energy lies
    # Separates bright pop (high rolloff) from dark ambient (low rolloff)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    spectral_rolloff = float(np.mean(rolloff))

    # 11. Spectral Bandwidth - width of the frequency spread
    # Full-range production (high) vs narrow/thin sound (low)
    bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    spectral_bandwidth = float(np.mean(bw))

    # 12. Dynamic Range - log-scaled ratio of loud to quiet RMS frames
    # Uses 95th/5th percentiles to avoid blowup from silence.
    # Log scale compresses the range: raw ratio 1-237K → log1p → ~0.7-12.4
    # Most songs cluster in 0.7-3.5 on log scale. Prevents outlier dominance.
    rms_flat = rms.flatten()
    rms_p95 = float(np.percentile(rms_flat, 95))
    rms_p5 = float(np.percentile(rms_flat, 5))
    dynamic_range = float(np.log1p(rms_p95 / (rms_p5 + 1e-6)))

    # === MOOD/VALENCE ESTIMATION ===
    valence = estimate_valence(
        bpm, energy, brightness, mode, spectral_contrast, zero_crossing, key_confidence
    )
    arousal = estimate_arousal(bpm, energy)

    # === SEMANTIC DESCRIPTION ===
    description = build_description(bpm, energy, brightness, mode, valence, arousal)

    return {
        "bpm": round(bpm, 1),
        "energy": round(energy, 4),
        "brightness": round(brightness, 1),
        "key": key,
        "mode": mode,  # 'major' or 'minor'
        "key_confidence": round(key_confidence, 2),
        "valence": round(valence, 2),  # -1 (sad) to +1 (happy)
        "arousal": round(arousal, 2),  # 0 (calm) to 1 (energetic)
        "spectral_contrast": round(spectral_contrast, 2),
        "zero_crossing": round(zero_crossing, 4),
        "harmonic_ratio": round(harmonic_ratio, 2),
        "spectral_rolloff": round(spectral_rolloff, 1),
        "spectral_bandwidth": round(spectral_bandwidth, 1),
        "dynamic_range": round(dynamic_range, 2),
        "mfccs": mfccs,
        "description": description,
    }


def detect_key(y, sr):
    """
    Detects musical key using Krumhansl-Kessler key-finding algorithm.

    This correlates the chroma distribution with theoretical major/minor
    key profiles derived from music cognition research.

    Includes tuning estimation to handle non-A440 recordings (e.g., 432Hz).

    Returns:
        tuple: (key_name, mode, confidence)
        e.g., ('C', 'major', 0.85)
    """
    # Estimate tuning deviation from A440
    tuning_deviation = 0.0
    if TUNING_ESTIMATION_ENABLED:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                tuning_deviation = librosa.estimate_tuning(y=y, sr=sr)
            # tuning_deviation is in fractions of a bin (+-0.5 = +-50 cents)
            tuning_confidence = 1.0 - abs(tuning_deviation) / 0.5
        except (RuntimeError, ValueError):
            tuning_confidence = 0.0
            tuning_deviation = 0.0
    else:
        tuning_confidence = 0.0

    # Compute chromagram (12 pitch classes) using STFT for speed
    # Apply tuning correction if confidence is high enough
    if (
        tuning_confidence >= TUNING_CONFIDENCE_THRESHOLD
        and abs(tuning_deviation) > 0.05
    ):
        # Use CQT with tuning correction for better accuracy on detuned tracks
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, tuning=tuning_deviation)
    else:
        # Standard STFT chromagram for speed on properly tuned tracks
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)

    chroma_mean = np.mean(chroma, axis=1)

    # Normalize
    chroma_mean = chroma_mean / (np.sum(chroma_mean) + 1e-6)

    best_corr = -1
    best_key = 0
    best_mode = "major"

    # Test all 12 keys in both major and minor
    for shift in range(12):
        # Rotate the profile to match different keys
        major_rotated = np.roll(MAJOR_PROFILE, shift)
        minor_rotated = np.roll(MINOR_PROFILE, shift)

        # Normalize profiles
        major_norm = major_rotated / np.sum(major_rotated)
        minor_norm = minor_rotated / np.sum(minor_rotated)

        # Pearson correlation
        corr_major = np.corrcoef(chroma_mean, major_norm)[0, 1]
        corr_minor = np.corrcoef(chroma_mean, minor_norm)[0, 1]

        if corr_major > best_corr:
            best_corr = corr_major
            best_key = shift
            best_mode = "major"

        if corr_minor > best_corr:
            best_corr = corr_minor
            best_key = shift
            best_mode = "minor"

    key_name = PITCH_CLASSES[best_key]
    confidence = max(0, min(1, best_corr))  # Clamp to 0-1

    # If confidence is too low, mark as unknown
    if confidence < 0.3:
        key_name = "unknown"
        best_mode = "unknown"

    return key_name, best_mode, confidence


def estimate_valence(bpm, energy, brightness, mode, contrast, zcr, key_confidence=0.5):
    """
    Estimates emotional valence (happiness) from audio features.

    Based on research showing correlations:
    - Major mode → positive valence
    - Higher tempo → positive valence
    - Higher brightness → positive valence
    - Higher spectral contrast → positive valence

    Args:
        key_confidence: 0-1 confidence in key detection.
                       Low confidence reduces mode's influence on valence.

    Returns:
        float: -1 (very sad) to +1 (very happy)
    """
    valence = 0.0

    # Mode contribution: GATED by confidence threshold
    # Below KEY_CONFIDENCE_THRESHOLD, mode detection is unreliable — treat as neutral
    # Above threshold, scale linearly to VALENCE_MODE_MAX_WEIGHT
    if key_confidence >= KEY_CONFIDENCE_THRESHOLD:
        mode_weight = (
            VALENCE_MODE_MAX_WEIGHT
            * (key_confidence - KEY_CONFIDENCE_THRESHOLD)
            / (1.0 - KEY_CONFIDENCE_THRESHOLD)
        )
    else:
        mode_weight = 0.0

    if mode == "major":
        valence += mode_weight
    else:  # minor
        valence -= mode_weight

    # Tempo contribution (normalized around reference BPM)
    if bpm > 0:
        tempo_factor = (bpm - VALENCE_TEMPO_REFERENCE) / VALENCE_TEMPO_RANGE
        valence += np.clip(
            tempo_factor * VALENCE_TEMPO_WEIGHT,
            -VALENCE_TEMPO_WEIGHT,
            VALENCE_TEMPO_WEIGHT,
        )

    # Brightness contribution
    if brightness > 0:
        bright_factor = (
            brightness - VALENCE_BRIGHTNESS_REFERENCE
        ) / VALENCE_BRIGHTNESS_RANGE
        valence += np.clip(
            bright_factor * VALENCE_BRIGHTNESS_WEIGHT,
            -VALENCE_BRIGHTNESS_WEIGHT,
            VALENCE_BRIGHTNESS_WEIGHT,
        )

    # Spectral contrast (dynamic music tends to be more positive)
    contrast_factor = (contrast - VALENCE_CONTRAST_REFERENCE) / VALENCE_CONTRAST_RANGE
    valence += np.clip(
        contrast_factor * VALENCE_CONTRAST_WEIGHT,
        -VALENCE_CONTRAST_WEIGHT,
        VALENCE_CONTRAST_WEIGHT,
    )

    # High zero-crossing can indicate harshness (negative) or percussion (neutral)
    if zcr > VALENCE_ZCR_PENALTY_THRESHOLD:
        valence -= VALENCE_ZCR_PENALTY  # Slight penalty for very harsh/noisy

    return np.clip(valence, -1, 1)


def estimate_arousal(bpm, energy):
    """
    Estimates arousal (energy/excitement level) from audio features.

    Calibrated for actual data ranges:
      - BPM: 55-200 (after octave correction), centered at 80 for calm baseline
      - Energy (RMS): 0.054-0.386 (mean 0.246), linearly mapped

    Returns:
        float: 0 (very calm) to 1 (very energetic)
    """
    arousal = 0.0

    # BPM contribution: reference BPM → 0 (calm baseline)
    # Allow negative drag for very slow songs to pull arousal down
    if bpm > 0:
        arousal += np.clip(
            (bpm - AROUSAL_BPM_REFERENCE) / AROUSAL_BPM_RANGE,
            AROUSAL_BPM_MIN_CLIP,
            AROUSAL_BPM_MAX_CLIP,
        )

    # Energy (RMS) contribution: linear map across actual range
    arousal += (
        np.clip((energy - AROUSAL_ENERGY_MIN) / AROUSAL_ENERGY_RANGE, 0, 1)
        * AROUSAL_ENERGY_WEIGHT
    )

    return np.clip(arousal, 0, 1)


def build_description(bpm, energy, brightness, mode, valence, arousal):
    """
    Builds a human-readable mood description from features.
    """
    parts = []

    # Tempo description
    if bpm < 70:
        parts.append("Very Slow (Largo)")
    elif bpm < 100:
        parts.append("Slow (Adagio)")
    elif bpm < 120:
        parts.append("Moderate Tempo")
    elif bpm < 160:
        parts.append("Fast (Allegro)")
    else:
        parts.append("Very Fast (Presto)")

    # Energy description
    if energy < 0.05:
        parts.append("Quiet")
    elif energy > 0.12:
        parts.append("Intense")

    # Mode/Key feeling
    if mode == "major":
        parts.append("Major Key")
    else:
        parts.append("Minor Key")

    # Valence-based mood words
    if valence > 0.3:
        parts.append("Happy/Uplifting")
    elif valence > 0.1:
        parts.append("Positive/Bright")
    elif valence < -0.3:
        parts.append("Sad/Melancholic")
    elif valence < -0.1:
        parts.append("Somber/Reflective")

    # Arousal-based energy words
    if arousal > 0.7:
        parts.append("High Energy")
    elif arousal < 0.3:
        parts.append("Calm/Relaxed")

    # Brightness
    if brightness < 1500:
        parts.append("Dark Timbre")
    elif brightness > 3000:
        parts.append("Bright Timbre")

    return ", ".join(parts)


if __name__ == "__main__":
    # Test with a sample file
    test_file = "Z:/Code/pbl2/songs_testing/01. Ponpon Shit.flac"
    if os.path.exists(test_file):
        print(f"Analyzing {test_file}...")
        result = analyze_track(test_file)
        if result:
            for k, v in result.items():
                print(f"  {k}: {v}")
    else:
        print("Test file not found.")

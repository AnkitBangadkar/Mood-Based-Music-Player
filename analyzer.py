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

# Suppress warnings from librosa for cleaner logs
warnings.filterwarnings('ignore')

log = get_logger("Analyzer")

# Pitch class names for key detection
PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Krumhansl-Kessler key profiles (from music cognition research)
# These represent the "ideal" distribution of pitch classes for each key
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def analyze_track(filepath, duration=60, offset=30):
    """
    Analyzes an audio file to extract semantic music theory data.
    
    Args:
        filepath (str): Path to audio file.
        duration (int): How many seconds to analyze.
        offset (int): Where to start (skip intro).
        
    Returns:
        dict with audio features and mood descriptors.
    """
    try:
        # Load audio as mono
        y, sr = librosa.load(filepath, sr=22050, mono=True, offset=offset, duration=duration)
    except Exception as e:
        log.error(f"Failed to load audio {filepath}: {e}")
        return None

    if len(y) == 0:
        return None

    # === CORE FEATURES ===
    
    # 1. Tempo (BPM)
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo) if not isinstance(tempo, np.ndarray) else float(tempo[0])
    except Exception:
        bpm = 0.0

    # 2. Energy (RMS)
    rms = librosa.feature.rms(y=y)
    energy = float(np.mean(rms))

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
    
    # === MOOD/VALENCE ESTIMATION ===
    valence = estimate_valence(bpm, energy, brightness, mode, spectral_contrast, zero_crossing)
    arousal = estimate_arousal(bpm, energy, spectral_contrast)
    
    # === SEMANTIC DESCRIPTION ===
    description = build_description(bpm, energy, brightness, mode, valence, arousal)

    return {
        'bpm': round(bpm, 1),
        'energy': round(energy, 4),
        'brightness': round(brightness, 1),
        'key': key,
        'mode': mode,  # 'major' or 'minor'
        'key_confidence': round(key_confidence, 2),
        'valence': round(valence, 2),  # -1 (sad) to +1 (happy)
        'arousal': round(arousal, 2),  # 0 (calm) to 1 (energetic)
        'spectral_contrast': round(spectral_contrast, 2),
        'zero_crossing': round(zero_crossing, 4),
        'harmonic_ratio': round(harmonic_ratio, 2),
        'description': description
    }


def detect_key(y, sr):
    """
    Detects musical key using Krumhansl-Kessler key-finding algorithm.
    
    This correlates the chroma distribution with theoretical major/minor
    key profiles derived from music cognition research.
    
    Returns:
        tuple: (key_name, mode, confidence)
        e.g., ('C', 'major', 0.85)
    """
    # Compute chromagram (12 pitch classes)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)
    
    # Normalize
    chroma_mean = chroma_mean / (np.sum(chroma_mean) + 1e-6)
    
    best_corr = -1
    best_key = 0
    best_mode = 'major'
    
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
            best_mode = 'major'
            
        if corr_minor > best_corr:
            best_corr = corr_minor
            best_key = shift
            best_mode = 'minor'
    
    key_name = PITCH_CLASSES[best_key]
    confidence = max(0, min(1, best_corr))  # Clamp to 0-1
    
    return key_name, best_mode, confidence


def estimate_valence(bpm, energy, brightness, mode, contrast, zcr):
    """
    Estimates emotional valence (happiness) from audio features.
    
    Based on research showing correlations:
    - Major mode → positive valence
    - Higher tempo → positive valence  
    - Higher brightness → positive valence
    - Higher spectral contrast → positive valence
    
    Returns:
        float: -1 (very sad) to +1 (very happy)
    """
    valence = 0.0
    
    # Mode is the strongest predictor of valence
    if mode == 'major':
        valence += 0.3
    else:  # minor
        valence -= 0.3
    
    # Tempo contribution (normalized around 120 BPM)
    if bpm > 0:
        tempo_factor = (bpm - 100) / 80  # Maps 60-180 to roughly -0.5 to +1
        valence += np.clip(tempo_factor * 0.2, -0.2, 0.2)
    
    # Brightness contribution
    if brightness > 0:
        bright_factor = (brightness - 2000) / 2000  # Maps 1000-4000 to -0.5 to +1
        valence += np.clip(bright_factor * 0.15, -0.15, 0.15)
    
    # Spectral contrast (dynamic music tends to be more positive)
    contrast_factor = (contrast - 20) / 20
    valence += np.clip(contrast_factor * 0.1, -0.1, 0.1)
    
    # High zero-crossing can indicate harshness (negative) or percussion (neutral)
    if zcr > 0.15:
        valence -= 0.05  # Slight penalty for very harsh/noisy
    
    return np.clip(valence, -1, 1)


def estimate_arousal(bpm, energy, contrast):
    """
    Estimates arousal (energy/excitement level) from audio features.
    
    Returns:
        float: 0 (very calm) to 1 (very energetic)
    """
    arousal = 0.0
    
    # BPM is primary arousal indicator
    if bpm > 0:
        arousal += np.clip((bpm - 60) / 140, 0, 0.5)  # 60-200 BPM → 0-0.5
    
    # Energy (RMS) contribution
    arousal += np.clip(energy * 3, 0, 0.3)  # Typical RMS 0-0.15 → 0-0.3
    
    # Spectral contrast adds excitement
    arousal += np.clip((contrast - 15) / 50, 0, 0.2)
    
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
    if mode == 'major':
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

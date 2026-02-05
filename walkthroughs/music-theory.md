# 🎼 Music Theory & Audio Analysis Logic

This document explains the non-code logic the system uses to "hear" and categorize your music. Instead of just reading text tags, we analyze the physical sound waves and translate them into musical concepts.

## 1. Tempo (The Pulse)
We calculate the **BPM (Beats Per Minute)** to determine the "heartbeat" of the track.

*   **Largo (< 70 BPM):** Very slow. Associated with sadness, relaxation, or epic cinematic scores.
*   **Adagio (70-100 BPM):** Slow and leisurely. Common in ballads and "chill" tracks.
*   **Moderato (100-120 BPM):** The "walking pace". Standard for most pop and easy-listening.
*   **Allegro (120-160 BPM):** Fast and bright. High energy, dance, and rock.
*   **Presto (> 160 BPM):** Extremely fast. High-intensity action, drum & bass, or metal.

## 2. Dynamic Energy (Intensity)
This is measured using **RMS (Root Mean Square)** energy. It tells us the "perceived loudness" and power of the track.

*   **Low Energy:** Minimal instruments, quiet vocals, acoustic. (e.g., a solo piano or acoustic guitar).
*   **Moderate Energy:** Standard production levels.
*   **High Energy:** "Wall of Sound," distorted guitars, heavy bass, or compressed electronic production.

## 3. Timbre & Brightness (Spectral Centroid)
We use the **Spectral Centroid** to find the "center of gravity" of the frequencies.

*   **Dark Timbre (< 1500Hz):** Sub-heavy, bass-driven, or "warm" sounds. Often perceived as "moody," "deep," or "mysterious."
*   **Neutral:** Balanced frequency spectrum.
*   **Bright Timbre (> 3000Hz):** High-frequency dominance. Percussive, "sharp," "airy," or "crystalline." Often associated with "happiness," "clarity," or "aggression."

---

## 🧠 Why we do this?
By combining these three metrics, the AI can distinguish between two songs in the same genre. 

**Example:** 
If you have two "Jazz" songs:
1.  **Song A:** Slow BPM + Low Energy + Dark Timbre = **"Relaxing Late Night Jazz"**
2.  **Song B:** Fast BPM + High Energy + Bright Timbre = **"Intense Bebop / Chase Music"**

Without audio analysis, both are just labeled "Jazz". With this logic, the system knows exactly which one to play when you ask for "chill vibes."

---

## 4. Musical Key Detection (Major vs Minor)

### The Theory
Musical **key** is one of the strongest predictors of emotional perception in music. This is consistent across cultures and languages.

| Mode | Emotional Association | Technical Description |
|------|----------------------|----------------------|
| **Major** | Happy, bright, resolved, triumphant | Scale: W-W-H-W-W-W-H |
| **Minor** | Sad, dark, tense, mysterious | Scale: W-H-W-W-H-W-W |

*(W = Whole step, H = Half step)*

### Krumhansl-Kessler Key-Finding Algorithm
We implement the research-backed **Krumhansl-Kessler profiles** to detect key:

1. Extract **chroma features** (12 pitch classes: C, C#, D, ... B)
2. Average the chroma across the entire track
3. Correlate against **major and minor key profiles** derived from music cognition research
4. The highest correlation determines the detected key

**Key Profiles (Krumhansl, 1990):**
```
Major: [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
Minor: [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
```

These profiles represent how often each pitch class appears in typical major vs minor compositions.

### Confidence Score
We output a **confidence score** (0-1) based on how well the track matches the detected key. Low confidence can indicate:
- Atonal music
- Key changes mid-song
- Ambiguous harmonic content

---

## 5. Valence Estimation (Happy vs Sad)

### Thayer's Arousal-Valence Model
We use the **arousal-valence model** from emotion psychology:

```
         High Arousal
              ↑
    Angry ←   |   → Excited
              |
  ← Negative --+-- Positive →   (Valence)
              |
      Sad  ←  |   → Relaxed
              ↓
         Low Arousal
```

### How We Calculate Valence
Valence is estimated from multiple audio features:

| Feature | Weight | Direction |
|---------|--------|-----------|
| **Mode (Major/Minor)** | 30% | Major = +, Minor = - |
| **Tempo** | 20% | Fast = +, Slow = - |
| **Brightness** | 15% | Bright = +, Dark = - |
| **Spectral Contrast** | 10% | High = +, Low = - |

**Output:** -1 (very sad) to +1 (very happy)

### Research Basis
This approach is based on studies showing correlations between acoustic features and perceived emotion:
- Gabrielsson & Lindström (2010): "The Role of Structure in the Musical Expression of Emotions"
- Eerola et al. (2013): "A comparison of the discrete and dimensional models of emotion in music"

---

## 6. Arousal Estimation (Energy Level)

### How We Calculate Arousal
Arousal measures the energy/excitement level:

| Feature | Weight | Direction |
|---------|--------|-----------|
| **Tempo (BPM)** | 50% | Higher = more aroused |
| **RMS Energy** | 30% | Louder = more aroused |
| **Spectral Contrast** | 20% | More dynamic = more aroused |

**Output:** 0 (very calm) to 1 (very energetic)

---

## 7. Additional Audio Features

### Spectral Contrast
Measures the difference between peaks (harmonics) and valleys (noise floor) in the spectrum.
- **High contrast:** Punchy, dynamic, exciting
- **Low contrast:** Smooth, ambient, "blended"

### Zero Crossing Rate (ZCR)
How often the audio waveform crosses zero amplitude.
- **High ZCR:** Noisy, percussive, maybe harsh
- **Low ZCR:** Smooth, melodic, sustained tones

### Harmonic-to-Noise Ratio
The balance between harmonic (pitched) content and noise/percussion.
- **High ratio:** Melodic, vocal-heavy, instrumental
- **Low ratio:** Percussive, noisy, aggressive

---

## 8. Language-Agnostic Design

All features are extracted from **raw audio**, not lyrics or metadata. This means:

✅ Works for Hindi songs  
✅ Works for Japanese songs  
✅ Works for instrumental music  
✅ Works for songs with no lyrics  

The system "hears" emotion the same way a non-speaker would perceive it: through tempo, key, dynamics, and timbre.

---

## 9. Practical Mood Mapping

### "Happy, Upbeat" Query
The system boosts songs with:
- **Major key** (valence signal)
- **Positive valence score** (>0.1)
- **Fast tempo** (>100 BPM)
- **High brightness** (>2500 Hz centroid)

### "Sad, Melancholic" Query
The system boosts songs with:
- **Minor key** (valence signal)
- **Negative valence score** (<-0.1)
- **Slow tempo** (<100 BPM)
- **Dark timbre** (<2000 Hz centroid)

### The YOASOBI Problem (Solved)
A song that is **fast BPM but minor key** (like YOASOBI's 群青) will:
- Get a **high arousal score** (energetic)
- Get a **negative valence score** (not purely happy)
- Be correctly identified as "dramatic/intense" rather than "happy"

This solves the original problem of high-energy-but-melancholic songs being incorrectly matched to "happy" queries.

---

*Last updated: 2026-01-07*

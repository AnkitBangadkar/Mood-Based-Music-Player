# Plan: Backend Intermediate Upgrade (Audio Analysis)

## 1. The Goal
Stop guessing the mood based on the Artist/Genre tag. Start actually "listening" to the audio signal to determine if a song is fast, aggressive, calm, or happy.

## 2. The Approach: "Signal to Semantics"
We will not build a separate search engine for numbers. Instead, we will extract physical audio characteristics, convert them into descriptive English words, and feed them into our existing AI Brain (`all-MiniLM-L6-v2`).

**Why this way?**
It keeps the system simple. The AI already understands what "Fast" means. We just need to tell it, "This song is Fast" based on hard data.

## 3. The New Technology Stack
*   **Audio Processing:** `librosa` (Standard Python library for audio analysis).
*   **Math:** `numpy` (Already installed).

## 4. What We Will Extract (The "Ears")

We will analyze the **middle 30-60 seconds** of each song (to save CPU/Time) and extract three core metrics:

### A. Tempo (BPM)
*   **What is it?** Beats Per Minute.
*   **Translation:**
    *   < 70 BPM → "Very Slow, Downtempo"
    *   70-100 BPM → "Slow, Relaxed"
    *   100-130 BPM → "Mid-tempo, Groovy"
    *   > 130 BPM → "Fast, Upbeat, High Energy"

### B. RMS Energy (Loudness/Intensity)
*   **What is it?** The average power of the audio signal.
*   **Translation:**
    *   Low Energy → "Quiet, Soft, Minimal"
    *   High Energy → "Loud, Powerful, Intense"

### C. Spectral Centroid (Timbre/Brightness)
*   **What is it?** Where the "center of mass" of the frequency is.
*   **Translation:**
    *   Low frequencies dominant → "Dark, Deep, Bass-heavy"
    *   High frequencies dominant → "Bright, Sharp, Airy"

## 5. Implementation Steps

### Step 1: Install `librosa`
It requires `scipy` and `numpy` (which we have), but is a heavier dependency.

### Step 2: Update `database.py`
Add columns to the `songs` table to store these raw numbers (useful for debugging or future sorting).
*   `bpm` (float)
*   `energy_level` (float)

### Step 3: Upgrade `scanner.py`
Create a new function `analyze_audio(filepath)`.
*   **Safety:** This is the risky part. Corrupt audio files can crash scripts. We need strict error handling.
*   **Performance:** We process only a slice of the audio, not the whole file, to keep scanning from taking hours.

### Step 4: The "Rich Description" Update
We update the string we send to the AI.

*   **Old:** `Song: Numb. Artist: Linkin Park. Genre: Rock.`
*   **New:** `Song: Numb. Artist: Linkin Park. Genre: Rock. Audio: Slow tempo (80 BPM). High Energy. Dark timbre.`

## 6. Pros & Cons

| Pros | Cons |
| :--- | :--- |
| **Truthful:** No more guessing "Sad" just because the band is "Radiohead". | **Slower Scanning:** Analyzing audio takes ~1-3 seconds per song vs 0.01s for tags. |
| **Discovery:** Finds "Fast" songs in "Slow" genres (e.g., a fast Jazz track). | **CPU Intensive:** Scanning a large library will heat up the CPU. |

## 7. Execution Order
1.  Install dependencies.
2.  Create the `analyzer` module.
3.  Test the analyzer on a few files to tune the thresholds (what counts as "High Energy"?).
4.  Integrate into the main Scanner.

---

# Plan: Backend Upgrade Phase 2 (Lyrics Integration)

## 1. The Goal (The "Eyes")
Give the system the ability to "read" the song. Audio analysis gives us the *energy*, but Lyrics give us the *story* and *emotion*. 
*   A song can be fast and major key (Happy Audio) but the lyrics are about heartbreak (Sad Context).
*   We need both to be truly accurate.

## 2. The Strategy: "Local First, Fetch Optional"
We cannot rely on scraping websites constantly (slow, gets banned). We need a tiered approach.

### Tier 1: Embedded Lyrics (Fastest & Best)
*   Many MP3/FLAC files have a `USLT` (Unsynchronized Lyrics) frame.
*   **Action:** Use `mutagen` to extract this text if it exists.

### Tier 2: Local LRC Files (Standard for Power Users)
*   If `song.mp3` exists, look for `song.lrc` in the same folder.
*   **Action:** Parse the text from the timestamped file.

### Tier 3: Fetch (Optional & Future)
*   If user enables "Online Mode", query a lightweight API (like Genius or OVH) for missing lyrics. **(Out of scope for now to keep it local/fast).**

## 3. Processing Lyrics
We can't feed the whole song lyrics to the embedding model (Token limit is usually 512 tokens).
*   **Solution:** Summarization or Chorus Extraction.
*   **Simple Approach:** Take the first 50 lines (usually Verse 1 + Chorus). The mood is almost always established there.

## 4. Integration with Vector Engine
We update the "Rich Description" again.

*   **Format:** 
    `{Title} by {Artist}. {Audio Analysis Data}. Lyrics snippet: "{First 10 lines of lyrics...}"`

*   **Why?** The embedding model `all-MiniLM-L6-v2` is trained on massive amounts of text. If the lyrics contain words like "tears", "pain", "rain", it will pull the vector towards the "Sad" cluster *even if the song is fast*.

## 5. Implementation Plan

1.  **Upgrade `scanner.py`:** Add a `extract_lyrics(filepath)` function.
2.  **Mutagen Logic:** Add handlers for ID3 USLT frames and FLAC lyrics tags.
3.  **File Logic:** Add check for `.lrc` sidecar files.
4.  **Database Update:** Add `has_lyrics` (boolean) column to DB for stats.

---

# Plan: Backend Optimization Phase 3 (Weighted Hybrid Engine)

## 1. The Problem
The current "One Big String" approach confuses the AI. A song with "Sad" lyrics but "Happy" genre tags often gets misclassified because the AI treats all words equally.
*   **Result:** A prompt for "Happy" returns "Duvet" (Sad Lyrics) because the Genre/Audio said "Rock/Moderate".

## 2. The Solution: Weighted Multi-Vector Search
Instead of creating one embedding for the whole song, we create **Three Separate Embeddings** and weigh them during the search.

### The 3 Pillars:
1.  **Lyrics Vector (Weight: 50%):** The "Truth". If a song says "I am sad", it is sad.
2.  **Audio Vector (Weight: 30%):** The "Vibe". Fast/Slow/Intense.
3.  **Metadata Vector (Weight: 20%):** The "Context". Genre/Artist reputation.

## 3. Architecture Changes

### A. Database (`songs` table)
We need to store 3 separate vectors instead of one.
*   `embedding_lyrics` (Blob)
*   `embedding_audio` (Blob)
*   `embedding_meta` (Blob)

### B. Scanner (`scanner.py`)
Instead of `rich_desc`, we generate:
*   `text_lyrics`: "I am falling, I am fading..."
*   `text_audio`: "Fast Tempo. High Energy. Bright Timbre."
*   `text_meta`: "Song: Title. Artist: Name. Genre: Pop."

### C. Engine (`engine.py`)
The search function becomes a **Weighted Sum**:
```python
Score = (Cosine(Prompt, LyricsVec) * W_L) + 
        (Cosine(Prompt, AudioVec) * W_A) + 
        (Cosine(Prompt, MetaVec) * W_M)
```

### D. Dynamic Weighting
If a song has **No Lyrics**, we cannot punish it with a 0 score.
*   **Logic:**
    *   If `has_lyrics`: W_L=0.5, W_A=0.3, W_M=0.2
    *   If `no_lyrics`: W_L=0.0, W_A=0.6, W_M=0.4 (Redistribute importance to Audio/Meta)

## 4. Expected Outcome
*   "Duvet" (Sad Lyrics) will have a low Lyrics Score for "Happy" prompt. Even if Audio Score is moderate, the heavy Lyric weight will tank its final ranking.
*   "Ponpon Shit" (Happy Lyrics + Fast Audio) will score high on both.

## 5. Execution Steps
1.  **Database Migration:** Drop table and recreate with new vector columns.
2.  **Scanner Refactor:** Generate 3 embeddings per song.
3.  **Engine Refactor:** Implement the weighted search logic.

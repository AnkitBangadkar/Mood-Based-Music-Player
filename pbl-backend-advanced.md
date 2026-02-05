# Plan: Backend Advanced Optimization (Tiered Architecture)

## 1. The "Tiered" Philosophy
One size does not fit all. We will implement a dynamic system that scales its intelligence based on the available hardware.

### Hardware Configuration
We use `config.py` to control the system tier.
*   **Low End:** Uses `VADER` (Rule-based) and `bge-small`.
*   **Normal:** Uses `DistilBERT` (Transformer) and `bge-small` + `Cross-Encoder`.
*   **High End:** (Future) LLM-based reasoning.

---

## 2. Implemented Architecture (Tier 2 - "The Standard")

This architecture is now **LIVE** in the codebase.

### A. The "Smart" Scanner
The scanner is no longer just a text-reader. It is an **Analyzer**.
1.  **Multi-Threaded:** 8 concurrent workers for speed (~0.8s/song).
2.  **Audio Analysis:** `librosa` extracts BPM, Energy, and Timbre (30s sample).
3.  **Lyrics Pipeline:**
    *   **Source 1:** Embedded Tags (USLT).
    *   **Source 2:** Genius.com Scraping (Aggressive Cleaning).
    *   **Source 3:** OVH API (Fallback).
    *   **Source 4:** Musixmatch API (Requires `MUSIXMATCH_API_KEY`).
4.  **Sentiment Engine:**
    *   Uses `distilbert-base-uncased-finetuned-sst-2-english`.
    *   Reads the lyrics and assigns a `sentiment_score` (-1.0 to 1.0).
    *   This "Truth Score" is baked into the database.

### B. The "Hybrid" Database
We store **Three Separate Vectors** per song:
1.  `lyrics_vec`: The story.
2.  `audio_vec`: The physical vibe.
3.  `meta_vec`: The genre/artist context.

### C. The "Judge" Engine (Generation)
When a user asks for a playlist, we don't just find similar vectors. We **Judge** them.

1.  **Weighted Retrieval:**
    *   `Score = (Lyrics * 0.5) + (Audio * 0.3) + (Meta * 0.2)`
    *   This forces the system to prioritize lyrics for meaning, but audio for vibe.

2.  **Logic Filter (The Guardrails):**
    *   If Prompt = "Happy" and Song Sentiment = "Sad" (-0.8) -> **Penalty**.
    *   If Prompt = "Fast" and Song BPM < 100 -> **Penalty**.

3.  **Cross-Encoder Reranking:**
    *   The top 50 candidates are fed into `cross-encoder/ms-marco-TinyBERT-L-2`.
    *   This model acts as a human judge, reading the specific pair `(Prompt, Song)` and re-scoring them for nuance.

---

## 3. Performance Metrics
*   **Scan Speed:** ~30 songs in 25 seconds (with heavy AI analysis).
*   **Generation Speed:** ~1 second (due to Reranker).
*   **Accuracy:** Significantly improved "Mood Matching" by separating Lyrics/Audio.

---

## 4. Future Roadmap (Tier 3)
*   **LLM Integration:** Using `Phi-3` to "describe" songs in natural language.
*   **Audio Transformers:** Using `Music2Emo` to replace `librosa` logic.
*   **User Feedback Loop:** "This song is wrong" button to retrain the local Reranker.

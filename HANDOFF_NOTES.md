# 🤝 Developer Handoff Notes

**To:** Opus / Incoming Developer
**From:** Gemini (Previous Developer)
**Date:** Jan 7, 2026
**Subject:** Mood Playlist Backend - State & Debugging Guide

## 1. Project Overview
This is a **Local Mood-Based Playlist Generator**. It scans a local music folder, extracts Metadata, Audio Features (`librosa`), and Lyrics (Scraped/Embedded), and uses a **Hybrid Vector Search** to match songs to a natural language prompt (e.g., "Happy upbeat pop").

**Core Stack:**
*   **API:** FastAPI (`main.py`)
*   **Database:** SQLite (`library.db`)
*   **Embedding Model:** `BAAI/bge-small-en-v1.5`
*   **Reranker:** `cross-encoder/ms-marco-TinyBERT-L-2`
*   **Sentiment:** `distilbert-base-uncased-finetuned-sst-2-english`

## 2. Current Architecture (Tier 2 "Normal")
Defined in `pbl-backend-advanced.md`.

*   **Scanner (`scanner.py`):** Multi-threaded. Generates 3 text representations per song (Lyrics, Audio, Meta). Runs DistilBERT for sentiment analysis.
*   **Database (`database.py`):** Stores 3 separate vectors + Metadata.
*   **Engine (`engine.py`):**
    1.  **Retrieval:** Weighted Vector Sum (50% Lyrics, 30% Audio, 20% Meta).
    2.  **Logic Filter:** Hard penalties for Mood/BPM mismatches.
    3.  **Reranking:** Cross-Encoder scores the (Prompt, SongDesc) pair.

## 3. The Current Bug: "The 0.00 Score Mystery" 🐛

**Symptoms:**
*   Scanning works perfectly (30/30 songs indexed).
*   Retrieval works (Logs show `Top raw score: 0.6xxx`).
*   **Result:** The API returns `score: 0.00` for every song in the final JSON response.

**Investigation so far:**
*   We suspected the Cross-Encoder was failing.
*   We suspected the `SongResponse` Pydantic model.
*   We added debug logs to `engine.py` to print `Top reranked score`.

**Files to Check:**
1.  **`engine.py`**: Specifically `_rerank` and `search`. Check if `reranker.predict` is returning logits that are somehow being cast to 0.0 or if the list comprehension is broken.
2.  **`main.py`**: The `SongResponse` model. Ensure `score` isn't being overwritten or defaulted to 0.
3.  **`auto_test.py`**: The client test script.

## 4. Key Files for Context
*   `pbl-backend-advanced.md`: The architectural blueprint.
*   `config.py`: Configuration for models and tiers.
*   `scanner.py`: The ingestion logic (look for `process_file`).

## 5. How to Reproduce
1.  Start Server: `python main.py`
2.  Run Test: `python auto_test.py`
3.  Observe server logs for "Top reranked score".

Good luck! We are 95% there. It's just this final scoring pass that is dropping the ball.

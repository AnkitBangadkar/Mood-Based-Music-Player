# Design Document: Local Mood-Based Playlist Generator (Backend)

## 1. Overview
This project aims to build a **local-only, backend-driven system** that generates music playlists based on natural language mood prompts (e.g., "upbeat songs for a workout" or "melancholy tunes for a rainy night").

**Key Constraints:**
*   **Local Execution:** No external APIs for processing. Privacy-first.
*   **Performance:** Fast response times for generation.
*   **Hardware Compatibility:** Must run smoothly on lower-end desktops (limited RAM/CPU, no dedicated GPU).

## 2. Architecture

The system follows a modular architecture centered around a fast embedding-based retrieval system.

### High-Level Components
1.  **API Layer (FastAPI):** Handles requests for scanning directories and generating playlists.
2.  **Library Scanner (Ingestion):** Crawls local directories for audio files and extracts metadata.
3.  **Vector Engine (The "Brain"):** Converts song metadata/lyrics into numerical vectors and performs similarity searches against the user's prompt.
4.  **Data Store:**
    *   **Metadata DB (SQLite):** Stores file paths, title, artist, album, and status.
    *   **Vector Index:** Stores pre-computed embeddings for fast retrieval.

## 3. Technology Stack

*   **Language:** Python 3.9+
*   **Web Framework:** **FastAPI** (Lightweight, async, high performance).
*   **Database:** **SQLite** (Zero-configuration, standard library, file-based).
*   **Audio Metadata:** **Mutagen** (Robust parsing of ID3, FLAC, MP4 tags).
*   **ML/AI Model:** **Sentence-Transformers** (specifically `all-MiniLM-L6-v2`).
    *   *Why?* It is extremely small (~80MB), runs very fast on standard CPUs, and provides high-quality semantic mapping.
*   **Vector Search:** **NumPy** or **FAISS** (CPU version).
    *   *Strategy:* For libraries < 50,000 songs, simple NumPy cosine similarity is instant and requires no complex dependencies.

## 4. Data Flow

### A. Library Ingestion (Indexing)
1.  User provides a local directory path via API.
2.  **Scanner** walks the tree, identifying supported files (.mp3, .flac, .wav, .m4a).
3.  **Metadata Extractor** reads tags (Artist, Title, Album, Genre).
4.  **Text Processor** creates a "rich representation" string.
    *   *Format:* `"{Title} by {Artist}. Genre: {Genre}. Mood: {Energy/Valence heuristic if available}"`
5.  **Vector Engine** computes an embedding for this string using `all-MiniLM-L6-v2`.
6.  Metadata is saved to **SQLite**; Embedding is saved to the **Vector Index**.

### B. Playlist Generation
1.  User sends a prompt: *"Relaxing jazz for studying"*
2.  **Vector Engine** computes the embedding for the *prompt*.
3.  System calculates **Cosine Similarity** between the prompt vector and all song vectors.
4.  Sorts results by similarity score (descending).
5.  Returns the top N file paths and metadata.

## 5. Low-End Optimization Strategy

To ensure performance on lower-end hardware:

1.  **Model Selection:** `all-MiniLM-L6-v2` is the critical choice. It uses minimal RAM (<500MB loaded) and inference is milliseconds per item on CPU.
2.  **Batch Processing:** During ingestion, files are processed in small batches (e.g., 50 songs) to prevent RAM spikes.
3.  **Lazy Loading:** The Vector Engine loads embeddings into memory only when needed (mmap can be used for larger libraries).
4.  **No Heavy Audio Analysis:** We avoid raw audio waveform analysis (FFT/Spectrograms) which is CPU intensive. We rely on *semantic matching* of metadata.
    *   *Note:* If metadata is sparse, we can fallback to file path/name parsing.

## 6. API Endpoints (Draft)

*   `POST /library/scan`: Input `{path: string}`. Triggers background scan.
*   `GET /library/status`: Returns count of indexed songs and indexing status.
*   `POST /playlist/generate`: Input `{prompt: string, limit: int}`. Returns list of songs.
*   `GET /health`: System health check.

## 7. Future Scalability
*   **Lyrics Integration:** If available, lyrics can be added to the embedding text for significantly better mood matching.
*   **Audio Features:** Optionally integrate `librosa` for BPM detection if the CPU allows, strictly as an optional background task.

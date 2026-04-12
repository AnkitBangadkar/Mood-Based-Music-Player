# SoulSeek: AI-Powered Mood Playlist Generator

A local-first, privacy-focused music player that generates intelligent playlists from natural language mood queries using a multi-signal ensemble approach.

![SoulSeek Showcase](showcase.png)

## Features

- **Natural Language Queries**: Describe your mood in plain English - "sad songs for a rainy day", "hype workout music", "chill but not sleepy"
- **Multi-Signal Ensemble Scoring**: Combines three signals for accurate recommendations:
  - **Semantic Similarity (40%)** - BGE embeddings match your query to song mood descriptions
  - **Audio Feature Matching (46%)** - Gaussian similarity on 20+ extracted features
  - **Genre Detection (14%)** - Keyword-based genre matching
- **Comprehensive Audio Analysis** via Librosa:
  - Tempo (BPM) with octave correction
  - Musical key & mode (Krumhansl-Kessler algorithm)
  - Valence (-1 sad to +1 happy) and Arousal (0 calm to 1 energetic)
  - MFCCs, spectral centroid/rolloff/bandwidth
  - RMS energy, dynamic range, zero-crossing rate
- **Negation Support**: Queries like "happy but not energetic" intelligently exclude unwanted traits
- **Query Expansion**: 70+ synonym mappings - "gym" → ["energetic", "workout", "hype"]
- **Incremental Indexing**: Embeddings stored in SQLite - rescan without re-encoding
- **100% Offline**: Your music and queries never leave your machine

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, SQLite, Uvicorn |
| **Embeddings** | BAAI/bge-base-en-v1.5 (768-dim) |
| **Audio Analysis** | Librosa, NumPy, SciPy |
| **Metadata** | Mutagen (ID3, Vorbis, MP4) |
| **Frontend** | React + TypeScript + shadcn/ui |
| **Styling** | Tailwind CSS |
| **Icons** | Lucide React |
| **State** | Zustand |

## Quick Start

### Prerequisites

- Python 3.9+
- ~4GB disk space (for ML models)
- Music files (.mp3, .flac, .wav, .m4a, .ogg)

### Using the Launcher Script

```bash
# Clone
git clone https://github.com/AnkitBangadkar/Mood-Based-Music-Player.git
cd Mood-Based-Music-Player

# Run
./start.sh        # Linux/Mac
start.bat         # Windows
```

The script automatically:
- Creates a virtual environment (first run)
- Installs dependencies (first run)
- Activates venv and starts the server

### Manual Installation

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

Open http://localhost:8000 in your browser.

1. Click **Scan Library** → enter path to your music folder
2. Wait for indexing (analyzes audio, builds embeddings)
3. Type a mood query → **Generate Playlist**

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User Query │ ──► │ Query Processor  │ ──► │ Ensemble Scorer │
└─────────────┘     │  • Expansion     │     │  (40/46/14%)    │
                    │  • BGE Encoding  │     └────────┬────────┘
                    └──────────────────┘              │
                                                      ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Audio Files │ ──► │ Indexing Phase   │ ──► │  Ranked Results │
└─────────────┘     │  • Librosa feat. │     └─────────────────┘
                    │  • BGE embedding │
                    │  • SQLite store  │
                    └──────────────────┘
```

## How Scoring Works

### Semantic Similarity (40%)
- Query and song descriptions encoded with BGE-base-en-v1.5
- Cosine similarity between 768-dim vectors
- Query prefix: `"Represent this sentence for searching relevant passages:"`
- Song prefix: `"Represent this passage for retrieval:"`

### Audio Feature Matching (46%)
- Each mood maps to target (valence, arousal, BPM, energy, etc.)
- Gaussian similarity: `exp(-(x - target)² / (2σ²))`
- Sigma values tuned per feature (see `constants.py`)

### Genre Matching (14%)
- Genre extracted from metadata keywords
- Binary match scoring against query genre hints

## Project Structure

```
├── main.py              # FastAPI app, routes, scan endpoint
├── engine.py            # Core scoring logic, query processing
├── scanner.py           # Library scanning, embedding storage
├── analyzer.py          # Audio feature extraction (Librosa)
├── database.py          # SQLite operations, embedding storage
├── profiles.py          # Mood profiles, synonyms, genre keywords
├── constants.py         # Weights, sigma values, thresholds
├── lyrics_extractor.py  # Lyrics fetching (optional)
├── sentiment.py         # Emotion classification (optional)
├── frontend/            # React + shadcn/ui frontend
│   ├── src/            # Source code
│   ├── dist/           # Production build
│   └── package.json
├── static/              # Legacy vanilla JS frontend
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── lucide.js
└── presentation/        # PBL presentation slides
```

### React Frontend

The new React frontend provides a modern, beautiful UI with:
- **Sidebar Navigation** - Switch between Discover, Library, Scan, and Settings
- **Playlist Generator** - Natural language mood queries with beautiful cards
- **Library Browser** - Search, sort, and browse your music collection
- **Audio Player** - Full-featured player with progress, volume, shuffle, repeat
- **Real-time Updates** - Monitor library scanning progress
- **Keyboard Shortcuts** - Space (play/pause), arrows (navigation/volume)

**To use the React frontend:**
```bash
cd frontend
npm install
npm run build    # Creates production build in dist/
cd ..
python main.py   # FastAPI automatically serves from frontend/dist/
```

The legacy static frontend is still available as a fallback.

## Mood Profiles

Built-in profiles for 20+ moods with target audio features:

| Mood | Valence | Arousal | BPM Range |
|------|---------|---------|-----------|
| happy | +0.58 | high | 110-140 |
| sad | -0.62 | low | 60-90 |
| energetic | neutral | high | 130-180 |
| calm | neutral | low | 60-90 |
| angry | -0.35 | high | 120-160 |
| romantic | +0.35 | low | 70-100 |
| bittersweet | +0.15 | medium | 80-110 |
| anthemic | +0.45 | high | 100-140 |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/generate` | POST | Generate playlist from query |
| `/scan` | POST | Start library scan |
| `/scan/status` | GET | Get scan progress |
| `/scan/folders` | GET | List indexed folders |
| `/library/flush` | POST | Clear library |
| `/audio/{id}` | GET | Stream audio file |

## Configuration

Key parameters in `constants.py`:

```python
W_SEMANTIC = 0.40    # Semantic weight
W_FEATURES = 0.46    # Audio features weight
W_GENRE = 0.14       # Genre weight
SIGMA_BPM = 25       # BPM matching strictness
SIGMA_VALENCE = 0.5  # Valence matching strictness
```

## Performance

- **Indexing**: ~1.6 songs/second (audio extraction bottleneck)
- **Query latency**: ~15ms (pre-computed embeddings)
- **Precision@5**: 75% on test queries

## License

MIT License

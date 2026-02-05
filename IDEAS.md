# 🚀 Future Improvement Ideas for Mood Playlist Generator

*Last updated: 2026-01-07*

---

## ✅ Completed (This Session)

- [x] Upgraded to `all-mpnet-base-v2` embedding model
- [x] Single combined vector per song (mood text approach)
- [x] Krumhansl-Kessler key detection (Major/Minor)
- [x] Valence/Arousal estimation from audio
- [x] 35+ boost keywords with valence/mode constraints
- [x] Lyrics caching in separate folder
- [x] Incremental scanning (skip unchanged files)
- [x] LRCLib integration (better J-Pop lyrics)
- [x] Lyrics quality filter

---

## 📋 Priority 1: Quick Wins (1-2 hours each)

### Whisper Transcription (Hindi/Punjabi)
- Use `openai-whisper` tiny model (39MB)
- Transcribe first 60 seconds as fallback when no lyrics found
- Cache transcription results
- Languages: Hindi (`hi`), Punjabi (`pa`), Tamil (`ta`), etc.

### Audio Fingerprint Cache
- Use acoustid/chromaprint hash instead of filepath
- Same song in different folders → same cache entry
- More robust across folder switches

### Negative Keyword Boosting
- "happy but not sad" → boost happy, penalize sad
- Parse query for "not X" patterns

### Smart Lyrics Cleaning
- Strip `[Verse 1]`, `[Chorus]`, annotations
- Remove translations/romanizations
- Keep only actual lyrics for embedding

---

## 📋 Priority 2: Medium Effort (Half day each)

### Playlist History & Variety
- Remember generated playlists in SQLite
- Avoid recommending same songs repeatedly
- "Shuffle" mode that ensures variety

### User Feedback Loop
- "This song doesn't fit" button
- Store negative feedback
- Reduce score for future queries

### Genre-Aware Boosting
- If query mentions "pop", boost `genre=pop`
- Parse query for genre keywords
- Combine with mood matching

### Parallel Audio Analysis
- Currently sequential, bottleneck is librosa
- Use ThreadPoolExecutor for audio analysis
- 2-3x faster scans on multi-core

### Hindi Lyrics APIs
- Integrate Gaana/JioSaavn scraping
- Or use Musixmatch with Bollywood focus
- Region-specific lyrics sources

---

## 📋 Priority 3: Significant Investment (1-2 days)

### Audio Embeddings (CLAP/Music2Vec)
- Embed actual audio, not descriptions
- CLAP: Text-audio alignment model
- Much better mood detection without lyrics

### Key Change Detection
- Detect modulation within songs
- Some songs start minor, end major
- Better valence accuracy

### Tempo Variation Analysis
- Detect if tempo changes mid-song
- Rubato vs steady rhythm
- "Dynamic" vs "driving" classification

### Ensemble Scoring
- Combine multiple signals:
  - Embedding similarity
  - Audio features (valence/arousal)
  - Lyrics sentiment (if available)
- Learn optimal weights

---

## 📋 Priority 4: Moonshots (Multi-day R&D)

### LLM-Generated Descriptions
- Use Phi-3 or Llama to describe songs
- "This song is about heartbreak and lost love..."
- Rich semantic matching

### Mood Timeline Playlists
- "Start upbeat, transition to mellow"
- Generate journey-style playlists
- Time-based mood curves

### Cross-Song Similarity
- "Songs similar to [X]"
- Audio fingerprint similarity
- Discovery/recommendation feature

### Fine-Tuned Embedding Model
- Train on music-emotion datasets
- Domain-specific accuracy
- Could significantly boost results

### Real-Time Mood Matching
- Analyze audio during playback
- Suggest next song based on ending mood
- DJ-like flow

---

## 🐛 Known Issues to Fix

1. **Folder switching clears DB** - Maybe support multiple libraries?
2. **OVH API timeouts** - Now deprioritized under LRCLib
3. **Japanese lyrics sometimes wrong** - LRCLib should help
4. **Orphaned cache files** - Need periodic cleanup

---

## 📊 Current Performance Baseline

| Metric | Value |
|--------|-------|
| Accuracy Rating | 7/10 (user evaluation) |
| Top Score | 0.82 (after v8 changes) |
| Score Differentiation | Excellent (0.82 → 0.36) |
| Scan Time (30 songs) | ~26 seconds |
| Model Size | 438 MB |
| RAM Usage | ~1.5 GB peak |

---

*Pick up tomorrow: Whisper transcription for Hindi songs!*

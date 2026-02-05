# Backup: The "7/10" Stable System

This file captures the codebase state that achieved a 7/10 accuracy rating.
It uses `bge-small-en-v1.5` with a weighted hybrid search (Lyrics+Audio+Meta) but **WITHOUT** the Cross-Encoder Reranker and **WITHOUT** the DistilBERT sentiment pipeline that caused regressions.

---

## 1. `config.py` (Simple)
```python
import os

# Model: Lightweight BGE-Small
MODEL_EMBEDDING = "BAAI/bge-small-en-v1.5"

# Tuning Weights
WEIGHTS = {
    'lyrics': 0.5,
    'audio': 0.3,
    'meta': 0.2
}

# Paths
DB_PATH = "library.db"
EMBEDDINGS_PATH = "embeddings_v2.npz"
IDS_PATH = "ids_v2.json"
```

---

## 2. `engine.py` (No Reranker, No Logic Filter)
```python
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util
from logger import get_logger
import config
import database

log = get_logger("Engine")

class VectorEngine:
    def __init__(self):
        self.config = config
        self.model = None
        self.lyrics_embeddings = None
        self.audio_embeddings = None
        self.meta_embeddings = None
        self.ids = []

    def load_model(self):
        if self.model is None:
            log.info(f"Loading Embedding Model: {self.config.MODEL_EMBEDDING}...")
            self.model = SentenceTransformer(self.config.MODEL_EMBEDDING)
            if 'bge' in self.config.MODEL_EMBEDDING.lower():
                self.query_prefix = "Represent this sentence for searching relevant passages: "
            else:
                self.query_prefix = ""
        return self.model

    def encode(self, texts, is_query=False):
        model = self.load_model()
        if is_query and hasattr(self, 'query_prefix') and self.query_prefix:
            if isinstance(texts, str):
                texts = self.query_prefix + texts
            else:
                texts = [self.query_prefix + t for t in texts]
        return model.encode(texts, convert_to_numpy=True)

    def save_index(self, ids, lyrics_embs, audio_embs, meta_embs):
        np.savez(self.config.EMBEDDINGS_PATH, 
                 lyrics=lyrics_embs, 
                 audio=audio_embs, 
                 meta=meta_embs)
        with open(self.config.IDS_PATH, 'w') as f:
            json.dump(ids, f)
        log.info(f"Saved hybrid index with {len(ids)} items.")

    def load_index(self):
        if not os.path.exists(self.config.EMBEDDINGS_PATH) or not os.path.exists(self.config.IDS_PATH):
            return False
        
        data = np.load(self.config.EMBEDDINGS_PATH)
        self.lyrics_embeddings = data['lyrics']
        self.audio_embeddings = data['audio']
        self.meta_embeddings = data['meta']
        
        with open(self.config.IDS_PATH, 'r') as f:
            self.ids = json.load(f)
        return True

    def search(self, query, limit=20):
        if self.lyrics_embeddings is None:
            if not self.load_index():
                return []

        query_vec = self.encode(query, is_query=True)
        w = self.config.WEIGHTS
        
        # Calculate cosine similarities
        sim_lyrics = util.cos_sim(query_vec, self.lyrics_embeddings)[0].numpy()
        sim_audio = util.cos_sim(query_vec, self.audio_embeddings)[0].numpy()
        sim_meta = util.cos_sim(query_vec, self.meta_embeddings)[0].numpy()

        # Weighted Sum
        final_scores = (sim_lyrics * w['lyrics'] + sim_audio * w['audio'] + sim_meta * w['meta'])

        # Simple Sorting (No Reranking, No Filtering)
        indices = np.argsort(final_scores)[::-1][:limit]
        
        results = []
        for idx in indices:
            results.append((self.ids[idx], float(final_scores[idx])))
            
        return results

_engine_instance = VectorEngine()
def get_engine():
    return _engine_instance
```

---

## 3. `scanner.py` (No DistilBERT, No Threading Complexity)
*Note: This version uses simple multi-threading for the scraper but doesn't run heavy Transformer inference.*

```python
# ... imports ...
def process_file(filepath, enable_audio, enable_lyrics, enable_online_lyrics):
    import os
    try:
        title, artist, album, genre = get_metadata(filepath)
        
        text_meta = f"Song: {title}. Artist: {artist}. Genre: {genre}."
        
        # Audio (Librosa)
        bpm = 0.0
        energy = 0.0
        brightness = 0.0
        text_audio = "None."
        if enable_audio:
            audio_stats = analyzer.analyze_track(filepath, duration=30) 
            if audio_stats:
                bpm = audio_stats['bpm']
                energy = audio_stats['energy']
                brightness = audio_stats['brightness']
                text_audio = audio_stats['description']
        
        # Lyrics (No Sentiment Analysis)
        text_lyrics = "No lyrics available."
        has_lyrics = False
        if enable_lyrics:
            lyrics = lyrics_extractor.get_lyrics(filepath, title=title, artist=artist, allow_online=enable_online_lyrics)
            if lyrics:
                has_lyrics = True
                text_lyrics = lyrics[:500].replace('\n', ' ')

        rich_desc = f"{text_meta} Vibe: {text_audio} Lyrics: {text_lyrics[:100]}..."
        
        # Return dict WITHOUT 'sentiment' field
        return {
            'filepath': filepath,
            'title': title,
            # ... metadata ...
            'rich_desc': rich_desc,
            'bpm': bpm, 
            'energy': energy, 
            'brightness': brightness,
            'has_lyrics': has_lyrics,
            'sentiment': 0.0, # Placeholder
            'texts': {
                'meta': text_meta,
                'audio': text_audio,
                'lyrics': text_lyrics
            }
        }
    except Exception as e:
        return None
```

## 4. Why this worked (7/10)
1.  **Fast:** No heavy cross-encoders or sentiment transformers.
2.  **Stable:** Simple weighted math never returns 0.00 unless the vectors are broken.
3.  **Good Enough:** The 50% Lyric Weight was enough to push "Happy" songs to the top, even without "Hard Logic" filters.

```
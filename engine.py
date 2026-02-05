"""
v8 Engine - Simplified single-vector approach with BPM/energy boosting.
No Cross-Encoder, no sentiment ML. Just good embeddings and smart boosting.
"""
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
        self.embeddings = None  # Single vector per song
        self.ids = []

    def load_model(self):
        if self.model is None:
            log.info(f"Loading Embedding Model: {self.config.MODEL_EMBEDDING}...")
            self.model = SentenceTransformer(self.config.MODEL_EMBEDDING)
        return self.model

    def encode(self, texts, is_query=False):
        """Encode text(s) to embeddings."""
        model = self.load_model()
        return model.encode(texts, convert_to_numpy=True)

    def save_index(self, ids, embeddings):
        """Save single-vector index to disk."""
        np.save(self.config.EMBEDDINGS_PATH, embeddings)
        with open(self.config.IDS_PATH, 'w') as f:
            json.dump(ids, f)
        log.info(f"Saved index with {len(ids)} items.")

    def load_index(self):
        """Load index from disk."""
        if not os.path.exists(self.config.EMBEDDINGS_PATH) or not os.path.exists(self.config.IDS_PATH):
            log.warning("Index files not found.")
            return False
        
        self.embeddings = np.load(self.config.EMBEDDINGS_PATH)
        with open(self.config.IDS_PATH, 'r') as f:
            self.ids = json.load(f)
        
        log.info(f"Loaded index with {len(self.ids)} items.")
        return True

    def search(self, query, limit=20):
        """
        Search for songs matching the query.
        Uses cosine similarity + optional BPM/energy boosting.
        """
        if self.embeddings is None:
            if not self.load_index():
                return []

        # 1. Encode query and compute cosine similarities
        query_vec = self.encode(query)
        similarities = util.cos_sim(query_vec, self.embeddings)[0].numpy()
        
        log.info(f"Top raw similarity: {np.max(similarities):.4f}")

        # 2. Apply BPM/energy boosting if enabled
        if self.config.ENABLE_QUERY_BOOSTING:
            boosts = self._calculate_boosts(query)
            if boosts:
                # Fetch all songs in one batch query
                songs_map = database.get_songs_by_ids(self.ids)
                for i, song_id in enumerate(self.ids):
                    song = songs_map.get(song_id)
                    if song:
                        bonus = self._get_song_boost(song, boosts)
                        similarities[i] += bonus

        # 3. Sort and return top results
        indices = np.argsort(similarities)[::-1][:limit]
        
        results = []
        for idx in indices:
            results.append((self.ids[idx], float(similarities[idx])))
        
        if results:
            log.info(f"Top final score: {results[0][1]:.4f}")
            
        return results

    def _calculate_boosts(self, query):
        """Detect boost keywords in query."""
        q_lower = query.lower()
        active_boosts = []
        
        for keyword, params in self.config.BOOST_KEYWORDS.items():
            if keyword in q_lower:
                active_boosts.append(params)
                log.info(f"Boost activated: '{keyword}' -> {params}")
        
        return active_boosts

    def _get_song_boost(self, song, boosts):
        """
        Calculate total boost for a song based on active boost rules.
        Now includes valence and mode (major/minor) for emotional matching.
        """
        total_boost = 0.0
        bpm = song['bpm'] or 0
        energy = song['energy'] or 0
        valence = song['valence'] if 'valence' in song.keys() else 0
        mode = song['mode'] if 'mode' in song.keys() else ''
        brightness = song['brightness'] or 0
        
        for boost in boosts:
            matches = True
            
            # Check BPM constraints
            if 'min_bpm' in boost and bpm < boost['min_bpm']:
                matches = False
            if 'max_bpm' in boost and bpm > boost['max_bpm']:
                matches = False
                
            # Check energy constraints  
            if 'min_energy' in boost and energy < boost['min_energy']:
                matches = False
            if 'max_energy' in boost and energy > boost['max_energy']:
                matches = False
            
            # Check valence constraints (new!)
            if 'min_valence' in boost and valence < boost['min_valence']:
                matches = False
            if 'max_valence' in boost and valence > boost['max_valence']:
                matches = False
            
            # Check mode constraints (new!)
            if 'mode' in boost and mode != boost['mode']:
                matches = False
            
            # Check brightness constraints
            if 'min_brightness' in boost and brightness < boost['min_brightness']:
                matches = False
            if 'max_brightness' in boost and brightness > boost['max_brightness']:
                matches = False
            
            if matches:
                total_boost += boost.get('boost', 0.05)
        
        return total_boost


# Singleton instance
_engine_instance = VectorEngine()

def get_engine():
    return _engine_instance

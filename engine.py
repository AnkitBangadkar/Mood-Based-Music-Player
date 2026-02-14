"""
v10 Engine - Multi-signal ensemble scoring with query expansion, genre matching,
negative query parsing, emotion distribution matching, and score normalization.

Scoring formula:
  final = w_semantic * cosine_sim + w_features * feature_match + w_genre * genre_match
        + w_emotion * emotion_match - negative_penalties

This replaces the v9 system with:
- Negative query parsing ("happy but not slow", "not aggressive")
- Soft emotion distribution matching instead of binary emotion labels
- Score normalization to 0-100 for frontend display
"""

import os
import json
import re
import numpy as np
from sentence_transformers import SentenceTransformer, util
from logger import get_logger
import config
import database

log = get_logger("Engine")

# ──────────────────────────────────────────────────────────────────────
# Query Expansion: map common non-keyword terms to boost keywords
# ──────────────────────────────────────────────────────────────────────
QUERY_SYNONYMS = {
    # Activity-based
    "gym": ["energetic", "workout", "hype"],
    "running": ["energetic", "workout", "fast"],
    "jogging": ["energetic", "workout", "fast"],
    "exercise": ["energetic", "workout"],
    "training": ["energetic", "workout"],
    "driving": ["energetic", "upbeat", "fast"],
    "road trip": ["upbeat", "happy", "energetic"],
    "cooking": ["chill", "happy", "upbeat"],
    # Situation-based
    "sleeping": ["sleep", "calm", "relaxing"],
    "bedtime": ["sleep", "calm", "relaxing"],
    "rainy": ["sad", "melancholy", "calm"],
    "rain": ["sad", "melancholy", "calm"],
    "funeral": ["sad", "somber", "dark"],
    "wedding": ["romantic", "happy", "love"],
    "studying": ["study", "calm", "chill"],
    "homework": ["study", "calm", "chill"],
    "meditation": ["calm", "peaceful", "relaxing"],
    "yoga": ["calm", "peaceful", "relaxing"],
    "morning": ["happy", "upbeat", "bright"],
    "sunrise": ["happy", "uplifting", "bright"],
    "sunset": ["nostalgic", "calm", "romantic"],
    "night": ["dark", "moody", "chill"],
    "late night": ["dark", "moody", "chill"],
    # Mood synonyms
    "depressing": ["sad", "melancholy", "somber"],
    "depressed": ["sad", "melancholy", "somber"],
    "crying": ["sad", "heartbreak", "emotional"],
    "tears": ["sad", "heartbreak", "emotional"],
    "heartbroken": ["heartbreak", "sad", "emotional"],
    "grief": ["sad", "somber", "emotional"],
    "lonely": ["sad", "melancholy", "nostalgic"],
    "excited": ["energetic", "hype", "upbeat"],
    "pumped": ["energetic", "hype", "workout"],
    "hyped": ["hype", "energetic", "fast"],
    "mellow": ["calm", "chill", "relaxing"],
    "soothing": ["calm", "peaceful", "relaxing"],
    "gentle": ["calm", "peaceful", "slow"],
    "powerful": ["intense", "epic"],
    "fierce": ["intense", "aggressive", "angry"],
    "brutal": ["aggressive", "intense", "dark"],
    "gloomy": ["dark", "sad", "moody"],
    "eerie": ["dark", "mysterious", "fear"],
    "creepy": ["dark", "mysterious", "fear"],
    "spooky": ["dark", "mysterious", "fear"],
    "triumphant": ["epic", "powerful"],
    "victorious": ["epic", "powerful"],
    "anthems": ["epic", "powerful"],
    "anthem": ["epic", "powerful"],
    "cinematic": ["epic"],
    "motivational": ["energetic", "uplifting", "powerful"],
    "motivation": ["energetic", "uplifting", "workout"],
    "inspiring": ["uplifting", "positive", "epic"],
    "lo-fi": ["calm", "chill", "study"],
    "lofi": ["calm", "chill", "study"],
    "vibes": [],  # Too generic, let other words carry weight
    "songs": [],
    "music": [],
    "throwback": ["nostalgic"],
    "retro": ["nostalgic"],
    "vintage": ["nostalgic"],
    "club": ["dance", "party", "energetic"],
    "rave": ["dance", "party", "hype"],
    "edm": ["dance", "party", "energetic"],
    "ballad": ["slow", "romantic", "emotional"],
    "lullaby": ["sleep", "calm", "peaceful"],
    "wistful": ["nostalgic", "melancholy", "sad"],
    "bittersweet": ["nostalgic", "sad", "emotional"],
    "upbeat": ["upbeat"],  # Already a keyword, but include for completeness
}

# ──────────────────────────────────────────────────────────────────────
# Genre keyword mapping: query term -> list of genre substrings to match
# ──────────────────────────────────────────────────────────────────────
GENRE_KEYWORDS = {
    "rock": ["rock", "hard rock", "metal"],
    "pop": ["pop", "k-pop", "j-pop"],
    "hip hop": ["hip-hop", "rap"],
    "hip-hop": ["hip-hop", "rap"],
    "rap": ["hip-hop", "rap"],
    "electronic": ["electronic", "dance", "house", "edm"],
    "edm": ["electronic", "dance", "house"],
    "dance": ["dance", "house", "disco", "electronic"],
    "jazz": ["jazz"],
    "classical": ["classical", "klassik", "orchestra"],
    "country": ["country"],
    "metal": ["metal", "hard rock"],
    "indie": ["indie", "alternative", "alternativ"],
    "alternative": ["indie", "alternative", "alternativ"],
    "r&b": ["r&b", "soul"],
    "soul": ["soul", "r&b"],
    "disco": ["disco"],
    "anime": ["anime"],
    "j-pop": ["j-pop"],
    "k-pop": ["k-pop"],
    "folk": ["folk"],
    "punk": ["punk"],
    "soundtrack": ["soundtrack", "original soundtrack", "game soundtrack", "film"],
    "cinematic": ["soundtrack", "original soundtrack", "film soundtracks"],
    "ost": ["soundtrack", "original soundtrack", "game soundtrack"],
}

# ──────────────────────────────────────────────────────────────────────
# Query-to-feature target profiles: maps mood keywords to ideal
# audio feature ranges. Used for feature-based scoring.
# ──────────────────────────────────────────────────────────────────────
FEATURE_PROFILES = {
    # (target_value, weight) -- higher weight = more important for this mood
    # Energy: actual range 0.054-0.386 (mean 0.24)
    # BPM: actual range 60-172 (mean 113)
    # Valence: actual range -0.35 to +0.25 — targets MUST stay within this
    # Spectral rolloff: 1095-7354 Hz (dark ~3000, bright ~6000+)
    # Spectral bandwidth: 842-3310 Hz (thin ~1500, full ~2800+)
    # Dynamic range: log1p scale 0.85-12.38 (median 1.60, p90=2.38)
    #
    # Phase 1.5: mode_major weight reduced for happy/joyful (ground truth is 80% minor)
    "happy": {
        "valence": (0.20, 0.8),
        "mode_major": (True, 0.2),
        "bpm": (120, 0.5),
        "energy": (0.25, 0.5),
        "spectral_rolloff": (5500, 0.3),
        "mfcc1": (105.0, 0.25),  # Brighter timbre
    },
    "joyful": {
        "valence": (0.20, 0.8),
        "mode_major": (True, 0.2),
        "bpm": (125, 0.5),
        "energy": (0.25, 0.5),
        "spectral_rolloff": (5500, 0.3),
        "mfcc1": (105.0, 0.25),
    },
    "sad": {
        "valence": (-0.2, 1.0),
        "mode_major": (False, 0.6),
        "bpm": (80, 0.4),
        "energy": (0.12, 0.3),
        "spectral_rolloff": (3500, 0.3),
        "mfcc1": (85.0, 0.25),  # Darker timbre
        "mfcc2": (-8.0, 0.2),
    },
    "melancholy": {
        "valence": (-0.2, 1.0),
        "mode_major": (False, 0.6),
        "bpm": (80, 0.5),
        "spectral_rolloff": (3500, 0.3),
        "mfcc1": (85.0, 0.25),
        "mfcc2": (-8.0, 0.2),
    },
    "somber": {
        "valence": (-0.25, 1.0),
        "mode_major": (False, 0.7),
        "bpm": (75, 0.5),
        "spectral_rolloff": (3000, 0.3),
        "mfcc1": (80.0, 0.25),
        "mfcc2": (-10.0, 0.2),
    },
    "heartbreak": {
        "valence": (-0.2, 0.9),
        "mode_major": (False, 0.5),
        "energy": (0.12, 0.3),
        "mfcc1": (85.0, 0.25),
        "mfcc2": (-8.0, 0.2),
    },
    "joyful": {
        "valence": (0.20, 0.8),
        "mode_major": (True, 0.2),
        "bpm": (125, 0.5),
        "energy": (0.25, 0.5),
        "spectral_rolloff": (5500, 0.3),
    },
    "cheerful": {
        "valence": (0.18, 0.7),
        "mode_major": (True, 0.2),
        "bpm": (120, 0.4),
        "spectral_rolloff": (5000, 0.2),
    },
    "uplifting": {"valence": (0.15, 0.6), "mode_major": (True, 0.3), "bpm": (120, 0.4)},
    "upbeat": {"valence": (0.10, 0.4), "bpm": (120, 0.7), "energy": (0.25, 0.5)},
    "positive": {"valence": (0.15, 0.7), "mode_major": (True, 0.3)},
    "sad": {
        "valence": (-0.2, 1.0),
        "mode_major": (False, 0.6),
        "bpm": (80, 0.4),
        "energy": (0.12, 0.3),
        "spectral_rolloff": (3500, 0.3),
    },
    "melancholy": {
        "valence": (-0.2, 1.0),
        "mode_major": (False, 0.6),
        "bpm": (80, 0.5),
        "spectral_rolloff": (3500, 0.3),
    },
    "somber": {
        "valence": (-0.25, 1.0),
        "mode_major": (False, 0.7),
        "bpm": (75, 0.5),
        "spectral_rolloff": (3000, 0.3),
    },
    "heartbreak": {
        "valence": (-0.2, 0.9),
        "mode_major": (False, 0.5),
        "energy": (0.12, 0.3),
    },
    # dynamic_range targets are LOG-SCALED: log1p(raw_ratio)
    # Typical range: 0.85 (flat/compressed) to 3.5 (dramatic swells)
    # Calm/ambient songs: ~0.8-1.5 (low dynamic variation)
    # Intense/epic songs: ~2.0-3.0 (large loud-quiet contrast)
    "calm": {
        "energy": (0.10, 1.0),
        "bpm": (80, 1.0),
        "brightness": (1500, 0.4),
        "dynamic_range": (1.0, 0.4),
        "spectral_bandwidth": (1800, 0.3),
        "mfcc1": (80.0, 0.2),  # Darker, softer timbre
    },
    "relaxing": {
        "energy": (0.10, 0.8),
        "bpm": (80, 0.6),
        "dynamic_range": (1.0, 0.4),
        "spectral_bandwidth": (1800, 0.3),
        "mfcc1": (80.0, 0.2),
    },
    "peaceful": {
        "energy": (0.08, 0.8),
        "bpm": (75, 0.6),
        "valence": (0.1, 0.3),
        "dynamic_range": (1.0, 0.4),
        "spectral_bandwidth": (1800, 0.3),
        "mfcc1": (75.0, 0.2),
    },
    "chill": {"energy": (0.12, 0.8), "bpm": (90, 0.6), "dynamic_range": (1.2, 0.3)},
    "sleep": {
        "energy": (0.07, 1.0),
        "bpm": (70, 1.0),
        "dynamic_range": (0.9, 0.6),
        "spectral_bandwidth": (1500, 0.4),
    },
    "study": {"energy": (0.10, 0.8), "bpm": (85, 0.6), "dynamic_range": (1.2, 0.3)},
    "energetic": {
        "energy": (0.32, 1.0),
        "bpm": (140, 0.8),
        "spectral_bandwidth": (2800, 0.3),
    },
    "workout": {
        "energy": (0.32, 1.0),
        "bpm": (140, 0.8),
        "spectral_bandwidth": (2800, 0.3),
    },
    "fast": {"bpm": (145, 1.0), "energy": (0.28, 0.5)},
    "hype": {"energy": (0.32, 1.0), "bpm": (140, 0.8)},
    "dance": {"bpm": (125, 0.8), "energy": (0.25, 0.7)},
    "party": {"bpm": (125, 0.8), "energy": (0.25, 0.7), "valence": (0.1, 0.4)},
    "dark": {
        "mode_major": (False, 1.0),
        "brightness": (1500, 0.6),
        "valence": (-0.1, 0.5),
        "spectral_rolloff": (3000, 0.5),
    },
    "moody": {
        "valence": (-0.1, 0.7),
        "brightness": (1800, 0.5),
        "spectral_rolloff": (3500, 0.3),
    },
    "mysterious": {
        "mode_major": (False, 0.9),
        "brightness": (1500, 0.6),
        "spectral_rolloff": (3000, 0.4),
    },
    "intense": {
        "energy": (0.28, 0.8),
        "bpm": (130, 0.5),
        "dynamic_range": (1.6, 0.4),
        "spectral_bandwidth": (2600, 0.3),
    },
    "aggressive": {
        "energy": (0.32, 1.0),
        "bpm": (140, 0.8),
        "mode_major": (False, 0.5),
        "spectral_bandwidth": (2800, 0.3),
    },
    "angry": {"energy": (0.28, 1.0), "bpm": (130, 0.6), "mode_major": (False, 0.7)},
    "epic": {
        "energy": (0.22, 0.5),
        "bpm": (125, 0.3),
        "dynamic_range": (1.6, 0.5),
        "spectral_bandwidth": (2400, 0.4),
        "spectral_rolloff": (4800, 0.3),
    },
    "powerful": {
        "energy": (0.26, 0.7),
        "bpm": (120, 0.3),
        "dynamic_range": (1.6, 0.4),
        "spectral_bandwidth": (2500, 0.3),
    },
    "cinematic": {
        "dynamic_range": (1.6, 0.5),
        "spectral_bandwidth": (2300, 0.4),
        "spectral_rolloff": (4500, 0.3),
        "energy": (0.20, 0.4),
    },
    "romantic": {"bpm": (95, 0.5), "valence": (0.1, 0.5), "energy": (0.14, 0.4)},
    "love": {"valence": (0.1, 0.4), "bpm": (95, 0.3)},
    "nostalgic": {
        "mode_major": (False, 0.3),
        "bpm": (105, 0.4),
        "energy": (0.20, 0.5),
        "spectral_rolloff": (4800, 0.3),
        "spectral_bandwidth": (2500, 0.3),
    },
    "emotional": {"energy": (0.14, 0.4)},
    "bright": {
        "mode_major": (True, 0.6),
        "brightness": (3000, 0.6),
        "spectral_rolloff": (5500, 0.5),
    },
}

# ──────────────────────────────────────────────────────────────────────
# Emotion-to-query relevance: maps query mood keywords to expected
# emotion distributions for soft matching.
# Each entry is {emotion: relevance_weight} where higher = more relevant
# ──────────────────────────────────────────────────────────────────────
QUERY_EMOTION_TARGETS = {
    "happy": {"joy": 1.0, "surprise": 0.3},
    "joyful": {"joy": 1.0, "surprise": 0.2},
    "cheerful": {"joy": 0.9, "surprise": 0.3},
    "uplifting": {"joy": 0.8, "surprise": 0.4},
    "upbeat": {"joy": 0.7, "surprise": 0.3},
    "positive": {"joy": 0.8, "neutral": 0.3},
    "sad": {"sadness": 1.0, "fear": 0.2},
    "melancholy": {"sadness": 0.9, "neutral": 0.3},
    "somber": {"sadness": 0.8, "fear": 0.2},
    "heartbreak": {"sadness": 1.0, "anger": 0.2},
    "depressing": {"sadness": 1.0, "fear": 0.3},
    "dark": {"anger": 0.6, "fear": 0.6, "sadness": 0.3},
    "intense": {"anger": 0.8, "fear": 0.4},
    "aggressive": {"anger": 1.0, "disgust": 0.3},
    "angry": {"anger": 1.0, "disgust": 0.3},
    "calm": {"neutral": 0.8, "joy": 0.3},
    "peaceful": {"neutral": 0.9, "joy": 0.2},
    "relaxing": {"neutral": 0.8, "joy": 0.3},
    "romantic": {"joy": 0.5, "sadness": 0.3, "neutral": 0.3},
    "love": {"joy": 0.5, "sadness": 0.3},
    "emotional": {"sadness": 0.6, "joy": 0.3, "fear": 0.2},
    "nostalgic": {"sadness": 0.5, "joy": 0.3, "neutral": 0.2},
    "epic": {"surprise": 0.5, "joy": 0.3, "anger": 0.3},
    "powerful": {"anger": 0.5, "surprise": 0.5},
    "mysterious": {"fear": 0.7, "surprise": 0.5},
    "moody": {"sadness": 0.5, "anger": 0.3, "fear": 0.3},
    "fear": {"fear": 1.0, "surprise": 0.3},
}

# ──────────────────────────────────────────────────────────────────────
# Ensemble weights
# ──────────────────────────────────────────────────────────────────────
W_SEMANTIC = 0.40  # Sentence-transformer cosine similarity (mood text keywords)
W_FEATURES = 0.48  # Audio feature match weight (hand-crafted profiles)
W_GENRE = 0.12  # Genre match weight
W_EMOTION = (
    0.00  # Emotion distribution match weight (no songs have lyrics/emotion data yet)
)


class VectorEngine:
    def __init__(self):
        self.config = config
        self.model = None
        self.embeddings = None  # Single vector per song
        self.ids = []

    def load_model(self):
        if self.model is None:
            log.info(f"Loading Embedding Model: {self.config.MODEL_EMBEDDING}...")
            try:
                self.model = SentenceTransformer(self.config.MODEL_EMBEDDING)
            except Exception as e:
                log.warning(f"Online load failed: {e}. Trying offline cache...")
                self.model = SentenceTransformer(
                    self.config.MODEL_EMBEDDING, local_files_only=True
                )
        return self.model

    def encode(self, texts, is_query=False):
        """Encode text(s) to embeddings."""
        model = self.load_model()
        return model.encode(texts, convert_to_numpy=True)

    def save_index(self, ids, embeddings):
        """Save single-vector index to disk."""
        np.save(self.config.EMBEDDINGS_PATH, embeddings)
        with open(self.config.IDS_PATH, "w") as f:
            json.dump(ids, f)
        log.info(f"Saved index with {len(ids)} items.")

    def load_index(self):
        """Load index from disk."""
        if not os.path.exists(self.config.EMBEDDINGS_PATH) or not os.path.exists(
            self.config.IDS_PATH
        ):
            log.warning("Index files not found.")
            return False

        self.embeddings = np.load(self.config.EMBEDDINGS_PATH)
        with open(self.config.IDS_PATH, "r") as f:
            self.ids = json.load(f)

        log.info(f"Loaded index with {len(self.ids)} items.")
        return True

    def search(self, query, limit=20):
        """
        Search for songs matching the query using multi-signal ensemble scoring.

        Signals:
          1. Semantic similarity (sentence-transformer cosine sim of mood text)
          2. Audio feature matching (how well song features match query intent)
          3. Genre matching (if query mentions a genre)
          4. Emotion distribution matching (soft match against lyrics emotion scores)

        Also supports:
          - Negative query parsing ("happy but not slow", "not aggressive")
          - Score normalization to 0-100
        """
        if self.embeddings is None:
            if not self.load_index():
                return []

        # Parse negations from query
        clean_query, negated_keywords = self._parse_negations(query)

        # 1. Semantic similarity (cosine sim) - use clean query without negation words
        query_vec = self.encode(clean_query)
        raw_similarities = util.cos_sim(query_vec, self.embeddings)[0].numpy()

        max_similarity = np.max(raw_similarities)
        log.info(f"Top raw similarity: {max_similarity:.4f}")

        # 2. Expand query and detect signals
        expanded_keywords = self._expand_query(clean_query)
        genre_targets = self._detect_genre(clean_query)
        feature_profile = self._build_feature_profile(expanded_keywords)
        emotion_targets = self._build_emotion_targets(expanded_keywords)

        has_feature_signal = len(feature_profile) > 0
        has_genre_signal = len(genre_targets) > 0
        has_emotion_signal = len(emotion_targets) > 0
        has_negation = len(negated_keywords) > 0

        # Adjust weights based on available signals
        w_sem = W_SEMANTIC
        w_feat = W_FEATURES if has_feature_signal else 0.0
        w_genre = W_GENRE if has_genre_signal else 0.0
        w_emotion = W_EMOTION if has_emotion_signal else 0.0

        # Redistribute unused weight proportionally
        total_active = w_sem + w_feat + w_genre + w_emotion
        if total_active > 0:
            w_sem /= total_active
            w_feat /= total_active
            w_genre /= total_active
            w_emotion /= total_active

        log.info(
            f"Weights: Semantic={w_sem:.2f}, "
            f"Features={w_feat:.2f}, Genre={w_genre:.2f}, Emotion={w_emotion:.2f}"
        )

        # Normalize semantic scores: min-max with safe range floor
        sim_min = float(np.min(raw_similarities))
        sim_max = float(np.max(raw_similarities))
        sim_range = max(sim_max - sim_min, 0.05)
        norm_semantic = np.clip((raw_similarities - sim_min) / sim_range, 0.0, 1.0)

        # 3. Compute feature, genre, and emotion scores per song
        feature_scores = np.zeros(len(self.ids))
        genre_scores = np.zeros(len(self.ids))
        emotion_scores = np.zeros(len(self.ids))
        negation_penalties = np.zeros(len(self.ids))

        needs_songs = (
            has_feature_signal or has_genre_signal or has_emotion_signal or has_negation
        )
        songs_map = database.get_songs_by_ids(self.ids) if needs_songs else {}

        for i, song_id in enumerate(self.ids):
            song = songs_map.get(song_id)
            if not song:
                continue

            if has_feature_signal:
                feature_scores[i] = self._compute_feature_score(song, feature_profile)

            if has_genre_signal:
                genre_scores[i] = self._compute_genre_score(song, genre_targets)

            if has_emotion_signal:
                emotion_scores[i] = self._compute_emotion_score(song, emotion_targets)

            if has_negation:
                negation_penalties[i] = self._compute_negation_penalty(
                    song, negated_keywords
                )

        # Log signal info
        if has_feature_signal:
            log.info(f"Feature profile active: {list(feature_profile.keys())}")
            log.info(f"Top feature score: {np.max(feature_scores):.4f}")
        if has_genre_signal:
            log.info(f"Genre targets: {genre_targets}")
            log.info(f"Genre matches: {int(np.sum(genre_scores > 0))}")
        if has_emotion_signal:
            log.info(f"Emotion targets: {list(emotion_targets.keys())}")
            log.info(f"Top emotion score: {np.max(emotion_scores):.4f}")
        if has_negation:
            log.info(f"Negated keywords: {negated_keywords}")
            log.info(f"Songs penalized: {int(np.sum(negation_penalties > 0))}")

        # 4. Blend signals
        final_scores = (
            w_sem * norm_semantic
            + w_feat * feature_scores
            + w_genre * genre_scores
            + w_emotion * emotion_scores
            - negation_penalties
        )

        # Also apply keyword boosts from config (existing system, but lighter)
        if self.config.ENABLE_QUERY_BOOSTING:
            boosts = self._calculate_boosts(clean_query, expanded_keywords)
            if boosts:
                max_possible_boost = sum(b.get("boost", 0.05) for b in boosts)
                # Boost cap is now 15% since emotion scoring handles some of the work
                boost_cap = 0.15

                for i, song_id in enumerate(self.ids):
                    song = songs_map.get(song_id)
                    if song:
                        bonus = self._get_song_boost(song, boosts)
                        # Normalize bonus relative to max possible
                        if max_possible_boost > 0:
                            norm_bonus = (bonus / max_possible_boost) * boost_cap
                        else:
                            norm_bonus = 0
                        final_scores[i] += norm_bonus

        # 5. Normalize scores to 0-100 range
        score_min = np.min(final_scores)
        score_max = np.max(final_scores)
        score_range = score_max - score_min
        if score_range > 0:
            normalized_scores = ((final_scores - score_min) / score_range) * 100
        else:
            normalized_scores = np.full_like(final_scores, 50.0)

        # 6. Sort and return top results
        indices = np.argsort(normalized_scores)[::-1][:limit]

        results = []
        for idx in indices:
            results.append((self.ids[idx], float(normalized_scores[idx])))

        if results:
            log.info(f"Top normalized score: {results[0][1]:.1f}/100")

        return results

    def _parse_negations(self, query):
        """
        Parse negative terms from query.
        Handles patterns like:
          - "happy but not slow"
          - "not aggressive"
          - "energetic without sadness"
          - "upbeat no ballads"

        Returns:
            (clean_query, negated_keywords): query without negation phrases,
            and set of negated terms.
        """
        q = query
        negated = set()

        # Pattern: "but not X", "and not X", "not X", "without X", "no X"
        patterns = [
            r"\b(?:but\s+)?not\s+(\w+)",
            r"\bwithout\s+(\w+)",
            r"\bno\s+(\w+)",
            r"\bexcept\s+(\w+)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, q, re.IGNORECASE):
                negated_word = match.group(1).lower()
                negated.add(negated_word)
                # Also expand negated word through synonyms
                if negated_word in QUERY_SYNONYMS:
                    for syn in QUERY_SYNONYMS[negated_word]:
                        negated.add(syn)
                # Remove the negation phrase from query for embedding
                q = q[: match.start()] + q[match.end() :]

        # Clean up extra whitespace
        q = re.sub(r"\s+", " ", q).strip()

        if negated:
            log.info(f"Negation parsed: negated={negated}, clean_query='{q}'")

        return q if q else query, negated

    def _build_emotion_targets(self, keywords):
        """
        Build a merged emotion target profile from active keywords.
        Returns {emotion: target_weight} for soft emotion matching.
        """
        emotion_accum = {}

        for kw in keywords:
            if kw in QUERY_EMOTION_TARGETS:
                for emotion, weight in QUERY_EMOTION_TARGETS[kw].items():
                    if emotion not in emotion_accum:
                        emotion_accum[emotion] = []
                    emotion_accum[emotion].append(weight)

        # Merge: take max weight per emotion
        merged = {}
        for emotion, weights in emotion_accum.items():
            merged[emotion] = max(weights)

        return merged

    def _compute_emotion_score(self, song, emotion_targets):
        """
        Compute how well a song's emotion distribution matches the target.
        Uses the full 7-emotion distribution for soft matching instead of
        binary lyrics_emotion label.

        Returns 0.0 (no match) to 1.0 (perfect match).
        """
        if not emotion_targets:
            return 0.0

        # Try to get emotion_distribution from song (stored as JSON string)
        dist_str = (
            song["emotion_distribution"]
            if "emotion_distribution" in song.keys()
            else None
        )

        if dist_str:
            try:
                dist = json.loads(dist_str)
            except (json.JSONDecodeError, TypeError):
                dist = None
        else:
            dist = None

        if not dist:
            # Fall back to binary emotion matching
            song_emotion = (
                song["lyrics_emotion"] if "lyrics_emotion" in song.keys() else ""
            )
            if song_emotion and song_emotion in emotion_targets:
                return emotion_targets[song_emotion]
            return 0.0

        # Soft matching: dot product of target weights and song distribution
        # This gives partial credit for emotional similarity
        score = 0.0
        total_weight = 0.0

        for emotion, target_weight in emotion_targets.items():
            song_score = dist.get(emotion, 0.0)
            score += target_weight * song_score
            total_weight += target_weight

        if total_weight > 0:
            return score / total_weight

        return 0.0

    def _compute_negation_penalty(self, song, negated_keywords):
        """
        Compute a penalty for songs that match negated keywords.
        Checks audio features and emotion against negated profiles.

        Returns 0.0 (no penalty) to 0.3 (heavy penalty).
        """
        if not negated_keywords:
            return 0.0

        penalty = 0.0
        bpm = song["bpm"] or 0
        energy = song["energy"] or 0
        valence = song["valence"] if "valence" in song.keys() else 0
        mode = song["mode"] if "mode" in song.keys() else ""

        for neg_kw in negated_keywords:
            if neg_kw in FEATURE_PROFILES:
                profile = FEATURE_PROFILES[neg_kw]
                match_score = 0.0
                match_count = 0

                for feat, (target, weight) in profile.items():
                    if feat == "mode_major":
                        is_major = mode == "major"
                        if is_major == target:
                            match_score += weight
                        match_count += 1
                    elif feat == "bpm" and bpm > 0:
                        diff = abs(bpm - target)
                        match = np.exp(-(diff**2) / (2 * 25**2))
                        match_score += match * weight
                        match_count += 1
                    elif feat == "energy" and energy > 0:
                        diff = abs(energy - target)
                        match = np.exp(-(diff**2) / (2 * 0.12**2))
                        match_score += match * weight
                        match_count += 1

                if match_count > 0:
                    # Higher match to negated profile = higher penalty
                    avg_match = match_score / match_count
                    penalty += avg_match * 0.15  # Scale penalty

            # Check emotion negation
            if neg_kw in QUERY_EMOTION_TARGETS:
                song_emotion = (
                    song["lyrics_emotion"] if "lyrics_emotion" in song.keys() else ""
                )
                if song_emotion:
                    for emotion in QUERY_EMOTION_TARGETS[neg_kw]:
                        if song_emotion == emotion:
                            penalty += 0.10

        return min(penalty, 0.30)  # Cap total penalty

    def _expand_query(self, query):
        """
        Expand query with synonym mappings to activate more boost keywords.
        Returns deduplicated list of all relevant keywords.
        """
        q_lower = query.lower()
        words = set(re.findall(r"\b\w+(?:-\w+)*\b", q_lower))

        # Also check multi-word phrases
        expanded = set()
        for word in words:
            expanded.add(word)

        # Check single words against synonym map
        for word in words:
            if word in QUERY_SYNONYMS:
                for syn in QUERY_SYNONYMS[word]:
                    expanded.add(syn)
                    log.info(f"Query expansion: '{word}' -> '{syn}'")

        # Check multi-word phrases (e.g., "road trip", "late night")
        for phrase, syns in QUERY_SYNONYMS.items():
            if " " in phrase and phrase in q_lower:
                for syn in syns:
                    expanded.add(syn)
                    log.info(f"Query expansion: '{phrase}' -> '{syn}'")

        return expanded

    def _detect_genre(self, query):
        """Detect genre keywords in query and return matching genre substrings."""
        q_lower = query.lower()
        targets = set()

        for keyword, genres in GENRE_KEYWORDS.items():
            if re.search(r"\b" + re.escape(keyword) + r"\b", q_lower):
                targets.update(genres)
                log.info(f"Genre detected: '{keyword}' -> {genres}")

        return targets

    def _build_feature_profile(self, keywords):
        """
        Build a merged feature profile from all active keywords.
        When multiple keywords target the same feature, average their targets
        weighted by their individual weights.
        """
        feature_accum = {}  # feature -> [(target, weight), ...]

        for kw in keywords:
            if kw in FEATURE_PROFILES:
                profile = FEATURE_PROFILES[kw]
                for feat, (target, weight) in profile.items():
                    if feat not in feature_accum:
                        feature_accum[feat] = []
                    feature_accum[feat].append((target, weight))

        # Merge: weighted average of targets, max of weights
        merged = {}
        for feat, entries in feature_accum.items():
            total_weight = sum(w for _, w in entries)
            if total_weight > 0:
                avg_target = sum(t * w for t, w in entries) / total_weight
                max_weight = max(w for _, w in entries)
                merged[feat] = (avg_target, max_weight)

        return merged

    def _compute_feature_score(self, song, profile):
        """
        Compute how well a song's audio features match the target profile.
        Returns 0.0 (poor match) to 1.0 (perfect match).
        """
        if not profile:
            return 0.0

        bpm = song["bpm"] or 0
        energy = song["energy"] or 0
        valence = song["valence"] if "valence" in song.keys() else 0
        mode = song["mode"] if "mode" in song.keys() else ""
        brightness = song["brightness"] or 0
        dynamic_range = song["dynamic_range"] if "dynamic_range" in song.keys() else 0
        spectral_rolloff = (
            song["spectral_rolloff"] if "spectral_rolloff" in song.keys() else 0
        )
        spectral_bandwidth = (
            song["spectral_bandwidth"] if "spectral_bandwidth" in song.keys() else 0
        )

        total_score = 0.0
        total_weight = 0.0

        for feat, (target, weight) in profile.items():
            if feat == "mode_major":
                # Boolean match: is mode major?
                is_major = mode == "major"
                match = 1.0 if is_major == target else 0.0
                total_score += match * weight
                total_weight += weight

            elif feat == "bpm" and bpm > 0:
                # Gaussian similarity: closer to target = higher score
                diff = abs(bpm - target)
                # sigma = 25 BPM (tighter than before for better discrimination)
                match = np.exp(-(diff**2) / (2 * 25**2))
                total_score += match * weight
                total_weight += weight

            elif feat == "energy" and energy > 0:
                # For energy, we want songs NEAR the target
                diff = abs(energy - target)
                # sigma = 0.12 (calibrated to actual energy range 0.054-0.386)
                match = np.exp(-(diff**2) / (2 * 0.12**2))
                total_score += match * weight
                total_weight += weight

            elif feat == "valence":
                # For valence, direction matters more than exact value
                # If target is positive, higher valence = better
                # If target is negative, lower valence = better
                if target >= 0:
                    # Normalize: map valence from [-1,1] to [0,1]
                    match = max(0.0, min(1.0, (valence + 1) / 2))
                else:
                    # Invert: more negative = higher score
                    match = max(0.0, min(1.0, (1 - valence) / 2))
                total_score += match * weight
                total_weight += weight

            elif feat == "brightness" and brightness > 0:
                diff = abs(brightness - target)
                match = np.exp(-(diff**2) / (2 * 1000**2))
                total_score += match * weight
                total_weight += weight

            elif feat == "dynamic_range" and dynamic_range and dynamic_range > 0:
                # Gaussian similarity for dynamic range (LOG-SCALED values)
                # sigma = 1.0 (log scale range is ~0.7-3.5, so 1.0 gives good discrimination)
                diff = abs(dynamic_range - target)
                match = np.exp(-(diff**2) / (2 * 1.0**2))
                total_score += match * weight
                total_weight += weight

            elif (
                feat == "spectral_rolloff" and spectral_rolloff and spectral_rolloff > 0
            ):
                # Gaussian similarity for spectral rolloff (Hz)
                # Range: 1095-7354, sigma=1500 gives good dark/bright discrimination
                diff = abs(spectral_rolloff - target)
                match = np.exp(-(diff**2) / (2 * 1500**2))
                total_score += match * weight
                total_weight += weight

            elif (
                feat == "spectral_bandwidth"
                and spectral_bandwidth
                and spectral_bandwidth > 0
            ):
                # Gaussian similarity for spectral bandwidth (Hz)
                # Range: 842-3310, sigma=800 gives good thin/full discrimination
                diff = abs(spectral_bandwidth - target)
                match = np.exp(-(diff**2) / (2 * 800**2))
                total_score += match * weight
                total_weight += weight

            elif feat.startswith("mfcc") and len(feat) == 5:
                # MFCC coefficient scoring (mfcc0 through mfcc12)
                # Parse coefficient index
                try:
                    coeff_idx = int(feat[4])
                except ValueError:
                    continue

                # Get MFCCs from song
                try:
                    import ast

                    mfccs_raw = song.get("mfccs", "")
                    if isinstance(mfccs_raw, str) and mfccs_raw:
                        mfccs = ast.literal_eval(mfccs_raw)
                    else:
                        mfccs = mfccs_raw

                    if mfccs and isinstance(mfccs, list) and len(mfccs) > coeff_idx:
                        coeff_val = mfccs[coeff_idx]
                        # Gaussian similarity: sigma=30 works for MFCC range (std ~36)
                        diff = abs(coeff_val - target)
                        match = np.exp(-(diff**2) / (2 * 30**2))
                        total_score += match * weight
                        total_weight += weight
                except:
                    pass

        return total_score / total_weight if total_weight > 0 else 0.0

    def _compute_genre_score(self, song, genre_targets):
        """
        Check if song's genre matches any target genre.
        Returns 1.0 for match, 0.0 for no match.
        """
        song_genre = (song["genre"] or "").lower()
        if not song_genre:
            return 0.0

        for target in genre_targets:
            if target.lower() in song_genre:
                return 1.0
        return 0.0

    def _calculate_boosts(self, query, expanded_keywords=None):
        """Detect boost keywords in query (with expansion support)."""
        q_lower = query.lower()
        active_boosts = []

        check_words = (
            expanded_keywords
            if expanded_keywords
            else set(re.findall(r"\b\w+\b", q_lower))
        )

        for keyword, params in self.config.BOOST_KEYWORDS.items():
            # Use word-boundary matching for the original query
            if re.search(r"\b" + re.escape(keyword) + r"\b", q_lower):
                active_boosts.append(params)
                log.info(f"Boost activated: '{keyword}' -> {params}")
            elif expanded_keywords and keyword in expanded_keywords:
                # Also activate from expanded synonyms
                active_boosts.append(params)
                log.info(f"Boost activated (expanded): '{keyword}' -> {params}")

        return active_boosts

    def _get_song_boost(self, song, boosts):
        """
        Calculate total boost for a song based on active boost rules.
        Includes valence, mode, and lyrics_emotion constraints.
        """
        total_boost = 0.0
        bpm = song["bpm"] or 0
        energy = song["energy"] or 0
        valence = song["valence"] if "valence" in song.keys() else 0
        mode = song["mode"] if "mode" in song.keys() else ""
        brightness = song["brightness"] or 0

        for boost in boosts:
            matches = True

            if "min_bpm" in boost and bpm < boost["min_bpm"]:
                matches = False
            if "max_bpm" in boost and bpm > boost["max_bpm"]:
                matches = False
            if "min_energy" in boost and energy < boost["min_energy"]:
                matches = False
            if "max_energy" in boost and energy > boost["max_energy"]:
                matches = False
            if "min_valence" in boost and valence < boost["min_valence"]:
                matches = False
            if "max_valence" in boost and valence > boost["max_valence"]:
                matches = False
            if "mode" in boost and mode != boost["mode"]:
                matches = False
            if "min_brightness" in boost and brightness < boost["min_brightness"]:
                matches = False
            if "max_brightness" in boost and brightness > boost["max_brightness"]:
                matches = False

            if "lyrics_emotion" in boost:
                song_emotion = (
                    song["lyrics_emotion"] if "lyrics_emotion" in song.keys() else ""
                )
                if (
                    song_emotion
                    and song_emotion.lower() != boost["lyrics_emotion"].lower()
                ):
                    matches = False

            if matches:
                total_boost += boost.get("boost", 0.05)

        return total_boost


# Singleton instance
_engine_instance = VectorEngine()


def get_engine():
    return _engine_instance

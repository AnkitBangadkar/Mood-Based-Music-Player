"""
v11 Engine - Clean, modular multi-signal ensemble scoring.

Key improvements over v10:
- Consolidated FEATURE_PROFILES (no duplicates)
- Arousal support for 2D emotion model
- Pre-parsed JSON data from database
- Named constants instead of magic numbers
- Clean pipeline architecture

Scoring formula:
  final = w_sem * norm_semantic + w_feat * feature_match + w_genre * genre_match
        + w_emotion * emotion_match - negative_penalties
"""

import os
import numpy as np
from sentence_transformers import SentenceTransformer, util
from logger import get_logger

import config
import database

# Import from our clean modules
from constants import (
    W_SEMANTIC,
    W_FEATURES,
    W_GENRE,
    W_EMOTION,
    SIGMA_BPM,
    SIGMA_ENERGY,
    SIGMA_BRIGHTNESS,
    SIGMA_AROUSAL,
    SIGMA_VALENCE,
    SIGMA_DYNAMIC_RANGE,
    SIGMA_SPECTRAL_ROLLOFF,
    SIGMA_SPECTRAL_BANDWIDTH,
    SIGMA_MFCC,
    SCORE_NORMALIZATION_FLOOR,
    NEGATION_PENALTY_SCALE,
    KEY_CONFIDENCE_THRESHOLD,
    EMBEDDING_MODEL,
)
from profiles import (
    QUERY_SYNONYMS,
    GENRE_KEYWORDS,
    FEATURE_PROFILES,
    QUERY_EMOTION_TARGETS,
    NEGATION_WORDS,
)

log = get_logger("Engine")


class VectorEngine:
    def __init__(self):
        self.model = None
        self.embeddings = None
        self.ids = None
        self.embeddings_path = config.EMBEDDINGS_PATH
        self.ids_path = config.IDS_PATH

    def load_model(self):
        """Load the sentence transformer model."""
        if self.model is None:
            log.info(f"Loading embedding model: {EMBEDDING_MODEL}")
            self.model = SentenceTransformer(EMBEDDING_MODEL)
        return self.model

    def encode(self, texts):
        """Encode text(s) to embeddings."""
        model = self.load_model()
        if isinstance(texts, str):
            texts = [texts]
        return model.encode(texts, convert_to_numpy=True)

    def build_index(self, songs, save=True):
        """Build embedding index from songs."""
        if not songs:
            log.warning("No songs to index")
            return False

        model = self.load_model()
        texts = [s.get("rich_description", "") or "" for s in songs]

        log.info(f"Encoding {len(texts)} songs...")
        self.embeddings = self.encode(texts)
        self.ids = [s["id"] for s in songs]

        if save:
            self.save_index()

        log.info(
            f"Index built: {len(self.ids)} songs, embed shape: {self.embeddings.shape}"
        )
        return True

    def save_index(self):
        """Save index to disk."""
        if self.embeddings is None or self.ids is None:
            return False

        folder = os.path.dirname(self.embeddings_path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        np.save(self.ids_path.replace(".json", "_ids.npy"), self.ids)
        np.save(self.embeddings_path.replace(".npy", "_emb.npy"), self.embeddings)
        log.info(f"Index saved to {self.embeddings_path}")
        return True

    def load_index(self):
        """Load index from disk."""
        ids_path = self.ids_path.replace(".json", "_ids.npy")
        emb_path = self.embeddings_path.replace(".npy", "_emb.npy")

        if not os.path.exists(ids_path) or not os.path.exists(emb_path):
            log.warning("No index found")
            return False

        self.ids = np.load(ids_path).tolist()
        self.embeddings = np.load(emb_path)
        log.info(f"Index loaded: {len(self.ids)} songs")
        return True

    @classmethod
    def get_engine(cls):
        """Singleton accessor."""
        if not hasattr(cls, "_instance"):
            cls._instance = VectorEngine()
        return cls._instance


# ──────────────────────────────────────────────────────────────────────
# PIPELINE STEPS
# ──────────────────────────────────────────────────────────────────────


def parse_query(query):
    """
    Parse query into components.

    Returns:
        clean_query: str - query without negation words
        negated_keywords: list - keywords to penalize
    """
    query_lower = query.lower()
    words = query_lower.split()

    # Find negation words and split
    negation_found = False
    clean_parts = []
    negated_parts = []

    for word in words:
        if word in NEGATION_WORDS:
            negation_found = True
            continue

        if negation_found:
            negated_parts.append(word)
        else:
            clean_parts.append(word)

    clean_query = " ".join(clean_parts)
    negated_keywords = negated_parts

    return clean_query, negated_keywords


def expand_query(query):
    """
    Expand query with synonyms.

    Returns:
        keywords: list - expanded keywords
    """
    query_lower = query.lower()
    keywords = [query_lower]

    for term, synonyms in QUERY_SYNONYMS.items():
        if term in query_lower:
            keywords.extend(synonyms)

    # Dedupe while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    return unique_keywords


def detect_genre(query):
    """Detect genre keywords in query."""
    query_lower = query.lower()
    genre_targets = []

    for genre, keywords in GENRE_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                genre_targets.append(genre)
                break

    return genre_targets


def build_feature_profile(keywords):
    """Build audio feature profile from keywords."""
    profile = {}

    for kw in keywords:
        if kw in FEATURE_PROFILES:
            for feature, (target, weight) in FEATURE_PROFILES[kw].items():
                if feature not in profile or weight > profile[feature][1]:
                    profile[feature] = (target, weight)

    return profile


def build_emotion_targets(keywords):
    """Build emotion distribution targets from keywords."""
    targets = {}

    for kw in keywords:
        if kw in QUERY_EMOTION_TARGETS:
            for emotion, weight in QUERY_EMOTION_TARGETS[kw].items():
                if emotion not in targets or weight > targets[emotion]:
                    targets[emotion] = weight

    return targets


def compute_gaussian_match(value, target, sigma):
    """Gaussian similarity: 1.0 at target, approaches 0 as value diverges."""
    try:
        value = float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        return 0.0
    if value <= 0:
        return 0.0
    diff = abs(value - target)
    return np.exp(-(diff**2) / (2 * sigma**2))


def compute_feature_score(song, profile):
    """
    Compute how well song features match the target profile.
    Returns 0.0-1.0 score.
    """
    if not profile:
        return 0.0

    bpm = song.get("bpm", 0) or 0
    energy = song.get("energy", 0) or 0
    valence = song.get("valence", 0) or 0
    arousal = song.get("arousal", 0.5) or 0.5
    mode = song.get("mode", "") or ""
    brightness = song.get("brightness", 0) or 0
    dynamic_range = song.get("dynamic_range", 0) or 0
    spectral_rolloff = song.get("spectral_rolloff", 0) or 0
    spectral_bandwidth = song.get("spectral_bandwidth", 0) or 0

    total_score = 0.0
    total_weight = 0.0

    for feat, (target, weight) in profile.items():
        match = 0.0

        if feat == "mode_major":
            is_major = mode == "major"
            match = 1.0 if is_major == target else 0.0

        elif feat == "bpm" and bpm > 0:
            match = compute_gaussian_match(bpm, target, SIGMA_BPM)

        elif feat == "energy" and energy > 0:
            match = compute_gaussian_match(energy, target, SIGMA_ENERGY)

        elif feat == "valence" and valence != 0:
            match = compute_gaussian_match(valence, target, SIGMA_VALENCE)

        elif feat == "arousal":
            match = compute_gaussian_match(arousal, target, SIGMA_AROUSAL)

        elif feat == "brightness" and brightness > 0:
            match = compute_gaussian_match(brightness, target, SIGMA_BRIGHTNESS)

        elif feat == "dynamic_range" and dynamic_range > 0:
            match = compute_gaussian_match(dynamic_range, target, SIGMA_DYNAMIC_RANGE)

        elif feat == "spectral_rolloff" and spectral_rolloff > 0:
            match = compute_gaussian_match(
                spectral_rolloff, target, SIGMA_SPECTRAL_ROLLOFF
            )

        elif feat == "spectral_bandwidth" and spectral_bandwidth > 0:
            match = compute_gaussian_match(
                spectral_bandwidth, target, SIGMA_SPECTRAL_BANDWIDTH
            )

        elif feat.startswith("mfcc") and len(feat) == 5:
            mfcc_idx = int(feat[4]) - 1
            mfccs = song.get("mfccs", [])
            if mfccs and mfcc_idx < len(mfccs):
                match = compute_gaussian_match(mfccs[mfcc_idx], target, SIGMA_MFCC)

        total_score += match * weight
        total_weight += weight

    return total_score / total_weight if total_weight > 0 else 0.0


def compute_genre_score(song, genre_targets):
    """Compute genre matching score."""
    if not genre_targets:
        return 0.0

    song_genre = (song.get("genre", "") or "").lower()
    song_artist = (song.get("artist", "") or "").lower()

    matches = 0
    for genre in genre_targets:
        genre_keywords = GENRE_KEYWORDS.get(genre, [])
        if any(kw in song_genre or kw in song_artist for kw in genre_keywords):
            matches += 1

    return matches / len(genre_targets)


def compute_emotion_score(song, emotion_targets):
    """Compute lyrics emotion distribution matching score."""
    if not emotion_targets or not song.get("has_lyrics"):
        return 0.0

    # Get pre-parsed emotion distribution
    emotion_dist = song.get("emotion_distribution", {}) or {}
    if not emotion_dist:
        return 0.0

    # Soft matching: how well does song's emotion distribution match targets
    total_score = 0.0
    for target_emotion, target_weight in emotion_targets.items():
        song_weight = emotion_dist.get(target_emotion, 0.0)
        total_score += abs(song_weight - target_weight)

    # Normalize: 0 = no match, 1 = perfect match
    max_possible = len(emotion_targets)
    return max(0.0, 1.0 - (total_score / max_possible))


def compute_negation_penalty(song, negated_keywords):
    """Compute penalty for matching negated keywords."""
    if not negated_keywords:
        return 0.0

    penalty = 0.0
    count = 0

    for neg_kw in negated_keywords:
        if neg_kw in FEATURE_PROFILES:
            profile = FEATURE_PROFILES[neg_kw]
            match_score = compute_feature_score(song, profile)
            penalty += match_score * NEGATION_PENALTY_SCALE
            count += 1

    return penalty / count if count > 0 else 0.0


def search(query, limit=20):
    """
    Main search pipeline.

    Steps:
    1. Parse query (handle negations)
    2. Generate semantic embedding
    3. Expand query & detect signals
    4. Compute all scores
    5. Normalize and combine
    6. Return sorted results
    """
    engine = VectorEngine.get_engine()

    # Load index if needed
    if engine.embeddings is None:
        if not engine.load_index():
            return []

    # ─── STEP 1: Parse query ───
    clean_query, negated_keywords = parse_query(query)
    log.info(f"Query: '{query}' -> clean: '{clean_query}', negated: {negated_keywords}")

    # ─── STEP 2: Semantic similarity ───
    query_vec = engine.encode(clean_query)
    raw_similarities = util.cos_sim(query_vec, engine.embeddings)[0].numpy()

    log.info(f"Top raw similarity: {np.max(raw_similarities):.4f}")

    # ─── STEP 3: Gather signals ───
    keywords = expand_query(clean_query)
    genre_targets = detect_genre(clean_query)
    feature_profile = build_feature_profile(keywords)
    emotion_targets = build_emotion_targets(keywords)

    has_feature = len(feature_profile) > 0
    has_genre = len(genre_targets) > 0
    has_emotion = len(emotion_targets) > 0
    has_negation = len(negated_keywords) > 0

    # ─── STEP 4: Calculate weights ───
    w_sem = W_SEMANTIC
    w_feat = W_FEATURES if has_feature else 0.0
    w_genre = W_GENRE if has_genre else 0.0
    w_emotion = W_EMOTION if has_emotion else 0.0

    # Redistribute unused weight
    total_active = w_sem + w_feat + w_genre + w_emotion
    if total_active > 0:
        w_sem /= total_active
        w_feat /= total_active
        w_genre /= total_active
        w_emotion /= total_active

    log.info(
        f"Weights: Sem={w_sem:.2f}, Feat={w_feat:.2f}, Genre={w_genre:.2f}, Emotion={w_emotion:.2f}"
    )

    # ─── STEP 5: Normalize semantic scores ───
    sim_min = float(np.min(raw_similarities))
    sim_max = float(np.max(raw_similarities))
    sim_range = max(sim_max - sim_min, SCORE_NORMALIZATION_FLOOR)
    norm_semantic = np.clip((raw_similarities - sim_min) / sim_range, 0.0, 1.0)

    # ─── STEP 6: Compute per-song scores ───
    feature_scores = np.zeros(len(engine.ids))
    genre_scores = np.zeros(len(engine.ids))
    emotion_scores = np.zeros(len(engine.ids))
    negation_penalties = np.zeros(len(engine.ids))

    needs_songs = has_feature or has_genre or has_emotion or has_negation
    songs_map = database.get_songs_by_ids(engine.ids) if needs_songs else {}

    for i, song_id in enumerate(engine.ids):
        song = songs_map.get(song_id)
        if not song:
            continue

        if has_feature:
            feature_scores[i] = compute_feature_score(song, feature_profile)

        if has_genre:
            genre_scores[i] = compute_genre_score(song, genre_targets)

        if has_emotion:
            emotion_scores[i] = compute_emotion_score(song, emotion_targets)

        if has_negation:
            negation_penalties[i] = compute_negation_penalty(song, negated_keywords)

    # ─── STEP 7: Combine scores ───
    final_scores = (
        w_sem * norm_semantic
        + w_feat * feature_scores
        + w_genre * genre_scores
        + w_emotion * emotion_scores
        - negation_penalties
    )

    # ─── STEP 8: Get top results ───
    top_indices = np.argsort(final_scores)[::-1][:limit]

    results = []
    for idx in top_indices:
        song_id = engine.ids[idx]
        score = float(final_scores[idx])

        if score > 0:
            results.append((song_id, score))

    return results

"""
Lyrics Emotion Analyzer - Uses emotion classification model.
Maps 7 emotions to valence for improved mood matching.
"""

import threading
from logger import get_logger

log = get_logger("Sentiment")

MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"

EMOTION_TO_VALENCE = {
    "joy": 0.8,
    "surprise": 0.3,
    "neutral": 0.0,
    "anger": -0.4,
    "disgust": -0.5,
    "fear": -0.3,
    "sadness": -0.7,
}

EMOTION_MOOD_KEYWORDS = {
    "joy": ["happy", "joyful", "cheerful", "delighted", "ecstatic"],
    "surprise": ["unexpected", "surprising", "shocking"],
    "neutral": ["calm", "steady", "balanced"],
    "anger": ["angry", "furious", "rage", "mad", "intense"],
    "disgust": ["gross", "sick", "repulsed"],
    "fear": ["scared", "fearful", "terrified", "anxious", "dark"],
    "sadness": ["sad", "melancholy", "somber", "grief", "heartbroken", "depressed"],
}


class EmotionAnalyzer:
    def __init__(self):
        self.pipeline = None
        self._lock = threading.Lock()
        self._loaded = False

    def load_model(self):
        if self._loaded:
            return

        with self._lock:
            if self._loaded:
                return

            try:
                from transformers import pipeline

                log.info(f"Loading Emotion Model: {MODEL_NAME}...")
                try:
                    self.pipeline = pipeline(
                        "text-classification", model=MODEL_NAME, top_k=None, device=-1
                    )
                except Exception as e:
                    log.warning(f"Online load failed: {e}. Trying offline cache...")
                    self.pipeline = pipeline(
                        "text-classification",
                        model=MODEL_NAME,
                        top_k=None,
                        device=-1,
                        local_files_only=True,
                    )
                self._loaded = True
                log.info("Emotion model loaded successfully.")
            except Exception as e:
                log.error(f"Failed to load emotion model: {e}")
                self._loaded = True

    def _split_into_chunks(self, text, max_chars=2500):
        """
        Split lyrics into chunks that fit within the model's token limit.
        Each chunk is ~max_chars characters. Splits on paragraph/line boundaries.
        DistilRoBERTa handles ~512 tokens which is roughly 2000-3000 chars.
        """
        text = text.strip()
        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk += ("\n\n" + para) if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If a single paragraph exceeds max_chars, split by lines
                if len(para) > max_chars:
                    lines = para.split("\n")
                    current_chunk = ""
                    for line in lines:
                        if len(current_chunk) + len(line) + 1 <= max_chars:
                            current_chunk += ("\n" + line) if current_chunk else line
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = line
                else:
                    current_chunk = para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Filter out very short chunks (< 30 chars) that add noise
        return [c for c in chunks if len(c) >= 30] or [text[:max_chars]]

    def analyze(self, text):
        """
        Analyze lyrics text and return emotion info.
        Uses chunk-based analysis for long lyrics to capture the full
        emotional arc, then aggregates via weighted voting.

        Returns:
            dict: {
                'emotion': str,           # dominant emotion label
                'score': float,           # confidence 0-1
                'valence': float,         # -1 to +1 (confidence-weighted)
                'mood_words': list,       # keywords for mood text
                'emotion_distribution': dict  # {emotion: avg_score} across all chunks
            }
        """
        empty = {
            "emotion": None,
            "score": 0.0,
            "valence": 0.0,
            "mood_words": [],
            "emotion_distribution": {},
        }

        if not text or len(text.strip()) < 10:
            return empty

        self.load_model()
        if not self.pipeline:
            return empty

        try:
            chunks = self._split_into_chunks(text)

            # Accumulate emotion scores across all chunks
            emotion_totals = {e: 0.0 for e in EMOTION_TO_VALENCE}
            num_chunks = len(chunks)

            for chunk in chunks:
                result = self.pipeline(chunk)[0]
                if result:
                    for item in result:
                        label = item["label"]
                        if label in emotion_totals:
                            emotion_totals[label] += item["score"]

            # Average across chunks
            emotion_avg = {e: emotion_totals[e] / num_chunks for e in emotion_totals}

            # Dominant emotion is the one with highest average score
            top_emotion = max(emotion_avg, key=emotion_avg.get)
            top_score = emotion_avg[top_emotion]

            # Confidence-weighted valence: use full distribution instead of just top-1
            # Each emotion contributes its valence proportional to its score
            valence = sum(EMOTION_TO_VALENCE[e] * emotion_avg[e] for e in emotion_avg)

            # Mood words from top emotion, plus secondary if it's strong enough
            mood_words = list(EMOTION_MOOD_KEYWORDS.get(top_emotion, [])[:2])
            sorted_emotions = sorted(
                emotion_avg.items(), key=lambda x: x[1], reverse=True
            )
            if len(sorted_emotions) > 1 and sorted_emotions[1][1] > 0.2:
                secondary = sorted_emotions[1][0]
                secondary_words = EMOTION_MOOD_KEYWORDS.get(secondary, [])[:1]
                mood_words.extend(secondary_words)

            return {
                "emotion": top_emotion,
                "score": float(top_score),
                "valence": float(valence),
                "mood_words": mood_words,
                "emotion_distribution": {
                    e: round(s, 4) for e, s in emotion_avg.items()
                },
            }
        except Exception as e:
            log.warning(f"Emotion analysis failed: {e}")

        return empty


_analyzer = EmotionAnalyzer()


def analyze_lyrics(text):
    return _analyzer.analyze(text)

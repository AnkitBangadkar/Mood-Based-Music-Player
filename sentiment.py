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

    def analyze(self, text):
        """
        Analyze lyrics text and return emotion info.

        Returns:
            dict: {
                'emotion': str,      # e.g., 'joy', 'sadness', 'anger'
                'score': float,      # confidence 0-1
                'valence': float,   # -1 to +1 derived from emotion
                'mood_words': list   # keywords to add to mood text
            }
        """
        if not text or len(text.strip()) < 10:
            return {"emotion": None, "score": 0.0, "valence": 0.0, "mood_words": []}

        self.load_model()
        if not self.pipeline:
            return {"emotion": None, "score": 0.0, "valence": 0.0, "mood_words": []}

        try:
            truncated = text[:512]
            result = self.pipeline(truncated)[0]

            if result and len(result) > 0:
                top_emotion = result[0]["label"]
                top_score = result[0]["score"]
                valence = EMOTION_TO_VALENCE.get(top_emotion, 0.0)
                mood_words = EMOTION_MOOD_KEYWORDS.get(top_emotion, [])[:2]

                return {
                    "emotion": top_emotion,
                    "score": float(top_score),
                    "valence": valence,
                    "mood_words": mood_words,
                }
        except Exception as e:
            log.warning(f"Emotion analysis failed: {e}")

        return {"emotion": None, "score": 0.0, "valence": 0.0, "mood_words": []}


_analyzer = EmotionAnalyzer()


def analyze_lyrics(text):
    return _analyzer.analyze(text)

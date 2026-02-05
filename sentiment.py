import config
import threading
from logger import get_logger
# We delay imports of torch/transformers to keep startup fast if not needed

log = get_logger("Sentiment")

class SentimentAnalyzer:
    def __init__(self):
        self.pipeline = None
        self.model_name = config.MODEL_SENTIMENT
        self.use_deep = config.ENABLE_DEEP_SENTIMENT
        self._lock = threading.Lock()
        self._loaded = False

    def load_model(self):
        # Thread-safe model loading (scanner uses multiple threads)
        if self._loaded:
            return
            
        with self._lock:
            # Double-check after acquiring lock
            if self._loaded:
                return
                
            if self.use_deep and self.pipeline is None:
                try:
                    from transformers import pipeline
                    log.info(f"Loading Sentiment Model: {self.model_name}...")
                    
                    # Let pipeline handle device placement automatically
                    # This avoids the "meta tensor" error with newer transformers
                    self.pipeline = pipeline(
                        "sentiment-analysis", 
                        model=self.model_name,
                        device=-1  # -1 = CPU explicitly
                    )
                    self._loaded = True
                except Exception as e:
                    log.error(f"Failed to load transformer: {e}. Falling back to neutral.")
                    self.use_deep = False
                    self._loaded = True  # Mark as "loaded" to prevent retries

    def analyze(self, text):
        """
        Returns a float score from -1.0 (Negative) to 1.0 (Positive).
        """
        if not text or len(text.strip()) < 5:
            return 0.0

        if self.use_deep:
            self.load_model()
            if self.pipeline:
                # Truncate text to 512 chars to fit model context and speed it up
                # We analyze the "heart" of the lyrics (usually first chunk)
                truncated_text = text[:512]
                try:
                    result = self.pipeline(truncated_text)[0]
                    # Result ex: {'label': 'POSITIVE', 'score': 0.99}
                    label = result['label']
                    score = result['score']
                    
                    if label == 'NEGATIVE':
                        return -score
                    return score
                except Exception as e:
                    log.warning(f"Sentiment analysis failed: {e}")
                    return 0.0
        
        # Fallback / Low Tier (Placeholder for VADER)
        # For now, just return 0.0 so we don't break
        return 0.0

# Singleton
_analyzer = SentimentAnalyzer()

def analyze_text(text):
    return _analyzer.analyze(text)


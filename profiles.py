"""
All configuration dictionaries for the mood playlist engine.
Moved out from engine.py for cleaner architecture.

FEATURE_PROFILES now consolidated with Arousal support.
"""

# ──────────────────────────────────────────────────────────────────────
# QUERY SYNONYMS - map common terms to boost keywords
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
    "night": ["chill", "calm", "melancholy"],
    "evening": ["relaxing", "chill", "calm"],
    "party": ["party", "dance", "hype"],
    "date": ["romantic", "love", "chill"],
    "date night": ["romantic", "love", "chill"],
    "work": ["chill", "study", "calm"],
    "focus": ["study", "calm", "chill"],
    "concentration": ["study", "calm", "peaceful"],
    "coding": ["chill", "study", "calm"],
    "programming": ["chill", "study", "calm"],
    "gaming": ["energetic", "hype", "intense"],
    "roadtrip": ["upbeat", "happy", "energetic"],
    # Mood-based synonyms
    "cheerful": ["happy", "joyful", "upbeat"],
    "melancholic": ["melancholy", "sad", "somber"],
    "depressing": ["somber", "sad", "dark"],
    "angry": ["angry", "hate", "intense"],
    "mad": ["angry", "hate", "intense"],
    "furious": ["angry", "hate", "intense"],
    "relaxed": ["calm", "chill", "peaceful"],
    "chill": ["calm", "chill", "relaxing"],
    "laid back": ["calm", "chill", "relaxing"],
    "upset": ["sad", "angry", "melancholy"],
    "heartbroken": ["heartbreak", "sad", "somber"],
    "broke up": ["heartbreak", "sad", "melancholy"],
    "breakup": ["heartbreak", "sad", "melancholy"],
    "happy": ["happy", "joyful", "positive"],
    "sadness": ["sad", "melancholy", "somber"],
    "grief": ["somber", "sad", "melancholy"],
    "joy": ["happy", "joyful", "cheerful"],
    "excited": ["energetic", "hype", "happy"],
    "energetic": ["energetic", "workout", "hype"],
    "tired": ["calm", "sleep", "relaxing"],
    "exhausted": ["calm", "sleep", "relaxing"],
    "dreamy": ["chill", "calm", "peaceful"],
    "intense": ["intense", "angry", "energetic"],
    "powerful": ["hype", "energetic", "intense"],
    "epic": ["intense", "energetic", "hype"],
    "mysterious": ["mysterious", "dark", "moody"],
    "dark": ["dark", "somber", "moody"],
    "scary": ["dark", "intense", "fear"],
    "spooky": ["dark", "moody", "mysterious"],
    "halloween": ["dark", "mysterious", "intense"],
    "horror": ["dark", "intense", "fear"],
    "love": ["love", "romantic", "happy"],
    "in love": ["love", "romantic", "happy"],
    "crush": ["love", "romantic", "happy"],
    "heart": ["love", "romantic", "happy"],
    "beautiful": ["happy", "romantic", "peaceful"],
    "pretty": ["happy", "romantic", "positive"],
    "ugly": ["dark", "angry", "somber"],
    "metal": ["dark", "angry", "intense"],
    "rock": ["energetic", "intense", "hype"],
    "pop": ["happy", "upbeat", "energetic"],
    "jazz": ["chill", "calm", "relaxing"],
    "classical": ["calm", "peaceful", "emotional"],
    "edm": ["energetic", "dance", "hype"],
    "electronic": ["energetic", "dance", "chill"],
    "hip hop": ["energetic", "hype", "party"],
    "rap": ["energetic", "hype", "party"],
    "country": ["happy", "romantic", "upbeat"],
    "indie": ["chill", "melancholy", "emotional"],
    "lofi": ["chill", "calm", "study"],
    "lo-fi": ["chill", "calm", "study"],
    "acoustic": ["calm", "chill", "emotional"],
    "instrumental": ["calm", "study", "chill"],
    "ambient": ["calm", "peaceful", "chill"],
    "soundtrack": ["emotional", "intense", "peaceful"],
    "score": ["emotional", "intense", "peaceful"],
    "video game": ["energetic", "intense", "hype"],
    "gaming": ["energetic", "intense", "hype"],
}


# ──────────────────────────────────────────────────────────────────────
# GENRE KEYWORDS - map genre terms to match
# ──────────────────────────────────────────────────────────────────────
GENRE_KEYWORDS = {
    "pop": ["pop", "dance pop", "electropop", "synth pop"],
    "rock": ["rock", "alternative rock", "indie rock", "hard rock", "punk"],
    "metal": ["metal", "heavy metal", "death metal", "black metal", "metalcore"],
    "jazz": ["jazz", "smooth jazz", "bebop", "swing"],
    "classical": ["classical", "orchestral", "symphony", "chamber music"],
    "electronic": ["electronic", "edm", "house", "techno", "trance", "dubstep"],
    "hip hop": ["hip hop", "rap", "trap", "r&b", "soul"],
    "r&b": ["r&b", "soul", "funk", "disco"],
    "country": ["country", "folk", "americana", "bluegrass"],
    "indie": ["indie", "alternative", "dream pop", "shoegaze"],
    "folk": ["folk", "singer-songwriter", "acoustic"],
    "blues": ["blues", "delta blues", "electric blues"],
    "reggae": ["reggae", "dub", "dancehall"],
    "latin": ["latin", "salsa", "bachata", "reggaeton"],
    "ambient": ["ambient", "atmospheric", "soundscape", "drone"],
    "soundtrack": ["soundtrack", "score", "film score", "video game music"],
    "lofi": ["lofi", "lo-fi", "chillhop", "beats"],
    "punk": ["punk", "pop punk", "emo", "hardcore"],
    "dance": ["dance", "club", "house", "techno"],
    "chill": ["chill", "downtempo", "lounge"],
}


# ──────────────────────────────────────────────────────────────────────
# FEATURE PROFILES - consolidated with arousal
# ──────────────────────────────────────────────────────────────────────
# Format: "mood": {feature: (target_value, weight), ...}
#
# Key:
#   valence: -1 to +1 (sad to happy)
#   arousal: 0 to 1 (calm to excited)
#   energy: RMS 0.05-0.40
#   bpm: beats per minute
#   brightness: spectral centroid Hz
#   dynamic_range: log-scaled
#   mode_major: True/False
#   mfcc1-mfcc13: MFCC coefficients

FEATURE_PROFILES = {
    # ─── POSITIVE VALENCE (Happy/Upbeat) ───
    "happy": {
        "valence": (0.20, 0.8),
        "arousal": (0.6, 0.4),
        "mode_major": (True, 0.2),
        "bpm": (120, 0.5),
        "energy": (0.25, 0.5),
        "spectral_rolloff": (5500, 0.3),
        "mfcc1": (105.0, 0.25),
    },
    "joyful": {
        "valence": (0.20, 0.8),
        "arousal": (0.7, 0.5),
        "mode_major": (True, 0.2),
        "bpm": (125, 0.5),
        "energy": (0.25, 0.5),
        "spectral_rolloff": (5500, 0.3),
        "mfcc1": (105.0, 0.25),
    },
    "cheerful": {
        "valence": (0.18, 0.7),
        "arousal": (0.65, 0.5),
        "mode_major": (True, 0.2),
        "bpm": (120, 0.4),
        "spectral_rolloff": (5000, 0.2),
    },
    "uplifting": {
        "valence": (0.15, 0.6),
        "arousal": (0.65, 0.5),
        "mode_major": (True, 0.3),
        "bpm": (120, 0.4),
    },
    "upbeat": {
        "valence": (0.10, 0.4),
        "arousal": (0.7, 0.5),
        "bpm": (120, 0.7),
        "energy": (0.25, 0.5),
    },
    "positive": {
        "valence": (0.15, 0.7),
        "arousal": (0.55, 0.4),
        "mode_major": (True, 0.3),
    },
    "bright": {
        "valence": (0.15, 0.6),
        "arousal": (0.55, 0.4),
        "brightness": (4000, 0.5),
        "spectral_rolloff": (6000, 0.4),
    },
    # ─── NEGATIVE VALENCE (Sad/Melancholy) ───
    "sad": {
        "valence": (-0.2, 1.0),
        "arousal": (0.3, 0.5),
        "mode_major": (False, 0.6),
        "bpm": (80, 0.4),
        "energy": (0.12, 0.3),
        "spectral_rolloff": (3500, 0.3),
        "mfcc1": (85.0, 0.25),
        "mfcc2": (-8.0, 0.2),
    },
    "melancholy": {
        "valence": (-0.2, 1.0),
        "arousal": (0.25, 0.6),
        "mode_major": (False, 0.6),
        "bpm": (80, 0.5),
        "spectral_rolloff": (3500, 0.3),
        "mfcc1": (85.0, 0.25),
        "mfcc2": (-8.0, 0.2),
    },
    "somber": {
        "valence": (-0.25, 1.0),
        "arousal": (0.2, 0.7),
        "mode_major": (False, 0.7),
        "bpm": (75, 0.5),
        "spectral_rolloff": (3000, 0.3),
        "mfcc1": (80.0, 0.25),
        "mfcc2": (-10.0, 0.2),
    },
    "heartbreak": {
        "valence": (-0.2, 0.9),
        "arousal": (0.35, 0.5),
        "mode_major": (False, 0.5),
        "energy": (0.12, 0.3),
        "mfcc1": (85.0, 0.25),
        "mfcc2": (-8.0, 0.2),
    },
    "depressing": {
        "valence": (-0.25, 1.0),
        "arousal": (0.15, 0.8),
        "mode_major": (False, 0.7),
        "bpm": (70, 0.5),
        "energy": (0.08, 0.4),
        "spectral_rolloff": (2800, 0.4),
    },
    # ─── LOW AROUSAL (Calm/Relaxing) ───
    "calm": {
        "arousal": (0.2, 0.8),
        "energy": (0.10, 1.0),
        "bpm": (80, 1.0),
        "brightness": (1500, 0.4),
        "dynamic_range": (1.0, 0.4),
        "spectral_bandwidth": (1800, 0.3),
        "mfcc1": (80.0, 0.2),
    },
    "relaxing": {
        "arousal": (0.25, 0.8),
        "energy": (0.10, 0.8),
        "bpm": (80, 0.6),
        "dynamic_range": (1.0, 0.4),
        "spectral_bandwidth": (1800, 0.3),
        "mfcc1": (80.0, 0.2),
    },
    "peaceful": {
        "arousal": (0.2, 0.8),
        "energy": (0.08, 0.8),
        "bpm": (75, 0.6),
        "valence": (0.1, 0.3),
        "dynamic_range": (1.0, 0.4),
        "spectral_bandwidth": (1800, 0.3),
    },
    "chill": {
        "arousal": (0.3, 0.7),
        "energy": (0.12, 0.8),
        "bpm": (90, 0.6),
        "dynamic_range": (1.2, 0.3),
    },
    "sleep": {
        "arousal": (0.1, 1.0),
        "energy": (0.07, 1.0),
        "bpm": (55, 1.0),
        "dynamic_range": (0.9, 0.6),
        "spectral_bandwidth": (1500, 0.4),
    },
    "study": {
        "arousal": (0.25, 0.7),
        "energy": (0.10, 0.8),
        "bpm": (85, 0.6),
        "dynamic_range": (1.2, 0.3),
    },
    # ─── HIGH AROUSAL (Energetic/Hype) ───
    "energetic": {
        "arousal": (0.8, 0.8),
        "energy": (0.32, 1.0),
        "bpm": (140, 0.8),
        "spectral_bandwidth": (2800, 0.3),
    },
    "workout": {
        "arousal": (0.85, 0.9),
        "energy": (0.32, 1.0),
        "bpm": (140, 0.8),
        "spectral_bandwidth": (2800, 0.3),
    },
    "fast": {
        "arousal": (0.75, 0.7),
        "bpm": (145, 1.0),
        "energy": (0.28, 0.5),
    },
    "hype": {
        "arousal": (0.9, 0.9),
        "energy": (0.32, 1.0),
        "bpm": (140, 0.8),
    },
    "dance": {
        "arousal": (0.7, 0.7),
        "bpm": (125, 0.8),
        "energy": (0.25, 0.7),
    },
    "party": {
        "arousal": (0.75, 0.7),
        "bpm": (125, 0.8),
        "energy": (0.25, 0.7),
        "valence": (0.1, 0.4),
    },
    # ─── NEGATIVE VALENCE + HIGH AROUSAL (Angry/Intense) ───
    "angry": {
        "arousal": (0.85, 0.8),
        "energy": (0.28, 1.0),
        "bpm": (130, 0.6),
        "mode_major": (False, 0.7),
    },
    "intense": {
        "arousal": (0.8, 0.7),
        "energy": (0.28, 0.8),
        "bpm": (130, 0.5),
        "spectral_bandwidth": (2800, 0.3),
    },
    "dark": {
        "mode_major": (False, 1.0),
        "brightness": (1500, 0.6),
        "valence": (-0.5, 0.5),
        "spectral_rolloff": (3000, 0.5),
    },
    "moody": {
        "valence": (-0.1, 0.7),
        "arousal": (0.4, 0.5),
        "brightness": (1800, 0.5),
        "spectral_rolloff": (3500, 0.3),
    },
    "mysterious": {
        "mode_major": (False, 0.9),
        "brightness": (1500, 0.6),
        "arousal": (0.35, 0.5),
        "spectral_rolloff": (3000, 0.4),
    },
    # ─── POSITIVE VALENCE + LOW AROUSAL (Content/Romantic) ───
    "romantic": {
        "arousal": (0.4, 0.5),
        "bpm": (75, 0.5),
        "valence": (0.1, 0.5),
        "energy": (0.14, 0.4),
    },
    "love": {
        "arousal": (0.5, 0.5),
        "valence": (0.1, 0.4),
        "bpm": (75, 0.3),
    },
    "nostalgic": {
        "valence": (0.0, 0.6),
        "arousal": (0.35, 0.5),
        "bpm": (90, 0.4),
        "energy": (0.15, 0.3),
    },
    "emotional": {
        "valence": (0.0, 0.6),
        "arousal": (0.4, 0.5),
        "energy": (0.14, 0.4),
    },
}


# ──────────────────────────────────────────────────────────────────────
# LYRICS EMOTION TARGETS - for emotion distribution matching
# ──────────────────────────────────────────────────────────────────────
QUERY_EMOTION_TARGETS = {
    # Positive emotions
    "happy": {"joy": 1.0, "surprise": 0.3},
    "joyful": {"joy": 1.0, "surprise": 0.2},
    "cheerful": {"joy": 0.9, "surprise": 0.3},
    "uplifting": {"joy": 0.8, "surprise": 0.4},
    "upbeat": {"joy": 0.7, "surprise": 0.3},
    "positive": {"joy": 0.8, "neutral": 0.3},
    # Sad emotions
    "sad": {"sadness": 1.0, "fear": 0.2},
    "melancholy": {"sadness": 0.9, "neutral": 0.3},
    "somber": {"sadness": 0.8, "fear": 0.2},
    "heartbreak": {"sadness": 1.0, "anger": 0.2},
    "depressing": {"sadness": 1.0, "fear": 0.3},
    # Negative/high arousal emotions
    "dark": {"anger": 0.6, "fear": 0.6, "sadness": 0.3},
    "intense": {"anger": 0.8, "fear": 0.4},
    "aggressive": {"anger": 1.0, "disgust": 0.3},
    "angry": {"anger": 1.0, "disgust": 0.3},
    # Calm emotions
    "calm": {"neutral": 0.8, "joy": 0.3},
    "peaceful": {"neutral": 0.9, "joy": 0.2},
    "relaxing": {"neutral": 0.8, "joy": 0.3},
    # Romantic/love
    "romantic": {"joy": 0.5, "sadness": 0.3, "neutral": 0.3},
    "love": {"joy": 0.5, "sadness": 0.3},
    # Complex emotions
    "emotional": {"sadness": 0.6, "joy": 0.3, "fear": 0.2},
    "nostalgic": {"sadness": 0.5, "joy": 0.3, "neutral": 0.2},
    "epic": {"surprise": 0.5, "joy": 0.3, "anger": 0.3},
    "powerful": {"anger": 0.5, "surprise": 0.5},
    "mysterious": {"fear": 0.7, "surprise": 0.5},
    "moody": {"sadness": 0.5, "anger": 0.3, "fear": 0.3},
    "fear": {"fear": 1.0, "surprise": 0.3},
    "scary": {"fear": 1.0, "surprise": 0.4},
    "horror": {"fear": 1.0, "anger": 0.3},
}


# ──────────────────────────────────────────────────────────────────────
# NEGATION WORDS - words that trigger negative matching
# ──────────────────────────────────────────────────────────────────────
NEGATION_WORDS = {
    "not",
    "no",
    "without",
    "but",
    "except",
    "don't",
    "doesn't",
    "didn't",
    "won't",
    "wouldn't",
    "can't",
    "cannot",
    "never",
    "neither",
    "nor",
}

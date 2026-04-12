"""
CLAP Embedder - Audio-text alignment using CLAP (Contrastive Language-Audio Pretraining).

CLAP creates a shared embedding space where audio waveforms and text descriptions
are directly comparable via cosine similarity. This bypasses the need for
intermediate mood descriptions - the model hears the actual audio and matches
it against natural language queries.

Uses laion/clap-htsat-unfused (~700MB), runs efficiently on consumer GPUs.
Embeddings are cached in the database for incremental scanning.
"""

import os
import numpy as np
import torch
import threading
from logger import get_logger
import config

log = get_logger("CLAP")

CLAP_MODEL_NAME = config.CLAP_MODEL_NAME


class CLAPEmbedder:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    @classmethod
    def get_embedder(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = CLAPEmbedder()
        return cls._instance

    def load_model(self):
        if self.model is not None:
            return self.model

        log.info(f"Loading CLAP model: {CLAP_MODEL_NAME} on {self.device}")
        try:
            from transformers import ClapModel, ClapProcessor

            self.processor = ClapProcessor.from_pretrained(CLAP_MODEL_NAME)
            self.model = ClapModel.from_pretrained(CLAP_MODEL_NAME)
            self.model.to(self.device)
            self.model.eval()
            log.info(f"CLAP model loaded successfully on {self.device}")
        except Exception as e:
            log.error(f"Failed to load CLAP model: {e}")
            self.model = None
            self.processor = None
            raise

        return self.model

    def encode_audio(self, filepath, max_duration=30):
        """
        Encode an audio file into a CLAP embedding vector.

        Args:
            filepath: Path to the audio file.
            max_duration: Max seconds of audio to use (default 30s, centered).

        Returns:
            numpy array of shape (512,) or None if encoding fails.
        """
        self.load_model()

        try:
            import librosa

            y, sr = librosa.load(filepath, sr=48000, mono=True, duration=max_duration)

            if len(y) < sr * 0.5:
                log.warning(f"Audio too short for CLAP: {filepath}")
                return None

            max_samples = sr * max_duration
            if len(y) > max_samples:
                start = (len(y) - max_samples) // 2
                y = y[start : start + max_samples]

            inputs = self.processor(audio=y, sampling_rate=sr, return_tensors="pt")

            audio_input = inputs["input_features"].to(self.device)

            with torch.no_grad():
                audio_embed = self.model.get_audio_features(audio_input)

            # Handle both old API (tensor) and new API (BaseModelOutputWithPooling)
            if hasattr(audio_embed, "pooler_output"):
                embed = audio_embed.pooler_output.cpu().numpy().flatten()
            else:
                embed = audio_embed.cpu().numpy().flatten()
            embed = embed / (np.linalg.norm(embed) + 1e-8)
            return embed

        except Exception as e:
            log.warning(f"CLAP audio encoding failed for {filepath}: {e}")
            return None

    def encode_text(self, text):
        """
        Encode a text query into a CLAP embedding vector.

        Args:
            text: Natural language description (e.g., "angry aggressive metal song").

        Returns:
            numpy array of shape (512,) or None if encoding fails.
        """
        self.load_model()

        try:
            text_inputs = self.processor(text=[text], return_tensors="pt", padding=True)

            text_input = text_inputs["input_ids"].to(self.device)
            attention_mask = text_inputs["attention_mask"].to(self.device)

            with torch.no_grad():
                text_embed = self.model.get_text_features(
                    input_ids=text_input, attention_mask=attention_mask
                )

            # Handle both old API (tensor) and new API (BaseModelOutputWithPooling)
            if hasattr(text_embed, "pooler_output"):
                embed = text_embed.pooler_output.cpu().numpy().flatten()
            else:
                embed = text_embed.cpu().numpy().flatten()
            embed = embed / (np.linalg.norm(embed) + 1e-8)
            return embed

        except Exception as e:
            log.error(f"CLAP text encoding failed for '{text}': {e}")
            return None

    def encode_audio_batch(self, filepaths, max_duration=30):
        """
        Encode multiple audio files. Processes sequentially to avoid OOM.

        Args:
            filepaths: List of audio file paths.
            max_duration: Max seconds per file.

        Returns:
            List of numpy arrays (512,) or None for failed files.
        """
        embeddings = []
        for fp in filepaths:
            emb = self.encode_audio(fp, max_duration=max_duration)
            embeddings.append(emb)
        return embeddings


def get_embedder():
    return CLAPEmbedder.get_embedder()

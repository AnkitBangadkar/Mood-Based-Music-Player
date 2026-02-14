"""
CLAP Embedder - Contrastive Language-Audio Pretraining integration.

Uses HuggingFace transformers' built-in ClapModel to map audio and text
into the same 512-dim embedding space. This enables direct audio-text
similarity without keyword intermediaries.

Model: laion/clap-htsat-unfused (~600MB)
API:
  - get_audio_features() → L2-normalized 512-dim projected embeddings
  - get_text_features() → L2-normalized 512-dim projected embeddings

Singleton pattern: model loaded once, reused across scan and search.
"""

import os
import numpy as np
import torch
import librosa
from transformers import ClapModel, ClapProcessor
from logger import get_logger

log = get_logger("CLAP")

# CLAP expects 48kHz audio
CLAP_SR = 48000
# How many seconds of audio to use (CLAP was trained on ~10s clips,
# but longer gives more context; 30s is a good balance)
CLAP_DURATION = 30
# Offset into the track to skip intros (match analyzer.py behavior)
CLAP_OFFSET = 15
# Model identifier
CLAP_MODEL_ID = "laion/clap-htsat-unfused"

# Storage paths (alongside existing embeddings)
CLAP_EMBEDDINGS_PATH = "clap_embeddings.npy"
CLAP_IDS_PATH = "clap_ids.json"


class ClapEmbedder:
    """Singleton CLAP model wrapper for audio and text embedding."""

    def __init__(self):
        self.model = None
        self.processor = None
        self.device = None

    def _load_model(self):
        """Load CLAP model and processor (lazy, once)."""
        if self.model is not None:
            return

        # Detect device
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            log.info(f"CLAP using GPU: {torch.cuda.get_device_name(0)}")
        else:
            self.device = torch.device("cpu")
            log.info("CLAP using CPU")

        log.info(f"Loading CLAP model: {CLAP_MODEL_ID}...")
        try:
            self.processor = ClapProcessor.from_pretrained(CLAP_MODEL_ID)
            self.model = ClapModel.from_pretrained(CLAP_MODEL_ID)
        except Exception:
            log.warning("Online load failed, trying offline cache...")
            self.processor = ClapProcessor.from_pretrained(
                CLAP_MODEL_ID, local_files_only=True
            )
            self.model = ClapModel.from_pretrained(CLAP_MODEL_ID, local_files_only=True)

        self.model = self.model.to(self.device)
        self.model.eval()
        log.info("CLAP model loaded successfully.")

    def _load_audio(self, filepath):
        """
        Load audio from file for CLAP processing.
        Returns mono waveform at 48kHz, CLAP_DURATION seconds from CLAP_OFFSET.
        """
        try:
            # Get file duration first to handle short files
            duration_total = librosa.get_duration(path=filepath)

            offset = CLAP_OFFSET
            duration = CLAP_DURATION

            # If file is shorter than offset + duration, adjust
            if duration_total <= offset:
                # Very short file, start from beginning
                offset = 0
                duration = min(duration_total, CLAP_DURATION)
            elif duration_total < offset + duration:
                # File not long enough for full duration from offset
                duration = duration_total - offset

            y, sr = librosa.load(
                filepath, sr=CLAP_SR, mono=True, offset=offset, duration=duration
            )

            if len(y) == 0:
                log.warning(f"Empty audio loaded from {filepath}")
                return None

            return y

        except Exception as e:
            log.error(f"Failed to load audio {filepath}: {e}")
            return None

    def embed_audio(self, filepath):
        """
        Compute CLAP audio embedding for a file.

        Args:
            filepath: Path to audio file

        Returns:
            numpy array of shape (512,), L2-normalized. None on failure.
        """
        self._load_model()

        waveform = self._load_audio(filepath)
        if waveform is None:
            return None

        try:
            # Process audio through CLAP
            inputs = self.processor(
                audio=waveform,
                sampling_rate=CLAP_SR,
                return_tensors="pt",
            )

            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.inference_mode():
                audio_out = self.model.get_audio_features(**inputs)

            # pooler_output is overwritten with L2-normalized 512-dim projected embedding
            embedding = audio_out.pooler_output.cpu().numpy().squeeze()

            return embedding

        except Exception as e:
            log.error(f"CLAP audio embedding failed for {filepath}: {e}")
            return None

    def embed_audio_batch(self, filepaths, batch_size=4):
        """
        Compute CLAP audio embeddings for multiple files.
        Processes in batches for GPU efficiency.

        Args:
            filepaths: List of audio file paths
            batch_size: Number of files to process at once

        Returns:
            List of (filepath, embedding) tuples. Embedding is None on failure.
        """
        self._load_model()

        results = []
        batch_waves = []
        batch_paths = []

        for filepath in filepaths:
            waveform = self._load_audio(filepath)
            if waveform is None:
                results.append((filepath, None))
                continue

            batch_waves.append(waveform)
            batch_paths.append(filepath)

            if len(batch_waves) >= batch_size:
                embeddings = self._process_audio_batch(batch_waves)
                for path, emb in zip(batch_paths, embeddings):
                    results.append((path, emb))
                batch_waves = []
                batch_paths = []

        # Process remaining
        if batch_waves:
            embeddings = self._process_audio_batch(batch_waves)
            for path, emb in zip(batch_paths, embeddings):
                results.append((path, emb))

        return results

    def _process_audio_batch(self, waveforms):
        """Process a batch of waveforms through CLAP. Returns list of embeddings."""
        try:
            # Pad waveforms to same length for batching
            max_len = max(len(w) for w in waveforms)
            padded = []
            for w in waveforms:
                if len(w) < max_len:
                    w = np.pad(w, (0, max_len - len(w)))
                padded.append(w)

            inputs = self.processor(
                audio=padded,
                sampling_rate=CLAP_SR,
                return_tensors="pt",
            )

            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.inference_mode():
                audio_out = self.model.get_audio_features(**inputs)

            embeddings = audio_out.pooler_output.cpu().numpy()
            return [embeddings[i] for i in range(len(waveforms))]

        except Exception as e:
            log.error(f"CLAP batch processing failed: {e}")
            return [None] * len(waveforms)

    def embed_text(self, query):
        """
        Compute CLAP text embedding for a query string.

        Args:
            query: Text query (e.g., "happy upbeat joyful songs")

        Returns:
            numpy array of shape (512,), L2-normalized.
        """
        self._load_model()

        inputs = self.processor(
            text=[query],
            return_tensors="pt",
            padding=True,
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.inference_mode():
            text_out = self.model.get_text_features(**inputs)

        embedding = text_out.pooler_output.cpu().numpy().squeeze()
        return embedding

    def embed_texts(self, queries):
        """
        Compute CLAP text embeddings for multiple queries.

        Args:
            queries: List of text strings

        Returns:
            numpy array of shape (N, 512), L2-normalized.
        """
        self._load_model()

        inputs = self.processor(
            text=queries,
            return_tensors="pt",
            padding=True,
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.inference_mode():
            text_out = self.model.get_text_features(**inputs)

        embeddings = text_out.pooler_output.cpu().numpy()
        return embeddings


# Singleton
_clap_instance = ClapEmbedder()


def get_clap():
    return _clap_instance

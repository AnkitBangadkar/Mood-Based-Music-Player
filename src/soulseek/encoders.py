from __future__ import annotations

import hashlib
import re
import threading
from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from soulseek.domain import FloatVector

TOKEN_PATTERN = re.compile(r"[\w']+", re.UNICODE)


def _normalize(vectors: NDArray[np.float32]) -> NDArray[np.float32]:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return (vectors / norms).astype(np.float32)


class HashingTextEncoder:
    """Dependency-free deterministic encoder for tests and explicit baseline runs."""

    def __init__(self, dimensions: int = 256):
        self._dimensions = dimensions

    @property
    def encoder_id(self) -> str:
        return f"hashing-v1:{self._dimensions}"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def encode_query(self, text: str) -> FloatVector:
        return self.encode_documents([text])[0]

    def encode_documents(self, texts: Sequence[str]) -> NDArray[np.float32]:
        vectors = np.zeros((len(texts), self._dimensions), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = TOKEN_PATTERN.findall(text.casefold())
            for token in tokens:
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                number = int.from_bytes(digest, "little")
                index = number % self._dimensions
                sign = 1.0 if (number >> 8) & 1 else -1.0
                vectors[row, index] += sign
        return _normalize(vectors)


class SentenceTransformerEncoder:
    """Lazy local encoder; model details stay behind the TextEncoder contract."""

    QUERY_INSTRUCTION = (
        "Given a listener's situation, mood, activity, and exclusions, retrieve music "
        "from their library that fits the intent."
    )

    def __init__(self, model_name: str, dimensions: int, batch_size: int = 16):
        self.model_name = model_name
        self._dimensions = dimensions
        self.batch_size = batch_size
        self._model = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    @property
    def encoder_id(self) -> str:
        return f"sentence-transformers:{self.model_name}:{self._dimensions}:v1"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def _get_model(self):
        if self._model is None:
            with self._load_lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                    except ImportError as error:
                        raise RuntimeError(
                            "The ML extra is required. Run `uv sync --extra ml --extra dev`."
                        ) from error
                    self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode_query(self, text: str) -> FloatVector:
        model = self._get_model()
        prompt = f"Instruct: {self.QUERY_INSTRUCTION}\nQuery: "
        with self._inference_lock:
            result = model.encode_query(
                [text],
                prompt=prompt,
                normalize_embeddings=True,
                truncate_dim=self._dimensions,
                convert_to_numpy=True,
            )
        return np.asarray(result[0], dtype=np.float32)

    def encode_documents(self, texts: Sequence[str]) -> NDArray[np.float32]:
        if not texts:
            return np.empty((0, self._dimensions), dtype=np.float32)
        model = self._get_model()
        with self._inference_lock:
            result = model.encode_document(
                list(texts),
                batch_size=self.batch_size,
                normalize_embeddings=True,
                truncate_dim=self._dimensions,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        return np.asarray(result, dtype=np.float32)

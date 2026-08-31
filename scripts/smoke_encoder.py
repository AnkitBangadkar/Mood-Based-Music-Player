from __future__ import annotations

import argparse
import time

import numpy as np
import torch

from soulseek.encoders import SentenceTransformerEncoder


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the configured local text encoder")
    parser.add_argument("--model", default="Qwen/Qwen3-Embedding-0.6B")
    parser.add_argument("--dimensions", type=int, default=512)
    args = parser.parse_args()

    print(f"torch={torch.__version__}")
    print(f"compiled_cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"device={torch.cuda.get_device_name(0)}")

    encoder = SentenceTransformerEncoder(args.model, args.dimensions, batch_size=2)
    started = time.perf_counter()
    query = encoder.encode_query("rainy evening drive")
    documents = encoder.encode_documents(
        [
            "track: Quiet Roads. artist: Example. genre: Ambient",
            "track: Maximum Impact. artist: Example. genre: Thrash Metal",
        ]
    )
    elapsed = time.perf_counter() - started

    assert query.shape == (args.dimensions,)
    assert documents.shape == (2, args.dimensions)
    assert np.isfinite(query).all() and np.isfinite(documents).all()
    print(f"dimensions={args.dimensions}")
    print(f"similarities={(documents @ query).round(4).tolist()}")
    print(f"elapsed_seconds={elapsed:.3f}")


if __name__ == "__main__":
    main()

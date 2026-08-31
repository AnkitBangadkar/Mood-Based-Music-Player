# ADR 0001: initial text encoder

Status: accepted for the first benchmark cycle.

## Decision

Use `Qwen/Qwen3-Embedding-0.6B` through Sentence Transformers, with asymmetric query/document calls, normalized vectors, a music-retrieval query instruction, and Matryoshka truncation to 512 dimensions.

## Why

- It is a current 0.6B, Apache-2.0, instruction-aware embedding model with 100+ language support and configurable 32–1024 dimensions.
- Roughly 1.2 GB of weights fits the target RTX 4060 comfortably and the catalog is tiny enough for brute-force cosine search.
- The adapter is lazy, and its full model/config/dimension identity is stored with every vector.

## Alternatives considered

- `nomic-embed-text-v1.5`: much smaller and a credible benchmark candidate, but older and historically required model-specific code/prefix handling.
- `sentence-transformers/static-retrieval-mrl-en-v1`: fast English retrieval candidate, but the product needs subjective, compositional music intent rather than ordinary lexical passage retrieval.
- `laion/clap-htsat-unfused`: directly aligns audio and text, but adds costly audio preprocessing and represents a 2022 checkpoint already used without reliable evidence in V0. It remains an audio-aware benchmark candidate, not a default.
- BGE base v1.5: rejected as inherited legacy with no current evidence advantage.

The deterministic hashing encoder is available only for tests, zero-download demos, and an explicit lexical baseline. It is never presented as the quality model.


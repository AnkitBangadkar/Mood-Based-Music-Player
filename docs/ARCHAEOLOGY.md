# V0 archaeology findings

The old `/home/esscrimson/code/pbl2` repository was inspected read-only. No source, schema, model artifact, or frontend code was copied.

## Actual V0 path

`POST /generate` called a module-global `engine.search()`. That function parsed a few negation tokens, expanded hand-written synonyms, scored every indexed track with text embeddings, optional CLAP, audio features, genre, and lyrics emotion, min-max normalized scores over the current catalog, and returned the top N. `scanner.py` combined discovery, metadata, Librosa features, lyrics acquisition, description generation, two encoders, database writes, and index-file rebuilding.

## Evidence retained as behavior

- Incremental scans using file modification metadata are valuable.
- Embedded tags plus filename fallbacks are a practical local catalog source.
- HTTP byte-range playback is required by browser audio controls.
- Per-file scan failures should not abort a whole library scan.
- Cached derived data is necessary; expensive inference must not run on every request.

## Baseline-only evidence

- BGE, CLAP, Librosa feature formulas, lyrics emotion, synonym profiles, and ensemble weights have no privileged place in V1.
- Numpy sidecar indexes and vector blobs inside track rows are legacy storage choices, not contracts.
- V0 API payloads expose internal features and file paths and are intentionally not preserved.

## Why the reported evaluation is unreliable

`evaluator_ai.py` labels returned tracks using thresholds and keywords derived from the same features used by the ranker. It builds the “relevant” set only from retrieved results, making recall undefined and precision circular. There is no frozen human judgment set or held-out test split. Those numbers must not be used as a V1 benchmark.


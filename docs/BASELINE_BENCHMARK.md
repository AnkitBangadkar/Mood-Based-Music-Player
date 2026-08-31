# Qwen text baseline — development benchmark

Run date: 2026-08-31

The first valid baseline was produced after repairing all 506 catalog rows from the portable
manifest and regenerating their Qwen embeddings. The full result is locally reproducible with:

```bash
uv run python scripts/benchmark_recommender.py songs_for_research --scan-first \
  --output benchmarks/results/qwen-dev-v1.json
```

## Aggregate

| Metric | Result |
| --- | ---: |
| Precision@10 | 0.325 |
| Recall@10 | 0.075 |
| NDCG@10 | 0.325 |
| Playlist fill rate | 1.000 |
| Artist diversity | 1.000 |
| Warm query latency | 44.7 ms |

The labels are curated manifest contrast roles withheld from retrieval text. They are suitable for
development comparisons, not final claims; the final test set still requires frozen human relevance
judgments for complete natural-language requests.

## Failure slices

- Strong: angry (1.00 P@10), party (0.60), focus (0.50), sad (0.40).
- Middling: happy, workout, and sleepy (0.30 each).
- Weak: romantic and calm (0.20), energetic (0.10).
- Complete misses: nostalgic and nostalgic-vs-sad (0.00).

The next experiment should target contextual distinctions that catalog text alone does not express,
especially nostalgia versus sadness and energy versus anger. It must beat this frozen baseline without
regressing latency, playlist fill, or exclusion behavior enough to harm the local interactive product.

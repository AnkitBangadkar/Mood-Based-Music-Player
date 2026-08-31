# Research corpus audit

Audit date: 2026-08-31. The audit is read-only and reproducible with:

```bash
uv run python scripts/audit_research_corpus.py songs_for_research --hashes
```

## Result

- 506 manifest entries and 506 corresponding audio files
- 506/506 files readable by Mutagen and ffprobe
- 321 unique normalized artist names
- no missing audio, unlisted audio, duplicate manifest IDs, or blank manifest fields
- five exact duplicate-audio groups
- six duplicate artist/title groups; `Avicii — Levels` is the only logical duplicate whose audio hashes differ
- nine tracks longer than ten minutes
- 506 stale absolute paths in the legacy `corpus.db`

## Required cleanup before evaluation

1. Treat duplicate audio and duplicate artist/title entries as one group during data splitting. A
   track or alternate download must never occur in both development and held-out sets.
2. Audit the nine long tracks. `Q4_006` (“Aruarian Dance”, 32:25) is particularly suspicious;
   longer classical, ambient, and sleep works may be legitimate but need intentional excerpting.
3. Ignore or rebuild the legacy `corpus.db`; the application now reads the portable JSON manifest
   and resolves audio paths relative to the selected corpus root.
4. Keep audio outside Git. Only code, schemas, and legally shareable annotations should be pushed.
5. Obtain human relevance judgments for complete natural-language queries. Quadrants and primary
   moods provide stratification labels, not sufficient relevance truth.

## Evaluation posture

The corpus is strong enough for development, demonstrations, contrast tests, and a small frozen
benchmark. It is intentionally balanced and therefore does not represent the natural frequency of
music in a user's library. Report results both overall and by query family, and keep a held-out test
split untouched until the final comparison.


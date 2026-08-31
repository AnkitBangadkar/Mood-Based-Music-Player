# SoulSeek

SoulSeek is a local-first music backend that turns a request such as “rainy evening drive” into a cohesive playlist from the user's own library.

## Concise build plan

1. **V1 (implemented here):** scan and version the local catalog, index track text, interpret requests and exclusions, retrieve/rank/diversify, stream audio, and collect feedback behind `/api/v1`.
2. **Frontend (Gemini):** build React + TypeScript only against the frozen API contract in [`docs/FRONTEND_HANDOFF.md`](docs/FRONTEND_HANDOFF.md).
3. **Quality cycle:** create a small train/dev/test judgment set, compare the text baseline with audio-aware candidates, then keep only measured improvements.

## Run locally

Python 3.12–3.13 and [`uv`](https://docs.astral.sh/uv/) are expected.

```bash
uv sync --extra ml --extra dev
uv run soulseek
```

The API runs at `http://127.0.0.1:8000`; OpenAPI is at `/docs`. The first real scan downloads `Qwen/Qwen3-Embedding-0.6B` once, then inference is local. To run the dependency-free lexical baseline instead:

```bash
SOULSEEK_ENCODER_BACKEND=hashing uv run soulseek
```

Scan a library:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/library/scans \
  -H 'Content-Type: application/json' \
  -d '{"root":"/absolute/path/to/music"}'
```

The curated research corpus is detected automatically when the selected root contains
`data/manifest.json` and `audio/`. Its descriptive catalog metadata is indexed, while its mood
judgments remain reserved for evaluation.

Audit that corpus without changing it:

```bash
uv run python scripts/audit_research_corpus.py songs_for_research --hashes
```

Run verification:

```bash
uv run ruff check .
uv run pytest
```

After indexing the research corpus with the active Qwen encoder, run the frozen development
benchmark:

```bash
uv run python scripts/benchmark_recommender.py songs_for_research --scan-first \
  --output benchmarks/results/qwen-dev-v1.json
```

The development benchmark uses withheld manifest contrast labels as proxy judgments. It is useful
for iteration, but final quality claims require a separately frozen set of human judgments.

Configuration uses `SOULSEEK_` environment variables. Runtime state defaults to `./data/` and is intentionally excluded from version control.

## Repository map

- `src/soulseek/api.py` — stable HTTP boundary
- `src/soulseek/storage.py` — SQLite schema and persistence
- `src/soulseek/scanning.py` — incremental ingestion and persistent job state
- `src/soulseek/recommender.py` — intent, retrieval, ranking, diversification
- `src/soulseek/encoders.py` — replaceable encoder implementations
- `src/soulseek/research.py` — read-only research corpus auditing
- `docs/` — archaeology, decisions, architecture, and frontend handoff

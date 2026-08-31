# V1 architecture

Offline flow:

`filesystem provider → metadata ingestion → SQLite track catalog → versioned encoder → embedding table`

Online flow:

`prompt → intent/exclusions → broad cosine retrieval → semantic + lexical rank → MMR-style diversification → persisted playlist → feedback`

## Stable boundaries

- `CatalogProvider` owns discovery and metadata extraction.
- `TextEncoder` owns model loading, prompts, dimensions, and vector production.
- `Store` owns schema and serialization; routes never read vectors or filesystem paths directly.
- `RecommendationService` owns retrieval, rank composition, and diversification.
- Pydantic response models under `/api/v1` are the frontend contract.

The full catalog is searched in memory because the expected 500–800 tracks make an external vector database unnecessary. Embeddings are normalized float32 values keyed by `encoder_id`; changing a model creates a new index namespace instead of silently reusing incompatible vectors.

The provider router recognizes the curated research-corpus layout. It indexes ordinary catalog
facts—title, artist, genre, tempo class, production style, vocal type, language, and decade—but
deliberately excludes quadrant, mood, contrast role, valence/arousal, and rationale. Those fields
are judgments for evaluation and must not leak into retrieval documents.

## Deliberately deferred

- CLAP/audio embeddings and learned ranking until the frozen judgments show value.
- Online lyrics scraping, because it weakens local-first behavior and introduces data/licensing uncertainty.
- User accounts, cloud sync, distributed workers, and a vector database.
- Learned feedback personalization until enough real labels exist.

# SoulSeek — Continuation Brief

## Project Goal

SoulSeek is a local-first music player that turns a natural-language intent—such as “rainy evening driving” or “angry workout”—into a playlist drawn from the user's own music library.

It must interpret human context, retrieve plausible tracks, rank them, and assemble a cohesive playlist. It is a college project: prioritize a clean, demonstrable, locally deployable system over production-scale features or research-grade ML.

## Project Facts

- Frontend target: React + TypeScript; backend target: Python/FastAPI; local catalog/storage.
- Hardware: one RTX 4060. Prefer local pretrained inference and lightweight methods; do not train large models.
- Existing corpus: about 260 real tracks. Enough to begin; grow deliberately toward roughly 500–800 diverse tracks for the final demonstration.
- Existing `pbl2` repository: a messy, working prototype. It is read-only archaeological reference, not source code to port by default.
- User is product owner. Codex acts as technical lead and later delegates bounded frontend work to Gemini/Antigravity.

## Mission

Rebuild SoulSeek from a messy heuristic prototype into a local-first, evaluated natural-language music recommender. Do not preserve complexity for its own sake.

**No backward-compatibility obligation exists.** Remove or replace code, models, data formats, and ideas that are inefficient or do not earn their place. The prototype is evidence, not a foundation.

## Current Prototype

- Treat the existing system as an archaeological reference only.
- It combines BGE, CLAP, Librosa features, metadata, lyrics/emotion, keyword profiles, and manually tuned weights.
- Current path: query parsing/expansion → score every track with mixed heuristics → top N.
- It has no clean retrieval/ranking split, no playlist diversification, and no learned ranker.
- First understand the prototype sufficiently to extract useful lessons. Do not spend time reproducing it unless a specific comparison needs it.

## Target Architecture

Offline: catalog provider → ingestion → versioned metadata/audio/lyrics/embeddings → catalog store.

Online: query understanding → intent and exclusions → retrieve broad candidates → rank → diversify → playlist → feedback.

Evaluation runs independently: fixed query/relevance set → benchmark each change → keep or reject.

## Foundation Rule

- Build stable boundaries around volatile technology. Encoders, CLAP, audio-feature extractors, catalog providers, and rankers are replaceable implementations behind small explicit contracts.
- Do not let a model's vector format, package, or scoring assumptions leak into API routes, catalog storage, playlist logic, or the frontend.
- Do not create abstraction for hypothetical futures. Add a boundary only where a component is genuinely expected to change or is independently testable.
- **No legacy component is a default.** Before carrying forward BGE, CLAP, an audio feature, a schema, or a workflow, state the problem it solves, survey current viable alternatives, and record why it won the decision.

## Product Semantics

- Human intent is primary; valence/arousal are supporting signals, not the whole recommendation model.
- Example: “rainy evening driving” implies reflective, calm, nostalgic, mildly sad, and driving-suitable.
- “Angry” implies high arousal plus negative/tense emotional character; high energy alone is insufficient.
- “Nostalgic” is semantic and subjective; do not invent a single authoritative feature for it.

## Operating Rules

1. Build a clean first version; use prototype findings only where they provide evidence.
2. Keep evaluation lightweight: a small frozen set of representative queries and human relevance judgments is sufficient for this college project. Do not build research-grade infrastructure.
3. Hold out a small test subset. Do not tune against the results reported from it.
4. Run only decision-relevant comparisons between candidates that could plausibly survive. Use a learned ranker only if labels support it.
5. Keep the frontend behind a stable API contract; it must not dictate recommender internals.
6. Prefer simple modules and explicit data contracts over framework-heavy architecture.
7. No premature model, dataset, or orchestration commitment.

## Model Position

- BGE base v1.5 is an older text encoder and has no presumed place in the rebuild.
- Start encoder selection from current local options that fit the RTX 4060 and local-first requirement. Use only the chosen model; do not inherit BGE as a provisional default.

## Immediate Next Work: Read-Only Archaeology

- Map actual V0 call paths, stored data, model/index lifecycle, and API contract.
- Identify what is baseline-only evidence versus reusable building blocks.
- Audit the current tests and evaluator scripts; do not accept current Precision@5 as reliable until the methodology is verified.
- Produce a minimal rebuild boundary before authorizing code changes.

## Roles

- User: product owner; decides product direction and major trade-offs.
- Codex: technical lead; owns architecture, backend, recommender, evaluation, integration, and review.
- Gemini: bounded frontend worker only—React, TypeScript, UI/UX, API wiring, and frontend tests—working from written specs and API contracts.

## Repository Rule

- Do not add agent names, email addresses, signatures, co-author trailers, or contributor attribution to source files, commits, pull requests, or pushes. Do not change Git identity settings. Use the repository's existing user identity only after confirming it is configured appropriately.

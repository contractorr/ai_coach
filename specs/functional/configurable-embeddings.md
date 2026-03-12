# Configurable Embedding Provider

**Status:** Draft
**Author:** Claude
**Date:** 2026-03-12

## Problem

The app uses a deterministic hash-based bag-of-words function (256 dims) for all vector operations — journal search, intel dedup, RAG retrieval, thread detection. This produces lexical overlap matches, not semantic understanding. Replacing it with real embedding models (Gemini, OpenAI) significantly improves retrieval quality across all surfaces.

## Users

All users — improved semantic search in journal, better intel dedup, more relevant RAG context for advisor answers.

## Desired Behavior

1. By default, the system auto-detects the best available embedding provider based on which API keys are present (Gemini → OpenAI → hash fallback)
2. Users can override the provider in `config.yaml` under `embeddings.provider`
3. If no API key is available, the system silently falls back to the existing hash-based function — no errors, no degraded UX
4. After switching providers, users run `coach db rebuild --collection all` to re-embed existing data with the new model
5. All vector operations (journal, intel, memory, threads) use the same embedding provider for consistency

## Acceptance Criteria

- [ ] Auto-detects Gemini when `GOOGLE_API_KEY` is set, OpenAI when `OPENAI_API_KEY` is set
- [ ] Falls back to hash function when no embedding API key is present
- [ ] `embeddings.provider` config accepts: `auto`, `gemini`, `openai`, `hash`
- [ ] `embeddings.model` and `embeddings.dimensions` are optional overrides
- [ ] Existing tests pass without API keys (hash fallback activates)
- [ ] Memory FactStore uses the shared embedding function instead of ChromaDB's built-in ONNX
- [ ] Batch size limits respected (Gemini: 100 texts/request)

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| API key set but invalid | Fail on first embed call; log warning; no silent data loss |
| Switch provider mid-use | Old embeddings incompatible; `coach db rebuild` required |
| Empty input text | Return zero vector of correct dimensions |
| Very long input text | Truncate to model's token limit before sending |
| Network timeout on embed call | Retry with backoff; fall through to error |

## Out of Scope

- Automatic re-embedding on provider switch (manual rebuild required)
- Threshold auto-calibration for new embedding models
- Local/ONNX embedding models (removed, superseded by API providers)

## Open Questions

- Should similarity thresholds (0.78–0.92) be auto-adjusted per provider, or left for manual tuning?

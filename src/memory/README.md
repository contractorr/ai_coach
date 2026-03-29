# Memory Package

Persistent fact storage, extraction, and consolidation logic live here.

## Entry Points

- `store.py`: fact persistence and retrieval
- `pipeline.py`: extract and consolidate observations
- `resolver.py`: conflict resolution
- `models.py`: memory data structures

## Invariants

- Memory writes must remain user-scoped.
- Soft-delete and visibility semantics must stay consistent across API and retrieval paths.
- `store.py` is a hotspot; extract helpers before adding more branching.

## Validation

- `just test-memory`
- `uv run pytest tests/memory/test_store.py tests/memory/test_pipeline.py -q`
- `uv run pytest tests/web/test_memory_routes.py -q`

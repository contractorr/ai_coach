# Memory Observation Consolidation

## Problem

Individual memory facts are granular and lack synthesis. When the system stores "User uses Python for data pipelines", "User prefers Python over Java", and "User is learning Python async patterns", the advisor treats them as 3 separate signals instead of recognizing a cohesive pattern.

## Desired Behavior

A consolidation step synthesizes related raw facts into higher-level **observations** — one sentence capturing the overall pattern. Observations evolve as new facts are added and preserve contradiction narratives (e.g. "User moved from React to Vue").

### Triggers

- **Incremental**: after any memory pipeline run that stores/updates facts
- **Full pass**: on backfill, manual CLI command, or scheduled cron (default 3am daily)

### Output

Observations appear in the `<user_memory>` XML block under a dedicated `## Observations` section, above raw fact categories. They use `*` bullet (vs `-` for raw facts).

## Acceptance Criteria

1. Facts sharing an entity link (e.g. "Python") are grouped and synthesized into one observation
2. Groups with fewer than `min_facts_per_group` (default 2) are skipped
3. Unchanged fact groups don't trigger redundant LLM calls
4. When a source fact is deleted and an observation loses all active sources, the observation is auto-deleted
5. Observations appear in advisor RAG context and are queryable via MCP tool
6. Consolidation failures (LLM errors) are logged and silently skipped — no crash

## Edge Cases

- Single-fact entities: no observation generated
- Contradictory facts: LLM preserves evolution narrative
- Fact deletion cascades: orphaned observations cleaned up
- Concurrent pipeline runs: SQLite WAL mode handles contention
- Entity-less facts: excluded from consolidation in Phase 1

# Memory Observation Consolidation — Technical Spec

## Schema Changes (v3)

```sql
CREATE TABLE observation_sources (
    observation_id TEXT NOT NULL REFERENCES steward_facts(id),
    fact_id TEXT NOT NULL REFERENCES steward_facts(id),
    PRIMARY KEY (observation_id, fact_id)
);
CREATE INDEX idx_obs_sources_obs ON observation_sources(observation_id);
CREATE INDEX idx_obs_sources_fact ON observation_sources(fact_id);
```

## Model Additions

- `FactCategory.OBSERVATION = "observation"`
- `FactSource.CONSOLIDATION = "consolidation"`

## Components

### `ObservationConsolidator` (`src/memory/consolidator.py`)

```python
class ObservationConsolidator:
    def __init__(self, store: FactStore, provider=None, min_facts_per_group: int = 2)
    def consolidate_affected(self, fact_ids: list[str]) -> list[StewardFact]
    def consolidate_all(self) -> list[StewardFact]
```

- Grouping: `fact_entity_links` → group by `entity_id` (normalized name)
- Skip groups with `< min_facts_per_group` facts
- Skip unchanged groups (same source fact IDs as existing observation)
- LLM synthesis via cheap provider; failures logged + skipped
- Observations stored as `StewardFact(category=OBSERVATION, source_type=CONSOLIDATION, source_id=entity_key)`
- Source links via `store.link_observation_sources()`

### `FactStore` additions (`src/memory/store.py`)

- `link_observation_sources(observation_id, fact_ids)` — bulk insert junction
- `get_observation_source_ids(observation_id)` → `list[str]`
- `get_observations_for_fact(fact_id)` → `list[StewardFact]`
- `get_all_active_observations()` → `list[StewardFact]`
- `delete()` — after soft-delete, clean `observation_sources` rows, orphan-check observations
- `reset()` — also truncates `observation_sources`

### `MemoryPipeline` changes

- New `consolidator` param in `__init__()`
- `_maybe_consolidate()` called after `_execute()` in all public entry points
- `backfill()` calls `consolidator.consolidate_all()` at end

### RAG injection (`src/advisor/rag.py`)

- `get_memory_context()` fetches observations via `get_all_active_observations()`
- `_format_memory_block()` prepends `## Observations` section with `*` bullets

### MCP tool

`memory_list_observations` — returns observations with supporting fact IDs

### Scheduler

`run_memory_consolidation()` + `_schedule_memory_consolidation_job()` — config-gated, default cron `0 3 * * *`

## LLM Prompt

```
You synthesize memory observations from individual facts about a user.
Given these facts about "{entity_name}": ...
Write ONE sentence... Start with "User..."
```

## Config

```yaml
memory:
  consolidation:
    enabled: true
    min_facts_per_group: 2
    run_cron: "0 3 * * *"
```

## Error Paths

- LLM failure: per-group catch, log warning, skip group
- Missing entity links: group has 0 facts → filtered out
- Orphaned observations: auto-deleted when all source facts deleted
- Pipeline consolidation failure: caught in `_maybe_consolidate`, logged, does not block pipeline

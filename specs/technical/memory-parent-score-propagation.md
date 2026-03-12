# Parent-Score Propagation — Technical Spec

**Status:** Draft
**Issue:** #145 Phase 2
**Date:** 2026-03-12

## Overview

Replace flat RRF in `_graph_expand_and_merge` with OpenViking-style parent-score propagation. Embedding similarity scores flow from seeds → entity groups → neighbor facts.

## Changes

### 1. `_chroma_search` — return scores

Current: returns `list[StewardFact]`, discards ChromaDB distances.

New: returns `list[tuple[StewardFact, float]]` where float is similarity score (1 - cosine_distance, since ChromaDB uses cosine space and returns distances).

```python
def _chroma_search(
    self, query: str, limit: int, categories: list[FactCategory] | None = None
) -> list[tuple[StewardFact, float]]:
    # ... existing query logic ...
    distances = results["distances"][0]  # already fetched but unused
    facts_with_scores = []
    for idx, fid in enumerate(results["ids"][0]):
        if fid in active_ids:
            fact = self.get(fid)
            if fact:
                score = 1.0 - distances[idx]  # cosine distance → similarity
                facts_with_scores.append((fact, score))
        if len(facts_with_scores) >= limit:
            break
    return facts_with_scores
```

`_keyword_search` unchanged — returns `list[StewardFact]` (no embedding scores).

### 2. `search()` — adapt to scored results

```python
def search(
    self, query: str, limit: int = 10,
    categories: list[FactCategory] | None = None,
    use_graph: bool = True, graph_limit: int = 5,
    alpha: float = 0.5,
) -> list[StewardFact]:
    coll = self._chroma
    if not coll:
        seeds = self._keyword_search(query, limit, categories)
        # No scores — use existing RRF path
        if use_graph and seeds:
            return self._graph_expand_and_merge(seeds, limit, graph_limit, categories)
        return seeds[:limit]

    scored_seeds = self._chroma_search(query, limit, categories)
    if not use_graph or not scored_seeds:
        return [f for f, _ in scored_seeds][:limit]

    return self._propagate_and_merge(scored_seeds, limit, graph_limit, categories, alpha)
```

### 3. `_propagate_and_merge` — new method replacing `_graph_expand_and_merge` for scored path

```python
def _propagate_and_merge(
    self,
    scored_seeds: list[tuple[StewardFact, float]],
    limit: int,
    graph_limit: int,
    categories: list[FactCategory] | None = None,
    alpha: float = 0.5,
) -> list[StewardFact]:
```

**Step 1 — Build seed score map:**
```python
seed_scores: dict[str, float] = {f.id: score for f, score in scored_seeds}
fact_map: dict[str, StewardFact] = {f.id: f for f, _ in scored_seeds}
seed_ids = set(seed_scores.keys())
```

**Step 2 — Compute entity-group scores:**

Query `fact_entity_links` to get entity→seed_fact mappings for all seed facts:

```sql
SELECT l.entity_id, e.normalized, l.fact_id
FROM fact_entity_links l
JOIN fact_entities e ON l.entity_id = e.id
WHERE l.fact_id IN ({seed_placeholders})
```

Build `entity_group_scores: dict[int, float]` where key=entity_id, value=max embedding score of seed facts linked to that entity.

```python
entity_group_scores: dict[int, float] = {}
for entity_id, _, fact_id in rows:
    score = seed_scores.get(fact_id, 0.0)
    entity_group_scores[entity_id] = max(entity_group_scores.get(entity_id, 0.0), score)
```

**Step 3 — Get neighbor facts + their entity links:**

Use existing `_get_entity_neighbors(seed_ids, set())`. Then for each neighbor, query its linked entities to compute max group score:

```sql
SELECT entity_id FROM fact_entity_links WHERE fact_id = ?
```

Neighbor's group score = max of `entity_group_scores[eid]` across its linked entities (only entities that overlap with seeds contribute).

**Step 4 — Score all facts:**

For seeds:
```python
for fid, emb_score in seed_scores.items():
    group_score = max(entity_group_scores.get(eid, 0.0) for eid in seed_entity_map.get(fid, []))
    final_scores[fid] = alpha * emb_score + (1 - alpha) * group_score
```

For neighbors (no embedding score — use 0):
```python
for fid in neighbor_ids:
    group_score = max(entity_group_scores.get(eid, 0.0) for eid in neighbor_entity_map.get(fid, []))
    final_scores[fid] = (1 - alpha) * group_score
    # Neighbors have no direct embedding score (not in Chroma results), so α term is 0
```

**Step 5 — Observation → fact propagation:**

After scoring, check if any scored results are observations. For each observation in the result set, look up its source facts via `get_observation_source_ids()`. Boost each source fact:

```python
obs_boost = 0.1  # fixed boost factor
for fid, fact in fact_map.items():
    if fact.category == FactCategory.OBSERVATION:
        source_ids = self.get_observation_source_ids(fid)
        for sid in source_ids:
            if sid in final_scores:
                final_scores[sid] += obs_boost * final_scores[fid]
            elif sid not in fact_map:
                source_fact = self.get(sid)
                if source_fact:
                    fact_map[sid] = source_fact
                    final_scores[sid] = obs_boost * final_scores[fid]
```

**Step 6 — Sort and return:**
```python
ranked = sorted(final_scores.keys(), key=lambda fid: final_scores[fid], reverse=True)
return [fact_map[fid] for fid in ranked if fid in fact_map][:limit]
```

### 4. `_get_fact_entities` — new helper

```python
def _get_fact_entities(self, fact_ids: set[str]) -> dict[str, list[int]]:
    """Map fact_id → list of entity_ids it's linked to."""
    if not fact_ids:
        return {}
    placeholders = ",".join("?" for _ in fact_ids)
    with wal_connect(self.db_path) as conn:
        rows = conn.execute(
            f"SELECT fact_id, entity_id FROM fact_entity_links WHERE fact_id IN ({placeholders})",
            list(fact_ids),
        ).fetchall()
    result: dict[str, list[int]] = {}
    for fact_id, entity_id in rows:
        result.setdefault(fact_id, []).append(entity_id)
    return result
```

### 5. `_graph_expand_and_merge` — retained for keyword fallback

Unchanged. Used only when ChromaDB is unavailable (keyword search path has no embedding scores). This keeps the keyword fallback identical to current behavior.

## Data Flow

```
query
  → _chroma_search → [(fact, embedding_score), ...]
  → _propagate_and_merge:
      seeds + scores
        → entity_group_scores (entity_id → max seed embedding score)
        → _get_entity_neighbors → neighbor fact IDs + shared_counts
        → _get_fact_entities(neighbors) → neighbor entity links
        → score each fact: α * embedding + (1-α) * max_group
        → observation→fact boost
        → sort, return top limit
```

## Invariants

- `use_graph=False` returns ChromaDB order (no propagation)
- Keyword fallback uses existing `_graph_expand_and_merge` (no regression)
- `alpha=1.0` means pure embedding score (no group propagation)
- `alpha=0.0` means pure group score propagation
- Neighbors with no overlapping entities with seeds get score 0 (filtered out naturally)
- Observation boost is additive, capped by the observation's own score × boost factor

## Config

No new config keys. `alpha` is a `search()` parameter with default 0.5. Can be tuned per caller (MCP, RAG retriever, etc.) without config file changes.

## Test Plan

1. **Entity group scoring**: 3 seeds with different embedding scores sharing entities → verify group scores = max of member scores
2. **Neighbor ranking by group**: two neighbors, one linked to high-score entity, one to low → high-score neighbor ranks first
3. **Observation propagation**: observation matches query → its source facts appear in results even if they wouldn't otherwise
4. **Alpha extremes**: `alpha=1.0` produces same order as raw Chroma; `alpha=0.0` orders purely by group score
5. **Keyword fallback**: no ChromaDB → existing RRF behavior unchanged
6. **No entity links**: facts with no entities → ranked by embedding score alone (no group boost)

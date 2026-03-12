# Parent-Score Propagation in Memory Retrieval

**Status:** Draft
**Issue:** #145 Phase 2
**Date:** 2026-03-12

## Problem

Memory graph search uses flat RRF to merge seed results with entity neighbors. All seeds get rank-based scores (0.8 weight) and all neighbors get a weaker rank-based score (0.2 weight). This ignores *how relevant* each seed was to the query — a seed at rank 0 with 0.99 similarity and a seed at rank 1 with 0.51 similarity contribute nearly equal scores. Neighbors of the high-relevance seed should be boosted more than neighbors of the marginal seed.

Additionally, observations that match a query don't boost their underlying source facts' scores, even though those facts are the evidence for the observation.

## Users

All users. Retrieval quality improvement in advisor RAG pipeline and MCP memory search.

## Desired Behavior

1. Embedding similarity scores from ChromaDB are preserved through the retrieval pipeline (not discarded after ordering).
2. Entity groups are scored based on the embedding scores of seed facts that belong to them — if "Python" entity has seed facts scoring 0.95 and 0.7, the "Python" group score is high.
3. Neighbor facts inherit relevance from their entity groups: `final = α * own_score + (1-α) * group_score`.
4. When an observation matches the query, its source facts get a relevance boost (observation → fact propagation).
5. α defaults to 0.5 (matching OpenViking). Configurable per call.
6. Keyword fallback path unchanged — propagation only applies when ChromaDB is available.

## Acceptance Criteria

- [ ] `_chroma_search` returns embedding similarity scores alongside facts
- [ ] Entity-group scores computed from seed facts' embedding scores
- [ ] Neighbor facts scored via `α * embedding_score + (1-α) * max_group_score`
- [ ] Seed facts also re-scored: `α * embedding_score + (1-α) * max_group_score` (seeds benefit from group context too)
- [ ] Observations matching the query propagate a boost to their source facts
- [ ] `search()` accepts optional `alpha` parameter (default 0.5)
- [ ] `use_graph=False` behavior unchanged
- [ ] Keyword fallback behavior unchanged (no embedding scores available)
- [ ] Tests demonstrating: high-similarity seed's neighbors rank above low-similarity seed's neighbors
- [ ] Tests demonstrating: observation match boosts its source facts

## Edge Cases

- No ChromaDB (keyword fallback): graph expansion uses existing RRF, no propagation
- Seeds with no entity links: embedding score only, no group boost
- Neighbor facts linked to multiple entity groups: use max group score across all linked groups
- All seeds have identical embedding scores: degrades to current behavior (uniform group scores)
- Observations with no remaining source facts: no propagation (orphan observations ignored)
- `alpha=0.0`: pure group score propagation. `alpha=1.0`: pure embedding score (no propagation)

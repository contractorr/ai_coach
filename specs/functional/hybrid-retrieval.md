# Hybrid Retrieval

**Status:** Draft
**Author:** —
**Date:** 2026-03-09

## Problem

The advisor's retrieval pipeline has three limitations:

1. **Single-mode queries.** `get_combined_context()` runs one hybrid search (RRF over semantic + FTS5) per query. Complex questions like "compare the hiring trends at AI labs with their recent product launches" require decomposing into sub-queries and merging results — the current pipeline cannot do this.
2. **No entity-aware retrieval.** When entity extraction lands, retrieval needs a mode that traverses entity relationships — not just text similarity — to find connected items.
3. **Agentic tool bypasses hybrid search.** The `intel_search` tool in `AgenticOrchestrator` calls `storage.search()` (LIKE) directly, missing the semantic and profile-filtered paths entirely.

## Users

All users who ask the advisor multi-faceted or relational questions. Most impactful for users with large intel databases (100+ items) where keyword search alone returns poor results.

## Desired Behavior

### Sub-question decomposition

1. When a user asks a complex question, the system detects whether decomposition would help (heuristic: contains conjunctions, comparisons, multiple named entities, or explicit multi-part phrasing).
2. The system splits the query into 2–4 sub-questions using the cheap LLM.
3. Each sub-question runs through the existing hybrid retrieval pipeline in parallel.
4. Results are merged, deduplicated by URL, and re-ranked by aggregate relevance.
5. The merged context is passed to the advisor prompt as usual — the user sees no difference in the response format.

### Entity graph retrieval

1. When entity extraction is enabled and the query references known entities, the system retrieves the entity's relationships and connected items as supplementary context.
2. Entity retrieval runs alongside (not instead of) text-based retrieval. Results are merged into the context budget.
3. The advisor prompt receives a structured `<entity_context>` block showing entities, their types, relationships, and linked item summaries.

### Unified agentic retrieval

1. The `intel_search` tool in the agentic orchestrator uses the full hybrid retrieval pipeline (semantic + FTS5 + profile filtering + entity graph) instead of bare LIKE search.
2. A new `intel_entity_search` tool allows the agentic orchestrator to query by entity name, returning the entity's relationships and connected items.

### Retrieval mode selection

1. The system auto-selects retrieval mode based on query analysis:
   - **Simple** — single hybrid search (current behavior). Used for straightforward factual lookups.
   - **Decomposed** — sub-question split + parallel search + merge. Used for complex/comparative questions.
   - **Entity-traversal** — entity graph lookup + connected items. Used when query matches known entities.
   - **Combined** — decomposed + entity-traversal. Used for complex questions involving known entities.
2. Mode selection is automatic; no user action required. Override via config for testing.

## Acceptance Criteria

- [ ] Sub-question decomposition activates for qualifying complex queries (conjunction/comparison heuristic or LLM classification).
- [ ] Decomposition produces 2–4 sub-questions; never more than 4.
- [ ] Sub-question searches run concurrently (asyncio.gather or equivalent).
- [ ] Merged results are deduplicated by URL; items appearing in multiple sub-query results rank higher.
- [ ] Total context stays within the existing `max_context_chars` budget (default 8000) regardless of retrieval mode.
- [ ] Entity graph retrieval returns entities + relationships + linked item summaries when entity extraction is enabled.
- [ ] Entity context is injected as a distinct `<entity_context>` XML block in the advisor prompt.
- [ ] The agentic `intel_search` tool uses `IntelSearch.hybrid_search()` instead of `IntelStorage.search()`.
- [ ] A new `intel_entity_search` agentic tool exists for entity-specific queries.
- [ ] Retrieval mode auto-selection adds < 500ms latency (one cheap LLM call for classification, or heuristic-only).
- [ ] When entity extraction is disabled, entity-traversal mode is skipped silently — no errors, falls back to text-only retrieval.
- [ ] Decomposition uses the cheap LLM instance.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Query is simple ("latest HN posts") | No decomposition; single hybrid search as today |
| Decomposition produces duplicate sub-questions | Dedup sub-questions before searching; skip exact matches |
| Sub-question search returns zero results for one sub-query | Merge results from remaining sub-queries; do not fail |
| Entity referenced in query does not exist in graph | Fall back to text-only retrieval for that entity term |
| Context budget exceeded after merging all retrieval modes | Truncate lowest-ranked items first; entity context gets 20% budget ceiling |
| Agentic tool calls `intel_search` with a query matching entities | Returns hybrid results enriched with entity tags, same as classic RAG path |
| All sub-questions return the same items | Deduplicated result set is smaller; that's fine — items rank higher from multi-match boost |

### RRF standardization

1. All hybrid search paths (journal, intel, library) use Reciprocal Rank Fusion with a standard smoothing constant k=60.
2. A shared `rrf_fuse()` utility replaces the three separate RRF implementations.
3. The formula is: `score(item) = Σ weight_i / (k + rank_i + 1)` where rank_i is the item's 0-based position in result list i.

### Temporal search

1. When a query contains temporal expressions ("last week", "since January", "past 3 months", "yesterday", "recently"), the system detects this and applies date-range filtering to search results.
2. Temporal filtering is orthogonal to retrieval mode — a temporal + decomposed query decomposes the cleaned query and filters each sub-query's results by date.
3. Temporal expressions are parsed via regex heuristics (no LLM call, zero added latency).
4. Journal entries are filtered by their `created` frontmatter date. Intel items are filtered by `COALESCE(published, scraped_at)`.
5. The temporal expression is stripped from the query before semantic/keyword search to avoid polluting embeddings.

### Token-based context budgets

1. The RAG retriever's context budget is expressed in tokens (default 2000) rather than raw characters.
2. Token counting uses tiktoken's `cl100k_base` encoding for accuracy with Claude/GPT-class models.
3. Backward compatibility: `max_context_chars` is still accepted and converted to tokens via `chars // 4`.

### Cross-encoder reranking

1. An optional cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) applies as a final pass after all retrieval fusion in the RAG pipeline.
2. The reranker is an optional dependency (`pip install stewardme[reranking]`). When not installed, retrieval works identically to before.
3. Reranking runs on the final merged passage set, not per-module.

## Acceptance Criteria (Phase 2 additions)

- [ ] All three hybrid search modules (journal, intel, library) use RRF with k=60 via a shared utility.
- [ ] Queries with temporal expressions ("what happened last week", "news since March") apply date-range filters to both journal and intel results.
- [ ] Temporal detection adds zero LLM calls (regex-only parsing).
- [ ] The temporal expression is stripped from the semantic query to avoid noise.
- [ ] QueryAnalyzer populates a `temporal_filter` field on QueryAnalysis when temporal intent is detected.
- [ ] Journal temporal search filters entries by `created` date.
- [ ] Intel temporal search filters items by `COALESCE(published, scraped_at)`.
- [ ] RAGRetriever budgets are token-based (tiktoken `cl100k_base`), with char-based fallback for backward compat.
- [ ] Cross-encoder reranker is optional; when installed, it reranks final merged passages in `get_enhanced_context()`.
- [ ] When `sentence-transformers` is not installed, reranker is silently skipped.

## Edge Cases (Phase 2 additions)

| Scenario | Expected Behavior |
|----------|-------------------|
| Query has temporal expr but no other content ("last week") | Use temporal filter with empty semantic query; return recent items by date only |
| Temporal expr is ambiguous ("recently") | Default to 7 days |
| Intel item has NULL `published` | Fall back to `scraped_at` for filtering |
| Journal entry has no `created` field | Skip entry from temporal results |
| tiktoken import fails | Fall back to `len(text) // 4` approximation |
| Cross-encoder reranker receives empty passage list | Return empty list, no error |
| Temporal filter matches zero results | Return empty context for that source, do not fall back to unfiltered |

## Out of Scope

- User-facing retrieval mode picker or transparency about which mode was used
- Caching of decomposed sub-questions across sessions
- Cross-user entity graph traversal
- Retrieval from external APIs (web search is a separate agentic tool)
- LLM-based temporal expression parsing (regex heuristics only for now)

## Open Questions

- Should decomposition use a heuristic classifier (regex/keyword) or a cheap LLM call? Heuristic is faster but less accurate.
- What is the right budget split between entity context and text context? Proposed: 20% entity ceiling, remainder split by existing journal:intel ratio.
- Should entity-traversal depth be configurable (1-hop vs 2-hop relationships)?

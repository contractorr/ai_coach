# Memory & Threads

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

The advisor forgets user preferences, patterns, and ongoing themes between sessions. Without persistent memory, users repeat themselves, re-upload the same reference documents, and receive inconsistent advice.

## Users

All users. Memory value compounds over time and is most useful for regular users with enough history.

## Desired Behavior

### Memory (persistent facts)

1. When a journal entry is created or a PDF document is uploaded, system automatically extracts structured facts about the user when the source contains stable user-relevant context.
2. Facts are categorized as `preference`, `skill`, `constraint`, `pattern`, `context`, or `goal_context`.
3. Each fact has a confidence score.
4. The memory pipeline supports journal entries, uploaded documents, recommendation feedback, and goal events as source types.
5. Uploaded documents should contribute memory only for durable user context, such as skills, preferences, constraints, or current-role context, rather than storing every document sentence as memory.
6. Current product wiring automatically runs memory extraction on journal-entry writes; uploaded-document, recommendation-feedback, and goal-event ingestion should use the same pipeline, but are not yet fully wired into all product surfaces.
7. Duplicate or conflicting facts are resolved through similarity checks and, when needed, LLM arbitration.
8. Active facts are injected into advisor prompts as memory context.

### Viewing and managing memory

1. User can list all active facts, optionally filtered by category.
2. User can inspect a single fact.
3. User can delete incorrect facts.
4. User can view memory statistics.

Current interface scope:
- CLI and MCP expose memory search flows.
- Web currently exposes list, get, delete, and stats routes.
- Web does not yet expose a semantic fact-search endpoint.

### Threads (recurring topics)

1. System detects recurring topics across journal entries using similarity-based grouping.
2. A thread is formed when multiple entries discuss a similar topic.
3. Threads are stored with constituent entry references.
4. Active threads are injected into advisor prompts as recurring-thought context.
5. User can view detected threads and their entries.

Current interface scope:
- CLI and MCP expose thread browsing and reindex operations.
- Web currently exposes working list/detail API routes for threads.
- Web does not yet provide a dedicated dashboard page or reindex UX for threads.

### Reindexing

1. User can trigger a reindex of threads if detection seems stale.
2. Reindex re-processes entries against current thresholds.

Current interface scope:
- Reindex is exposed in CLI and MCP.
- Reindex is not yet exposed in web.

## Acceptance Criteria

- [ ] Facts are automatically extracted from new journal entries.
- [ ] Facts can also be extracted from uploaded PDF documents when the document contains durable user-relevant context.
- [ ] Facts are deduplicated before entering active context.
- [ ] Conflicting facts can be resolved through an arbitration step.
- [ ] A bounded set of facts is injected into advisor context.
- [ ] User can list and delete facts across the supported interfaces.
- [ ] Semantic fact search is available in CLI and MCP.
- [ ] Document-derived facts preserve a source link back to the uploaded document.
- [ ] Threads are detected from repeated themes across entries.
- [ ] Threads are injected into advisor prompts when enabled.
- [ ] Memory management is available via CLI, web, and MCP, with web currently limited to browse/delete/stats rather than semantic search.
- [ ] Thread browsing is available via CLI, MCP, and basic web API routes.
- [ ] Soft-deleted facts never appear in queries or prompt context.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| First journal entry | Facts may be extracted but threads are not yet possible |
| Contradictory facts from different entries | Resolver favors the stronger or more recent interpretation |
| Large fact set accumulates | Only a bounded subset is injected into context |
| Very short entry | May extract zero facts without error |
| Uploaded PDF contains useful reference material but no user facts | Document stays searchable for retrieval, but memory extraction may produce zero facts |
| User uploads a newer version of their CV | Older document-derived facts can be superseded by the newer interpretation |
| Thread falls below usefulness after data changes | Reindex can rebuild the thread set |

## Out of Scope

- User manually adding facts
- Cross-user memory or shared facts
- Automatic memory decay over time
- Explicit fact editing beyond deletion
- Treating every uploaded document sentence as a first-class memory fact

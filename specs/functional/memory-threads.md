# Memory & Threads

**Status:** Approved
**Author:** —
**Date:** 2026-03-02

## Problem

The advisor forgets user preferences, patterns, and ongoing themes between sessions. Without persistent memory, users repeat themselves and the advisor gives inconsistent advice.

## Users

All users. Memory value compounds over time — most useful for regular users with 20+ journal entries.

## Desired Behavior

### Memory (persistent facts)

1. When a journal entry is created, system automatically extracts structured facts about the user
2. Facts are categorized: `preference`, `skill`, `constraint`, `pattern`, `context`, `goal_context`
3. Each fact has a confidence score (0-1) assigned by the LLM
4. Facts from multiple sources: journal entries, recommendation feedback, goal events
5. Duplicate/conflicting facts are resolved: fast token-overlap similarity check auto-skips near-duplicates (>0.95 threshold); ambiguous conflicts go to LLM arbitration
6. Active facts are injected into advisor prompts as `<user_memory>` context

### Viewing and managing memory

1. User can list all active facts, optionally filtered by category
2. User can search facts semantically
3. User can delete incorrect facts
4. User can view memory statistics (total facts, by category, by source)

### Threads (recurring topics)

1. System detects recurring topics across journal entries using cosine-similarity clustering
2. A thread is formed when 2+ entries discuss a similar topic
3. Threads are stored with their constituent entry references
4. Active threads are injected into advisor prompts as `<recurring_thoughts>` context
5. User can view detected threads and their entries

### Reindexing

1. User can trigger a reindex of threads if detection seems stale
2. Reindex re-processes all entries against current similarity thresholds

## Acceptance Criteria

- [ ] Facts automatically extracted from new journal entries
- [ ] Facts deduplicated via token-overlap similarity (auto-NOOP at >0.95)
- [ ] Conflicting facts resolved via LLM arbitration
- [ ] Up to 25 facts injected into advisor context (configurable)
- [ ] User can list, search, and delete facts
- [ ] Threads detected from 2+ entries with similar topics
- [ ] Threads injected into advisor prompts when enabled
- [ ] Available via CLI, web, and MCP
- [ ] Soft-deleted facts never appear in queries or context

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| First journal entry | Facts extracted but no threads possible (need 2+ entries) |
| Contradictory facts from different entries | LLM conflict resolver picks the more recent/confident one |
| 100+ facts accumulated | Only top 25 (by confidence/recency) injected into context |
| Fact extraction from very short entry | May extract 0 facts; that's fine |
| Thread with only 2 entries, one deleted | Thread may drop below threshold; cleaned up on reindex |

## Out of Scope

- User manually adding facts (facts are always system-extracted)
- Cross-user memory or shared facts
- Memory decay over time (facts persist until deleted or superseded)
- Explicit memory editing (user can delete but not edit facts)

# Deep Research

**Status:** Approved
**Author:** —
**Date:** 2026-03-02

## Problem

Users want to go deeper on specific topics — not just surface-level intel summaries, but synthesized research reports with multiple sources and analysis. Manual research is time-consuming.

## Users

Users who want in-depth understanding of a topic relevant to their goals or interests. Requires Tavily API key for best results (falls back to DuckDuckGo).

## Desired Behavior

### Topic selection

1. System automatically selects research topics from: active goals, journal trend clusters, and word-frequency analysis of recent journal entries
2. User can also request research on a specific topic manually
3. System limits to a configurable max topics per cycle. `ResearchConfig.max_topics` defaults to 3 but is unused by the agent; `DeepResearchAgent` reads `max_topics_per_week` (default 2) from the research config dict, which is forwarded to `TopicSelector.max_topics`

### Research pipeline

1. For each topic, system generates targeted search queries
2. System performs web searches via Tavily (preferred) or DuckDuckGo (fallback)
3. Results are fetched and content extracted (up to 3000 chars per source)
4. LLM synthesizes sources into a structured research report
5. Report is saved as both a journal entry (`type=research`) and an intel DB item for future RAG retrieval

### Viewing research

1. User can list suggested research topics (without running them)
2. User can trigger research on a topic and receive the synthesized report
3. Past reports are searchable via journal search

### Scheduling

1. When enabled, research runs on a cron schedule (default: Sunday 9pm)
2. System auto-selects topics and generates reports unattended
3. Reports appear in journal and intel for next advisor query

## Acceptance Criteria

- [ ] Topic selector draws from goals, trends, and journal word-frequency themes
- [ ] User can manually request research on any topic
- [ ] Reports synthesize multiple web sources with citations
- [ ] Reports saved as journal entries and intel items
- [ ] Falls back to DuckDuckGo when no Tavily key is set
- [ ] Rate-limited to 1 request/second on sync web search client (async client is not rate-limited)
- [ ] Scheduled research runs unattended when enabled
- [ ] Available via CLI, web, and MCP

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No Tavily API key | Falls back to DuckDuckGo HTML scraping; lower quality results |
| All search results empty | Report states insufficient sources found |
| Topic too vague | LLM generates best-effort queries; results may be scattered |
| No goals/trends to derive topics from | Topic selector returns empty list; user can still request manually |
| Web search timeout | Retries with exponential backoff; skips source after max attempts |

## Out of Scope

- PDF or academic paper parsing
- Collaborative research shared between users
- Research quality scoring or feedback loops

## Related Features

- Multi-update, long-lived topic tracking is covered by `specs/functional/research-dossiers.md`

# Ask Advice

**Status:** Approved
**Author:** —
**Date:** 2026-03-02

## Problem

Users want personalized career and technical advice grounded in their own journal history, profile, and current industry intelligence — not generic LLM responses.

## Users

All users. Most valuable for users with 10+ journal entries and a completed profile.

## Desired Behavior

### Asking a question

1. User asks a free-text question (e.g., "Should I learn Rust or Go next?")
2. System retrieves relevant context: journal entries (semantic + keyword), intelligence items, user profile, memory facts, and recurring thoughts
3. System sends the assembled context + question to the LLM
4. User receives a personalized answer grounded in their data

### Advice types

User can optionally specify an advice type that adjusts the system prompt:
- `general` (default) — open-ended advice
- `career` — career trajectory focus
- `goals` — goal progress and next steps
- `opportunities` — what to pursue based on intel

### Two modes

- **Classic RAG**: single retrieval pass → single LLM call. Deterministic context assembly.
- **Agentic**: LLM decides what to look up via tool calls (search journal, query intel, check goals, etc.) in a multi-turn loop. Richer but uses more tokens.

Mode is set at engine construction time. In CLI, this is config-driven. In web, the client can toggle `use_tools` per request via query parameter.

### Context composition

- Journal and intel context are blended with a dynamic weight (default 70% journal, 30% intel), adjusted based on engagement data
- User profile is injected as structured context
- Memory facts (persistent user preferences/patterns) are injected if enabled
- Recurring thought threads are injected if enabled
- Recent research reports are optionally included

### Proactive greeting (chat-first home)

1. On home page load, system serves a cached personalized greeting (3-5 sentences)
2. Greeting is pre-computed by cheap LLM from current state: stale goals, top recommendations, recent intel highlights, profile name
3. Cache TTL: 4 hours; invalidated on journal create/update, goal check-in, or scrape batch
4. If no cache exists, static fallback shown while greeting generates in background
5. Greeting is the first assistant message in the home page chat
6. Chat input doubles as journal quick-capture (explicit mode toggle) or advisor question
7. No dashboard sections — dedicated pages (Goals, Journal, Radar) handle deep dives

### Conversation continuity

User can send follow-up questions with conversation history. The system passes prior turns to the LLM for multi-turn dialogue.

### Specialized analyses

Beyond free-form Q&A, the advisor can run:
- **Weekly review**: summarizes recent journal activity
- **Opportunity detection**: identifies opportunities from intel matched to profile
- **Goal analysis**: evaluates progress on specific or all goals
- **Skill gap analysis**: identifies gaps between current skills and aspirations

## Acceptance Criteria

- [ ] Question returns a personalized answer referencing user's journal/profile data
- [ ] Response quality degrades gracefully with no journal entries (uses profile + intel only)
- [ ] Agentic mode makes multiple tool calls to gather context before answering
- [ ] Classic RAG mode returns a response in a single LLM call
- [ ] Conversation history is passed through for multi-turn dialogue
- [ ] Advice type changes the framing/focus of the response
- [ ] Works via CLI, web (including SSE streaming), and MCP
- [ ] Greeting returns in <100ms when cached
- [ ] Greeting reflects current user state (stale goals, recent intel)
- [ ] Cache invalidated on data events (journal create/update, goal check-in, scrape batch)
- [ ] Static fallback shown on first visit (no blocking LLM call)
- [ ] Quick-capture mode creates journal entries via existing `/api/journal/quick`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No journal entries, no profile | Answer based on intel + general knowledge; quality warning optional |
| Question unrelated to career/tech | LLM answers normally, context may not be relevant |
| LLM API key missing or invalid | Clear error message, not a crash |
| Very long question (>10K chars) | Truncated or rejected at input boundary |
| Agentic mode with no tools available | Falls back to classic RAG |

---

## Proactive Infrastructure: Insights & Heartbeat

### Insights

Unified store for all proactive system-detected items. Merges what was previously signals, patterns, and heartbeat notifications.

1. System detects notable items from three sources:
   - **Signal detectors**: goal staleness, journal gaps, topic emergence, deadlines, research triggers, recurring blockers, goal completion candidates
   - **Pattern detectors**: blind spots (goals with no journal activity), blocker cycles (recurring negative keywords)
   - **Heartbeat pipeline**: intel-to-goal matches that pass heuristic + LLM evaluation
2. Each insight has a type, severity (1-10), title, detail, suggested actions, and evidence
3. Insights auto-expire after 14 days (TTL) — no acknowledge/dismiss workflow
4. Deduplication by content hash within TTL window prevents duplicate insights
5. Queryable via `GET /api/insights` and `get_insights` MCP tool
6. Engagement tracked implicitly via click-through (no explicit dismiss)

### Heartbeat (invisible infrastructure)

Heartbeat is an internal pipeline — no user-facing CLI, routes, or MCP tools. Output feeds into Insights.

1. System periodically scans recent intel items (within lookback window, default 2 hours)
2. Each item is scored against active goals using a composite heuristic: keyword overlap (35%), recency (35%), source affinity (30%)
3. Items passing the heuristic threshold (default 0.3) go to an LLM evaluator (budget-capped at 5 per cycle)
4. Items that pass LLM evaluation are saved as Insights (`type=intel_match`)
5. Dedup by insight hash within TTL window prevents spamming

### Daily brief

The `DailyBriefBuilder` and `/api/briefing` endpoint are retained for MCP backward compat. The chat-first home page replaces the dashboard UI.

1. User requests daily brief via MCP or API
2. System assembles: stale goals, top recommendations, goal-intel matches
3. Items are scored by urgency and filled within the user's weekly time budget
4. Available on demand, not scheduled

### Suggestions

Unified concept merging recommendations and daily brief items — both are "things the system suggests I do."

1. `GET /api/suggestions` returns a ranked list combining daily brief items (high-priority actionable nudges) and recommendations (deeper LLM-generated suggestions)
2. Brief items appear first (already priority-ranked), followed by remaining recommendations not already in the brief
3. Each suggestion has: source (brief/recommendation), kind, title, description, action (chat pre-fill), priority, score

### Proactive Acceptance Criteria

- [ ] Insights are queryable via `GET /api/insights` and `get_insights` MCP tool
- [ ] Insights auto-expire after 14 days (no manual acknowledge)
- [ ] Heartbeat runs on configured interval as invisible infra
- [ ] Heuristic + LLM two-stage filter limits token usage
- [ ] `GET /api/suggestions` merges daily brief items + recommendations
- [ ] Engagement tracked implicitly via click-through to source

### Proactive Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No goals set | Heartbeat has nothing to match against; brief shows intel-only summary |
| No recent intel | Brief reports "no new intelligence"; heartbeat finds nothing |
| All goals stale | Insight raised for stale goals |
| LLM budget exhausted in heartbeat cycle | Remaining items deferred to next cycle |
| Duplicate insight within TTL | Deduplicated by hash, not saved again |

---

## Out of Scope

- Real-time web search during Q&A (that's deep research)
- Multi-user advice (comparing users)
- Voice input/output
- Caching of answers (context is cached, not responses)
- Push notifications (insights are pull-only via web/MCP)
- Custom insight rules (insights are system-defined patterns)
- Manual acknowledge/dismiss of insights (TTL-only expiry)

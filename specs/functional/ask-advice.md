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

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No journal entries, no profile | Answer based on intel + general knowledge; quality warning optional |
| Question unrelated to career/tech | LLM answers normally, context may not be relevant |
| LLM API key missing or invalid | Clear error message, not a crash |
| Very long question (>10K chars) | Truncated or rejected at input boundary |
| Agentic mode with no tools available | Falls back to classic RAG |

## Out of Scope

- Real-time web search during Q&A (that's deep research)
- Multi-user advice (comparing users)
- Voice input/output
- Caching of answers (context is cached, not responses)

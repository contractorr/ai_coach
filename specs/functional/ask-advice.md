# Ask Advice

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

Users want personalized career and technical advice grounded in their own journal history, profile, uploaded reference documents, and current industry intelligence - not generic LLM responses.

## Users

All users. Most valuable for users with 10+ journal entries and a completed profile.

## Desired Behavior

### Asking a question

1. User asks a free-text question (e.g., "Should I learn Rust or Go next?").
2. User can optionally attach one or more PDF files to the same message from any first-party web chat surface.
3. System stores the uploaded PDFs as private user documents, extracts searchable text, and derives durable memory when the content contains stable user-relevant facts.
4. System retrieves relevant context: journal entries, intelligence items, user profile, memory facts, recurring thoughts, uploaded documents, and recent research when available.
5. System sends the assembled context plus question to the LLM.
6. User receives a personalized answer grounded in their data and attached documents.

### Advice types

User can optionally specify an advice type that adjusts the system prompt:
- `general` (default) - open-ended advice
- `career` - career trajectory focus
- `goals` - goal progress and next steps
- `opportunities` - what to pursue based on intel
- `skill_gap` - gap analysis against current skills and aspirations

### Two modes

- **Classic RAG**: single retrieval pass -> single LLM call. Deterministic context assembly.
- **Agentic**: LLM decides what to look up via tool calls (search journal, query intel, check goals, etc.) in a multi-step loop.

Current interface scope:
- CLI can choose behavior through config and command usage.
- Web requests default to `use_tools=true`, but users on shared/lite mode are forced onto the cheaper non-agentic path.
- MCP exposes advisor-supporting context tools rather than a direct ask endpoint.

### Context composition

- Journal and intel context are blended for retrieval.
- User profile is injected as structured context.
- Memory facts are injected when enabled.
- Recurring thought threads are injected when enabled.
- Uploaded PDF/document text is available as retrievable context when relevant to the question.
- Newly uploaded documents in the current chat turn can influence the same response instead of waiting for a later session.
- Recent research reports, including dossier material saved as research entries, can be included when relevant.

### Reference documents in chat

1. Any first-party web chat entry point can accept PDF attachments alongside a question.
2. Attached PDFs are shown as part of the conversation turn so the user can tell what was included.
3. The advisor can use extracted document text in the immediate answer and in later conversations.
4. Uploaded documents become searchable private assets in the user's account instead of one-off ephemeral chat attachments.
5. When a document contains durable user context, such as a CV or resume, the system can distill that into memory so later advice stays personalized without requiring repeated uploads.

Current interface scope:
- Home and advisor web chat surfaces support in-thread PDF attachments and pass `attachment_ids` through the ask flow.
- Chat-origin PDFs are stored as private user documents, remain searchable for later retrieval, and can be explicitly promoted into the visible Library workspace.

### Proactive greeting (chat-first home)

1. On home page load, system serves a cached personalized greeting.
2. Greeting is pre-computed from current state: stale goals, top recommendations, recent intel highlights, and the user's name.
3. Cache TTL is 4 hours and is invalidated on journal create/update, goal check-in, and scrape batches.
4. If no cache exists, a static fallback is shown while the greeting is generated in the background.
5. Greeting is the first assistant message in the home page chat.
6. Chat input doubles as either journal quick capture or advisor question via an explicit mode toggle.

### Conversation continuity

1. User can continue a prior conversation.
2. System persists conversation history and passes recent turns back to the model.
3. Web supports both normal responses and SSE streaming for live advisor replies.

### Specialized analyses

The advisor system can also run:
- **Weekly review** - summarizes recent journal activity
- **Goal analysis** - evaluates progress on one goal or all goals
- **Skill gap analysis** - identifies likely gaps between current skills and aspirations
- **Opportunity-oriented framing** - biases the answer toward near-term opportunities from profile and intel context

Current interface scope:
- CLI exposes dedicated weekly review and goal-analysis commands.
- Web currently focuses on free-form chat plus advice-type framing rather than separate specialist screens.

## Acceptance Criteria

- [ ] Question returns a personalized answer referencing the user's own context when available.
- [ ] Response quality degrades gracefully with sparse data.
- [ ] Agentic mode can make multiple tool calls before answering when tools are available.
- [ ] Classic RAG mode returns in a single model pass.
- [ ] Conversation history is passed through for multi-turn dialogue.
- [ ] Advice type changes the framing of the response.
- [ ] Works via CLI and web, including SSE streaming in web.
- [ ] MCP exposes advisor-supporting context tools rather than a direct `ask` tool.
- [ ] Users can attach PDF files from any first-party web chat surface.
- [ ] Uploaded PDF text is extracted and can be used in the same advisor response.
- [ ] Uploaded PDF text remains searchable and reusable in later advisor conversations.
- [ ] Durable user-relevant facts derived from uploaded documents are available to memory-backed advisor context.
- [ ] Chat UI makes it clear which documents were attached to a turn.
- [ ] Greeting returns immediately from cache when available.
- [ ] Greeting reflects current user state and falls back without blocking the page.
- [ ] Greeting cache is invalidated on journal create/update, goal check-in, and scrape batch.
- [ ] Quick-capture mode creates journal entries via `/api/journal/quick`.
- [ ] Web advisor input is bounded at the request layer to 5,000 characters.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No journal entries, no profile | Answer falls back to whatever profile, intel, or general context exists |
| Question unrelated to career or tech | System still answers, even if retrieved context is less relevant |
| LLM API key missing or invalid | User sees a clear error, not a crash |
| Very long question (>5K chars in web) | Rejected at the input boundary |
| User attaches a valid PDF with little or no extractable text | Upload can still succeed, but the user is told the document may not influence advice yet |
| User attaches a non-PDF file in chat | Upload is rejected with a clear validation message |
| User asks about their CV immediately after uploading it | Advisor can use the extracted content in that same response |
| Agentic mode with no tools available | Falls back to classic behavior |
| Shared/lite mode user asks from web | Request still works, but richer agentic behavior is disabled |

## Proactive Infrastructure: Insights, Heartbeat, and Suggestions

### Insights

Unified store for proactive system-detected items.

1. System detects notable items from signals, patterns, and heartbeat output.
2. Insights can be listed by severity and type.
3. Duplicate insights are deduplicated by hash while still active.
4. Insights expire automatically after their TTL instead of requiring manual acknowledgement.

### Heartbeat

1. A scheduled heartbeat evaluates fresh intel against user goals and watchlist context.
2. A heuristic filter narrows candidates before optional LLM evaluation.
3. The system saves proactive briefs or notifications for the most relevant items.

### Daily brief and suggestions

1. `GET /api/suggestions` merges daily brief items and saved recommendations into a single ranked list.
2. Brief items stay ahead of lower-priority recommendations.
3. The suggestions data is designed for conversational follow-up and chat pre-fill actions.

Current interface scope:
- Insights are queryable through web API and MCP.
- The engagement/event ingestion route exists in web API, but click-through wiring is not yet broadly enabled across the web client.
- Suggestions currently ship as API data, not as a dedicated standalone dashboard page.

## Proactive Acceptance Criteria

- [ ] Insights are queryable via `GET /api/insights` and an MCP insights tool.
- [ ] Insights auto-expire after 14 days unless given a different TTL.
- [ ] Heartbeat runs on a configured schedule as background infrastructure.
- [ ] Heuristic plus optional LLM filtering limits token usage.
- [ ] `GET /api/suggestions` merges daily brief items and recommendations.
- [ ] Engagement events are supportable through `POST /api/engagement`, even though broad web click-through wiring is still partial.

## Proactive Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No goals set | Heartbeat has nothing goal-specific to match; suggestions can still use other context |
| No recent intel | Brief reports little or no new intelligence |
| All goals stale | Insight can be raised for stale goals |
| LLM budget exhausted in heartbeat cycle | Remaining items defer to a later cycle or heuristic-only behavior |
| Duplicate insight within TTL | Deduplicated by hash |

## Out of Scope

- Replacing journal, goals, or radar pages with a single monolithic advisor page
- Real-time collaborative chat or shared conversations
- Guaranteed citations in every answer
- Non-PDF chat attachments such as images, spreadsheets, audio, or video

# Engagement Scoring

**Status:** Implemented

## Overview

Event-based engagement tracking feeding dynamic recommendation weighting.

## Key Modules

- `src/web/routes/engagement.py`
- `src/web/user_store.py` — `log_engagement()`, `get_engagement_stats()`, `get_feedback_count()`

## Interfaces

- `POST /api/engagement` — record event (body: `EngagementEvent`)
- `GET /api/engagement/stats?days=30` — grouped counts (response: `EngagementStats`)

## Event Types

`opened`, `saved`, `dismissed`, `acted_on`, `feedback_useful`, `feedback_irrelevant`

## Storage

- `engagement_events` table in users.db: user_id, target_type, target_id, event_type, created_at
- Feedback events also write to `usage_events` as `recommendation_feedback` for admin analytics

## Models

- `EngagementEvent` (Pydantic): target_type, target_id, event_type
- `EngagementStats` (Pydantic): grouped counts by target_type × event_type

## Dynamic Weighting

`get_feedback_count(user_id)` aggregates across both tables. Feeds `compute_dynamic_weight()` in `advisor.rag` to adjust journal:intel ratio (default 70:30).

## Message ID Propagation (Advisor Feedback)

To enable per-message feedback, the assistant message `id` is exposed end-to-end:

1. **`conversation_store.py`** — `get_conversation()` and `get_messages()` include `"id": message["id"]` in returned dicts.
2. **`services/advice.py`** — `finish_conversation_turn()` captures and returns the `msg_id` from `add_message_fn()`.
3. **`web/models.py`** — `ConversationMessage` gains `id: str | None = None`.
4. **`web/routes/advisor.py`** — After `finish_conversation_turn()`, emits `message_persisted` SSE event with `message_id`. Also includes `message_id` in the `answer` event when answer hasn't been sent yet (non-agentic path).

### Frontend

- `ChatMessage` type gains `id?: string`.
- `TargetType` union in `engagement.ts` gains `"advisor"`.
- `MessageFeedback` component: two ghost buttons (Signal = `Zap`, Noise = `ZapOff`), fires `logEngagement` on click, toggles disabled + highlight state.
- Advisor page handles `message_persisted` SSE event to patch last assistant message's `id`, and maps `id` from loaded conversation history.

## Dependencies

- `web.user_store`
- `web.models`
- `web.conversation_store` (message_id exposure)
- `services.advice` (message_id return)
- Consumed by: `advisor.rag.compute_dynamic_weight()`

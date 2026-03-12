# Engagement Scoring

**Status:** Implemented
**Author:** —
**Date:** 2026-03-11

## Problem

The system needs feedback on which suggestions and recommendations are useful to improve future prioritization. Without engagement data, the recommendation engine cannot learn from user behavior.

## Users

All web app users. Engagement data feeds into dynamic recommendation weighting.

## Desired Behavior

1. Users can record engagement events against any target: opened, saved, dismissed, acted_on, feedback_useful, feedback_irrelevant.
2. Feedback events (useful/irrelevant) also trigger secondary `recommendation_feedback` usage events for admin analytics.
3. Stats endpoint returns counts grouped by target_type × event_type for last N days plus totals.
4. Engagement data feeds `compute_dynamic_weight()` in advisor RAG to adjust journal:intel weighting.
5. Per-user feedback count available for rate-limiting or profile enrichment.

## Acceptance Criteria

- [ ] All 6 event types recorded correctly.
- [ ] Feedback events dual-write to engagement_events and usage_events.
- [ ] Stats grouped by target_type × event_type.
- [ ] Stats filterable by day range (default 30).
- [ ] Engagement data influences dynamic recommendation weighting.
- [ ] Frontend fires engagement events from all primary interaction surfaces (see call-sites below).
- [ ] Advisor responses display Signal/Noise feedback buttons; clicks log `feedback_useful`/`feedback_irrelevant` with `target_type=advisor`.

## Frontend Call-Sites

| Page | Interaction | Event | TargetType | TargetId |
|------|-------------|-------|------------|----------|
| `/intel` | Save/unsave button | `saved` / `dismissed` | `intel` | `item.url` |
| `/intel` | Title link click | `opened` | `intel` | `item.url` |
| `/journal` | Card click (view entry) | `opened` | `journal` | `entry.path` |
| `/goals` | Track recommendation | `acted_on` | `recommendation` | `rec.id` |
| `/goals` | Save feedback (rating) | `feedback_useful` / `feedback_irrelevant` | `recommendation` | `rec.id` |
| `/home` | Suggestion "Open" button | `acted_on` | `suggestion` | `item.title` |

## Advisor Feedback (Signal / Noise)

- Each assistant message in `/advisor` shows two ghost buttons: "Signal" (useful) and "Noise" (irrelevant).
- Buttons only render when the message has a persisted `message_id` and the user has a valid token.
- After clicking one button, the selected button highlights and both become disabled.
- Feedback logs `target_type=advisor`, `target_id=<message_id>`.
- Old messages without an `id` (pre-feature) do not render feedback buttons.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Same event recorded twice for same target | Both recorded (no dedup — events are append-only) |
| Unknown event type submitted | Validation error returned |
| No engagement data yet | Stats return empty groupings; dynamic weight uses defaults |
| No auth token yet | All `logEngagement` calls guarded with `if (token)` |
| Old messages (pre-feature) | `msg.id` undefined — feedback buttons not rendered |
| Agentic streaming | `message_persisted` SSE event patches id after persist |
| Long intel URLs | `target_id` truncated to 200 chars at call-site |

## Out of Scope

- Engagement-based A/B testing
- Cross-user engagement aggregation
- Signal/Noise on embedded/compact advisor surfaces (EmbeddedAdvisor, ChatSheet)

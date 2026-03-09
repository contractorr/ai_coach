# Recommendations & Suggestions

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-07

## Problem

Users want actionable, personalized recommendations based on their profile, goals, and current intel - not generic lists. They also need a unified view of things the system suggests they do.

## Users

Users with a completed profile and some journal history. Recommendations improve as more data accumulates.

## Desired Behavior

### Generation

1. System periodically generates recommendations by analyzing user profile, journal patterns, goals, and recent intel.
2. Each recommendation is scored on three weighted dimensions: relevance (50%), impact (30%), feasibility (20%).
3. Recommendations below a minimum score threshold (default 6.0) are filtered out.
4. At most 3 recommendations per category are kept to avoid overload.
5. Recommendations are deduplicated against recent ones using exact content-hash matching over a 30-day window.

### Viewing

1. User can list current recommendations.
2. Each recommendation includes title, category, score, description, and suggested action.
3. Recommendations can include lightweight watchlist evidence when matched intel supports the suggestion.
4. Recommendations are sorted by score descending.

Current interface scope:
- Web exposes recommendation retrieval through API and currently surfaces recommendation work mostly inside the goals and action-plan workflow rather than a dedicated recommendations page.
- CLI and MCP expose recommendation browsing directly.

### Feedback

1. User can provide explicit feedback on recommendations.
2. Explicit numeric ratings and optional comments tune future scoring.
3. Recommendation outcomes from tracked action items also influence future ranking.
4. Recommendations can leave the active list by being completed, dismissed, or converted into execution artifacts.

Current interface scope:
- CLI and MCP expose 1-5 ratings with optional comments.
- Web exposes the same 1-5 rating model with optional notes inline on recommendation cards in the goals workspace.
- Web still exposes the generic engagement event route for binary feedback elsewhere in the product.

### Delivery

1. Recommendations are saved as markdown files in the user's recommendations storage.
2. On the configured schedule, new recommendations are generated and stored.
3. Recommendations are retrievable through CLI, web API, and MCP.

### Suggestions (unified view)

Suggestions merge recommendations with daily brief items into a single ranked list.

1. `GET /api/suggestions` returns a combined list of brief items plus remaining recommendations.
2. Each suggestion includes source (`brief` or `recommendation`), kind, title, description, action, priority, and score.
3. Brief items appear first, followed by remaining recommendations.
4. Recommendations already represented in the brief are not repeated in the remainder.

### Action plans

1. A recommendation can be converted into a tracked action item.
2. Goal-linked recommendations can become goal-linked action items.
3. Action-item execution outcomes feed back into future recommendation scoring.
4. Detailed action-plan behavior is specified in `specs/functional/action-plans.md`.

## Acceptance Criteria

- [ ] Recommendations are personalized based on profile, goals, journal, and available intel.
- [ ] Scoring weights sum to 1.0 and low-scoring recommendations are excluded.
- [ ] Max 3 per category prevents recommendation fatigue.
- [ ] Exact content-hash dedup prevents the same recommendation from recurring within 30 days.
- [ ] CLI, MCP, and web support explicit 1-5 recommendation ratings with optional comments.
- [ ] Tracked execution outcomes influence future recommendation ranking alongside explicit feedback.
- [ ] Recommendations are retrievable via CLI, web API, and MCP.
- [ ] Scheduled generation runs without manual intervention.
- [ ] `GET /api/suggestions` merges daily brief items and recommendations into a unified ranked list.
- [ ] Brief items rank ahead of remaining recommendations.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No profile and no journal | Return empty or low-confidence fallback instead of fabricated precision |
| All recommendations fall below threshold | Return empty list rather than weak suggestions |
| User gives repeated low ratings in CLI or MCP | Future ranking shifts away from those patterns |
| No intel items available | Recommendations can still be based on profile and journal |
| Duplicate recommendation within 30 days | Filtered by content-hash dedup |
| No stale goals and no intel matches | Suggestions can contain only recommendations |
| Only brief items, no scored recommendations | Suggestions can contain only brief nudges |
| Web user wants to rate a recommendation numerically | Inline 1-5 rating and optional note are available on recommendation cards |

## Out of Scope

- External content fetching beyond recommendation metadata
- User-managed recommendation categories
- Email or push delivery of recommendations

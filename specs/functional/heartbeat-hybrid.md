# Heartbeat Hybrid: On-demand LLM Evaluation

**Status:** Implemented
**Date:** 2026-03-11

## Problem

Heartbeat runs LLM evaluation every 30 minutes on the scheduler, incurring cost even when no user is active. Most cycles produce no actionable output.

## Users

All web app users who have active goals and intelligence feeds configured.

## Desired Behavior

1. Scheduler continues running heuristic scoring every 30 minutes (free, no LLM)
2. When a user loads the home page, the system triggers LLM evaluation in the background
3. LLM evaluation respects a cooldown window to prevent repeated calls within a short period
4. Results upgrade heuristic-only insights to LLM-refined insights via upsert

## Acceptance Criteria

- [ ] Scheduler heartbeat cycle uses `llm_budget_per_cycle: 0` by default (heuristic only)
- [ ] Home page load triggers `evaluate_pending()` with `llm_budget_on_demand` budget
- [ ] LLM eval skips if last LLM run was within `notification_cooldown_hours`
- [ ] LLM eval skips if user has no active goals
- [ ] Insights produced by LLM eval upsert (update existing heuristic insights, insert new ones)
- [ ] Background task failure does not affect greeting response

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No API key for user | Heartbeat eval silently skips |
| No goals | Returns `{"skipped": "no_goals"}` |
| Within cooldown | Returns `{"skipped": "cooldown"}` |
| LLM call fails | Logged as warning, does not propagate |

## Out of Scope

- Real-time push notifications to frontend
- Per-user heartbeat config overrides

# Daily Brief & Signals

> **Deprecation note:** Daily Brief dashboard UI replaced by chat-first home page (see `ask-advice.md` → Proactive greeting). `DailyBriefBuilder` and `/api/briefing` endpoint retained for MCP tool backward compat.

**Status:** Approved
**Author:** —
**Date:** 2026-03-02

## Problem

Users miss relevant intelligence and goal-related updates buried in the intel feed. They need a curated summary of what matters to them right now, plus proactive alerts when something important surfaces.

## Users

Active users with goals and configured intel sources. Most useful for users running `coach daemon` or using the web app regularly.

## Desired Behavior

### Daily brief

1. User requests their daily brief
2. System assembles: recent intel highlights, goal progress summary, pending recommendation actions, upcoming events, trending topics relevant to profile
3. Brief is a concise, structured summary — not a wall of text
4. Available on demand, not just at a fixed time

### Heartbeat (proactive matching)

1. System periodically scans recent intel items (within lookback window, default 2 hours)
2. Each item is scored against active goals using a composite heuristic: keyword overlap (35%), recency (35%), source affinity (30%)
3. Items passing the heuristic threshold (default 0.3) go to an LLM evaluator (budget-capped at 5 per cycle)
4. Items that pass LLM evaluation are saved as action briefs
5. Notification cooldown prevents spamming (default 4 hours between notifications for same goal)

### Signals

1. System detects notable patterns: goal-relevant intel spikes, trending topics matching interests, stale goals needing attention
2. Signals are stored and surfaced to the user
3. User can acknowledge signals to dismiss them

### Predictions (experimental)

1. System records predictions (claims with confidence levels and evaluation dates)
2. When evaluation date passes, user reviews outcomes: confirmed, rejected, expired, skipped
3. System tracks accuracy statistics by category and confidence bucket
4. Helps calibrate user's and system's forecasting ability

## Acceptance Criteria

- [ ] Daily brief includes intel highlights, goal progress, and trending topics
- [ ] Heartbeat runs on configured interval (default 30 min)
- [ ] Heuristic + LLM two-stage filter limits token usage
- [ ] Notification cooldown prevents duplicate alerts
- [ ] Signals are surfaceable and acknowledgeable
- [ ] Predictions trackable with outcome review workflow
- [ ] Available via CLI, web, and MCP

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No goals set | Heartbeat has nothing to match against; brief shows intel-only summary |
| No recent intel | Brief reports "no new intelligence"; heartbeat finds nothing |
| All goals stale | Signal raised for stale goals |
| LLM budget exhausted in heartbeat cycle | Remaining items deferred to next cycle |
| Prediction review with no past-due items | "No predictions due for review" message |

## Out of Scope

- Push notifications to phone/email (signals are pull-only via CLI/web/MCP)
- Custom signal rules (signals are system-defined patterns)
- Brief scheduling (it's on-demand; scheduling is the daemon's job)
- Prediction auto-evaluation (always requires user review)

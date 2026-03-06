# Daily Brief & Insights

> **Deprecation note:** Daily Brief dashboard UI replaced by chat-first home page (see `ask-advice.md` → Proactive greeting). `DailyBriefBuilder` and `/api/briefing` endpoint retained for MCP tool backward compat.

**Status:** Approved
**Author:** —
**Date:** 2026-03-06

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

### Heartbeat (invisible infrastructure)

Heartbeat is an internal pipeline — no user-facing CLI, routes, or MCP tools. Output feeds into Insights.

1. System periodically scans recent intel items (within lookback window, default 2 hours)
2. Each item is scored against active goals using a composite heuristic: keyword overlap (35%), recency (35%), source affinity (30%)
3. Items passing the heuristic threshold (default 0.3) go to an LLM evaluator (budget-capped at 5 per cycle)
4. Items that pass LLM evaluation are saved as Insights (`type=intel_match`)
5. Dedup by insight hash within TTL window prevents spamming

### Insights

Unified store for all proactive system-detected items. Merges what was previously signals, patterns, and heartbeat notifications.

1. System detects notable items from three sources:
   - **Signal detectors**: goal staleness, journal gaps, topic emergence, deadlines, research triggers, recurring blockers, goal completion candidates
   - **Pattern detectors**: blind spots (goals with no journal activity), blocker cycles (recurring negative keywords)
   - **Heartbeat pipeline**: intel-to-goal matches that pass heuristic + LLM evaluation
2. Each insight has a type, severity (1-10), title, detail, suggested actions, and evidence
3. Insights auto-expire after 14 days (TTL) — no acknowledge/dismiss workflow
4. Deduplication by content hash within TTL window prevents duplicate insights

## Acceptance Criteria

- [ ] Daily brief includes intel highlights, goal progress, and trending topics
- [ ] Heartbeat runs on configured interval (default 30 min) as invisible infra
- [ ] Heuristic + LLM two-stage filter limits token usage
- [ ] Insights are queryable via `GET /api/insights` and `get_insights` MCP tool
- [ ] Insights auto-expire after 14 days (no manual acknowledge needed)
- [ ] Available via web API and MCP

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No goals set | Heartbeat has nothing to match against; brief shows intel-only summary |
| No recent intel | Brief reports "no new intelligence"; heartbeat finds nothing |
| All goals stale | Insight raised for stale goals |
| LLM budget exhausted in heartbeat cycle | Remaining items deferred to next cycle |
| Duplicate insight within TTL | Deduplicated by hash, not saved again |

## Out of Scope

- Push notifications to phone/email (insights are pull-only via web/MCP)
- Custom insight rules (insights are system-defined patterns)
- Brief scheduling (it's on-demand; scheduling is the daemon's job)
- Manual acknowledge/dismiss (TTL-only expiry)

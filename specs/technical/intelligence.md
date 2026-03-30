---
id: intelligence
category: tracked_module
status: updated
implements:
- intelligence-feed
code_paths:
- src/intelligence
- src/web/routes/intel.py
- web/src/app/(dashboard)/radar/page.tsx
- tests/intelligence
last_reviewed: '2026-03-30'
---

# Intelligence

**Status:** Updated for the simplified product model

## Overview

The intelligence layer powers Radar, the Home next-step feed, and part of Goals by ranking and annotating relevant external signals.

## Key Modules

- `src/web/routes/intel.py`
- `src/web/routes/suggestions.py`
- `web/src/app/(dashboard)/radar/page.tsx`
- `web/src/app/(dashboard)/intel/page.tsx`

## Interfaces

- `POST /api/intel/scrape`
- watchlist and follow-up endpoints under `/api/intel`
- suggestion feed consumed by Home and Radar

## Simplified Product Notes

- Radar is now the default intelligence UX.
- The advanced Intel page remains available for deeper filtering and power-user workflows.

## Heartbeat: Hybrid Heuristic + On-demand LLM

The heartbeat pipeline has two execution modes:

### Scheduler mode (heuristic only)
- Runs every `interval_minutes` (default 30)
- `llm_budget_per_cycle` defaults to 0 — no LLM calls
- `HeartbeatFilter.filter()` scores intel against goals using keyword/recency/source weights
- `HeartbeatEvaluator(budget=0)` produces heuristic-only `ActionBrief`s
- Saves insights via `InsightStore.save()`

### On-demand mode (LLM enabled)
- Triggered by `GET /api/greeting` (home page load)
- `_schedule_heartbeat_eval(user_id)` fires `asyncio.create_task` in background
- Calls `HeartbeatPipeline.evaluate_pending(budget=llm_budget_on_demand)`
- Cooldown: skips if `ActionBriefStore.get_last_llm_run_at()` is within `notification_cooldown_hours`
- Saves via `InsightStore.upsert()` — updates existing heuristic insights, inserts new ones

### Key methods
- `ActionBriefStore.get_last_llm_run_at()` — queries `heartbeat_runs WHERE llm_used = 1`
- `InsightStore.upsert(insight)` — UPDATE if unexpired hash match exists, else INSERT
- `HeartbeatPipeline.evaluate_pending(budget)` — cooldown check → filter → LLM evaluate → upsert

### Config (`HeartbeatConfig`)
- `enabled: true` (default)
- `llm_budget_per_cycle: 0` — scheduler never calls LLM
- `llm_budget_on_demand: 5` — web-triggered LLM budget
- `notification_cooldown_hours: 4` — min gap between LLM runs

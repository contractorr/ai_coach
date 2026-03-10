# Recurring Threads

**Status:** Updated for the simplified product model

## Overview

Recurring threads are now surfaced through Radar's `Threads` tab instead of a standalone workspace.

## Key Modules

- `src/web/routes/threads.py`
- thread extraction/grouping services
- `web/src/app/(dashboard)/radar/page.tsx`

## Interfaces

- `GET /api/threads/inbox?limit=...`
- thread action endpoints for goal, research, dossier, and dismiss flows
- thread state updates under `/api/threads/{id}/state`

## Thread Model

- `journal_threads` includes an internal `strength REAL NOT NULL DEFAULT 0.0` column.
- `Thread.strength` is derived from:
  - entry count / recurrence
  - average entry similarity inside the thread
  - inactivity since the last matching entry
  - divergence penalty for low-similarity clusters
- Strength is recomputed after entry joins and refreshed on thread reads so stale threads weaken over time.

## Ranking Behavior

- Radar thread APIs can still sort or group for UI workflows, but advisor recurring-thought injection now ranks threads by `strength` first.
- Recent entry count remains a secondary signal for display and tie-breaking, not the primary recurrence score.

## Simplified Product Notes

- This keeps active monitoring work together in Radar.
- Receipt and Journal follow-ups should deep-link to Radar, not to a separate thread workspace concept.

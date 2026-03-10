# Intelligence

**Status:** Updated for the simplified product model

## Overview

The intelligence layer powers Radar, the Home next-step feed, and part of Focus by ranking and annotating relevant external signals.

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

## Scheduler Architecture

- `IntelScheduler.start()` remains the minimal scrape path used by CLI daemon workflows: intel gather, extended intel pipelines, and entity extraction.
- `IntelScheduler.start_web()` registers the full background job set for web deployments:
  - daily signal detection
  - daily autonomous actions when agent mode is enabled
  - recurring goal-intel matching
  - trending radar refresh
  - heartbeat when enabled
  - weekly deep research
  - weekly recommendations / action-brief generation

## Lazy Web Context Construction

- Web scheduler jobs construct per-user journal storage, embedding managers, and LLM-backed engines lazily at execution time rather than at app startup.
- User-dependent jobs iterate known web users and build context only for that user run.
- Research and recommendation jobs are gated to users with personal LLM API keys; shared-key-only users are skipped.
- Signal detection, heartbeat, goal-intel matching, and trending radar still run for web-only users without personal keys.

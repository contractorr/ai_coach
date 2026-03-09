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

## Simplified Product Notes

- This keeps active monitoring work together in Radar.
- Receipt and Journal follow-ups should deep-link to Radar, not to a separate thread workspace concept.

# Memory

**Status:** Updated for the simplified product model

## Overview

Memory remains the durable personalization layer. The main user-facing affordance is now the `What I know about you` section in Settings.

## Key Modules

- `src/web/routes/memory.py`
- memory extraction and storage services
- `web/src/app/(dashboard)/settings/page.tsx`

## Interfaces

- `GET /api/memory/facts?limit=50`
- `GET /api/memory/stats`
- `DELETE /api/memory/facts/{id}`

## Simplified Product Notes

- Memory stays transparent and user-controllable from Settings.
- Memory continues to inform advisor, suggestions, and prioritization behind the scenes.

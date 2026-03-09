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

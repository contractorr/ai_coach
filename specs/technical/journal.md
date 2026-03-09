# Journal

**Status:** Updated for the simplified product model

## Overview

Journal APIs support both Home quick capture and the deeper Journal workspace reached from the sidebar shortcut.

## Key Modules

- `src/web/routes/journal.py`
- `web/src/app/(dashboard)/page.tsx`
- `web/src/app/(dashboard)/journal/page.tsx`
- `web/src/components/Sidebar.tsx`

## Interfaces

- `POST /api/journal/quick`
- full Journal list/search/filter/edit endpoints
- journal-derived extraction into threads and memory

## Simplified Product Notes

- Quick capture belongs on Home.
- The full Journal remains one tap away, but it is no longer a primary navigation concept.

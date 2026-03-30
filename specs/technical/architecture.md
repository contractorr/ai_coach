---
id: architecture
category: tracked_module
status: updated
implements: []
code_paths:
- src
- web/src
- tests
last_reviewed: '2026-03-30'
---

# Architecture

**Status:** Updated for the simplified product model

## Overview

The user-facing architecture is organized around four primary surfaces: `Home`, `Radar`, `Learn`, and `Journal`. `Goals` and `Research` remain in the product as secondary workspaces entered from those primary surfaces when a task needs more planning depth or deeper reference material. `Settings` remains a utility destination.

## Key Modules

- Dashboard pages in `web/src/app/(dashboard)`
- Navigation in `web/src/components/Sidebar.tsx`
- Page-view tracking in `web/src/hooks/usePageView.ts` and `src/web/routes/pageview.py`
- API routes in `src/web/routes`
- Canonical web persistence in `src/user_state_store.py`

## Interfaces

- Home consumes greeting, suggestions, journal quick-capture, and advisor streaming APIs.
- Goals consumes goals, recommendations, tracked actions, and weekly-plan APIs.
- Radar consumes suggestions, watchlist, threads, dossier-escalation, dossier, and follow-up APIs.
- Research consumes report and archived-dossier APIs.
- Learn consumes curriculum APIs.
- Journal consumes journal entry, search, and thread-adjacent workflows.
- Settings consumes account, profile, watchlist, and memory APIs.
- Web persistence bootstraps through the canonical `src/user_state_store.py` schema, with `src/web/user_store.py` acting as a compatibility import layer.

## Simplified Product Notes

- `/advisor`, `/intel`, and `/projects` remain as secondary deep-link pages.
- The primary experience should always be explainable through the four primary surfaces, with Goals and Research treated as secondary workspaces.

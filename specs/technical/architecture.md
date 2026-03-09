# Architecture

**Status:** Updated for the simplified product model

## Overview

The user-facing architecture is now organized around five jobs: `Home`, `Focus`, `Radar`, `Library`, and `Settings`. Advanced routes still exist, but the primary navigation explains the product through those five destinations.

## Key Modules

- Dashboard pages in `web/src/app/(dashboard)`
- Navigation in `web/src/components/Sidebar.tsx`
- Page-view tracking in `web/src/hooks/usePageView.ts` and `src/web/routes/pageview.py`
- API routes in `src/web/routes`

## Interfaces

- Home consumes greeting, suggestions, journal quick-capture, and advisor streaming APIs.
- Focus consumes goals, recommendations, tracked actions, and weekly-plan APIs.
- Radar consumes suggestions, watchlist, threads, dossier-escalation, dossier, and follow-up APIs.
- Library consumes report and archived-dossier APIs.
- Settings consumes account, profile, watchlist, and memory APIs.

## Simplified Product Notes

- `/advisor`, `/intel`, and `/projects` remain as secondary deep-link pages.
- The primary experience should always be explainable through the five simplified jobs.

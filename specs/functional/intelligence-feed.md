---
id: intelligence-feed
category: tracked_feature
status: stable
technical_specs:
- specs/technical/intelligence.md
- specs/technical/trending-radar.md
- specs/technical/web.md
foundations:
- specs/foundations/ux-guidelines.md
last_reviewed: '2026-03-30'
---

# Radar

**Status:** Updated for the simplified product model

## Purpose

Radar is the unified monitoring workspace for external signals, recurring threads, active dossiers, saved follow-ups, and tracked topics. Users should not need to learn separate monitoring tools before getting value.

## Product Placement

- Workspace: `Radar`
- Primary job: stay aware of meaningful change without manually checking many sources
- Tabs: `For you`, `Threads`, `Dossiers`, `Saved`, `Tracked topics`

## Current Behavior

- Radar mixes signal families into one ranked `For you` feed with simple badges and clear next actions.
- Radar should open directly into tabs and signal lists rather than a summary count dashboard.
- Threads and active dossiers live inside Radar because they are active monitoring work.
- A `Scan now` action refreshes monitoring on demand.
- The advanced `/intel` page remains available for power users but is no longer the primary monitoring entry point.

## User Flows

- Review the strongest signals in `For you`.
- Save an item, start a dossier, or jump to tracked-topic configuration.
- Open the `Threads` or `Dossiers` tab to continue active follow-up work.

## Key System Components

- `web/src/app/(dashboard)/radar/page.tsx`
- `web/src/app/(dashboard)/intel/page.tsx`
- `src/web/routes/intel.py`
- `src/web/routes/suggestions.py`
- `src/web/routes/dossier_escalations.py`

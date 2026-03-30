---
id: journaling
category: tracked_feature
status: stable
technical_specs:
- specs/technical/journal.md
- specs/technical/extraction-receipt.md
- specs/technical/web.md
foundations:
- specs/foundations/design-system.md
- specs/foundations/ux-guidelines.md
last_reviewed: '2026-03-30'
---

# Journaling

**Status:** Updated for the simplified product model

## Purpose

Journaling is the product's capture flywheel. Quick capture belongs on Home, while the full Journal workspace stays one tap away through the sidebar shortcut and related Research handoff.

## Product Placement

- Primary capture surface: `Home`
- Deep workspace: `Journal` sidebar shortcut
- Related reference path: `Research` handoff when the user wants durable artifacts instead of source notes

## Current Behavior

- Home quick capture optimizes for speed and minimal required fields.
- The full Journal workspace still supports richer editing, templates, filters, and search.
- Journal should open with capture/search/filter controls and the entry list, not a stats dashboard.
- Journal activity feeds threads, memory, extraction receipts, and downstream prioritization.

## User Flows

- Capture a quick note from Home.
- Open the Journal shortcut for deeper editing and browsing.
- Use Journal history to improve future Goals and Radar behavior.

## Key System Components

- `web/src/app/(dashboard)/page.tsx`
- `web/src/app/(dashboard)/journal/page.tsx`
- `web/src/components/Sidebar.tsx`
- `src/web/routes/journal.py`

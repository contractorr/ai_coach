---
id: deep-research
category: tracked_feature
status: experimental
technical_specs:
- specs/technical/research.md
- specs/technical/web.md
foundations:
- specs/foundations/ux-guidelines.md
last_reviewed: '2026-03-30'
---

# Research

**Status:** Updated for the simplified product model

## Purpose

Research remains available for power users, but it is entered from live work such as Radar signals, threads, and dossiers rather than from a separate first-run concept.

## Product Placement

- Primary surface: `Radar`
- Durable outputs: `Research`
- Entry points: threads, escalations, active dossiers, advanced flows

## Current Behavior

- Research starts from concrete user intent.
- Active work belongs in Radar so it can be monitored alongside other signals.
- Archived outputs belong in Research for later reference.

## User Flows

- Start research from a thread or dossier suggestion.
- Refresh active work while the topic remains important.
- Archive the resulting output into Research when active tracking is done.

## Key System Components

- `src/web/routes/research.py`
- `src/web/routes/dossier_escalations.py`
- `web/src/app/(dashboard)/radar/page.tsx`
- `web/src/app/(dashboard)/research/page.tsx`
- `web/src/components/research/ResearchWorkspace.tsx`

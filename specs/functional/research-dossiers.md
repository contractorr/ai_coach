---
id: research-dossiers
category: tracked_feature
status: experimental
technical_specs:
- specs/technical/research-dossiers.md
- specs/technical/dossier-escalation-engine.md
foundations:
- specs/foundations/ux-guidelines.md
last_reviewed: '2026-03-30'
---

# Research Dossiers

**Status:** Updated for the simplified product model

## Purpose

Dossiers now have a clear lifecycle: active work lives in Radar and archived outputs live in Research.

## Product Placement

- Active dossiers: `Radar` > `Dossiers`
- Archived dossier outputs: `Research`
- Primary job: keep tracking evolving topics that deserve sustained attention

## Current Behavior

- Users can start dossiers from escalations or threads.
- Active dossiers can be refreshed from Radar.
- Archiving moves the dossier into Research for durable reference.

## User Flows

- Start a dossier from a signal or thread.
- Refresh it while the topic remains active.
- Archive it to Research once active tracking is done.

## Key System Components

- `web/src/app/(dashboard)/radar/page.tsx`
- `web/src/app/(dashboard)/research/page.tsx`
- `web/src/components/research/ResearchWorkspace.tsx`
- `src/web/routes/research.py`
- `src/web/routes/dossier_escalations.py`

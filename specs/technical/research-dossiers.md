---
id: research-dossiers
category: tracked_module
status: experimental
implements:
- research-dossiers
code_paths:
- src/research/dossiers.py
- src/research/escalation.py
- src/web/routes/dossier_escalations.py
- tests/research/test_dossiers.py
- tests/research/test_escalation.py
last_reviewed: '2026-03-30'
---

# Research Dossiers

**Status:** Updated for the simplified product model

## Overview

Research dossiers now have a clear active-versus-archived lifecycle mapped to Radar and Research.

## Key Modules

- `src/web/routes/research.py`
- `src/web/routes/dossier_escalations.py`
- `web/src/app/(dashboard)/radar/page.tsx`
- `web/src/app/(dashboard)/research/page.tsx`
- `web/src/components/research/ResearchWorkspace.tsx`

## Interfaces

- `GET /api/research/dossiers`
- `POST /api/research/run?dossier_id=...`
- `POST /api/research/dossiers/{dossier_id}/archive`

## Simplified Product Notes

- Active work stays in Radar.
- The new archive route moves a finished dossier into Research for durable reference.

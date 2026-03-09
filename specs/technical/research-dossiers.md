# Research Dossiers

**Status:** Updated for the simplified product model

## Overview

Research dossiers now have a clear active-versus-archived lifecycle mapped to Radar and Library.

## Key Modules

- `src/web/routes/research.py`
- `src/web/routes/dossier_escalations.py`
- `web/src/app/(dashboard)/radar/page.tsx`
- `web/src/app/(dashboard)/library/page.tsx`

## Interfaces

- `GET /api/research/dossiers`
- `POST /api/research/run?dossier_id=...`
- `POST /api/research/dossiers/{dossier_id}/archive`

## Simplified Product Notes

- Active work stays in Radar.
- The new archive route moves a finished dossier into Library for durable reference.

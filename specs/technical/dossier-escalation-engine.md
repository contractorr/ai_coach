# Dossier Escalation Engine

**Status:** Updated for the simplified product model

## Overview

The escalation engine decides when repeated signals or threads deserve active dossier tracking and exposes the decision in Radar.

## Key Modules

- `src/web/routes/dossier_escalations.py`
- `src/web/routes/research.py`
- `web/src/app/(dashboard)/radar/page.tsx`

## Interfaces

- `GET /api/dossier-escalations`
- `POST /api/dossier-escalations/{id}/accept|dismiss|snooze`
- dossier creation and refresh flows

## Simplified Product Notes

- Accepting an escalation creates active dossier work in Radar.
- The user-facing lifecycle stays simple: active in Radar, archived in Library.

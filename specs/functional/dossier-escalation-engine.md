# Dossier Escalation

**Status:** Updated for the simplified product model

## Purpose

Explain how repeated signals and threads graduate into dossier suggestions inside Radar.

## Product Placement

- Workspace: `Radar`
- Primary job: decide when a signal deserves deeper ongoing tracking
- Resulting artifact: active dossier in Radar, archived dossier in Library

## Current Behavior

- Escalations appear as Radar cards rather than as a separate workflow.
- Users can accept, snooze, or dismiss an escalation inline.
- Accepted escalations convert into active dossiers that can be refreshed and later archived.

## User Flows

- Review an escalation in Radar.
- Accept it to start a dossier or dismiss/snooze it.
- Track the resulting dossier until it is archived into Library.

## Key System Components

- `src/web/routes/dossier_escalations.py`
- `src/web/routes/research.py`
- `web/src/app/(dashboard)/radar/page.tsx`

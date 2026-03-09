# Library

**Status:** Updated for the simplified product model

## Purpose

Library is the durable reference workspace for uploaded documents, generated reports, and archived dossier outputs. It should feel like a calm reference surface rather than an active monitoring console.

## Product Placement

- Workspace: `Library`
- Primary job: find, reuse, and manage durable reference material
- Journal handoff: the user can jump from Library into the deeper Journal workspace when they need source notes instead of durable artifacts

## Current Behavior

- Library supports type filtering across documents, reports, and dossiers.
- Active dossiers stay in Radar until they are archived.
- Archived dossiers become read-only reference material in Library.
- Report-like items can still be refreshed or edited from the Library workspace.

## User Flows

- Filter the library by content type.
- Open a report or archived dossier for later reference.
- Jump from Library to Journal when the user wants source captures rather than durable outputs.

## Key System Components

- `web/src/app/(dashboard)/library/page.tsx`
- `src/web/routes/library.py`
- `src/web/routes/research.py`

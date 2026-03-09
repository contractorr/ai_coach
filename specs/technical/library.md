# Library

**Status:** Updated for the simplified product model

## Overview

Library is the durable reference workspace for uploaded documents, generated reports, and archived dossier outputs.

## Key Modules

- `src/web/routes/library.py`
- `src/web/routes/research.py`
- `web/src/app/(dashboard)/library/page.tsx`

## Interfaces

- `GET /api/library/reports` and related detail/update endpoints
- `GET /api/research/dossiers?include_archived=true&limit=50`
- report refresh, archive, and file download flows

## Simplified Product Notes

- Active dossiers stay in Radar until archived.
- Library should feel like a reference surface, not an active monitoring console.

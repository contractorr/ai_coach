# Advisor

**Status:** Updated for the simplified product model

## Overview

Advisor remains the conversational engine, but Home is now the primary entry point. The full chat page exists as a continuation surface for longer threads.

## Key Modules

- `src/web/routes/advisor.py`
- `web/src/app/(dashboard)/page.tsx`
- `web/src/app/(dashboard)/advisor/page.tsx`
- `web/src/components/MessageRenderer.tsx`

## Interfaces

- `POST /api/advisor/ask/stream`
- conversation continuation via `/advisor?conv=...`
- attachment ids passed from the Home Ask flow

## Simplified Product Notes

- Home defaults to capture and upgrades into advisor only when input clearly looks like a question or the user toggles Ask.
- The advisor page is no longer part of the primary navigation model.

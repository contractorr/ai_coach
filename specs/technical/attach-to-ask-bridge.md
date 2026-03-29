# Attach to Ask Bridge

**Status:** Updated for the simplified product model

## Overview

The attach-to-ask bridge keeps same-turn PDF uploads inside the Home Ask flow and passes durable attachment ids to the advisor stream.

## Key Modules

- `web/src/components/ChatPdfAttachments.tsx`
- `web/src/hooks/useChatPdfAttachments.ts`
- `src/web/routes/advisor.py`
- `src/web/routes/library.py`

## Interfaces

- attachment upload and indexing before advisor submission
- `POST /api/advisor/ask/stream` with `attachment_ids`
- Research retrieval for uploaded PDFs and derived reports

## Simplified Product Notes

- Ask mode owns attachments so capture stays lightweight.
- File work should feel like conversational context, not a separate destination.

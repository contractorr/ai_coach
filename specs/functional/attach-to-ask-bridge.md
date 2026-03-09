# Attach to Ask on Home

**Status:** Updated for the simplified product model

## Purpose

Keep PDF attachment handling inside the Home Ask flow so files feel like context for a conversation rather than a separate workflow.

## Product Placement

- Workspace: `Home`
- Primary job: ask grounded questions about uploaded files
- Related durable storage: `Library`

## Current Behavior

- Attachments are available only in Ask mode.
- Same-turn uploads can be indexed and referenced in the streamed answer.
- Uploaded files remain durable and user-scoped for later reuse in Library.

## User Flows

- Attach one or more PDFs while in Ask mode.
- Submit a grounded question and receive an answer.
- Revisit the stored file or derived report later from Library.

## Key System Components

- `web/src/components/ChatPdfAttachments.tsx`
- `web/src/hooks/useChatPdfAttachments.ts`
- `src/web/routes/advisor.py`
- `src/web/routes/library.py`

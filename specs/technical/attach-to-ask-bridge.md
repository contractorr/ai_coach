# Attach-to-Ask Bridge

## Overview

Attach-to-Ask Bridge extends the web advisor flow so same-turn PDF uploads can be attached, indexed, persisted, and retrieved without forcing the user through the Library workspace first. Architecturally it reuses the existing uploaded-document pipeline from the Library module, while adding chat-scoped attachment lifecycle, readiness states, and conversation persistence.

## Dependencies

**Depends on:** `web` (advisor routes, conversation store, auth), `library` (PDF persistence + extraction + indexing), `advisor` (attachment-aware retrieval), `memory` (optional document-derived fact extraction), `llm`
**Depended on by:** `web chat surfaces`, `advisor ask/stream routes`, `conversation history rendering`

---

## Components

### Library Upload Extensions for Chat Origin

**Files:** `src/library/reports.py`, `src/web/routes/library.py`, `src/web/models.py`
**Status:** Partially Implemented

#### Behavior

The existing uploaded-PDF path remains the source of truth. Chat attachments are stored as uploaded Library items with two metadata fields:

- `origin_surface`: `library` or `chat`
- `visibility_state`: `hidden`, `saved`, or `archived`

Chat uploads default to `origin_surface="chat"` and `visibility_state="hidden"`. This lets the product reuse one storage/indexing path while preserving the functional requirement that the user can choose whether to save the document into the visible Library workspace.

Extraction and indexing remain synchronous for ordinary uploads so same-turn advisor use works with bounded latency.

#### Inputs / Outputs

Current model additions:

| Field | Type | Notes |
|---|---|---|
| `origin_surface` | `str` | `library` \| `chat` |
| `visibility_state` | `str` | `hidden` \| `saved` \| `archived` |
| `index_status` | `str` | persisted backend values are `ready` \| `limited_text`; frontend adds local `pending` \| `uploading` \| `failed` states |
| `extracted_chars` | `int` | best-effort extraction size |

#### Invariants

- Uploaded bytes and extracted text remain per-user and never enter shared/global indexes.
- `ready` means the item is searchable by the advisor in the same request cycle.
- Hidden chat-origin documents are addressable by ID for advisor retrieval even when absent from the visible Library list.

#### Error Handling

- Invalid or oversized PDF -> HTTP 400.
- Extraction succeeds with minimal text -> artifact retained with `index_status="limited_text"`.
- Upload or indexing failure -> request fails and the caller must not treat the attachment as available for the current turn.

#### Configuration

| Key | Default | Source |
|---|---|---|
| max PDF bytes | `10 MB` | existing Library route constant |
| supported MIME types | `application/pdf` | hardcoded in route validation |

---

### Chat Attachment API

**Files:** `src/web/routes/advisor.py`, `src/web/models.py`
**Status:** Partially Implemented

#### Behavior

Adds chat-first upload and promotion endpoints that reuse the Library upload flow:

```python
POST /api/advisor/attachments
POST /api/advisor/attachments/{attachment_id}/save
```

The upload route:

1. validates PDF-only multipart uploads
2. optionally validates `conversation_id` ownership when supplied
3. extracts text and indexes synchronously through the existing Library path with `origin_surface="chat"`
4. returns an attachment envelope consumable by the composer

The save route promotes a hidden chat upload into the visible Library workspace without changing its underlying document identity.

Response shape:

```json
{
  "attachment_id": "lib_xxx",
  "file_name": "resume.pdf",
  "mime_type": "application/pdf",
  "index_status": "ready",
  "visibility_state": "hidden",
  "extracted_chars": 48213,
  "warning": null
}
```

`POST /api/advisor/ask` and `POST /api/advisor/ask/stream` both accept `attachment_ids`, and the web client now actively uses that request shape.

#### Inputs / Outputs

| Endpoint | Method | Input | Response |
|---|---|---|---|
| `/api/advisor/attachments` | POST | multipart `file` + optional `conversation_id` | `ChatAttachmentResponse` |
| `/api/advisor/attachments/{attachment_id}/save` | POST | path `attachment_id` | `ChatAttachmentResponse` |
| `/api/advisor/ask` | POST | JSON body with `attachment_ids: list[str]` | existing advisor response |
| `/api/advisor/ask/stream` | POST | JSON body with `attachment_ids: list[str]` | existing SSE response |

#### Invariants

- Only `index_status in {"ready", "limited_text"}` attachments may be sent to the advisor.
- Attachment ownership is enforced at query level; cross-user attachment IDs are rejected.
- Attachment IDs must resolve to Library items, not arbitrary filesystem paths.

#### Error Handling

- Unknown or wrong-user `attachment_id` in ask/save routes -> HTTP 404.
- Non-ready attachment in ask routes -> HTTP 422.
- Shared/lite mode continues to allow attachments, but the richer agentic path stays disabled per existing rules.

---

### ConversationStore Attachment Persistence

**Files:** `src/web/conversation_store.py`, `src/web/routes/advisor.py`
**Status:** Implemented

#### Behavior

Implements the attachment-aware conversation shape already called out in `web.md`:

- each user message may retain zero or more attachment references
- attachment metadata is stored in `conversation_message_attachments`
- conversation reads include attachment metadata for transcript rendering

`add_message(..., attachments=[...])` is now used in the active web advisor route implementation.

#### Invariants

- Conversation history keeps references, not duplicated document bodies.
- Deleting a conversation removes message-attachment rows but does not delete the underlying Library document.

#### Error Handling

- Missing attachment metadata on read yields `attachments=[]`, not a broken conversation payload.

---

### Frontend Chat Attachment Composer

**Files:** `web/src/components/ChatPdfAttachments.tsx`, `web/src/hooks/useChatPdfAttachments.ts`, `web/src/app/(dashboard)/page.tsx`, `web/src/app/(dashboard)/advisor/page.tsx`
**Status:** Partially Implemented

#### Behavior

Adds composer-local attachment state with upload progress and readiness labels. The UI uses shared cards, badges, inline warning text, and a secondary `Save to Library` action on transcript attachments.

Current local states per attachment:

- `pending`
- `uploading`
- `ready`
- `limited_text`
- `failed`

The current web client supports up to 5 PDFs per message. On submit, it uploads pending PDFs first, then sends the advisor request with the returned attachment ids.

#### Invariants

- Ready-state attachment badges are visible before send.
- Users can remove pending or failed attachments before submitting a turn.
- `Save to Library` is a secondary action on hidden chat-origin uploads.

#### Error Handling

- Failed upload remains visible with inline error text and can be removed before retrying the send.
- Limited-text state is warning-level, not destructive.

---

## Cross-Cutting Concerns

### Lifecycle model

- Chat upload -> hidden Library item -> advisor ask with `attachment_ids` -> attachment references stored on the user turn -> optional explicit save makes it visible in the Library workspace.

### Advisor retrieval

- `RAGRetriever.get_document_context(query, attachment_ids=...)` already prioritizes explicit attachments. This feature activates that path for web chat.

## Test Expectations

- Upload route tests: PDF-only validation, size validation, hidden chat-origin persistence, readiness-state response shape.
- Save route tests: hidden upload promotion, repeat-save idempotence, wrong-user rejection.
- Advisor route tests: valid `attachment_ids` included in same-turn ask, wrong-user attachment rejection, non-ready attachment rejection.
- Conversation store tests: message attachment insert/read/delete cascade behavior.
- Frontend tests: upload lifecycle, ready state before send, remove flow, save-to-library action.
- Mock: PDF extraction, Library indexing, advisor ask, filesystem, users with isolated ownership.


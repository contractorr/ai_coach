# Library

## Overview

The `library` module owns durable user-scoped knowledge artifacts: generated reports and uploaded source documents. It sits between the web layer and downstream consumers such as the advisor and memory pipeline, preserving the original artifact, normalized metadata, extracted text, and searchable snippets under each user's data directory.

The module now has two equally important jobs:
- persist and lifecycle-manage `Library` items (`generated` reports and `uploaded_pdf` documents)
- provide a retrievable text layer that can be searched in the Library UI, reused by the advisor, and mined for durable memory facts

The recommended architecture keeps the original PDF as the source artifact, markdown/frontmatter as the durable metadata record, and a rebuildable user-scoped text index for search and retrieval.

## Dependencies

**Depends on:** `llm`, `profile`, `journal` (light context only via goals/journal storage), `web`, `memory`, `storage_paths`
**Depended on by:** `web`, `advisor`, `memory`

---

## Components

### ReportStore

**File:** `src/library/reports.py`
**Status:** Experimental

#### Behavior

`ReportStore` manages file-backed Library items in a dedicated per-user `library` directory. Generated reports remain markdown files with YAML frontmatter. Uploaded PDFs are represented by a markdown metadata file plus a binary attachment in `library/attachments/`.

The store is responsible for:
- creating backing directories on first use
- generating safe metadata filenames from titles
- persisting generated reports and uploaded PDF records
- resolving attachment paths safely
- listing items with lightweight metadata and previews
- reading a full item by ID
- updating item metadata and generated content in place
- archiving and restoring items via status mutation rather than destructive deletion

The store does not perform PDF extraction, indexing, or advisor retrieval itself. It is the durable artifact layer.

#### Inputs / Outputs

| Method | Inputs | Returns |
|--------|--------|---------|
| `__init__(library_dir)` | `str | Path` | `None` |
| `create(...)` | title, prompt, report_type, content, collection, source_kind, status | `dict` item record |
| `create_uploaded_pdf(...)` | title, file_name, file_bytes, mime_type, collection | `dict` item record |
| `list_reports(...)` | search, status, collection, limit | `list[dict]` |
| `get_report(report_id)` | `str` | `dict | None` |
| `update_report(report_id, ...)` | partial fields | `dict | None` |
| `archive_report(report_id)` | `str` | `dict | None` |
| `restore_report(report_id)` | `str` | `dict | None` |
| `get_attachment_path(report_id)` | `str` | `Path | None` |

Frontmatter / normalized metadata fields:

| Field | Type | Notes |
|------|------|-------|
| `report_id` | `str` | Stable identifier across refreshes and edits |
| `title` | `str` | User-visible title |
| `report_type` | `str` | Generated reports: `crash_course`, `overview`, `memo`, `plan`, `custom`; uploaded docs: `document` |
| `status` | `str` | `ready` or `archived` |
| `collection` | `str | None` | Flat folder-like grouping |
| `prompt` | `str` | Generation prompt or synthetic upload prompt (`Uploaded PDF: ...`) |
| `source_kind` | `str` | `generated` or `uploaded_pdf` |
| `created` | `str` | ISO timestamp |
| `updated` | `str` | ISO timestamp |
| `last_generated_at` | `str` | ISO timestamp; for uploaded PDFs this is effectively the added-at time |
| `file_name` | `str | None` | Original upload filename |
| `file_size` | `int | None` | Bytes |
| `mime_type` | `str | None` | Usually `application/pdf` |
| `attachment_path` | `str | None` | Relative path under `library/` |
| `extraction_status` | `str | None` | `pending`, `ready`, `failed`, `empty` |
| `extracted_text_path` | `str | None` | Relative path for extracted text sidecar if used |

#### Invariants

- All writes stay inside the resolved `library_dir`.
- Every Library item has a stable `report_id` in frontmatter.
- Uploaded PDFs preserve the original file separately from metadata.
- `archive_report()` never deletes the artifact; it only mutates `status`.
- `list_reports()` returns newest-updated items first.
- Filename is not the source of truth for identity; `report_id` is.

Not guaranteed:
- No concurrent-write protection across multiple processes.
- No automatic deduplication of semantically similar uploads.
- No immutable revision graph for repeated uploads of the same logical document.

#### Error Handling

- Path traversal attempts are rejected by resolved-path checks.
- Missing IDs return `None` from store methods and become `404` at the route layer.
- Malformed metadata files are skipped during listing rather than crashing the whole workspace.
- Invalid update fields should be rejected before reaching the store.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `library_dir` | `{user_data_dir}/library` | derived from `get_user_paths(user_id)["data_dir"]` |
| attachments dir | `{library_dir}/attachments` | hardcoded convention |
| extracted text dir | `{library_dir}/extracted` | hardcoded convention |
| filename slug length | `60` chars max | hardcoded |

#### Caveats

- ReportStore is the durable source of truth, not the search layer.
- Search over extracted document text should not rely on repeatedly scanning every markdown file on each request once document volume grows.

---

### LibraryIndex

**File:** `src/library/index.py`
**Status:** Experimental

#### Behavior

`LibraryIndex` is the retrieval layer for Library items. It stores normalized searchable text for generated reports and uploaded PDFs, and returns ranked snippets for UI search and advisor context assembly.

The recommended implementation is a per-user SQLite FTS5 index rooted under the user's library data path. The index is rebuildable from `ReportStore` artifacts and therefore is not the primary source of truth.

Responsibilities:
- upsert searchable text for Library items after generation or upload
- index extracted PDF text and generated report text separately from the original artifact
- support title/file-name/text search for the Library page
- return bounded snippets for advisor retrieval
- support deletion/archive-aware filtering and full rebuilds

#### Inputs / Outputs

| Method | Inputs | Returns |
|--------|--------|---------|
| `__init__(index_path)` | `str | Path` | `None` |
| `upsert_item(...)` | item id, title, source_kind, report_type, collection, status, file_name, body_text, extracted_text, updated_at | `None` |
| `delete_item(item_id)` | `str` | `None` |
| `search(...)` | query, limit, source_kind?, status?, collection? | `list[dict]` |
| `get_item_text(item_id)` | `str` | `dict | None` |
| `rebuild(records)` | iterable of normalized store records | `dict` rebuild stats |

Recommended search result shape:

| Field | Type | Notes |
|------|------|-------|
| `id` | `str` | `report_id` |
| `title` | `str` | display title |
| `source_kind` | `str` | `generated` or `uploaded_pdf` |
| `file_name` | `str | None` | upload name for documents |
| `snippet` | `str` | bounded matching excerpt |
| `score` | `float | None` | optional ranking score |

#### Invariants

- The index is always user-scoped.
- The index is rebuildable; corruption should not imply artifact loss.
- Archived items may remain indexed but must be filterable by status.
- Snippet generation must be bounded and safe to inject into prompts.

#### Error Handling

- Index failures should never delete or mutate the source artifact.
- Search failures should degrade to empty results or store-backed fallback, not crash the page.
- Rebuild should skip malformed items and report counts rather than aborting the whole run.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `index_path` | `{library_dir}/library_index.db` | module convention |
| UI search limit | `50` | route default |
| advisor retrieval limit | `3-5` items | advisor retrieval config |
| max snippet chars | `300-1200` | caller-specific |

---

### Library Web Routes

**File:** `src/web/routes/library.py`
**Status:** Experimental

#### Behavior

The route module exposes authenticated endpoints for Library generation, upload, retrieval, and file download. It owns:
- building the per-user `ReportStore` and `LibraryIndex`
- generating report content via the configured LLM provider
- validating PDF uploads and storing them durably
- extracting text from PDFs synchronously enough for same-turn advisor use
- indexing generated text and extracted document text
- translating store/index records into `web.models` response shapes
- logging lifecycle events for analytics

Target route set:
- `GET /api/library/reports`
- `POST /api/library/reports`
- `POST /api/library/reports/upload`
- `GET /api/library/reports/{report_id}`
- `GET /api/library/reports/{report_id}/file`
- `PUT /api/library/reports/{report_id}`
- `POST /api/library/reports/{report_id}/refresh`
- `POST /api/library/reports/{report_id}/archive`
- `POST /api/library/reports/{report_id}/restore`

Behavior details:
1. `POST /api/library/reports` generates markdown immediately, persists it, and indexes the generated text.
2. `POST /api/library/reports/upload` validates PDF content, stores the original file, extracts text, indexes that text, and returns a Library item record suitable for immediate advisor attachment.
3. `GET /file` resolves attachment path through the store layer and streams the original PDF back with the original filename.
4. `POST /refresh` is valid only for `source_kind="generated"`; uploaded documents are replaced by later uploads rather than prompt refresh.

Generation prompt construction should:
1. include the requested report type and user prompt
2. add profile summary when available
3. add active goal titles when available
4. instruct the model to return markdown with clear headings and practical structure

Shared-key users follow the same web rate-limit path used by other LLM-backed surfaces.

#### Inputs / Outputs

| Model / Input | Fields |
|------|--------|
| `LibraryReportCreate` | `prompt`, `title?`, `report_type`, `collection?` |
| upload form | `file`, `title?`, `collection?` |
| `LibraryReportUpdate` | `title?`, `content?`, `collection?` |
| `LibraryReportResponse` | stored metadata + full content + attachment metadata |
| `LibraryReportListItem` | stored metadata + preview + attachment metadata |

#### Invariants

- All routes are user-scoped and must only access that user's items.
- Upload returns a durable Library item ID that can be reused by chat surfaces immediately.
- `refresh` preserves `report_id` while updating generated content and timestamps.
- `archive` and `restore` mutate status only.
- Download is ID-based and never accepts arbitrary relative file paths from clients.

#### Error Handling

- Missing API key on generation returns `400` when no personal or shared key is configured.
- Invalid or oversized PDF upload returns `400`.
- Missing item ID or wrong-user item returns `404`.
- Extraction/indexing failures should surface as item status/metadata where possible; raw upload should not be silently dropped.
- Validation failures return `422` via FastAPI/Pydantic for structured fields.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| provider | user secret or configured default | `web.deps` |
| model | shared-model override for shared-key users | `web.deps.SHARED_LLM_MODEL` |
| generation max tokens | `~2500` | route helper |
| max PDF bytes | `10 MB` | route constant |
| allowed MIME types | `application/pdf` | route validation |

#### Caveats

- The first extraction phase is text-only PDF parsing; OCR-heavy scanned PDFs may index poorly.
- Extraction should be synchronous for ordinary uploads so same-turn chat usage works, but pathological documents may still yield empty text.

---

### Library Dashboard Page

**File:** `web/src/app/(dashboard)/library/page.tsx`
**Status:** Experimental

#### Behavior

The Next.js page provides the first Library workspace UX. It now covers both generated reports and uploaded PDFs:
- a left-side list of Library items with search and status filters
- a create form for generated reports
- a PDF upload form with collection/title metadata
- a detail view that branches by source type
- inline actions for save, refresh (generated only), archive/restore, preview, and download

The page is optimized for retrieval and iteration:
- newly created or uploaded items are selected automatically
- generated items remain editable in place
- uploaded PDFs show metadata and embedded preview rather than a textarea body editor
- archived items remain recoverable in place

#### Inputs / Outputs

Client-side state covers:
- item list
- selected item ID
- create form state
- upload form state
- edit/detail state
- loading/saving/generating/uploading flags
- active search/status filters
- local preview URL state for downloaded blobs or file previews

The page depends on `/api/library/reports*` endpoints and download routes.

#### Invariants

- Selected detail stays in sync with successful save/refresh/archive/upload actions.
- Search and status filters should not clear the selected item unexpectedly.
- Upload and create actions reset their respective form state after success.
- UI must not offer `refresh` for uploaded documents.

#### Error Handling

- API errors surface as toast messages.
- Empty states remain actionable.
- Upload/generation actions show explicit loading state rather than appearing idle.
- Preview failure does not imply artifact loss; download should still be available when the file exists.

#### Caveats

- Generated reports use a simple textarea editor, not rich markdown editing.
- Uploaded PDFs are previewed, not edited as binary artifacts.
- Search UX depends on indexed extracted text quality.

---

## Cross-Cutting Concerns

### Security

- All Library storage is fully user-scoped.
- File lookup must always be ID-based through the store layer.
- Uploaded PDFs and extracted text can contain sensitive user data and must never be stored in shared/global indexes.
- Advisor and memory consumers should access Library data only through validated user-owned IDs or user-scoped retrieval helpers.

### Analytics

Recommended lifecycle events:
- `library_report_created`
- `library_report_refreshed`
- `library_report_updated`
- `library_report_archived`
- `library_report_restored`
- `library_pdf_uploaded`
- `library_pdf_indexed`
- `library_pdf_extraction_failed`

### Spec Alignment

This module now supports the durable-document side of the functional spec, even when the first UI entry point is chat. Chat upload should reuse the same underlying Library persistence and indexing path rather than inventing a second attachment store.

Deferred beyond first phase:
- non-PDF office documents
- OCR-heavy extraction for scans
- deep version history and diffing across document replacements
- autonomous report creation

## Test Expectations

A correct test suite should verify:
- create/list/get/update/archive/restore happy paths for generated reports
- upload/list/get/download happy paths for PDFs
- extracted-text indexing after upload and after report generation
- per-user isolation between at least two users
- refresh regenerates in place without changing generated report identity
- uploaded documents reject refresh and preserve original file downloads
- listing/search/filter behavior across generated and uploaded items
- advisor-facing retrieval helpers can search indexed extracted text
- frontend build/lint passes with generated and uploaded item states
- LLM calls and PDF extraction are mocked in route tests where appropriate

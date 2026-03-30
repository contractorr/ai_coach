---
id: library
category: tracked_module
status: updated
implements:
- library-reports
code_paths:
- src/library
- src/web/routes/library.py
- web/src/app/(dashboard)/research/page.tsx
- tests/library
last_reviewed: '2026-03-30'
---

# Research

**Status:** Updated for the simplified product model

## Overview

Research is the durable reference workspace for uploaded documents, generated reports, and archived dossier outputs.

## Key Modules

- `src/web/routes/library.py`
- `src/web/routes/research.py`
- `web/src/app/(dashboard)/research/page.tsx`
- `web/src/components/research/ResearchWorkspace.tsx`

## Interfaces

- `GET /api/library/reports` and related detail/update endpoints
- `GET /api/research/dossiers?include_archived=true&limit=50`
- report refresh, archive, and file download flows

## Library Package (`src/library/`)

### `reports.py` — `ReportStore`
- Markdown files with YAML frontmatter in `~/coach/users/{id}/library/`
- Lifecycle states: `ready`, `archived`, `restored`
- `_generate_report_content()` uses LLM with user profile + active goals as context
- PDF binary storage in `attachments/{report_id}.pdf`, extracted text in `extracted/`

### `embeddings.py` — `LibraryEmbeddingManager`
- Mirrors `journal/embeddings.py` pattern
- Constructor: `__init__(chroma_dir)` → `LocalCollection(name="library")` + `build_embedding_function()`
- `add_item(id, content, metadata)` — upsert with metadata sanitization (lists → comma-joined strings)
- `remove_item(id)` — delete, swallow errors
- `query(text, n_results=5)` → `list[dict]` with `{id, content, metadata, distance}`
- `sync_from_storage(items)` → `(added, removed)` — upsert all, prune deleted
- `count()` → int

### `index.py` — `LibraryIndex`
- SQLite FTS5 index with Porter stemmer
- Columns: title, body, extracted_text, collection, filename
- Supports search across all library item types (reports + uploads)
- Optional `embedding_manager: LibraryEmbeddingManager` injected at construction
- `semantic_search(query, *, n_results, source_kind, status, collection)` → delegates to embedding manager, enriches from FTS5 `get_item_text()`
- `hybrid_search(query, *, limit, semantic_weight=0.7, source_kind, status, collection)` → RRF over `semantic_search` + `search`, falls back to FTS5-only when no embeddings

### `pdf_text.py`
- `extract_text_from_pdf_bytes()` — uses `pypdf` (optional)
- Falls back gracefully if pypdf unavailable
- Extracted text feeds FTS5 index + optional memory pipeline

### Routes
- `POST /api/library/reports/upload` — PDF upload with text extraction
- `GET /api/library/reports/{id}/file` — FileResponse download, path traversal protected
- `GET /api/library/reports` — list with FTS search support
- Report CRUD: create, update, archive, restore, delete

## Simplified Product Notes

- Active dossiers stay in Radar until archived.
- Research should feel like a reference surface, not an active monitoring console.

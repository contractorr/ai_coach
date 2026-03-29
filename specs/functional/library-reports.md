# Research

**Status:** Updated for the simplified product model

## Purpose

Research is the durable reference workspace for uploaded documents, generated reports, and archived dossier outputs. It should feel like a calm reference surface rather than an active monitoring console.

## Product Placement

- Workspace: secondary `Research` workspace
- Current route: `/research` (with `/library` kept as an alias)
- Entry points: contextual links from `Radar`, `Journal`, and guided flows
- Primary job: find, reuse, and manage durable reference material
- Journal handoff: the user can jump from Research into the deeper Journal workspace when they need source notes instead of durable artifacts

## Current Behavior

- Research supports type filtering across documents, reports, and dossiers.
- Report generation should be available as a secondary action, not a permanent top-of-page form.
- Active dossiers stay in Radar until they are archived.
- Archived dossiers become read-only reference material in Research.
- Report-like items can still be refreshed or edited from the Research workspace.

## User Flows

- Filter the research workspace by content type.
- Open a report or archived dossier for later reference.
- Jump from Research to Journal when the user wants source captures rather than durable outputs.

## Research Index and Search

- `LibraryIndex` provides FTS5 full-text search (Porter stemmer) across title, body, extracted text, collection, and filename.
- Search covers both LLM-generated reports and uploaded PDFs.
- Results ranked by FTS5 relevance score.

## PDF Upload and Extraction

- Users upload PDFs via `POST /api/library/reports/upload`.
- Binary stored in `library/attachments/{report_id}.pdf`; extracted text saved in `library/extracted/`.
- Text extraction uses `pypdf` (optional dependency). Falls back to empty text if unavailable.
- Extracted text feeds into the FTS5 index and optionally into the memory pipeline (`config.memory.enabled`).
- Download via `GET /api/library/reports/{id}/file` as `FileResponse` with path traversal protection.

## Report Storage

- `ReportStore` persists LLM-generated reports as markdown files with YAML frontmatter in `~/coach/users/{id}/library/`.
- Report lifecycle: `ready` → `archived` → `restored`.
- Reports generated using user profile + active goals as context.

## Semantic Search

- Embeddings generated via the shared embedding factory (`chroma_utils.build_embedding_function()`), one vector per document.
- Stored in a `LocalCollection(name="library")` inside the user's chroma directory.
- Embeddings upserted on every `upsert_item()` and removed on every `delete_item()`.
- **Advisor RAG path** uses hybrid search (semantic + FTS5 via reciprocal rank fusion, default 70/30 semantic weight).
- **Web list search** stays FTS5-only for latency.
- Graceful fallback: when no embedding manager is present, `hybrid_search()` delegates to FTS5-only `search()`.

### Acceptance Criteria

- Concept search works: querying "exhaustion" retrieves a doc containing "burnout" (via semantic similarity).
- FTS fallback works: `LibraryIndex` without an embedding manager still returns keyword results.
- Deleting a library item removes its embedding.
- Every write (create, update, refresh, upload) upserts the embedding automatically.

## Key System Components

- `web/src/app/(dashboard)/research/page.tsx`
- `web/src/components/research/ResearchWorkspace.tsx`
- `src/web/routes/library.py`
- `src/web/routes/research.py`
- `src/library/reports.py` — `ReportStore`
- `src/library/index.py` — `LibraryIndex` (FTS5 + optional semantic)
- `src/library/embeddings.py` — `LibraryEmbeddingManager` (ChromaDB vectors)
- `src/library/pdf_text.py` — PDF extraction

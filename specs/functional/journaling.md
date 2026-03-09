# Journaling

**Status:** Approved
**Author:** —
**Date:** 2026-03-02

## Problem

Users need a structured way to capture professional reflections, project notes, and career insights over time. Without persistent journaling, the advisor has no personal context to ground its advice in.

## Users

All users. Daily journalers get the most value, but even occasional entries improve advisor quality.

## Desired Behavior

### Creating entries

1. User writes a journal entry with a body and optional title, type, and tags
2. System assigns a date-stamped filename, generates an LLM title if none provided, and saves as markdown with YAML frontmatter
3. Entry is automatically embedded into the vector store for future semantic retrieval

Entry types: `daily`, `project`, `goal`, `reflection`, `insight`, `note`, `quick`, `research`, `action_brief`.

### Templates

1. User requests a template (e.g., daily reflection, weekly review, goal setting, project update, learning log)
2. System returns a structured prompt with section headings the user fills in
3. Completed template is saved as a normal entry

Current interface scope:
- CLI exposes templates directly during `journal add`
- Web and MCP do not currently expose dedicated template endpoints

### Searching entries

1. User searches by keyword, semantic similarity, or both
2. System returns ranked results combining full-text search (keyword) and vector search (semantic) via weighted rank fusion (configurable semantic weight, default 0.7)
3. User can filter by entry type, tags, or date range

Current interface scope:
- CLI exposes semantic search directly
- MCP exposes semantic journal search
- Web currently focuses on browse/create/read/update/delete and quick capture; it does not expose a search route yet, but it does support client-side search/filtering over the currently loaded entries

### Browsing entries

1. User lists recent entries, optionally filtered by type or tags
2. System shows entries newest-first with title, date, type, tags, and a preview (first 200 chars)

### Web journal workspace

1. The web journal page supports client-side narrowing over the loaded entry list with keyword search, a type filter, and quick tag chips.
2. Search matches against the loaded entry title, preview, tags, and loaded content when available.
3. When filters return no matches, the web UI shows a contextual empty state and offers a reset action.
4. The web entry composer clarifies that titles are optional and can be auto-generated if left blank.

### Editing and deleting

1. User can update an entry's body or metadata; system stamps `updated` timestamp
2. User can delete an entry; file removal is supported across interfaces
3. Embedding cleanup currently happens in CLI and MCP delete paths; the web delete route currently removes only the file

### Trends and threads

1. System periodically detects recurring topics across entries using cosine-similarity clustering
2. System detects trends over time windows using KMeans clustering and LLM summarization
3. User can view detected threads and trends

### Sentiment

1. System performs lexicon-based sentiment analysis on each entry
2. Sentiment is stored as metadata and available for trend analysis

## Acceptance Criteria

- [ ] User can create entries via CLI, web, and MCP
- [ ] Entries with no title get an LLM-generated title
- [ ] New entries are embedded into ChromaDB (via MCP and web layers; direct `JournalStorage.create()` callers must embed separately)
- [ ] Hybrid keyword + semantic search exists in the journal module and is used by advisor retrieval
- [ ] Search is exposed directly in CLI and MCP; web currently does not expose a journal search endpoint
- [ ] The web journal page supports client-side search, type filtering, and tag chips over the loaded entries
- [ ] List entries returns newest-first, respects type/tag filters
- [ ] Editing an entry updates the `updated` timestamp
- [ ] Deleting an entry removes the file in all interfaces
- [ ] CLI and MCP delete paths also remove embeddings; web embedding cleanup is not yet wired
- [ ] Templates exist for all 5 template types in the journal module; direct template UX is currently CLI-only
- [ ] Entries exceeding 100KB are rejected with a clear error
- [ ] Tags are limited to 20 per entry; excess silently dropped

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty journal (no entries) | Search returns empty results; list shows nothing; no crash |
| Duplicate title on same day | Filename gets `_1`, `_2` suffix — no overwrite |
| Entry body exceeds 100KB | Rejected with error before save |
| Search query matches nothing | Return empty results, not an error |
| Web browse filters match nothing | Web UI shows a contextual empty state and keeps reset actions visible |
| Malformed markdown file in journal dir | Skipped silently during list/search |
| Tag with special characters | Sanitized; empty-after-sanitization tags dropped |

## Out of Scope

- Rich text / WYSIWYG editing (entries are plaintext markdown)
- Image or file attachments in entries
- Collaborative / shared journals
- Entry versioning (only current state is stored)

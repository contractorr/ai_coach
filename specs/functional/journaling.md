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

### Searching entries

1. User searches by keyword, semantic similarity, or both
2. System returns ranked results combining full-text search (keyword) and vector search (semantic) via weighted rank fusion (configurable semantic weight, default 0.7)
3. User can filter by entry type, tags, or date range

### Browsing entries

1. User lists recent entries, optionally filtered by type or tags
2. System shows entries newest-first with title, date, type, tags, and a preview (first 200 chars)

### Editing and deleting

1. User can update an entry's body or metadata; system stamps `updated` timestamp
2. User can delete an entry; system removes file and cleans up embeddings

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
- [ ] Search returns results combining keyword and semantic matches
- [ ] List entries returns newest-first, respects type/tag filters
- [ ] Editing an entry updates the `updated` timestamp
- [ ] Deleting an entry removes both the file and its embedding
- [ ] Templates return structured prompts for all 5 template types
- [ ] Entries exceeding 100KB are rejected with a clear error
- [ ] Tags are limited to 20 per entry; excess silently dropped

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty journal (no entries) | Search returns empty results; list shows nothing; no crash |
| Duplicate title on same day | Filename gets `_1`, `_2` suffix — no overwrite |
| Entry body exceeds 100KB | Rejected with error before save |
| Search query matches nothing | Return empty results, not an error |
| Malformed markdown file in journal dir | Skipped silently during list/search |
| Tag with special characters | Sanitized; empty-after-sanitization tags dropped |

## Out of Scope

- Rich text / WYSIWYG editing (entries are plaintext markdown)
- Image or file attachments in entries
- Collaborative / shared journals
- Entry versioning (only current state is stored)

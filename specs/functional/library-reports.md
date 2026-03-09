# Library Workspace

**Status:** Partially Implemented
**Author:** OpenAI
**Date:** 2026-03-08

## Problem

Useful long-form answers and reference documents currently live in chat or research flows, which makes them easy to lose, hard to revisit, and awkward to refine over time. Users need a durable place to generate, save, organize, refresh, and reuse AI-created knowledge artifacts such as crash courses, market overviews, preparation memos, and synthesis documents.

## Users

- Users who ask the advisor for deep explanations, overviews, or strategic syntheses
- Users doing research on an industry, company, skill area, or opportunity
- Users who want to turn one-off AI output into a reusable personal knowledge library

## Desired Behavior

Naming model:
- Workspace: `Library`
- Saved artifact: `Library item`
- Generated artifact: `Report`
- Optional report types: `Crash Course`, `Overview`, `Memo`, `Strategy Note`, `Update`


### Core concept

1. The product includes a dedicated workspace called `Library`.
2. A library item is currently a saved AI-generated report.
3. A generated report is a saved AI-created artifact with a title, body, status, source context, and update history.
4. Library items are meant for durable outputs and reference materials such as:
   - crash courses
   - industry overviews
   - prep memos
   - strategy notes
   - opportunity summaries
   - weekly or monthly synthesized reports
5. A library item is a reusable asset, not just a transient chat reply or attachment.

### Creating a report on demand

1. User can create a new report from the `Library` workspace.
2. User provides a prompt or topic, such as `Give me a crash course on the insurance industry`.
3. User can optionally choose a report type such as `crash course`, `overview`, `memo`, `plan`, or `custom`.
4. User can optionally include relevant product context such as profile, goals, projects, watchlist items, saved intel, or research dossiers.
5. System generates the report and saves it as a durable artifact instead of leaving it only in chat.
6. The saved report appears in the `Library` list immediately after generation.

Current interface scope:
- Web supports prompt-to-report generation, list browsing, search, editing, refresh, archive, restore, and simple free-text collections.
- Save-from-chat, save-from-dossier, assistant-suggested generation, extracted-text search, and recurring reports are not yet fully shipped.
- New PDF upload is not currently supported from the `Library` workspace or chat surfaces.

### Saving work from other surfaces

1. User can save a response from chat, deep research, dossiers, goals, or intel as a report.
2. When a user saves existing output as a report, the system preserves the original prompt or origin where available.
3. The new report opens in the `Library` workspace so the user can continue refining or revisiting it later.

### Organization and retrieval

1. User can browse all reports from a single index view.
2. Each library item shows lightweight metadata such as title, type, updated time, status, and originating context.
3. User can search generated reports by title and content preview.
4. User can filter library items by status, type, or origin.
5. User can group library items into collections so related work stays together.
6. Collections should feel like simple folders from the user perspective, without requiring deep nested hierarchy for the initial experience.

Current interface scope:
- The MVP uses a single optional collection field on each report rather than a dedicated collection-management surface.

### Reading and editing

1. User can open any generated report and read it as a long-form document.
2. User can rename a report.
3. User can lightly edit generated report content after generation.
4. User can regenerate a generated report or ask the assistant to expand, shorten, or refocus it.
5. User can archive a library item without deleting it.

Current interface scope:
- The MVP uses a plain textarea editor rather than rich markdown tooling.

### Refreshing and staying current

1. User can refresh an existing report instead of creating a duplicate when they want the same topic updated.
2. Refreshed reports keep their identity and should not feel like unrelated new documents.
3. When important source context has changed materially, the product can mark a report as stale and suggest refreshing it.
4. Users should be able to see when the current version was last generated or refreshed.
5. Refresh applies only to generated reports.

Current interface scope:
- The MVP supports manual refresh from the stored prompt, but it does not yet auto-mark reports as stale based on changing upstream context.

### Assistant-initiated generation

1. The assistant can suggest creating a report when it detects repeated interest in a topic or a need for a reusable synthesis.
2. Example triggers include:
   - repeated questions on the same industry or company
   - a dossier with enough accumulated context to summarize
   - a major watchlist or intel shift that merits a synthesized update
3. Suggested report generation should be user-confirmed by default.
4. The product may later support user-enabled recurring or auto-generated reports, but that should be explicitly opt-in.
5. The assistant should not silently flood the workspace with unrequested reports.

Current interface scope:
- Assistant-suggested or autonomous report creation is not yet implemented.

### Relationship to dossiers and chat

1. Chat remains the fastest place to ask ad hoc questions.
2. Library reports are durable, reusable artifacts that should outlive a single conversation.
3. Research dossiers remain the place for ongoing topic tracking over time.
4. A dossier can produce reports, but a report is a generated deliverable rather than a live monitored topic.
5. Library reports should remain clearly distinct from transient chat replies and from live dossiers.

## Acceptance Criteria

- [ ] Users can create a saved report directly from a freeform prompt.
- [ ] Users can save long-form outputs from other surfaces as reports.
- [ ] The `Library` workspace lists saved reports with title, status, type, and updated time.
- [ ] Users can search and filter library items without opening each one individually.
- [ ] Users can organize reports into simple collections.
- [ ] Users can rename, edit, refresh, and archive a generated report.
- [ ] The current report view clearly indicates when it was last generated or refreshed.
- [ ] The assistant can suggest creating a report, but user confirmation is required by default.
- [ ] Refreshing a report updates the existing artifact rather than always creating a duplicate.
- [ ] The distinction between library reports, chat replies, and research dossiers is understandable from the UI.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User asks for a crash course but has no profile or saved context | System still generates a useful general report instead of blocking |
| User generates a report on a topic that already exists | Product suggests updating the existing report or creating a second one intentionally |
| Source context has changed since the report was generated | Report can be marked stale and offer a refresh action |
| User starts a generation that takes longer than normal | Report shows an in-progress state instead of appearing missing |
| Assistant thinks a report would help but the user is busy | Suggestion is dismissible and does not auto-create clutter |
| User archives a report by mistake | Archived reports remain recoverable |
| User saves a short chat reply as a report | Product still creates the artifact, but the user can expand it later |

## Out of Scope

- Real-time collaborative editing across multiple users
- Publishing library reports publicly as web pages
- Replacing research dossiers as the system for ongoing monitored topics
- Full document-layout or slide-design tooling inside the report editor
- Deep nested folder trees in the first version

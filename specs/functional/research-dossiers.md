# Research Dossiers

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-07

## Problem

Deep research currently produces one-off reports. That is useful for snapshots, but it breaks down when a user needs ongoing monitoring of a strategic topic over days or weeks.

## Users

Users who want persistent research on topics tied to their goals, career plans, projects, investment theses, job search, or technical decisions.

## Desired Behavior

### Creating a dossier

1. User creates a dossier for a long-lived topic such as a company, market, career path, or technical decision.
2. User can provide a topic, scope, core questions, assumptions, related goals, and tracked subtopics.
3. System saves the dossier as a persistent research object that can be revisited later.

### Viewing dossiers

1. User can list existing dossiers.
2. Each dossier shows its topic, status, last updated time, and a short summary of the latest change.
3. User can open a dossier to view its current brief, accumulated updates, and open questions.

Current interface scope:
- Web currently exposes dossier behavior through API routes; there is not yet a dedicated dashboard page.
- CLI exposes list, create, and view flows.
- MCP currently exposes dossier create/list and research-run flows, but not dossier-detail retrieval.

### Updating dossiers

1. User can manually run research against an existing dossier.
2. When scheduled research runs, the system prefers active dossiers before creating fresh one-off topics.
3. Each new update is appended to the dossier timeline instead of replacing prior updates.

### Dossier update contents

1. Every dossier update includes:
   - what changed
   - why it matters
   - evidence with citations or source references
   - confidence
   - recommended next actions
   - open questions
2. The system stores a concise change-since-last-update summary that is visible when listing or opening the dossier.

### Advisor and recommendation usage

1. Advisor can use research entries, including dossier content and dossier updates, as part of its broader research context.
2. Recommendation generation can also draw on the same research context when available.

### Lifecycle and status

1. Dossiers carry a status such as `active` or `archived`.
2. Archived dossiers are skipped by scheduled dossier updates.

Current interface scope:
- Storage and list filtering understand archived dossiers.
- User-facing archive or reactivate controls are not yet exposed in web, CLI, or MCP.

## Acceptance Criteria

- [ ] User can create a dossier with topic plus optional scope, questions, assumptions, goals, and tracked subtopics.
- [ ] User can list existing dossiers with status and latest change summary.
- [ ] Manual research can target an existing dossier.
- [ ] Scheduled research appends updates to active dossiers when dossiers exist.
- [ ] Dossier updates accumulate over time with timestamps and source references.
- [ ] The system exposes a summary of what changed since the prior dossier update.
- [ ] Advisor queries can pull from dossier-backed research context indirectly through shared research retrieval.
- [ ] Recommendation generation can use dossier-backed research context.
- [ ] Dossier create/list/run are available via CLI, web API, and MCP.
- [ ] Dossier detail/view is currently available in CLI and web API; MCP detail retrieval is not yet exposed.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User creates a dossier with only a topic | System accepts it and uses sensible defaults for optional fields |
| Dossier has no prior updates | Dossier detail clearly shows that no updates have been recorded yet |
| Dossier update finds weak or conflicting evidence | Update still saves and calls out uncertainty |
| User requests research for an unknown dossier ID | System returns a clear not-found error |
| User has no dossiers | Scheduled research falls back to normal topic selection |
| Dossier is archived out-of-band | It remains viewable and is skipped by automatic scheduled research |

## Out of Scope

- Shared dossiers across multiple users
- Automatic dossier creation from title similarity
- Human-in-the-loop approval workflows
- A dedicated dossier dashboard page or timeline redesign
- User-facing archive/reactivate controls until they are explicitly implemented

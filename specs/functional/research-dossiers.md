# Research Dossiers

**Status:** Approved
**Author:** —
**Date:** 2026-03-06

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

### Updating dossiers

1. User can manually run research against an existing dossier.
2. When scheduled research runs, the system prefers active dossiers before creating fresh one-off topics.
3. Each new update is appended to the dossier timeline instead of replacing prior updates.

### Dossier update contents

1. Every dossier update includes:
   - what changed
   - why it matters
   - evidence with citations
   - confidence
   - recommended next actions
   - open questions
2. The system stores a concise “change since last update” summary that is visible when listing or opening the dossier.

### Advisor and recommendation usage

1. When the user asks related questions, the advisor can use dossier summaries and updates as research context.
2. The recommendation engine can also draw on dossier state when generating recommendations.

## Acceptance Criteria

- [ ] User can create a dossier with topic plus optional scope, questions, assumptions, goals, and tracked subtopics
- [ ] User can list existing dossiers with status and latest change summary
- [ ] Manual research can target an existing dossier
- [ ] Scheduled research appends updates to active dossiers when dossiers exist
- [ ] Dossier updates accumulate over time with timestamps and citations
- [ ] The system exposes a summary of what changed since the prior dossier update
- [ ] Advisor queries can retrieve dossier content as research context
- [ ] Recommendation generation can use dossier-backed research context
- [ ] Available via CLI, web API, and MCP

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User creates a dossier with only a topic | System accepts it and uses sensible defaults for the optional fields |
| Dossier has no prior updates | Dossier detail clearly shows that no updates have been recorded yet |
| Dossier update finds weak or conflicting evidence | Update still saves, calls out uncertainty, and lowers confidence |
| User requests research for an unknown dossier ID | System returns a clear not-found error |
| User has no dossiers | Scheduled research falls back to normal topic selection |
| Dossier is archived | It remains viewable but is skipped by automatic scheduled research |

## Out of Scope

- Shared dossiers across multiple users
- Automatic dossier creation from title similarity
- Human-in-the-loop review workflows or approvals
- Full UI timeline redesign beyond exposing the new data


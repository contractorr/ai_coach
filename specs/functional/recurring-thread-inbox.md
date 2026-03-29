# Radar Threads

**Status:** Updated for the simplified product model

## Purpose

Recurring threads now live in Radar so active monitoring and triage stay in one place.

## Product Placement

- Workspace: `Radar`
- Tab: `Threads`
- Primary job: review recurring themes from the Journal and decide what deserves action

## Current Behavior

- Each thread shows label, activity timing, recent snippets, and inbox state.
- Inline actions allow goal creation, research, dossier creation, or dismissal.
- Thread review is part of monitoring, not a standalone workspace.
- Each thread also carries an internal strength score that rises with repeated high-similarity recurrence and falls with inactivity or divergence.
- Thread strength is the primary ranking signal for advisor recurring-thought context, with recent activity used only as a secondary tie-breaker.

## User Flows

- Open Radar > Threads.
- Review the thread summary and recent snippets.
- Convert, investigate, dossier, or dismiss from the same tab.

## Key System Components

- `web/src/app/(dashboard)/radar/page.tsx`
- `src/web/routes/threads.py`
- journal-to-thread extraction services

## Thread Inbox State Machine

Each thread has a persistent inbox state that controls what actions are available and whether it resurfaces.

### States

| State | Meaning |
|---|---|
| `active` | Visible in inbox, awaiting user triage |
| `dismissed` | User dismissed; hidden unless new matching entries arrive |
| `goal_created` | Thread converted to a goal; shown as resolved |
| `research_started` | Research triggered from this thread |
| `dossier_started` | Dossier creation triggered from this thread |
| `dormant` | No recent activity; deprioritized automatically |

### Transitions

- `active` → `dismissed` — user taps Dismiss
- `active` → `goal_created` — user converts thread to goal
- `active` → `research_started` — user triggers research
- `active` → `dossier_started` — user triggers dossier creation
- `dismissed` → `active` — new journal entry matches the thread (automatic resurface)
- any state → `dormant` — no new matching entries for an extended period (inactivity threshold)

### Available Actions Per State

Each thread exposes an `available_actions` list based on current state so the UI can render only valid controls:

- `active`: dismiss, create_goal, start_research, start_dossier
- `dismissed`: (none shown; resurfaces automatically)
- `goal_created`, `research_started`, `dossier_started`: view_linked (deep-link to created artifact)
- `dormant`: reactivate

### Persistence and Service

- `ThreadInboxStateStore` persists state to a `thread_inbox_state` SQLite table.
- `ThreadInboxService.list_inbox()` merges thread detection results with state overlays, attaches recent snippets (last 3 entries, up to 160 chars each), and supports filtering by state or free-text query.

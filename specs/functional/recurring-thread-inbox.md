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

# Recurring Thread Inbox

**Status:** Draft
**Author:** -
**Date:** 2026-03-08

## Problem

The system can already detect recurring topics across journal entries, but threads are not yet a first-class operating surface in web. That makes pattern detection feel passive and underused, even though recurring themes are often the best bridge from reflection into action.

## Overview

Recurring Thread Inbox turns detected journal threads into a dedicated workspace. Each thread becomes a reviewable unit with context, recent activity, and clear next actions such as making a goal, running research, or starting a dossier.

## Users

Users with enough journal history for repeated themes to emerge. Most useful for reflective users, people with several active projects, and users whose advice quality improves from recurring-thought context.

## User Stories

- As a user, I want to see the themes I keep returning to so I can decide what deserves action.
- As a user, I want one place where recurring topics can become goals, research runs, or dossiers.
- As a user, I want to dismiss or deprioritize a thread if it is no longer useful.
- As a user, I want thread state to reflect whether I have already acted on it.

## Dependencies

- Depends on thread detection and thread browsing described in `specs/functional/memory-threads.md`.
- Integrates with goals from `specs/functional/goal-tracking.md`, research from `specs/functional/deep-research.md`, and dossiers from `specs/functional/research-dossiers.md`.
- Receipts in `specs/functional/extraction-receipt.md` can deep-link into this workspace.
- Dossier suggestions in `specs/functional/dossier-escalation-engine.md` can be surfaced from thread cards.
- Not yet built: a dedicated web thread workspace, reindex controls in web, and user-facing inbox state beyond the raw thread store.

## Detailed Behavior

### Thread eligibility

1. A recurring thread becomes inbox-eligible when the existing thread detector has created an active thread.
2. In practical terms, that means at least two sufficiently similar entries have been grouped into one thread.
3. The inbox should not invent a second definition of a thread separate from the existing detector.
4. The inbox may prioritize threads with more recent activity, but eligibility is based on the underlying thread system.

### Inbox layout

1. User can open a dedicated recurring-thread workspace in web.
2. The inbox lists active threads with:
   - thread label
   - last updated time
   - number of entries
   - recent activity count
   - short summary or representative snippets
   - current inbox state
3. Threads are sorted by recent activity first, then by most recently updated.
4. User can filter by state such as `active`, `dismissed`, `goal_created`, `research_started`, `dossier_started`, or `dormant`.
5. User can search by thread label over the loaded list.

### Thread actions

Each thread card can offer the following actions:

1. `Make goal`
   - opens a prefilled goal-create flow using the thread label and recent entry context
   - resulting goal can store a backlink to the thread where supported
2. `Run research`
   - starts a deep-research run using the thread topic
   - result appears in research output and can be revisited later
3. `Start dossier`
   - opens a prefilled dossier-create flow using the thread label, recent evidence, and any related goals
4. `View entries`
   - opens the entries associated with the thread
5. `Dismiss`
   - hides the thread from the active inbox without deleting the underlying thread data

### Thread state over time

1. A thread begins as `active` when first surfaced.
2. If the user dismisses it, it becomes `dismissed`.
3. If the user creates a goal from it, the inbox state becomes `goal_created`.
4. If the user starts research, the inbox state becomes `research_started`.
5. If the user starts a dossier, the inbox state becomes `dossier_started`.
6. Threads with no recent activity can be shown as `dormant` without deleting their history.

Current interface scope:
- The inbox state is a user-facing workflow state layered on top of the underlying thread store.
- The raw thread detector remains responsible for grouping entries.
- V1 does not require the underlying thread store to support manual thread merging.

### Manual control

1. User can rename a thread label from the workspace.
2. User can dismiss and later re-open a dismissed thread.
3. User can trigger a thread reindex from web when thread quality appears stale.

Current interface scope:
- V1 does not support manually creating a brand-new thread that bypasses detection.
- V1 does not support merging two detected threads into one.

## Acceptance Criteria

- [ ] Web exposes a dedicated recurring-thread inbox that lists active threads.
- [ ] Inbox eligibility is based on the existing thread-detection system rather than a separate ad hoc rule.
- [ ] Thread cards show label, recency, entry count, and actionable next steps.
- [ ] Users can launch goal creation, research, or dossier creation from a thread card.
- [ ] Users can dismiss threads without deleting the underlying thread data.
- [ ] Users can rename threads and trigger reindexing from web.
- [ ] Thread inbox state reflects whether the user has already acted on a thread.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User has only one journal entry | Inbox is empty and explains that recurring threads need repeated themes |
| Thread routes are still miswired in web | Feature remains unavailable until thread-route wiring is fixed |
| Thread has old history but no recent activity | It can appear as dormant or in a secondary filter rather than crowding active work |
| User dismisses a thread by mistake | Thread can be restored from dismissed state |
| Thread label is poor or generic | User can rename it without changing the underlying entry content |
| User starts research from a thread with weak evidence | Research still runs, but results may be sparse or low-confidence |

## Success Metrics

- Increase in thread views from users with enough journal history
- Increase in conversions from threads into goals, research runs, or dossiers
- Increase in repeat usage of thread-derived workflows over passive thread inspection
- Healthy ratio of active versus dismissed threads, indicating manageable noise

## Out of Scope

- Manual creation of arbitrary threads in V1
- Manual merging or splitting of detected threads in V1
- Cross-user shared threads
- Replacing journal search or entry browsing with the inbox

## Open Questions

- Should dormant threads reappear automatically when new matching entries arrive, even if previously dismissed?
- Should starting a dossier from a thread suppress future thread-to-dossier suggestions automatically?

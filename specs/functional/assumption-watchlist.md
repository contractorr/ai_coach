# Assumption Watchlist

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

Users often make plans based on implicit assumptions, but those assumptions are easy to forget and hard to monitor over time. The product now has a structured assumption store and alerting path, but it still needs stronger extraction quality and tighter workflow integration to make assumptions feel first-class.

## Overview

Assumption Watchlist extracts or captures explicit assumptions, tracks the external signals most relevant to them, and surfaces confirmations or invalidations when the evidence changes. The feature should help users notice when the strategic foundation of a plan has shifted, rather than only reacting after outcomes are already visible.

## Users

Users making strategic plans, monitoring markets or companies, or using dossiers and research to inform decisions over weeks or months.

## User Stories

- As a user, I want important assumptions from my plans or research captured so they do not stay implicit.
- As a user, I want to add an assumption manually when I know something should be watched.
- As a user, I want alerts when evidence starts confirming or invalidating an assumption.
- As a user, I want resolved assumptions to remain part of my history without cluttering the active watchlist.

## Dependencies

- Can extract assumptions from journals, action plans, and dossier context from `specs/functional/journaling.md`, `specs/functional/action-plans.md`, and `specs/functional/research-dossiers.md`.
- Can consume signals from `specs/functional/company-movement-pipeline.md`, `specs/functional/hiring-activity-pipeline.md`, and `specs/functional/regulatory-change-pipeline.md`.
- Can surface in return briefings from `specs/functional/since-you-were-away-why-now.md`.
- Current implementation includes a per-user assumption store, journal-based suggestion extraction, signal refresh against company/hiring/regulatory intel, manual CRUD plus activate/resolve/archive flows, and alert surfacing in suggestions and return briefings. Follow-up work is mainly richer review UX and deeper dossier-native authoring.

## Detailed Behavior

### Assumption capture

1. The product can capture assumptions automatically from journals, plans, and research when the language is sufficiently explicit.
2. The user can also add an assumption manually.
3. Automatically extracted assumptions should be presented as reviewable suggestions rather than silently treated as confirmed active assumptions.
4. Manual assumptions should go directly into the user's watchlist.

### Assumption record

Each assumption record should include:

- statement
- status such as `active`, `confirmed`, `invalidated`, `resolved`, or `archived`
- confidence of the extraction when auto-created
- created date
- source type and source reference
- linked goals, dossiers, or watched entities when available
- latest evidence summary when available
- last reviewed or evaluated time

### Signal matching

1. Each assumption should be matched to the most relevant external signals using its statement, linked entities, and related dossier or watchlist context.
2. Matching can draw from the general intelligence feed and from specialized company, hiring, or regulatory pipelines when those exist.
3. The product should prefer explainable matching over opaque broad semantic matches.
4. Weak evidence should not flip an assumption state on its own.

### Confirmation and invalidation

1. A matched signal can count as confirming, invalidating, or merely informative.
2. The user should be shown why the signal appears to support or undermine the assumption.
3. The product should surface confirmation or invalidation as a distinct assumption alert rather than burying it in a generic feed.
4. User can resolve the assumption once the question is settled or no longer relevant.

### Watchlist management

1. User can add, edit, archive, and resolve assumptions.
2. Active assumptions appear in the assumption watchlist.
3. Resolved or archived assumptions remain reviewable as history.
4. The user can link an assumption to a dossier, company, sector, topic, or goal when helpful.

### Feedback into memory and future extraction

1. Resolved assumptions can inform the user's longer-term memory when they represent durable context.
2. Archived or resolved assumptions should help prevent the product from repeatedly re-suggesting the same assumption extraction without new evidence.
3. The product should distinguish between the historical fact that an assumption existed and the current state of whether it still holds.

## Acceptance Criteria

- [ ] Users can maintain an assumption watchlist with both automatic suggestions and manual entries.
- [ ] Each assumption record stores a statement, source, confidence or review state, and current status.
- [ ] The product can match relevant external signals to active assumptions.
- [ ] Confirming or invalidating evidence is surfaced clearly to the user.
- [ ] Users can archive or resolve assumptions without deleting their history.
- [ ] Resolved assumptions can inform future memory or extraction behavior where appropriate.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Automatically extracted assumption is vague | It is shown as low-confidence or not activated automatically |
| External evidence is mixed | Assumption remains active with conflicting evidence rather than prematurely flipping |
| User enters a manual assumption with no linked entity | Product still stores it, but monitoring may rely on weaker topic matching |
| Assumption is no longer strategically relevant | User can resolve or archive it without losing the historical record |
| New evidence contradicts a previously confirmed assumption | Product can surface a new invalidation alert rather than silently changing history |

## Success Metrics

- Number of reviewed and accepted assumption suggestions
- Engagement with confirmation or invalidation alerts
- Share of assumptions linked to dossiers, goals, or watched entities
- User feedback that the watchlist helps catch strategic shifts earlier

## Out of Scope

- Fully autonomous trading, legal, or financial decisions based on assumption changes
- Cross-user shared assumption boards
- Treating every speculative sentence in a journal as an active assumption
- Hidden state changes with no user-visible evidence trail

## Open Questions

- Should an automatically extracted assumption require explicit user approval before active monitoring begins?
- How should the product distinguish between an assumption and a goal, preference, or prediction in ambiguous language?

# Feature Map

**Status:** Draft
**Author:** -
**Date:** 2026-03-08

## Overview

## Implementation Audit - 2026-03-09

Current implementation status after repo audit:

- Attach-to-Ask Bridge - shipped on first-party web chat surfaces with same-turn PDF upload, transcript attachment persistence, and chat-to-Library save flow. Readiness and warning states are surfaced in chat UI.
- Extraction Receipt - backend implemented, but first-party web receipt surfaces are still incomplete. The journal API generates and serves receipts, but the journal UI does not yet render or reopen them directly.
- Recurring Thread Inbox - backend implemented, but first-party web inbox UI is still missing. Thread routes exist and support actions, but there is no dedicated dashboard surface yet.
- Dossier Escalation Engine - backend implemented and merged into suggestion generation, but there is no first-party dossier workspace or escalation management UI yet.
- Since-You-Were-Away + Why-Now - backend implemented, but frontend rendering is partial. Greeting responses include `return_brief`, and recommendations or suggestions include `why_now`, but these are not yet fully rendered in the dashboard UI.
- Outcome Harvester - backend implemented, but review and override flows are not yet surfaced in first-party web UI.
- Company Movement Pipeline - API implemented, but the specialized company-movement surface is not yet wired into the Radar UI.
- Hiring Activity Pipeline - API implemented, but the specialized hiring-signal surface is not yet wired into the Radar UI.
- Regulatory Change Pipeline - API implemented, but the specialized regulatory-alert surface is not yet wired into the Radar UI.
- Assumption Watchlist - backend implemented, including journal-driven suggestion capture, but there is not yet a first-party assumptions workspace in the dashboard.

This map shows how the 10 new feature specs relate to each other, which ones share infrastructure, and the recommended order to build them. The set naturally clusters into three layers:

1. input and transparency surfaces
2. learning and explanation surfaces
3. external monitoring pipelines

## Feature Relationships

### Input and transparency layer

- `specs/functional/extraction-receipt.md` makes journal processing visible and can launch thread, goal, research, or dossier actions.
- `specs/functional/attach-to-ask-bridge.md` makes document-grounded chat immediate and reuses private document indexing.
- `specs/functional/recurring-thread-inbox.md` turns passive recurring-topic detection into a working surface.

### Escalation and explanation layer

- `specs/functional/dossier-escalation-engine.md` depends most directly on recurring threads plus external relevance.
- `specs/functional/since-you-were-away-why-now.md` explains why the system is surfacing things now and can consume evidence from threads, dossiers, intel, and later outcomes.
- `specs/functional/outcome-harvester.md` closes the learning loop by feeding later user progress back into recommendation quality.

### External monitoring layer

- `specs/functional/company-movement-pipeline.md` creates company-specific strategic monitoring.
- `specs/functional/hiring-activity-pipeline.md` is a specialized company-monitoring pipeline that shares infrastructure with company movement.
- `specs/functional/regulatory-change-pipeline.md` adds sector, geography, and standards monitoring.
- `specs/functional/assumption-watchlist.md` sits above the monitoring pipelines and uses their signals to confirm or invalidate assumptions.

## Shared Infrastructure

### Shared with existing product infrastructure

- **Watchlist + matching**
  - reused by company movement, hiring activity, regulatory change, and assumption watchlist
- **Scheduler + heartbeat-style runs**
  - reused by company movement, hiring activity, regulatory change, and dossier escalation
- **Dossier integration**
  - reused by recurring thread inbox, dossier escalation, company movement, hiring activity, regulatory change, and assumption watchlist
- **Per-user document ingestion**
  - reused by attach-to-ask bridge and existing Library behavior
- **Journal post-create pipeline**
  - reused by extraction receipt and any future assumption suggestion sourced from journals

### New shared infrastructure introduced by this set

- **User-review state for extracted or suggested items**
  - needed by extraction receipt, dossier escalation, and assumption watchlist
- **Topic or entity suppression state**
  - needed by dossier escalation and potentially by return briefings
- **Company identity and source-normalization layer**
  - shared by company movement and hiring activity
- **Reason or evidence-chain view model**
  - shared by why-now chips, outcome review, company movement cards, regulatory alerts, and assumption alerts
- **Signal-to-dossier attachment model**
  - shared by company movement, hiring activity, regulatory change, and assumption watchlist

## Recommended Build Order

### Phase 1 - strengthen existing user loop

1. `specs/functional/attach-to-ask-bridge.md`
   - unlocks an important existing advisor promise with minimal conceptual sprawl
2. `specs/functional/extraction-receipt.md`
   - improves trust in journaling and creates visible launch points into other workflows
3. `specs/functional/recurring-thread-inbox.md`
   - turns existing thread detection into a real surface and sets up dossier escalation

### Phase 2 - add explanation and learning

4. `specs/functional/dossier-escalation-engine.md`
   - depends on thread visibility and should arrive after thread inbox exists
5. `specs/functional/since-you-were-away-why-now.md`
   - ties together existing proactive surfaces and improves explainability
6. `specs/functional/outcome-harvester.md`
   - adds the strongest feedback loop once action plans and recommendations are already visible in product surfaces

### Phase 3 - add specialized monitoring pipelines

7. `specs/functional/company-movement-pipeline.md`
   - establishes entity-specific monitoring infrastructure
8. `specs/functional/hiring-activity-pipeline.md`
   - can share company identity, scheduling, and ranking infrastructure from company movement
9. `specs/functional/regulatory-change-pipeline.md`
   - extends the same monitoring model into policy and standards-sensitive domains

### Phase 4 - strategic abstraction layer

10. `specs/functional/assumption-watchlist.md`
   - should come last because it becomes materially better once company, hiring, and regulatory signals exist to evaluate assumptions against

## Why this order

- The first phase improves trust and immediacy in already-existing product loops.
- The second phase makes the system feel more like a chief of staff by explaining timing and learning from outcomes.
- The third phase expands the range of external signals the system can monitor.
- The fourth phase turns those signals into a more abstract strategic reasoning loop.

## Open Questions

- Should assumption watchlist ship earlier in a manual-entry-only form before the specialized pipelines are live?
- Should company movement and hiring activity share one combined card surface from the start, or begin as separate signal families that later converge?





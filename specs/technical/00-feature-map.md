# Technical Feature Map

## Overview

## Implementation Audit - 2026-03-09

Current implementation status after repo audit:

- Attach-to-Ask Bridge - route, storage, retrieval, transcript persistence, and first-party web chat UX are implemented. Chat-origin uploads stay hidden until explicitly saved into Library.
- Extraction Receipt - receipt store, journal hooks, and receipt endpoint are implemented. First-party dashboard rendering is still missing.
- Recurring Thread Inbox - the thread inbox service, state store, summary/detail routes, inbox-state update endpoint, and goal/research/dossier action endpoints are implemented. Dedicated web inbox navigation is still missing, and `tests/web/test_threads_routes.py` still only covers the basic list/detail paths.
- Dossier Escalation Engine - escalation engine, storage, and API routes are implemented, and shared escalation-context plus briefing-data reuse now feed suggestions, dedicated escalation routes, `/api/briefing`, and return-briefing surfaces with active-dossier suppression. First-party dossier and escalation management UI remains incomplete.
- Since-You-Were-Away + Why-Now - `GET /api/greeting` is now wired into a dedicated home `return_brief` card, and recommendation surfaces render expandable `why_now` chips. Harvested-outcome reasoning is inspectable through chip detail when present, while suggestion-chip coverage still depends on a first-party suggestions surface.
- Outcome Harvester - store, evaluation, ranking boost, override APIs, and shared briefing recommendation enrichment are implemented. No first-party web review surface exists yet.
- Company Movement Pipeline - watchlist metadata, scheduler hooks, storage, API routes, Radar Pipelines UI, and briefing/suggestion/return-brief integrations are implemented. Source adapters and deeper company drill-down remain incomplete.
- Hiring Activity Pipeline - watchlist metadata, scheduler hooks, signal analysis, API routes, Radar Pipelines UI, and briefing/suggestion/return-brief integrations are implemented. Dedicated careers-page or ATS collectors and richer baseline analysis remain incomplete.
- Regulatory Change Pipeline - watchlist metadata, scheduler hooks, classification, API routes, Radar Pipelines UI, and briefing/suggestion/return-brief integrations are implemented. Dedicated regulatory-source jobs and deeper dossier/watchlist workflows remain incomplete.
- Assumption Watchlist - store, signal matching, memory adapter, routes, journal suggestion capture, and shared briefing/return-brief integration are implemented. A dedicated assumptions workspace is still missing, but assumption updates are now consumed outside the standalone route.

This map summarizes how the 10 new technical feature specs fit into StewardMe's existing architecture. It highlights:

1. which features share modules and infrastructure
2. which new stores, tables, and routes are introduced
3. which scheduler jobs or background processes are needed
4. the recommended technical build order based on dependency depth

This file mirrors `specs/functional/00-feature-map.md`, but focuses on implementation shape rather than product behavior.

## Feature Inventory

| Feature | Technical spec |
|---|---|
| Extraction Receipt | `specs/technical/extraction-receipt.md` |
| Attach-to-Ask Bridge | `specs/technical/attach-to-ask-bridge.md` |
| Recurring Thread Inbox | `specs/technical/recurring-thread-inbox.md` |
| Dossier Escalation Engine | `specs/technical/dossier-escalation-engine.md` |
| Since-You-Were-Away + Why-Now | `specs/technical/since-you-were-away-why-now.md` |
| Outcome Harvester | `specs/technical/outcome-harvester.md` |
| Competitor / Company Movement Pipeline | `specs/technical/company-movement-pipeline.md` |
| Hiring Activity Pipeline | `specs/technical/hiring-activity-pipeline.md` |
| Regulatory Change Pipeline | `specs/technical/regulatory-change-pipeline.md` |
| Assumption Watchlist | `specs/technical/assumption-watchlist.md` |

---

## Shared Modules

### Journal layer

Shared by:

- `Extraction Receipt`
- `Recurring Thread Inbox`
- `Dossier Escalation Engine`
- `Outcome Harvester`
- `Assumption Watchlist`

Key existing modules:

- `src/journal/storage.py`
- `src/journal/threads.py`
- `src/journal/thread_store.py`
- `src/journal/search.py`

New technical additions proposed:

- `src/journal/extraction_receipts.py`
- `src/journal/thread_inbox.py`

### Web layer

Shared by all 10 features through routes, models, and frontend surfaces.

Key existing modules:

- `src/web/routes/*`
- `src/web/models.py`
- `src/web/conversation_store.py`
- `src/web/deps.py`
- `web/src/app/*`

New or extended route areas:

- journal receipt reads
- advisor attachments
- thread inbox actions
- dossier escalation actions
- return briefing and why-now payload enrichments
- harvested outcome review routes
- company / hiring / regulatory intel routes
- assumption CRUD routes

### Advisor layer

Shared by:

- `Attach-to-Ask Bridge`
- `Since-You-Were-Away + Why-Now`
- `Outcome Harvester`
- `Assumption Watchlist`

Key existing modules:

- `src/advisor/engine.py`
- `src/advisor/rag.py`
- `src/advisor/recommendation_storage.py`
- `src/advisor/scoring.py`
- `src/advisor/greeting.py`
- `src/advisor/insights.py`

New technical additions proposed:

- `src/advisor/return_brief.py`
- `src/advisor/why_now.py`
- `src/advisor/outcomes.py`
- `src/advisor/assumptions.py`

### Intelligence layer

Shared by:

- `Dossier Escalation Engine`
- `Since-You-Were-Away + Why-Now`
- `Competitor / Company Movement Pipeline`
- `Hiring Activity Pipeline`
- `Regulatory Change Pipeline`
- `Assumption Watchlist`

Key existing modules:

- `src/intelligence/scheduler.py`
- `src/intelligence/watchlist.py`
- `src/intelligence/heartbeat.py`
- `src/intelligence/scraper.py`
- `src/intelligence/sources/*`

New technical additions proposed:

- `src/intelligence/company_watch.py`
- `src/intelligence/hiring_signals.py`
- `src/intelligence/regulatory.py`

### Research + dossier layer

Shared by:

- `Recurring Thread Inbox`
- `Dossier Escalation Engine`
- `Competitor / Company Movement Pipeline`
- `Regulatory Change Pipeline`
- `Assumption Watchlist`

Key existing modules:

- `src/research/dossiers.py`
- `src/research/agent.py`

New technical additions proposed:

- `src/research/escalation.py`

### Memory layer

Shared by:

- `Extraction Receipt`
- `Attach-to-Ask Bridge`
- `Outcome Harvester`
- `Assumption Watchlist`

Key existing modules:

- `src/memory/store.py`
- `src/memory/pipeline.py`
- `src/memory/extractor.py`

Notable extension:

- `FactSource.ASSUMPTION` for resolved assumption memory writes

---

## Storage Map

### New per-user stores

| Feature | Path | Purpose |
|---|---|---|
| Extraction Receipt | `~/coach/users/{safe_id}/receipts.db` | Per-entry extraction receipts |
| Dossier Escalation Engine | `~/coach/users/{safe_id}/escalations.db` | Private escalation suggestions and snooze state |
| Outcome Harvester | `~/coach/users/{safe_id}/outcomes.db` | Inferred recommendation/action outcomes |
| Assumption Watchlist | `~/coach/users/{safe_id}/assumptions.db` | Active assumptions and evidence history |

### New or extended per-user tables in existing stores

| Store | Table | Used by |
|---|---|---|
| `threads.db` | `thread_inbox_state` | Recurring Thread Inbox |
| `users.db` | `conversation_message_attachments` | Attach-to-Ask Bridge |

### New shared `intel.db` tables

| Table | Used by |
|---|---|
| `company_movements` | Competitor / Company Movement Pipeline |
| `hiring_signals` | Hiring Activity Pipeline |
| `hiring_baselines` | Hiring Activity Pipeline |
| `regulatory_alerts` | Regulatory Change Pipeline |

### Existing shared stores reused heavily

| Existing store | Reused by |
|---|---|
| `intel.db` `intel_items` + FTS | Dossier Escalation, Return Brief, Assumptions, company / hiring / regulatory routing |
| per-user Library storage | Attach-to-Ask Bridge |
| recommendation markdown files | Outcome Harvester |
| dossier journal-backed entries | Dossier Escalation, company / regulatory enrichment, assumptions |

---

## Route Map

### New routes

| Route area | Suggested endpoints |
|---|---|
| Journal receipts | `GET /api/journal/{filepath}/receipt` |
| Advisor attachments | `POST /api/advisor/attachments` |
| Thread inbox | `GET /api/threads/inbox`, `PATCH /api/threads/{thread_id}/state`, thread action endpoints, `POST /api/threads/reindex` |
| Dossier escalations | `GET /api/dossier-escalations`, dismiss/snooze/accept endpoints |
| Recommendation outcomes | `GET /api/recommendations/{id}/outcome`, `POST /api/recommendations/{id}/outcome/override` |
| Company movement | `GET /api/intel/company-movements`, detail by company |
| Hiring signals | `GET /api/intel/hiring-signals`, detail by entity |
| Regulatory alerts | `GET /api/intel/regulatory-alerts`, detail by target |
| Assumptions | `GET/POST/PATCH /api/assumptions`, activate/resolve/archive endpoints |

### Existing routes extended

| Existing route | Extension |
|---|---|
| `POST /api/advisor/ask` | activate `attachment_ids` support |
| `POST /api/advisor/ask/stream` | activate `attachment_ids` support |
| `GET /api/greeting` | optional `return_brief` payload |
| `GET /api/suggestions` | `why_now` chips and optional dossier escalation rows |
| `GET /api/recommendations` | `why_now` chips and harvested outcome metadata |
| journal create / quick-create | seed extraction receipt |

---

## Scheduler / Background Work Map

### Existing jobs reused or extended

| Existing job | Reused by |
|---|---|
| `heartbeat` | Dossier Escalation signals, why-now evidence, future company/regulatory relevance surfacing |
| `goal_intel_matching` | Can contribute dossier escalation or why-now evidence indirectly |
| `research` | Feeds dossier updates, which can feed return briefs, assumptions, and escalations |

### New proposed jobs

| Job | Purpose | Features |
|---|---|---|
| `company_movement` | collect and rank company-specific movement events | Company Movement Pipeline |
| `hiring_activity` | collect hiring snapshots and detect strategic hiring signals | Hiring Activity Pipeline |
| `regulatory` | collect and classify regulatory updates | Regulatory Change Pipeline |
| `outcome_harvest` | scan recent recommendations/actions for later evidence | Outcome Harvester |
| `assumption_evaluate` | scan active assumptions against fresh signals | Assumption Watchlist |

### Async but not scheduled-first workflows

| Workflow | Trigger | Features |
|---|---|---|
| receipt generation | journal create / quick-create | Extraction Receipt |
| attachment indexing | advisor attachment upload | Attach-to-Ask Bridge |
| thread inbox state updates | user actions | Recurring Thread Inbox |
| return brief build | home / greeting fetch | Since-You-Were-Away |
| dossier escalation refresh | suggestion or thread surfaces | Dossier Escalation Engine |

---

## Dependency Clusters

### Cluster A - immediate UX loop

- `Extraction Receipt`
- `Attach-to-Ask Bridge`
- `Recurring Thread Inbox`

Shared technical dependencies:

- journal post-create hooks
- per-user route wiring
- web component patterns from foundations

### Cluster B - explainability + learning

- `Dossier Escalation Engine`
- `Since-You-Were-Away + Why-Now`
- `Outcome Harvester`

Shared technical dependencies:

- suggestions / recommendations payload enrichment
- per-user learned-state stores
- event and activity reads from `users.db`

### Cluster C - specialized monitoring pipelines

- `Competitor / Company Movement Pipeline`
- `Hiring Activity Pipeline`
- `Regulatory Change Pipeline`

Shared technical dependencies:

- watchlist resolution
- scheduler integration
- shared `intel.db` event tables
- route-level user matching over shared public events

### Cluster D - strategic synthesis layer

- `Assumption Watchlist`

Shared technical dependencies:

- private assumption store
- signal matching over company / hiring / regulatory / intel events
- optional memory write-back

---

## Recommended Technical Build Order

1. `specs/technical/attach-to-ask-bridge.md`
   - activates an already-planned advisor capability and mostly reuses Library + advisor plumbing
2. `specs/technical/extraction-receipt.md`
   - layers transparency onto existing journal post-create work
3. `specs/technical/recurring-thread-inbox.md`
   - depends mainly on fixing existing thread route wiring and adding a state overlay
4. `specs/technical/dossier-escalation-engine.md`
   - builds directly on threads, suggestions, dossiers, and recent intel
5. `specs/technical/since-you-were-away-why-now.md`
   - enriches greeting and suggestion surfaces after the underlying signals are more mature
6. `specs/technical/outcome-harvester.md`
   - adds learning once recommendations, action plans, and journaling evidence are already flowing
7. `specs/technical/company-movement-pipeline.md`
   - establishes company identity and structured event infrastructure
8. `specs/technical/hiring-activity-pipeline.md`
   - shares the company identity and scheduling base while adding hiring-specific logic
9. `specs/technical/regulatory-change-pipeline.md`
   - reuses monitoring patterns for a new source family with different classification rules
10. `specs/technical/assumption-watchlist.md`
   - benefits most once multiple specialized signal pipelines already exist

## Why this order

- The first three features mostly improve existing loops without introducing large new external-monitoring systems.
- The middle three create more adaptive and explainable product behavior.
- The next three expand the surface area of monitored external signals.
- Assumptions come last because they are strongest when several signal families already exist.

---

## Highest-Risk Technical Dependencies

| Dependency | Risk |
|---|---|
| Web thread-route fix | Recurring Thread Inbox depends on unblocking an existing miswire |
| Chat attachment hidden/saved lifecycle | Needs clean Library integration without confusing user-visible duplication |
| Company identity resolution | Shared company monitoring can become noisy without stable normalization |
| New scheduler jobs | More background jobs increase failure modes and operational complexity |
| Assumption extraction precision | Low-precision extraction would pollute the watchlist and downstream memory |

## Open Questions

- Should there also be a `specs/technical/00-storage-map.md` later if these tables grow further?
- Should `Outcome Harvester` and `Assumption Watchlist` eventually merge into a more general private learned-state subsystem, or stay separate for clarity?




# Regulatory Change Pipeline

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

Users operating in regulated or standards-sensitive areas need early visibility into policy, regulatory, and standards changes relevant to their sectors or geographies. The product now has a focused regulatory alert path, but it still needs broader source coverage and better urgency/actionability shaping than the generic intelligence feed alone can provide.

## Overview

Regulatory Change Pipeline monitors selected sectors, topics, and geographies for meaningful regulatory or standards changes, classifies them by urgency and relevance, and surfaces them as actionable alerts that can feed dossiers, threads, and strategic briefings.

## Users

Founders, operators, investors, and technical leaders who care about policy shifts, compliance risk, market-entry changes, or standards movement relevant to their work.

## User Stories

- As a user, I want to watch a sector, topic, or geography for regulatory movement without manually checking many sources.
- As a user, I want regulatory alerts classified by urgency and relevance so I know what needs attention now.
- As a user, I want regulatory changes linked into existing dossiers or strategic topics when they matter.
- As a user, I want a clear next step when a regulatory change is surfaced.

## Dependencies

- Builds on watchlist and intelligence ingestion from `specs/functional/intelligence-feed.md`.
- Integrates with dossiers in `specs/functional/research-dossiers.md`, threads in `specs/functional/recurring-thread-inbox.md`, and return briefings in `specs/functional/since-you-were-away-why-now.md`.
- Can feed assumption evaluation in `specs/functional/assumption-watchlist.md`.
- Current implementation includes regulatory target resolution, alert persistence, scheduler support, web routes, and briefing/suggestion surfacing. Follow-up work is mainly broader adapters, richer classification, and UI polish.

## Detailed Behavior

### Monitoring targets

1. User can specify sectors, topics, or geographies to monitor.
2. These monitoring targets should reuse the watchlist model where possible instead of requiring a separate configuration system.
3. The user can also link a regulatory watch target to an active dossier or project when relevant.

### Source families

Potential source families include:

1. government registers and agency feeds
2. standards bodies and technical working-group announcements
3. formal consultation or rulemaking updates
4. legal or industry-news sources where direct feeds are not available

Current capability scope:
- Generic RSS and feed ingestion already exist and can support part of this pipeline.
- Regulatory-specific agency and standards adapters require new source work.

### Classification

Each regulatory signal should be classified by:

1. urgency - such as `high`, `medium`, or `low`
2. relevance - how closely it matches the user's watched sector, topic, or geography
3. change type - such as `proposed`, `finalized`, `guidance`, `standard`, or `enforcement-related`
4. timing - whether the change is immediate, upcoming, or only exploratory

Classification should stay conservative and should not imply legal advice.

### Connection to existing context

1. If a regulatory signal matches an active dossier, it should be attachable to that dossier as evidence.
2. If it matches a recurring thread, the user can start research or a dossier from the alert.
3. If it reinforces or invalidates an assumption, the assumption watchlist can consume it when that feature exists.

### Regulatory alert

Each alert should include:

- title
- regulator, body, or standards organization
- short summary of the change
- watched topic or geography it matched
- urgency and relevance labels
- effective or expected timing when known
- why it matters in plain language
- actions such as `run research`, `start dossier`, `save`, or `dismiss`

## Acceptance Criteria

- [ ] Users can configure sectors, topics, or geographies to monitor for regulatory movement.
- [ ] The product can ingest and normalize regulatory or standards updates from supported source families.
- [ ] Regulatory alerts are classified by urgency and relevance.
- [ ] Alerts can connect to relevant dossiers or thread-driven workflows.
- [ ] Alerts present a clear summary and next action rather than only a raw source link.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| A source reports a proposed change with no clear timeline | Alert stays conservative and communicates uncertainty |
| A change is relevant to a broad sector but not the user's exact geography | Relevance can be lowered rather than hidden entirely |
| Multiple sources report the same regulatory update | User sees one normalized alert with multiple source references |
| A standards update is technically important but not urgent | It can surface as lower urgency while remaining searchable or attachable |
| User has no dossiers yet | Regulatory alert can still offer research or watchlist actions |

## Success Metrics

- User engagement with regulatory alerts and related follow-up actions
- Share of regulatory alerts attached to dossiers or followed by research
- User feedback that urgency and relevance labels feel accurate
- Low duplicate rate for the same regulatory event across source families

## Out of Scope

- Legal advice or compliance certification
- Full document diffing for every regulation text in MVP
- Monitoring every geography or agency by default without user signal
- Cross-user shared compliance workspaces

## Open Questions

- Should standards changes and legal-news summaries ship in the same phase as direct agency-feed monitoring?
- How much jurisdiction-specific detail is required before the alert is useful rather than noisy?

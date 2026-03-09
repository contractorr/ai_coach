# Competitor / Company Movement Pipeline

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

Users often care about the strategic movement of specific companies, and a generic intelligence feed alone is not enough. The product now has a structured company-monitoring path, but it still needs broader source coverage, stronger identity resolution, and better significance ranking to make important company changes hard to miss.

## Overview

Competitor / Company Movement Pipeline continuously monitors watched companies and normalizes significant changes into structured company-movement cards. Findings can feed proactive briefings, active dossiers, and on-demand company review flows.

## Users

Founders tracking competitors, operators watching adjacent companies, investors following portfolio or target companies, and career-oriented users tracking employers or strategic companies.

## User Stories

- As a user, I want to watch a company once and have important movement tracked automatically.
- As a user, I want company findings ranked by strategic significance rather than dumped as a raw feed.
- As a user, I want company findings to enrich relevant dossiers and return briefings.
- As a user, I want each finding to explain what changed and why it matters.

## Dependencies

- Builds on watchlist and heartbeat behaviors in `specs/functional/intelligence-feed.md`.
- Integrates with dossiers in `specs/functional/research-dossiers.md` and return briefings in `specs/functional/since-you-were-away-why-now.md`.
- Shares infrastructure with `specs/functional/hiring-activity-pipeline.md` for company identity, scheduling, normalization, and ranking.
- Current implementation includes watchlist-derived company resolution, movement persistence, scheduler support, web routes, and briefing/suggestion surfacing. Follow-up work is mainly broader source adapters, stronger entity resolution, and richer card polish.

## Detailed Behavior

### Adding a company to monitor

1. User can add a company through the existing watchlist flow using a company-type watch item.
2. User can also promote a company into the watchlist from an intel item, dossier, or company-related recommendation surface.
3. A watched company record should support, when available:
   - company name
   - aliases
   - primary domain
   - optional GitHub org or repo namespace
   - optional ticker or filing identity
   - priority
   - linked dossier ids or goals

### Monitored source families

The pipeline can monitor company movement across multiple source families such as:

1. official company news, blogs, changelogs, or press pages
2. pricing or product pages
3. GitHub org velocity, releases, or repo activity
4. partnership or press-release feeds
5. job or career pages where relevant
6. filings and formal disclosures where available
7. business or industry news sources

Current capability scope:
- RSS-backed and general intelligence infrastructure already exists and can cover part of this surface.
- Company-specific pricing-page tracking, GitHub-org monitoring, filings, and leadership-change adapters require new source work.

### Monitoring cadence

1. Monitoring should run on a scheduled basis rather than only on demand.
2. High-priority watched companies can run on a faster cadence than low-priority companies.
3. The system should balance timeliness with rate limits and source reliability.

### Deduplication and significance ranking

1. Raw findings should be normalized into company movement events.
2. Duplicate events across source families should be collapsed into one company movement card when they describe the same change.
3. Events should be ranked by significance using factors such as:
   - source authority
   - event novelty
   - linkage to user watchlist, dossiers, or goals
   - likely strategic impact
4. Low-signal or repeated events should not flood the user.

### Surfacing findings

Company movement findings can surface:

1. proactively in suggestions or return briefings
2. inside active company-related dossiers as fresh evidence
3. on demand through a company-focused view or filtered intel results

### Company movement card

Each card should include:

- company name
- movement type such as `product`, `pricing`, `partnership`, `leadership`, `roadmap`, `github`, or `filing`
- short summary of what changed
- why it matters
- confidence or significance label
- source links or source references
- detected time
- actions such as `view dossier`, `run research`, `save`, or `dismiss`

## Acceptance Criteria

- [ ] Users can add a company to a monitored watchlist.
- [ ] The pipeline can normalize significant company changes into structured movement cards.
- [ ] Findings are deduplicated when the same change is observed across multiple sources.
- [ ] Findings are ranked by strategic significance rather than pure recency alone.
- [ ] Company findings can surface proactively and also feed relevant dossiers.
- [ ] Each company movement card explains what changed and why it matters.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Company has many aliases or spelling variants | Matching should consolidate them under one watched company where possible |
| Multiple sources report the same launch | User sees one movement card with multiple source references rather than duplicates |
| Company is watched but no reliable source data exists yet | Watch remains valid without fabricating movement |
| A change is real but low-significance | It can be stored or searchable without forcing proactive surfacing |
| User already has an active dossier on the company | New movement should enrich the existing dossier rather than imply a second tracked object |

## Success Metrics

- Increase in company-linked dossiers or company-focused research runs
- Open and save rate on company movement cards
- Share of surfaced company movements judged useful by user feedback
- Low duplicate rate for materially identical company events

## Out of Scope

- CRM-style account tracking or sales intelligence
- Private financial data integrations
- Automatic creation of dossiers without user confirmation
- Monitoring companies for every user without a watched-company signal

## Open Questions

- What should be the minimum required identity fields for a watched company before monitoring begins?
- Should low-priority companies use a noticeably slower cadence by default?

# Hiring Activity Pipeline

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

Hiring patterns often reveal strategic movement before formal announcements do, but raw job data still needs interpretation before it becomes useful strategic insight. The product now has a hiring-signal pipeline, but it still needs broader adapters and stronger baselines so users do not miss capability buildup, expansion, geography shifts, or sharp changes in hiring intensity.

## Overview

Hiring Activity Pipeline monitors watched companies or sectors for changes in job-posting behavior and interprets those changes into strategic insights rather than only listing raw openings. It should behave as a specialized pipeline that shares core monitoring infrastructure with company movement, but uses hiring-specific source adapters and signal logic.

## Users

Founders tracking competitors, operators reading market direction, investors monitoring company posture, and career users following employers or sectors.

## User Stories

- As a user, I want to know when a company's hiring pattern changes meaningfully.
- As a user, I want hiring signals translated into capability or strategy insights, not just a list of roles.
- As a user, I want to monitor either named companies or broader sectors.
- As a user, I want hiring insights to feed into dossiers and briefings when relevant.

## Dependencies

- Shares watchlist, scheduling, normalization, and card-surfacing infrastructure with `specs/functional/company-movement-pipeline.md`.
- Integrates with dossiers in `specs/functional/research-dossiers.md` and return briefings in `specs/functional/since-you-were-away-why-now.md`.
- Current implementation includes hiring-signal persistence, scheduler support, watchlist-derived company matching, web routes, and briefing/suggestion surfacing. Follow-up work is mainly broader adapters, stronger baselines, and deeper signal interpretation.
- External-source dependency note: LinkedIn support is not assumed because API and terms constraints may require a separate decision.

## Detailed Behavior

### What the user can monitor

1. User can monitor hiring activity for one or more watched companies.
2. User can also monitor a sector or theme where sector-level hiring changes matter.
3. Company-level and sector-level monitoring should use the same user-facing watchlist model where possible.

### Monitored sources

Potential source families include:

1. official company career pages
2. ATS-hosted boards such as Greenhouse or Lever
3. Indeed and similar public job sources where the product already has adjacent intelligence infrastructure
4. company engineering or recruiting announcements when they clearly imply hiring movement

Current capability scope:
- Macro hiring sources already exist in the wider intelligence system.
- Company-specific job-board monitoring requires new source adapters and should be called out as a dependency.
- LinkedIn support is an open question rather than assumed MVP behavior.

### Signal types

The pipeline should detect signals such as:

1. hiring spike - materially higher posting volume than the recent baseline
2. new role family - roles appearing in a function the company was not previously hiring for
3. capability buildup - clustered hiring around one capability, team, or strategic area
4. geography expansion - openings concentrated in a new region or office footprint
5. seniority shift - unusual concentration of executive, manager, or specialist roles

### Interpretation layer

1. The product should not stop at raw counts.
2. Each surfaced signal should include a short interpretation such as:
   - `appears to be building enterprise sales capacity`
   - `appears to be expanding applied AI hiring`
   - `appears to be opening a new geography`
3. Interpretations should remain evidence-based and avoid overclaiming certainty.

### Shared vs separate infrastructure

1. Hiring Activity Pipeline shares monitored-company identity, scheduling, normalization, and ranking infrastructure with company movement.
2. It remains a distinct signal family because hiring evidence has its own baselines, source adapters, and interpretation logic.
3. Hiring signals can contribute to company movement cards or dossier updates when the company movement pipeline is also enabled.

## Acceptance Criteria

- [ ] Users can configure hiring monitoring for watched companies or sectors.
- [ ] The product can detect meaningful hiring-pattern changes rather than only listing new postings.
- [ ] Hiring signals are translated into short strategic interpretations.
- [ ] Hiring signals can enrich dossiers, briefings, or company movement surfaces when relevant.
- [ ] The feature clearly distinguishes already-supported macro sources from new company-specific source dependencies.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Company posts only one or two roles occasionally | Product avoids calling this a hiring spike without sufficient baseline evidence |
| Company changes job-title wording without changing strategy | Interpretation stays conservative and may surface as low-significance |
| Sector monitoring is broad and noisy | Results are filtered to the strongest aggregate signals rather than every posting cluster |
| Source coverage is incomplete for one company | Product should say the signal is partial rather than pretending full coverage |
| Hiring and company-movement pipelines both detect the same shift | User sees a coordinated view, not two competing alerts |

## Success Metrics

- Open and save rate on hiring-signal cards
- Share of hiring signals used in dossiers or follow-up research
- User feedback indicating hiring interpretations are useful rather than noisy
- Low false-positive rate on `hiring spike` and `capability buildup` labels

## Out of Scope

- Compensation benchmarking
- Individual-candidate recruiting workflows
- Private HRIS or applicant-tracking integrations beyond public-source monitoring
- Assuming LinkedIn-based monitoring is available in MVP

## Open Questions

- What baseline window should define a meaningful hiring spike for company-level monitoring?
- Should sector-level hiring monitoring ship in the same phase as company-level monitoring, or after it proves useful?

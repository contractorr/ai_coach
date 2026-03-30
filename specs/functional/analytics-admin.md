---
id: analytics-admin
category: tracked_feature
status: stable
technical_specs:
- specs/technical/web.md
- specs/technical/usage-cost-estimation.md
foundations:
- specs/foundations/design-system.md
- specs/foundations/ux-guidelines.md
last_reviewed: '2026-03-30'
---

# Analytics & Admin

**Status:** Implemented
**Author:** -
**Date:** 2026-03-07

## Problem

The product needs lightweight operational visibility: core page traffic, recent activity counts, scraper health, and feedback summaries for administrators or operators.

## Users

Internal operators and admins.

## Desired Behavior

### Page-view tracking

1. The app tracks page views for the core dashboard routes.
2. Tracking happens automatically when a logged-in user navigates to a tracked page.

### Admin stats

1. Admin can request aggregate usage stats for a recent time window.
2. Stats include chat volume, journal and goal creation counts, onboarding completions, active-user rollups, scraper health, page views, and recommendation-feedback summaries.
3. A web admin page renders this data for inspection.

Current interface scope:
- Analytics collection is intentionally lightweight and focused on product operations rather than a full BI stack.
- The shipped admin stats surface is internal-facing.
- The admin page exposes fixed day-window controls (`7`, `30`, `90`) and a manual refresh action.
- Usage totals render as summary cards; denser subsections render as scroll-safe tables on smaller screens.

## Acceptance Criteria

- [ ] Core dashboard page views are logged.
- [ ] Admin stats can be queried by day range.
- [ ] Admin stats include usage, scraper health, page-view, and feedback summary sections.
- [ ] A web admin page can render the aggregated stats.
- [ ] The admin page remains readable on smaller screens without clipping table content.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User visits an untracked route | No page-view event is logged |
| A stats subsection has no data yet | Admin page shows the rest of the dashboard without failing |
| Analytics write fails | Product continues functioning; analytics loss is non-fatal |

## Out of Scope

- External analytics vendor integrations
- Granular per-click heatmaps
- End-user self-serve analytics dashboards

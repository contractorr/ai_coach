# Suggestions Engine

**Status:** Implemented
**Author:** —
**Date:** 2026-03-11

## Problem

Users need a single prioritized feed of actionable next steps drawn from multiple subsystems (briefing, recommendations, company movements, hiring signals, regulatory alerts, assumptions, dossier escalations). Without unification, the user must check each subsystem separately.

## Users

All web app users. Suggestions surface in Home and Goals.

## Product Placement

- Workspace: `Home` (top next steps), `Goals` (suggested next actions)
- Each suggestion carries a `why_now` annotation explaining its timeliness

## Desired Behavior

1. `GET /api/suggestions` returns a merged, prioritized list from all active subsystems.
2. Each item includes source type, title, summary, and `why_now` reasoning.
3. Items are sorted by source priority: daily brief first, then recommendations, company movements, hiring, regulatory, assumptions, escalations.
4. Default limit is 10 items; max 30.
5. `WhyNowReasoner` annotates each item with timing context.

## Acceptance Criteria

- [ ] Endpoint merges items from all active subsystems into one list.
- [ ] Each item has a `why_now` annotation.
- [ ] Source priority ordering is consistent.
- [ ] Limit parameter respected (1–30).
- [ ] Missing or empty subsystems don't cause errors.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No active subsystems have items | Empty list returned |
| A subsystem throws an error during assembly | Other subsystems still contribute; error logged |
| User has no profile yet | Suggestions still work from non-profile-dependent sources |

## Out of Scope

- Per-item dismiss/save (handled by engagement endpoints)
- Suggestion generation logic (owned by each subsystem)

# Outcome Harvester

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

The product can already collect explicit ratings and action-item updates, but it still relies too heavily on the user to declare whether advice led to progress. Without a stronger feedback loop, recommendation quality improves more slowly and the system misses evidence already present in later journal entries, goal check-ins, and action updates.

## Overview

Outcome Harvester reviews later user activity and infers whether advice, recommendations, or suggested next steps led to progress, produced negative outcomes, or appear unresolved. The feature should support recommendation learning while staying transparent and easy for the user to override.

## Users

Users who receive recommendations, create action items, track goals, and journal after acting on advice.

## User Stories

- As a user, I want the product to notice when I actually followed through on something without making me log every outcome manually.
- As a user, I want the system to show me the evidence behind a harvested outcome so I can confirm or correct it.
- As a user, I want my later progress to improve future recommendations automatically.
- As a user, I do not want silence to be treated as failure when the system simply lacks evidence.

## Dependencies

- Depends on recommendations and action plans from `specs/functional/recommendations.md` and `specs/functional/action-plans.md`.
- Depends on journal entries and goal check-ins from `specs/functional/journaling.md` and `specs/functional/goal-tracking.md`.
- Can enrich why-now reasoning in `specs/functional/since-you-were-away-why-now.md`.
- Can feed memory extraction from recommendation feedback and goal events described in `specs/functional/memory-threads.md`.
- Current implementation includes harvested-outcome storage, recommendation outcome evaluation on read, user override controls, and why-now enrichment for positive prior outcomes. Follow-up work is mainly broader background inference across more activity types and richer review surfaces.

## Detailed Behavior

### Outcome sources

The harvester can evaluate later evidence from:

1. explicit action-item status updates
2. goal progress changes or goal check-ins
3. later journal entries that mention the action, goal, or recommendation topic
4. explicit recommendation feedback when available

The harvester should prefer explicit status updates over inferred textual evidence when both exist.

### Outcome classes

Each harvested result should land in one of the following user-comprehensible states:

- `positive` - evidence suggests the recommendation or action helped and moved work forward
- `negative` - evidence suggests the recommendation led to blockage, abandonment, or clearly poor results
- `unresolved` - the system has not found enough evidence yet to determine an outcome
- `conflicted` - strong signals point in different directions and the system needs user confirmation

### Positive signals

Positive signals can include:

1. action item marked `completed`
2. goal progress increased after the recommendation or action item was created
3. goal check-in or journal language indicating completion, shipping, learning progress, or successful follow-through
4. explicit positive recommendation feedback

### Negative signals

Negative signals can include:

1. action item marked `blocked` or `abandoned`
2. goal check-in showing stalled progress or reversal after following the suggested action
3. journal evidence that the attempted action failed, backfired, or created a blocker
4. explicit negative recommendation feedback

### Unresolved timing

1. The harvester should not mark silence as negative by default.
2. It should keep looking for evidence during an appropriate review window.
3. Default review windows can align to the action item's due window when available:
   - `today` - review within a few days
   - `this_week` - review within a few weeks
   - `later` - review over a longer window
4. If that window passes without clear evidence, the item becomes `unresolved`, not failed.

### User-facing outcome review

1. Harvested outcomes should be surfaced back to the user where the recommendation or action already lives.
2. The UI should use plain language such as:
   - `Looks like this worked`
   - `Looks blocked`
   - `No clear outcome yet`
3. The user should be able to inspect the supporting evidence snippets.
4. The user should be able to confirm or correct the harvested outcome.
5. User correction should override the inferred result for future learning.

### Learning loop

1. Harvested outcomes should feed into the same recommendation-learning loop as explicit ratings and execution events.
2. Positive harvested outcomes can strengthen similar future recommendations.
3. Negative harvested outcomes can reduce similar future recommendations or change their framing.
4. Unresolved outcomes should stay lower-confidence and should not count like a negative outcome.

## Acceptance Criteria

- [ ] The system can evaluate later journal entries, goal check-ins, and action updates for evidence related to prior suggestions.
- [ ] Harvested outcomes distinguish between positive, negative, unresolved, and conflicted states.
- [ ] Silence or missing evidence does not automatically count as failure.
- [ ] Harvested outcomes are surfaced back to the user in a reviewable form with supporting evidence.
- [ ] User corrections override inferred outcomes.
- [ ] Harvested outcomes can influence future recommendation ranking alongside explicit feedback.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User never updates the action item but journals clear progress | Harvester can infer a positive outcome from later evidence |
| Journal evidence is ambiguous | Outcome remains unresolved or conflicted rather than overconfident |
| Action item is marked completed but later notes are negative | Explicit completion and later negative evidence can produce a conflicted state for user review |
| User has no later journal entries or check-ins | Outcome remains unresolved rather than assumed negative |
| User corrects an inferred outcome | Corrected value becomes the one used for future learning |

## Success Metrics

- Increase in recommendations improved by harvested outcomes rather than only explicit ratings
- Increase in user confirmations of harvested outcomes
- Reduction in repeated weak recommendations for patterns that later proved unsuccessful
- Increase in completed or positively reviewed actions after the learning loop matures

## Out of Scope

- Fully autonomous claims of success without any user-visible evidence trail
- Replacing explicit action-item status controls
- Financial or business attribution modeling beyond the product's advisory loop
- Cross-user outcome learning

## Open Questions

- Should unresolved outcomes ever decay out of the learning loop, and if so after how long?
- How conservative should the system be before showing a `Looks like this worked` label to the user?

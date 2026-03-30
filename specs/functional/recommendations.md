---
id: recommendations
category: tracked_feature
status: stable
technical_specs:
- specs/technical/action-plans.md
- specs/technical/suggestions-engine.md
- specs/technical/goal-learning-merge.md
foundations:
- specs/foundations/ux-guidelines.md
last_reviewed: '2026-03-30'
---

# Recommendations and Next Steps

**Status:** Updated for the simplified product model

## Purpose

Recommendations are exposed as small, obvious next steps in Home and Goals rather than as a concept the user must learn separately.

## Product Placement

- `Home` shows at most three prioritized next-step items in one short list
- `Goals` shows best next moves and the weekly plan
- Feedback remains available for improving future recommendation quality

## Current Behavior

- Home prioritizes a short set of next-step items directly below the main composer.
- Goals keeps recommendation cards close to active execution work.
- Ratings and notes remain part of the recommendation feedback loop.

## User Flows

- Review a next-step item from Home.
- Track or score a recommendation from Goals.
- Improve future suggestions through feedback.

## Key System Components

- `src/web/routes/suggestions.py`
- `src/web/routes/recommendations.py`
- `web/src/app/(dashboard)/page.tsx`
- `web/src/app/(dashboard)/goals/page.tsx`

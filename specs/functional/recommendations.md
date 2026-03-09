# Recommendations and Next Steps

**Status:** Updated for the simplified product model

## Purpose

Recommendations are exposed as small, obvious next steps in Home and Focus rather than as a concept the user must learn separately.

## Product Placement

- `Home` shows at most three prioritized next-step cards
- `Focus` shows best next moves and the weekly plan
- Feedback remains available for improving future recommendation quality

## Current Behavior

- Home prioritizes a short set of next-step cards near the top of the page.
- Focus keeps recommendation cards close to active execution work.
- Ratings and notes remain part of the recommendation feedback loop.

## User Flows

- Review a next-step card from Home.
- Track or score a recommendation from Focus.
- Improve future suggestions through feedback.

## Key System Components

- `src/web/routes/suggestions.py`
- `src/web/routes/recommendations.py`
- `web/src/app/(dashboard)/page.tsx`
- `web/src/app/(dashboard)/goals/page.tsx`

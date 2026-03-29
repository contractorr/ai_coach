# Return Briefs and Why Now

**Status:** Updated for the simplified product model

## Purpose

Return briefs and why-now evidence reduce re-orientation time and help users understand why a surfaced item matters now.

## Product Placement

- Return brief: `Home`
- Why-now chips: Home next steps, Goals cards, Radar cards when helpful
- Primary job: shorten the path from `I am back` to `I know what matters`

## Current Behavior

- If the user has been away for seven days or more, the return brief replaces the normal greeting.
- For shorter absences, the return brief can appear alongside the greeting.
- Why-now evidence should stay compact and action-oriented.

## User Flows

- Return to Home after an absence and read the brief.
- Inspect the strongest surfaced items with why-now context.
- Open the related workspace when deeper work is needed.

## Key System Components

- `web/src/app/(dashboard)/page.tsx`
- `src/web/routes/greeting.py`
- `src/web/routes/suggestions.py`
- `web/src/components/home/ReturnBriefCard.tsx`

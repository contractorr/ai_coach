# Goals

**Status:** Updated for the simplified product model

## Purpose

Goals combines goals, recommendations, weekly planning, and actionable opportunities into one execution workspace. Users should understand it as `what should I do next?`, not as a collection of separate systems.

## Product Placement

- Workspace: `Goals`
- Current route: `/focus` (with `/goals` available as an alias)
- Primary job: decide what to do next and keep current work moving
- Advanced detail: `/projects` remains available for deeper opportunity browsing, but it is no longer a primary product concept

## Current Behavior

- Goals starts with the strongest next moves and weekly plan items.
- Goals remain durable objects with milestones, check-ins, and status changes.
- Recommendations and opportunities are treated as part of the same execution workflow.
- Users can create a goal, update progress, and score recommendation quality from one page.

## User Flows

- Review best next moves near the top of Goals.
- Create a goal, add milestones, and log a check-in.
- Open a deeper opportunity view only when the lightweight Goals surface is not enough.

## Key System Components

- `web/src/app/(dashboard)/goals/page.tsx`
- `web/src/app/(dashboard)/focus/page.tsx`
- `src/web/routes/goals.py`
- `src/web/routes/recommendations.py`

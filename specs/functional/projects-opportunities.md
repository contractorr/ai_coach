# Opportunities in Goals

**Status:** Updated for the simplified product model

## Purpose

Opportunities and project ideas are now framed as actionable work inside Goals. Users should not need to learn a separate primary `Projects` concept before the system can recommend something worth doing.

## Product Placement

- Primary workspace: `Goals`
- Secondary deep-dive page: `/projects`
- Primary job: decide whether an opportunity is worth acting on now

## Current Behavior

- Goals can surface opportunity-shaped next moves alongside goals and recommendations.
- The advanced `/projects` page remains available when the user wants deeper exploration.
- Opportunity handling should feel like part of one execution workflow.

## User Flows

- See an opportunity in Goals.
- Open the advanced page only when more detail is needed.
- Track or pursue the opportunity as part of normal Goals work.

## Key System Components

- `web/src/app/(dashboard)/goals/page.tsx`
- `web/src/app/(dashboard)/projects/page.tsx`
- `src/web/routes/projects.py`

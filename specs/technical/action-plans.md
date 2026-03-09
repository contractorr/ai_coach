# Action Plans

**Status:** Updated for the simplified product model

## Overview

Action plans are implemented as tracked recommendation actions and weekly-plan items surfaced inside Focus.

## Key Modules

- `src/web/routes/recommendations.py`
- `web/src/app/(dashboard)/goals/page.tsx`
- briefing and recommendation models shared with Focus cards

## Interfaces

- recommendation tracking endpoints under `/api/recommendations`
- weekly plan data from `/api/recommendations/weekly-plan`
- tracked action updates submitted from Focus

## Simplified Product Notes

- The product does not expose action plans as a standalone workspace.
- Focus owns the primary UX for reviewing and executing this work.

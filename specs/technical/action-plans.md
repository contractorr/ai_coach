# Action Plans

**Status:** Updated for the simplified product model

## Overview

Action plans are implemented as tracked recommendation actions and weekly-plan items surfaced inside Goals.

## Key Modules

- `src/web/routes/recommendations.py`
- `src/web/services/journal_entries.py`
- `web/src/app/(dashboard)/goals/page.tsx`
- briefing and recommendation models shared with Goals cards

## Interfaces

- recommendation tracking endpoints under `/api/recommendations`
- weekly plan data from `/api/recommendations/weekly-plan`
- tracked action updates submitted from Goals
- goal-linked tracked actions may reference only journal entries with frontmatter `type: goal`

## Simplified Product Notes

- The product does not expose action plans as a standalone workspace.
- Goals owns the primary UX for reviewing and executing this work.
- Goal-path filtering and linking are validated through a shared resolver so daily, quick, and research entries are rejected consistently.

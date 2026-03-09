# Return Briefs and Why Now

**Status:** Updated for the simplified product model

## Overview

This subsystem explains timing and priority on Home, Focus, and Radar without becoming a standalone product concept.

## Key Modules

- `src/web/routes/greeting.py`
- `src/web/routes/suggestions.py`
- `web/src/app/(dashboard)/page.tsx`
- shared why-now UI chips

## Interfaces

- return-brief payloads consumed by Home
- why-now arrays embedded in suggestion payloads
- dismissible return-brief state in Home

## Simplified Product Notes

- Seven-day absence logic determines whether the brief replaces or supplements the normal greeting.
- Why-now evidence should remain compact and action-oriented.

# Greeting Cache

**Status:** Updated for the simplified product model

## Overview

Greeting and return-brief caching support Home's personalized opening state and short re-orientation flow.

## Key Modules

- `src/web/routes/greeting.py`
- greeting/return-brief caching helpers
- `web/src/app/(dashboard)/page.tsx`

## Interfaces

- `GET /api/greeting`
- `GreetingResponse` and `ReturnBrief` payloads consumed by Home
- stale-then-refresh behavior for cached greeting payloads

## Simplified Product Notes

- When the user has been away for seven days or more, Home uses the return brief instead of the normal greeting.
- For shorter absences, the return brief can appear alongside the greeting.

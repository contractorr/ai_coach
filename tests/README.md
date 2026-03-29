# Test Layout

Tests mirror the backend and frontend surface areas they protect.

## Fast Navigation

- `tests/advisor/`: advisor and recommendation behavior
- `tests/curriculum/`: learning store and content flows
- `tests/intelligence/`: scrapers, radar, and ranking
- `tests/memory/`: fact persistence and consolidation
- `tests/web/`: FastAPI routes and app-level behavior

## Working Rules

- Prefer the smallest slice that covers the files you changed.
- Route changes should usually add or update a matching `tests/web/` case.
- Structural repo metadata changes should keep guardrail tests green.

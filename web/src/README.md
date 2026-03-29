# Frontend Source

Dashboard pages, shared UI, hooks, and API-facing types live here.

## Layout

- `app/`: route-level pages and layouts
- `components/`: reusable UI and workspace widgets
- `hooks/`: frontend state helpers
- `types/`: manual workspace types plus generated API contracts

## Invariants

- User-facing contract changes should update or consume `types/api.generated.ts`.
- Large page files are hotspots; prefer extracting route-specific hooks and components before adding new branches.
- New pages should keep API call shapes aligned with backend route tests.

## Validation

- `npm --prefix web run lint`
- `npm --prefix web run typecheck`
- `npm --prefix web run build`

# Web Backend Package

FastAPI app assembly, request models, route modules, and web persistence adapters live here.

## Entry Points

- `app.py`: application factory and middleware
- `models.py`: request/response schemas
- `routes/`: API surfaces grouped by workspace
- `user_store.py`: per-user web state storage

## Invariants

- Contract changes should regenerate `web/openapi.json` and `web/src/types/api.generated.ts`.
- Route modules should stay thin and delegate behavior to domain packages or services.
- Hotspots in `routes/curriculum.py` and `models.py` should only grow through helper extraction or split modules.

## Validation

- `just test-web`
- `just contracts-check`
- `uv run pytest tests/web/test_app_startup.py tests/web/test_api_versioning.py -q`

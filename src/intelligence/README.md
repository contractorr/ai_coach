# Intelligence Package

Radar ingestion, ranking, search, and trend detection live here.

## Entry Points

- `scheduler.py`: background source orchestration
- `search.py`: intel retrieval and filtering
- `trending_radar.py`: cross-source topic trend detection
- `sources/`: scraper implementations

## Invariants

- Scrapers should stay isolated behind shared base types and scheduler registration.
- New sources should add tests in `tests/intelligence/` and update the relevant specs.
- Trend and feed changes often affect `src/web/routes/intel.py` plus `web/src/types/radar.ts`.

## Validation

- `just test-intelligence`
- `uv run pytest tests/intelligence/test_scraper.py tests/intelligence/test_trending_radar.py -q`
- `uv run pytest tests/web/test_intel_routes.py -q`

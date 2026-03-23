# Scheduler Refactor — Break God Class into Pipeline Framework

## Problem

`IntelScheduler` in `src/intelligence/scheduler.py` is 1,447 lines with 27 methods spanning ~14 responsibilities: scraper init, async execution, 3 watchlist pipelines (copy-paste), signal detection, autonomous actions, research, recommendations, heartbeat, trending radar, capability model, memory consolidation, entity extraction, job scheduling, and error handling. Hard to test, review, or extend.

## Desired Behavior

- Split into 4 focused modules: `scraper_factory`, `watchlist_pipeline`, `runners`, `job_registry`
- `IntelScheduler` remains the public entry point but delegates to extracted modules
- All existing external imports continue working (re-exports)
- All existing tests pass unchanged
- `scheduler.py` drops from ~1,447 to <400 lines

## Acceptance Criteria

- [ ] `ScraperFactory` handles all scraper instantiation; `_init_scrapers` is a 3-line delegation
- [ ] `WatchlistPipeline` unifies company/hiring/regulatory into composition-based pipeline
- [ ] Runner functions extracted with shared `RunnerContext` dataclass
- [ ] `JobSpec` dataclass + `build_job_specs`/`register_jobs` replace 163-line `start_with_research`
- [ ] `scheduler.py` < 400 lines
- [ ] All external imports preserved: `ResearchRunner`, `RecommendationRunner`, `_parse_cron`, `IntelScheduler`
- [ ] `web/routes/intel.py` access to `scheduler._scrapers` and `scheduler._run_async()` works
- [ ] Existing test suite passes (especially `test_pipeline_scheduler.py`, `test_security.py`, web tests)
- [ ] New unit tests for `ScraperFactory`, `WatchlistPipeline`, runner functions

## Edge Cases

- Watchlist pipelines have slightly different dedup logic (regulatory uses nested loop + seen set) — `WatchlistPipeline` must support a custom `processor` callable
- `_run_async` is tightly coupled to health tracking + metrics — stays in `IntelScheduler`
- Entity extraction lifecycle is coupled to scheduler (`_get_entity_scheduler` lazy init) — stays
- Job registry must handle both cron and interval triggers

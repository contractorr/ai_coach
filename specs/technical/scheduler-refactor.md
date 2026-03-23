# Scheduler Refactor — Technical Spec

## New Modules

### `src/intelligence/scraper_factory.py`

```python
class ScraperFactory:
    def __init__(self, storage, sources_config, full_config): ...
    def create_all(self) -> tuple[list, Any, RSSFeedHealthTracker]: ...
```

Moves the entire `_init_scrapers` body. Returns `(scrapers, intel_embedding_mgr, feed_health)`.

### `src/intelligence/watchlist_pipeline.py`

```python
@dataclass
class WatchlistPipelineConfig:
    name: str
    config_key: str
    entity_key_field: str
    default_lookback_days: int
    default_limit_per_entity: int
    empty_result: dict

class WatchlistPipeline:
    def __init__(self, storage, full_config, pipeline_config,
                 resolver, processor, store_factory, result_filter=None): ...
    def run(self) -> dict: ...
```

Three factory functions: `create_company_movement_pipeline()`, `create_hiring_pipeline()`, `create_regulatory_pipeline()`.

### `src/intelligence/runners.py`

```python
@dataclass
class RunnerContext:
    storage: IntelStorage
    full_config: dict
    journal_storage: Any = None
    embeddings: Any = None
    intel_embedding_mgr: Any = None
```

Functions: `run_signal_detection`, `run_autonomous_actions`, `refresh_capability_model`, `run_github_repo_poll`, `run_goal_intel_matching`, `run_heartbeat`, `run_trending_radar`, `run_weekly_summary`, `run_memory_consolidation`.

`ResearchRunner` and `RecommendationRunner` classes also move here. Re-exported from `scheduler.py`.

### `src/intelligence/job_registry.py`

```python
@dataclass
class JobSpec:
    id: str
    func: Callable
    trigger_type: str         # "cron" | "interval"
    trigger_value: str | dict
    enabled_check: Callable[[dict], bool]
    coalesce: bool = False
    max_instances: int = 1

def build_job_specs(scheduler, scrape_cron, research_cron) -> list[JobSpec]: ...
def register_jobs(bg_scheduler, specs, full_config) -> None: ...
```

## IntelScheduler (post-refactor)

~350 lines. Keeps: `__init__`, `_init_scrapers` (3 lines), `_run_async`, `run_now`, pipeline delegates (lazy one-liners), runner delegates (one-liners), entity extraction methods, `_default_error_handler`, `start`/`start_with_research`/`stop`, `_add_recommendations_job`.

## Backward Compatibility

| Import | Location | Strategy |
|--------|----------|----------|
| `ResearchRunner` | `advisor/autonomous.py`, `test_pipeline_scheduler.py` | Re-export from scheduler.py |
| `RecommendationRunner` | `test_pipeline_scheduler.py` | Re-export from scheduler.py |
| `_parse_cron` | `test_security.py` | Stays in scheduler.py |
| `IntelScheduler` | 8+ files | Class stays in scheduler.py |
| `scheduler._scrapers` | `web/routes/intel.py` | Attribute stays on IntelScheduler |
| `scheduler._run_async()` | `web/routes/intel.py` | Method stays on IntelScheduler |

## Invariants

- No behavior change — purely structural refactor
- All metrics, health tracking, and error handling preserved
- Config keys and structure unchanged

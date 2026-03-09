# CLI

## Overview

Entry point, configuration, logging, retry/rate-limit utilities, and component bootstrap for the `coach` CLI. Implemented with Click (command groups), Pydantic v2 (config validation), structlog (logging), and tenacity (retries). All other modules are initialized via `get_components()` in `utils.py`; the CLI layer owns no domain logic.

## Dependencies

**Depends on:** `advisor`, `journal`, `intelligence`, `profile`, `research`, `llm`
**Depended on by:** nothing (top-level entry point); `coach_mcp` and `web` each load config independently

---

## Components

### `cli` group

**File:** `src/cli/main.py`
**Status:** Stable

#### Behavior

Root Click group. Registered as the `coach` console-script entry point. Loads config and sets up logging on every invocation via the group callback.

```python
@click.group()
@click.version_option(version="0.1.0")
@click.option("-v", "--verbose", is_flag=True)
def cli(verbose: bool): ...
```

**Startup sequence:**
1. `load_config()` → raw dict.
2. If `--verbose`: overrides `config["logging"]` to `{"level": "DEBUG", "file_level": "DEBUG"}`.
3. `setup_logging(config)`.

**Registered command groups:** `journal`, `daemon`, `db`, `research`, `recommend`, `export`, `profile`, `learn` (DEPRECATED — Phase 2), `projects`, `capabilities`, `heartbeat`, `memory`, `predictions`, `threads`

**Registered standalone commands:** `ask`, `review`, `opportunities`, `goals`, `scrape`, `brief`, `sources`, `intel_export`, `init`, `trends`, `reflect`, `today`, `radar`, `scraper_health`, `watchlist`, `eval_cmd`, `dedup_backfill`

#### Inputs / Outputs

No return value; side effects only (logging init, Click dispatch).

#### Invariants

- `setup_logging` is always called before any subcommand executes.
- `--verbose` only affects the current invocation; no config file is written.

#### Error Handling

- `load_config()` raises `ValueError` on YAML parse errors or Pydantic validation failures — these propagate unhandled, printing a traceback.
- No other error handling at the group level.

#### Configuration

| Key | Default | Notes |
|-----|---------|-------|
| `version` | `"0.1.0"` | hardcoded in `@click.version_option` |

---

### Config Loading

**File:** `src/cli/config.py`
**Status:** Stable

#### Behavior

Loads `config.yaml` from the first matching location, validates via Pydantic, and returns either a typed `CoachConfig` model or a plain dict (for backwards compatibility). All callers in commands use `load_config()` (dict); callers needing typed access use `load_config_model()`.

**`find_config()` search order:**
1. `./config.yaml` (cwd)
2. `~/.coach/config.yaml`
3. `~/coach/config.yaml`

Returns `None` if no file found; callers fall back to all-defaults `CoachConfig`.

**`get_paths(config: dict) -> dict`** — convenience helper that expands `~` in path strings; returns:
```python
{
    "journal_dir": Path,
    "chroma_dir": Path,
    "intel_db": Path,
    "log_file": Path,
}
```
Falls back to `DEFAULT_CONFIG["paths"]` if `"paths"` key absent.

**`get_limits(config: dict) -> dict`** — merges `config["limits"]` over `LimitsConfig()` defaults. Callers that pass `config["limits"]` directly (without this helper) may miss defaults for missing keys.

#### Inputs / Outputs

```python
def find_config() -> Optional[Path]
def load_config(config_path: Optional[Path] = None) -> dict
def load_config_model(config_path: Optional[Path] = None) -> CoachConfig
def get_paths(config: dict) -> dict
def get_limits(config: dict) -> dict
def setup_logging(config: dict) -> None   # delegates to logging_config.setup_logging
```

#### Invariants

- `load_config()` always returns a complete dict (all sections present with defaults filled in) — never a partial config.
- `load_config_model()` always returns a valid `CoachConfig`; raises `ValueError` on bad input.
- `_deep_merge()` is defined but not called anywhere in this module; it is dead code.

#### Error Handling

- YAML parse error → `ValueError("Invalid YAML in config file: ...")`, propagates to caller.
- Pydantic validation failure → `ValueError("Config validation failed: ...")`, propagates.
- Missing config file → silently uses all defaults (no warning logged).

#### Configuration

No config keys. Module exposes two module-level constants for backwards compat:
- `DEFAULTS = LimitsConfig().model_dump()`
- `DEFAULT_CONFIG = CoachConfig().to_dict()`

---

### CoachConfig

**File:** `src/cli/config_models.py`
**Status:** Stable

#### Behavior

Pydantic v2 model hierarchy that validates and normalises `config.yaml`. Root model is `CoachConfig`; all sub-models are composed via `Field(default_factory=...)`. Env-var interpolation (`${VAR}`) is applied at the root validator level for `llm.api_key`, `research.tavily_api_key`, and `sources.crunchbase.api_key`.

**Sub-models and their fields:**

| Model | Key fields |
|-------|-----------|
| `LLMConfig` | `provider` (`auto`/`claude`/`openai`/`gemini`), `model`, `api_key`, `extended_thinking=True`, `max_tokens=16000`, `cheap_max_tokens=4000` |
| `PathsConfig` | `journal_dir`, `chroma_dir`, `intel_db`, `log_file` — all `Path`, all `expanduser()`'d in `model_validator` |
| `SourcesConfig` | `custom_blogs=[]`, `rss_feeds=["https://news.ycombinator.com/rss"]`, `enabled=["hn_top","rss_feeds"]`, `github_trending={}`, `indeed_hiring_lab={}`, `google_trends={}`, `crunchbase={}` |
| `ResearchConfig` | `enabled=False`, `max_topics=3`, `tavily_api_key=None`, `schedule="0 21 * * 0"` |
| `ScoringConfig` | `min_threshold=6.0`, `max_per_category=3`, `weights={relevance:0.3, urgency:0.25, feasibility:0.25, impact:0.2}` |
| `RAGConfig` | `max_context_chars=8000`, `journal_weight=0.7`, `structured_profile=False`, `inject_memory=False`, `inject_recurring_thoughts=False`, `xml_delimiters=False` |
| `SearchConfig` | `default_results=5`, `intel_similarity_threshold=0.7` |
| `RateLimitSourceConfig` | `requests_per_second=2.0`, `burst=5` |
| `RateLimitsConfig` | `default`, `tavily` (1.0/1), `hackernews` (5.0/10), `reddit` (1.0/2) |
| `DeliveryConfig` | `methods=["journal"]`, `schedule="0 8 * * 0"` |
| `RecommendationsConfig` | `enabled=False`, `scoring`, `delivery`, `similarity_threshold=0.85`, `dedup_window_days=30` |
| `RetryConfig` | `max_attempts=3`, `min_wait=2.0`, `max_wait=10.0`, `llm_max_wait=30.0` |
| `LimitsConfig` | `hn_max_stories=30`, `rss_max_entries=20`, `github_max_repos=25`, `journal_max_entries=5`, `journal_max_chars=6000`, `intel_max_items=5`, `intel_max_chars=3000`, `total_context_chars=8000`, `summary_truncate=500`, `preview_truncate=200`, `llm_max_tokens=2000` |
| `LoggingConfig` | `level="INFO"`, `file_level="DEBUG"` (both uppercased + validated) |
| `HeartbeatConfig` | `enabled=False`, `interval_minutes=30`, `heuristic_threshold=0.3`, `llm_budget_per_cycle=5`, `notification_cooldown_hours=4`, `lookback_hours=2` |
| `MemoryConfig` | `enabled=True`, `max_facts_per_entry=5`, `similarity_threshold=0.7`, `auto_noop_threshold=0.95`, `max_context_facts=25`, `high_confidence_threshold=0.9`, `backfill_batch_size=10` |
| `ThreadsConfig` | `enabled=True`, `similarity_threshold=0.78`, `min_entries_for_thread=2`, `candidate_count=10` |
| `TrendingRadarConfig` | `enabled=True`, `min_sources=2`, `days=7`, `max_topics=15`, `interval_hours=6` |

**Env-var interpolation (`expand_env_vars` validator):** pattern `${VAR_NAME}` (exact match: starts with `${`, ends with `}`) → `os.getenv(VAR_NAME, "")`. Applied only to `llm.api_key`, `research.tavily_api_key`, `sources.crunchbase["api_key"]`.

**`validate_cron(expr)` standalone function:** validates that cron has exactly 5 space-separated fields using per-field regex patterns; also accepts any string matching `r"^[\d\-,\*/]+$"` as a catch-all. Used by `ResearchConfig.schedule` and `DeliveryConfig.schedule`.

#### Inputs / Outputs

```python
@classmethod
def from_dict(cls, data: dict) -> "CoachConfig"
# Migrates old string paths to Path objects before model_validate()

def to_dict(self) -> dict
# Returns model_dump(mode="python") — all Paths remain as Path objects
```

#### Invariants

- `ScoringConfig.weights` must sum to `1.0 ± 0.01`; raises `ValueError` otherwise.
- `RAGConfig.journal_weight` must be `[0.0, 1.0]`; raises `ValueError` otherwise.
- `LoggingConfig.level` and `file_level` must be in `{DEBUG, INFO, WARNING, ERROR, CRITICAL}`; stored uppercased.
- `LLMConfig.provider` must be in `{"auto", "claude", "openai", "gemini"}`.
- All `PathsConfig` paths are expanded at construction time; `~` is never present after init.

#### Error Handling

- Invalid field value → `ValueError` from Pydantic validator, propagates through `load_config_model()` as `ValueError("Config validation failed: ...")`.
- Unknown config keys are silently ignored (Pydantic default behavior; no `model_config = ConfigDict(extra="forbid")`).

#### Caveats

- `from_dict()` contains a dead comment block for migrating old flat-dict `limits` format — no migration code executes.
- `to_dict()` returns `Path` objects (not strings) for path fields; callers must call `.expanduser()` or convert to string themselves if needed.

---

### Logging Setup

**File:** `src/cli/logging_config.py`
**Status:** Stable

#### Behavior

Configures structlog with a shared processor chain and either a console renderer (default) or JSON renderer (daemon mode). All output goes to `sys.stderr` via a single `StreamHandler`. Idempotent — replaces all handlers on the root logger on each call.

**Processor chain (applied in order):**
1. `merge_contextvars` — merges structlog context vars
2. `add_log_level`
3. `add_logger_name`
4. `TimeStamper(fmt="iso")`
5. `CallsiteParameterAdder([MODULE, FUNC_NAME, LINENO])`
6. `StackInfoRenderer`
7. `UnicodeDecoder`
8. `_redact_sensitive` — custom processor (see below)
9. `ProcessorFormatter.wrap_for_formatter` (bridges structlog → stdlib)

Final rendering: `JSONRenderer` (json_mode=True) or `ConsoleRenderer` (default).

**`_redact_sensitive` processor** — runs regex substitutions on all string values in the event dict:

| Pattern | Replacement |
|---------|-------------|
| `sk-ant-[a-zA-Z0-9_-]{10}...` (Anthropic keys) | `sk-ant-XXXXXXXXXX...REDACTED` |
| `sk-[a-zA-Z0-9_-]{6}[20+chars]` (OpenAI-style) | `sk-XXXXXX...REDACTED` |
| `Bearer [20+chars]` | `Bearer REDACTED` |
| `api_key: value` / `api-key=value` patterns | `api_key: REDACTED` |
| email addresses | `REDACTED@email` |

#### Inputs / Outputs

```python
def setup_logging(json_mode: bool = False, level: str = "INFO") -> None
```

#### Invariants

- Root logger has exactly one handler after `setup_logging()`.
- Structlog is configured globally — affects all `structlog.get_logger()` calls in all modules.

#### Error Handling

- Invalid `level` string: `getattr(logging, level.upper(), logging.INFO)` — silently falls back to `INFO` for unknown level strings (unlike `LoggingConfig` which raises).

#### Caveats

- `cache_logger_on_first_use=True`: if `setup_logging()` is called after any logger has been used, the cached bound logger retains the old processor chain.
- Redaction patterns only match string values; nested dicts/lists within the event dict are not recursed into.

---

### Retry Decorators

**File:** `src/cli/retry.py`
**Status:** Stable

#### Behavior

Thin wrappers over tenacity that produce `@retry(...)` decorators. All three factory functions (`http_retry`, `llm_retry`, `with_retry`) produce semantically identical decorators differing only in default `max_wait`. All use `wait_exponential(multiplier=1, min=min_wait, max=max_wait)`, `stop_after_attempt(max_attempts)`, `retry_if_exception_type(exceptions)`, `before_sleep_log(..., logging.WARNING)`, `reraise=True`.

| Function | `max_wait` default | Intended use |
|----------|--------------------|--------------|
| `http_retry` | `10.0` s | HTTP/scraper calls |
| `llm_retry` | `30.0` s | LLM API calls |
| `with_retry` | `10.0` s | Generic |

**`retry_from_config(config, retry_type)`** — reads `config["retry"]` dict:
- `max_attempts` (default `3`)
- `min_wait` (default `2.0`)
- `max_wait` (default `10.0`) or `llm_max_wait` (default `30.0`) if `retry_type == "llm"`

Returns a `with_retry(...)` decorator (always, regardless of `retry_type`).

#### Inputs / Outputs

```python
def http_retry(max_attempts=3, min_wait=2.0, max_wait=10.0, exceptions=(Exception,)) -> tenacity.retry
def llm_retry(max_attempts=3, min_wait=2.0, max_wait=30.0, exceptions=(Exception,)) -> tenacity.retry
def with_retry(max_attempts=3, min_wait=2.0, max_wait=10.0, exceptions=(Exception,)) -> tenacity.retry
def retry_from_config(config: dict, retry_type: str = "http") -> tenacity.retry
```

#### Invariants

- `reraise=True` on all decorators: the original exception is re-raised after all attempts exhausted (no swallowing).
- `before_sleep` logs at `WARNING` level before each retry.

#### Caveats

- `http_retry` and `llm_retry` are functionally identical to `with_retry` with different default `max_wait`. There is no behavioral difference in exception handling or retry logic.
- `retry_from_config` always delegates to `with_retry`, so `retry_type` only controls which `max_wait` key is read.

---

### TokenBucketRateLimiter

**File:** `src/cli/rate_limit.py`
**Status:** Stable

#### Behavior

Token-bucket rate limiter. Tokens refill continuously at `rate` tokens/second up to `max_tokens` (burst cap). Each `acquire()` call consumes one token, waiting if none are available.

```python
def __init__(self, requests_per_second: float = 2.0, burst: int = 5)
```

Initial state: bucket full (`_tokens = float(burst)`). Uses `time.monotonic()` for drift-free timing. Async mode uses `asyncio.Lock()` to serialize concurrent `acquire()` calls.

**`_refill()` formula:**
```
_tokens = min(max_tokens, _tokens + elapsed_seconds * rate)
```
Called at the start of every `acquire()` and `acquire_sync()` before the wait loop.

#### Inputs / Outputs

```python
async def acquire(self) -> None          # async; holds asyncio.Lock while waiting
def acquire_sync(self) -> None           # sync; no locking — not safe for concurrent threads
@property
def available_tokens(self) -> float     # calls _refill() as side effect
```

#### Invariants

- `acquire()` always consumes exactly `1.0` token.
- `acquire_sync()` is not thread-safe (no lock).
- `available_tokens` has the side effect of updating `_tokens` and `_last_refill`.

#### Error Handling

No error handling. `asyncio.sleep()` and `time.sleep()` propagate `CancelledError`/`KeyboardInterrupt` normally.

#### Configuration

| Parameter | Default | Notes |
|-----------|---------|-------|
| `requests_per_second` | `2.0` | token refill rate |
| `burst` | `5` | max bucket size |

---

### `get_components`

**File:** `src/cli/utils.py`
**Status:** Stable

#### Behavior

Single bootstrap function that initialises all core components from config and returns them as a dict. Called by most CLI commands at the top of their handler. Components are constructed fresh on each call (no singleton caching).

**Construction order:**
1. `load_config()` + `load_config_model()`
2. `get_paths(config)`
3. `JournalStorage(journal_dir)`
4. `IntelStorage(intel_db)`
5. `EmbeddingManager(chroma_dir)` + `IntelEmbeddingManager(chroma_dir / "intel")`
6. `JournalFTSIndex(journal_dir)`
7. `JournalSearch(storage, embeddings, fts_index=fts_index)`
8. `IntelSearch(intel_storage, intel_embeddings)`
9. `RAGRetriever(search, intel_db, intel_search=..., max_context_chars=..., journal_weight=..., profile_path=...)`
10. `AdvisorEngine(rag, model=..., provider=..., api_key=...)` — skipped if `skip_advisor=True`

**ChromaDB dimension mismatch guard:** if `EmbeddingManager` or `IntelEmbeddingManager` raises an exception whose `str(e).lower()` contains `"dimension"` or `"mismatch"`, prints a Rich-formatted error and calls `sys.exit(1)`.

**`AdvisorEngine` key error guard:** if `APIKeyMissingError` is raised, prints the error and calls `sys.exit(1)`.

#### Inputs / Outputs

```python
def get_components(skip_advisor: bool = False) -> dict
```

Returned dict keys:

| Key | Type |
|-----|------|
| `config` | `dict` |
| `config_model` | `CoachConfig` |
| `paths` | `dict` (journal_dir, chroma_dir, intel_db, log_file) |
| `storage` | `JournalStorage` |
| `embeddings` | `EmbeddingManager` |
| `search` | `JournalSearch` |
| `intel_storage` | `IntelStorage` |
| `intel_search` | `IntelSearch` |
| `rag` | `RAGRetriever` |
| `advisor` | `AdvisorEngine` or `None` (if `skip_advisor=True`) |

**Helper functions also in `utils.py`:**

```python
def get_rec_db_path(config: dict) -> Path
# Returns intel_db.parent / "recommendations"

def get_profile_storage(config: dict | None = None) -> ProfileStorage
# Reads config["profile"]["path"], defaults to "~/coach/profile.yaml"

def get_profile_path(config: dict) -> str
# Returns config.get("profile", {}).get("path", "~/coach/profile.yaml")
```

#### Invariants

- `get_components()` always returns all keys; `advisor` is `None` only when `skip_advisor=True`.
- On ChromaDB dimension mismatch, the process exits — no exception propagates to the caller.
- On `APIKeyMissingError`, the process exits — no exception propagates.

#### Error Handling

| Condition | Behaviour |
|-----------|-----------|
| ChromaDB dimension/mismatch error | Print Rich error + `sys.exit(1)` |
| Any other `EmbeddingManager` exception | Re-raised |
| `APIKeyMissingError` on `AdvisorEngine` | Print error + `sys.exit(1)` |

#### Caveats

- No singleton caching: every call to `get_components()` constructs all objects from scratch, including opening DB connections. Commands that call it multiple times (e.g., in a loop) re-open all connections each time.
- `warn_experimental(feature)` utility is defined in this module but emits to `stderr` via `click.echo(..., err=True)`.

---

### Command Modules

**File:** `src/cli/commands/*.py`
**Status:** Mixed (see below)

#### Behavior

29 Click commands/groups registered on the root `cli` group. Commands use `get_components()` or `load_config()` directly for dependencies. No shared base class. Rich `Console` from `cli.utils.console` is used for output in most commands.

| Module | Commands | Status |
|--------|----------|--------|
| `advisor.py` | `ask`, `review`, `opportunities`, `goals`, `today` | Stable |
| `journal.py` | `journal` (group: `add`, `list`, `search`, `show`, `edit`, `delete`) | Stable |
| `intelligence.py` | `scrape`, `brief`, `sources`, `intel_export`, `radar`, `scraper_health`, `watchlist`, `dedup_backfill` | Stable |
| `daemon.py` | `daemon` (group: `start`, `stop`, `status`) | Stable |
| `database.py` | `db` (group: `rebuild`, `stats`, `migrate`) | Stable |
| `research.py` | `research` (group: `run`, `topics`) | Stable |
| `recommend.py` | `recommend` (group: `generate`, `list`, `show`, `dismiss`, `rate`) | Stable |
| `profile.py` | `profile` (group: `show`, `interview`, `edit`, `import`) | Stable |
| `init.py` | `init` | Stable |
| `export.py` | `export` | Stable |
| `capabilities.py` | `capabilities` | Stable |
| `heartbeat.py` | `heartbeat` (group: `run`, `status`) | Experimental |
| `memory.py` | `memory` (group: `list`, `search`, `delete`, `stats`, `backfill`) | Experimental |
| `predictions.py` | `predictions` (group: `list`, `review`, `stats`) | Experimental |
| `threads.py` | `threads` (group: `list`, `get`, `reindex`) | Experimental |
| `learn.py` | `learn` (group: `paths`, `gaps`, `checkin`) | DEPRECATED — removed in Phase 2 (learning merged into goals) |
| `projects.py` | `projects` (group: `discover`, `ideas`, `list`) | Experimental |
| `reflect.py` | `reflect` | Experimental |
| `trends.py` | `trends` | Experimental |
| `eval_cmd.py` | `eval` | Experimental |

#### Invariants

- Experimental commands call `warn_experimental(feature)` before executing (emits to stderr).
- Commands that don't need LLM pass `skip_advisor=True` to `get_components()`.

---

## Cross-Cutting Concerns

**Config dict vs model:** `load_config()` returns a plain `dict` (for widespread backwards compat); `load_config_model()` returns a typed `CoachConfig`. New code should prefer `load_config_model()`. Both return the same data; `to_dict()` is a lossless roundtrip except Path objects are not stringified.

**`sys.exit(1)` vs exception:** `get_components()` exits the process on two conditions (ChromaDB mismatch, missing API key) rather than raising. Commands are not expected to handle these cases.

**Global structlog state:** `setup_logging()` configures structlog globally. Any module that calls `structlog.get_logger()` before `setup_logging()` runs will get an unconfigured logger.

## Test Expectations

- `load_config()` must return all defaults when no config file exists.
- `load_config_model()` must raise `ValueError` for invalid provider, bad weights sum, bad log level, bad cron.
- `CoachConfig.expand_env_vars` must interpolate `${VAR}` and leave non-interpolated values unchanged.
- `TokenBucketRateLimiter.acquire()` must block until tokens are available; must not exceed `burst` token cap.
- `retry` decorators must retry exactly `max_attempts` times before re-raising.
- `get_components()` with a bad ChromaDB must call `sys.exit(1)` — mock `sys.exit` and assert called.
- `_redact_sensitive` must redact Anthropic keys, Bearer tokens, and email addresses in log event dicts.
- Mocking required: `EmbeddingManager`, `IntelEmbeddingManager`, `AdvisorEngine`, `JournalStorage`, `IntelStorage`, filesystem for config loading.

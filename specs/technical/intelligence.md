# intelligence

## Overview

The intelligence module handles external data ingestion: 19 async scrapers feed a shared SQLite store (`intel.db`), which is queried by the RAG layer, trending analysis, goal-matching, and heartbeat pipelines. Key architectural decisions: WAL-mode SQLite for all writes, FTS5 for full-text search, ChromaDB for semantic dedup and goal matching, APScheduler for cron-based orchestration.

## Dependencies

**Depends on:** `db` (WAL connect), `llm` (cheap provider for TrendingRadar/GoalIntelLLMEvaluator/HeartbeatEvaluator/CapabilityHorizonModel), `journal` (RecommendationRunner, ResearchRunner), `advisor` (RecommendationRunner, signal detection), `profile` (EventScraper + GitHubIssuesScraper location/language filters), `research` (ResearchRunner), `web.user_store` (scrape event logging, RSS feed merging), `cli.config` (paths for semantic dedup), `observability` (metrics counters/timers)

**Depended on by:** `advisor` (RAGRetriever queries intel.db), `coach_mcp` (intel tools), `web` (intel routes), `cli` (daemon scrape command)

---

## Components

### IntelItem

**File:** `src/intelligence/scraper.py`
**Status:** Stable

#### Behavior

Plain dataclass representing one scraped item.

```python
@dataclass
class IntelItem:
    source: str
    title: str
    url: str
    summary: str
    content: Optional[str] = None
    published: Optional[datetime] = None
    tags: Optional[list[str]] = None
    content_hash: Optional[str] = None

    def compute_hash(self) -> str: ...
```

`compute_hash()` returns a 16-char hex SHA-256 over `f"{title.lower().strip()}|{summary.lower().strip()}"`.

#### Inputs / Outputs

`compute_hash() -> str` — 16-char hex string. No side effects.

#### Invariants

- `source`, `title`, `url`, `summary` are always required (non-optional at type level).
- `content_hash` stored on the object is not authoritative — `IntelStorage.save()` recomputes it if `None`.

---

### validate_url

**File:** `src/intelligence/scraper.py`
**Status:** Stable

#### Behavior

Module-level function. Returns `True` if URL has an allowed scheme and non-trivial netloc.

Allowed schemes: `{"http", "https"}`. Internal schemes: `{"research"}` — always valid (used by deep research items).

Logic:
1. Empty string → `False`.
2. Parse with `urlparse`.
3. If scheme in `_INTERNAL_SCHEMES` → `True`.
4. If scheme not in `_ALLOWED_SCHEMES` → `False`.
5. If `netloc` empty or `"."` not in `netloc` → `False`.
6. Otherwise → `True`. Any exception → `False`.

#### Invariants

- `research://` URLs always pass regardless of path/netloc.
- Pure path strings (no scheme) → `False`.

---

### IntelStorage

**File:** `src/intelligence/scraper.py`
**Status:** Stable

#### Behavior

SQLite-backed store for intel items. Uses WAL mode (`wal_connect`). Auto-creates parent dirs on init.

**Schema — `intel_items`:**

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | autoincrement |
| `source` | TEXT NOT NULL | scraper source name |
| `title` | TEXT NOT NULL | |
| `url` | TEXT UNIQUE NOT NULL | dedup key |
| `summary` | TEXT | |
| `content` | TEXT | full body, optional |
| `published` | TIMESTAMP | original publish time |
| `scraped_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| `tags` | TEXT | comma-separated |
| `content_hash` | TEXT | 16-char hex for near-dedup |
| `duplicate_of` | INTEGER | FK to canonical row (semantic dedup) |

Indexes: `idx_intel_source(source)`, `idx_intel_scraped(scraped_at)`, `idx_intel_hash(content_hash)`.

FTS5 virtual table `intel_fts(title, summary, content, tags)` with porter+unicode61 tokenizer. Three triggers (`intel_fts_ai`, `intel_fts_ad`, `intel_fts_au`) keep FTS in sync. Init also backfills existing rows not in FTS.

**Schema — `scraper_health`:** see `ScraperHealthTracker`.

Migration strategy: `ALTER TABLE ... ADD COLUMN` wrapped in `try/except OperationalError` for `content_hash` and `duplicate_of` columns (idempotent on existing DBs). Same pattern for scraper health metric columns.

#### Inputs / Outputs

```python
def __init__(self, db_path: str | Path)

def save(self, item: IntelItem) -> int | None
# Returns row ID (truthy) on insert, None on skip (invalid URL, hash dup, URL dup, DB error).

def mark_duplicate(self, row_id: int, canonical_id: int) -> None
# Sets duplicate_of = canonical_id for row_id.

def hash_exists(self, content_hash: str, days: int = 7) -> bool
# True if same hash seen within last `days` days.

def get_recent(self, days: int = 7, limit: int = 50) -> list[dict]
# Excludes rows where duplicate_of IS NOT NULL. Ordered by scraped_at DESC.

def get_items_since(self, since: datetime, limit: int = 200) -> list[dict]
# Same exclusion. Ordered by scraped_at DESC.

def search(self, query: str, limit: int = 20) -> list[dict]
# LIKE-based search on title + summary. No dedup filtering.

def fts_search(self, query: str, limit: int = 20) -> list[dict]
# FTS5 BM25-ranked search. Falls back to search() on OperationalError.
```

`_row_to_dict()` deserializes `tags` from comma-separated string to `list[str]`.

`_to_fts5_query()` converts user query to FTS5 MATCH: tokenizes with `[\w]+`, joins as `word1* word2*` (prefix + AND semantics).

#### Invariants

- `save()` returns `None` in three distinct cases: invalid URL (logged WARNING), hash dup within 7 days (logged INFO), URL constraint violation (logged DEBUG), DB error (logged ERROR).
- `get_recent()` and `get_items_since()` never return semantic duplicates (`duplicate_of IS NULL`).
- `search()` does NOT filter duplicates — only `get_recent()`/`get_items_since()` do.
- FTS is eventually consistent with `intel_items` via triggers; backfill on init catches upgrades.

#### Error Handling

- `save()`: `sqlite3.IntegrityError` (URL dup) → `None`. `sqlite3.Error` (other) → logs ERROR, returns `None`.
- `fts_search()`: `sqlite3.OperationalError` → logs WARNING, falls back to `search()`.
- `hash_exists()`, `mark_duplicate()`, `get_*()`: no explicit error handling — SQLite errors propagate.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| hash dedup window | `7` days | `hash_exists()` default |
| `get_recent` days | `7` | default arg |
| `get_recent` limit | `50` | default arg |
| `get_items_since` limit | `200` | default arg |
| FTS tokenizer | `porter unicode61` | hardcoded in DDL |

---

### BaseScraper

**File:** `src/intelligence/scraper.py`
**Status:** Stable

#### Behavior

Abstract async base class. Subclasses must implement `source_name: str` (property) and `scrape() -> list[IntelItem]` (async).

```python
def __init__(self, storage: IntelStorage, embedding_manager=None)
```

HTTP client: `httpx.AsyncClient(timeout=30.0, headers={"User-Agent": "AI-Coach/1.0 (Personal Use)"})`. Subclasses share this client for all fetches.

`fetch_html(url)` — fetches URL, returns `BeautifulSoup` or `None` on error.

`save_items(items, semantic_dedup=True, dedup_threshold=0.92)` — the canonical save path. For each item:
1. If `semantic_dedup` and `embedding_manager` present: call `embedding_manager.find_similar(title + summary, threshold)`.
2. Call `storage.save(item)` → `row_id`.
3. If `row_id` and `canonical_id` found: `storage.mark_duplicate(row_id, canonical_id)`, increment `deduped_count`.
4. If `row_id` and no `canonical_id`: genuinely new — index into embedding manager (if available), increment `new_count`.
5. Otherwise: URL/hash dup, skip silently.

Returns `(new_count, deduped_count)` tuple.

Supports async context manager (`async with scraper:`).

#### Inputs / Outputs

```python
@abstractmethod
@property
def source_name(self) -> str

@abstractmethod
async def scrape(self) -> list[IntelItem]

async def fetch_html(self, url: str) -> Optional[BeautifulSoup]

async def save_items(
    self, items: list[IntelItem],
    semantic_dedup: bool = True,
    dedup_threshold: float = 0.92
) -> tuple[int, int]   # (new_count, deduped_count)

async def close(self) -> None
```

#### Invariants

- Semantic dedup only runs when `embedding_manager` is set AND `semantic_dedup=True`.
- Items with no `row_id` (URL/hash dup from storage) are silently skipped — not counted in either counter.
- `new_count + deduped_count <= len(items)` always.

#### Error Handling

- `fetch_html()`: `HTTPStatusError` → logs WARNING with status code, returns `None`. `RequestError` → logs WARNING, returns `None`.
- `save_items()`: no explicit error handling — delegates to `storage.save()` and `embedding_manager`. Exceptions from either propagate.

#### Configuration

| Key | Default | Notes |
|-----|---------|-------|
| HTTP timeout | `30.0` s | hardcoded |
| User-Agent | `"AI-Coach/1.0 (Personal Use)"` | hardcoded |
| semantic dedup threshold | `0.92` | default arg |

---

### ScraperHealthTracker

**File:** `src/intelligence/health.py`
**Status:** Stable

#### Behavior

Tracks per-source scrape outcomes in the `scraper_health` table (defined in `IntelStorage._init_db()`). Implements exponential backoff for failing sources.

```python
def __init__(self, db_path: str | Path)
```

**Backoff formula:** `min(2^new_errors * 60, 3600)` seconds. 1st failure → 120s, 2nd → 240s, ..., cap 3600s.

**`get_health_summary()` status classification:**

| Condition | Status |
|-----------|--------|
| `backoff_until > now` | `"backoff"` |
| `consecutive_errors >= 3` | `"failing"` |
| `consecutive_errors >= 1` | `"degraded"` |
| otherwise | `"healthy"` |

Also computes `error_rate = total_errors / total_runs * 100` (0.0 if no runs).

#### Inputs / Outputs

```python
def record_success(self, source: str, items_scraped: int = 0, items_new: int = 0,
                   duration_s: float | None = None, items_deduped: int = 0) -> None

def record_failure(self, source: str, error: str) -> None
# Truncates error to 500 chars. Logs WARNING at consecutive_errors >= 3.

def should_skip(self, source: str) -> bool
# True if backoff_until > utcnow(). False if no record or no backoff.

def get_all_health(self) -> list[dict]
def get_source_health(self, source: str) -> dict | None
def get_health_summary(self) -> list[dict]  # adds status + error_rate fields
```

`record_success()` upserts atomically (`INSERT ... ON CONFLICT DO UPDATE`), resets `consecutive_errors=0`, `last_error=NULL`, `backoff_until=NULL`.

`record_failure()` reads `consecutive_errors` first, then upserts with incremented count and computed `backoff_until`.

#### Invariants

- `should_skip()` compares UTC strings (ISO format); no timezone objects used.
- Health table is NOT created by this class — `IntelStorage._init_db()` owns the DDL.

#### Error Handling

No explicit error handling — SQLite errors propagate.

#### Configuration

| Key | Default |
|-----|---------|
| Max backoff | `3600` s |
| Backoff base | `2^n * 60` s |
| Error string limit | `500` chars |

---

### RSSFeedHealthTracker

**File:** `src/intelligence/health.py`
**Status:** Stable

#### Behavior

Per-feed-URL health tracking keyed by `feed_url`. No backoff logic — tracking only. Creates its own `rss_feed_health` table in `__init__`.

#### Inputs / Outputs

```python
def __init__(self, db_path: str | Path)
def record_success(self, feed_url: str) -> None
def record_failure(self, feed_url: str, error: str) -> None
def get_all_health(self) -> list[dict]
def get_feed_health(self, feed_url: str) -> dict | None
```

#### Invariants

- No `should_skip()` method — backoff not implemented.
- Table created in `__init__` (not delegated to `IntelStorage`).

---

### IntelEmbeddingManager

**File:** `src/intelligence/embeddings.py`
**Status:** Stable

#### Behavior

ChromaDB wrapper for intel item vectors. Collection `"intel"` with cosine distance. Embedding model: `all-MiniLM-L6-v2` (ChromaDB default; stored as metadata only — not loaded explicitly).

```python
def __init__(
    self, chroma_dir: str | Path,
    default_results: int = 5,
    similarity_threshold: float = 0.85
)
```

Creates `chroma_dir` if missing. `PersistentClient` with `anonymized_telemetry=False`.

**`find_similar()`** converts cosine distance to similarity as `1 - distance`. Returns Chroma doc ID string if `similarity >= threshold`, else `None`. Short-circuits to `None` if collection is empty.

#### Inputs / Outputs

```python
def add_item(self, item_id: str, content: str, metadata: dict | None = None) -> None
# Upserts — idempotent.

def add_items_batch(self, items: list[dict]) -> int
# Each item: {id, content, metadata?}. Returns count added.

def remove_item(self, item_id: str) -> None   # swallows exceptions

def query(self, query_text: str, n_results: int = 10,
          where: dict | None = None) -> list[dict]
# Returns [{id, content, metadata, distance}, ...]

def sync_from_storage(self, items: list[dict]) -> tuple[int, int]
# Returns (added, removed).

def find_similar(self, text: str, threshold: float | None = None,
                 where: dict | None = None) -> str | None

def count(self) -> int
def health_check(self) -> dict
def delete_collection(self) -> None
```

#### Invariants

- IDs are strings — callers must cast int row IDs with `str()`.
- `find_similar()` returns `None` (never `""` or `False`) — `if storage.find_similar(...)` is safe.
- `sync_from_storage()` upserts all input items; `added` count only reflects genuinely new IDs.

#### Error Handling

- `remove_item()`: bare `except Exception` → logs WARNING.
- `health_check()`: bare `except Exception` → returns `{status: "error", ...}`.
- `sync_from_storage()`: `collection.get()` failure caught, logged, treated as empty existing set.

#### Configuration

| Key | Default |
|-----|---------|
| Collection name | `"intel"` |
| Distance space | `cosine` |
| Default similarity threshold | `0.85` |
| `default_results` attr | `5` (unused by any method) |

#### Caveats

- `default_results` is stored but never used — `query()` defaults to `n_results=10`.

---

### TrendingRadar

**File:** `src/intelligence/trending_radar.py`
**Status:** Experimental

#### Behavior

Computes cross-source trending topics from recent intel items. Two modes: NLP-based (`compute()`) and LLM-based (`compute_llm()`). Persists snapshots to `trending_radar` table; prunes to `MAX_ROWS=20`.

```python
def __init__(self, db_path: str | Path)
# Creates trending_radar table on init.
```

**NLP pipeline (`compute()`):**

1. Fetch up to 2000 items from `intel_items` within `days` window, ordered by `scraped_at DESC`.
2. Detect statistically significant bigram collocations via Dunning log-likelihood (threshold `15.0`).
3. Extract phrases per item from tags + title terms (RAKE-style stopword splitting). Add any detected collocations present in the title.
4. Remove constituent unigrams when their collocation exists as a topic (e.g. if "machine learning" is significant, remove "machine" and "learning" as standalone topics).
5. Gate: topic must have `>= min_source_families` distinct source families AND `>= min_items` total mentions.
6. Score: `0.35 * sublinear_freq + 0.35 * diversity + 0.3 * velocity`.
   - `sublinear_freq = (1 + log(count)) / (1 + log(max_count))`.
   - `diversity = |source_families| / |all_active_families|`.
   - `velocity = min(recent_rate / baseline_rate, 5.0)`, normalized to `[0, 1]` by dividing by 5.
7. Sort by score desc, slice to `max_topics`.

**Source family grouping:** `hackernews` and `producthunt` → `"aggregator"`, `github_trending` → `"github"`, `rss:*` → `"rss"`, others → their raw source name.

**Velocity scoring (`_velocity_score()`):** compares mentions in last `hot_hours=24` vs baseline. Items with only `scraped_at` (no `published`) that all cluster within a 30-min window are batch-spread uniformly across the full look-back to avoid artificial velocity spikes from single scrape runs. Capped at `5.0`.

**LLM pipeline (`compute_llm()`):** sends up to 500 recent items as an article list to a cheap LLM, requests JSON array of `{topic, summary, article_ids}`. Filters out topics with `< 2` resolved article IDs. Falls back to `compute()` on any LLM error.

#### Inputs / Outputs

```python
def compute(
    self, days: int = 7, min_source_families: int = 2, min_items: int = 4,
    max_topics: int = 15, weights: dict | None = None,
    min_sources: int | None = None,  # legacy compat, ignored
) -> dict

def compute_llm(self, llm, days: int = 7, max_topics: int = 10) -> dict

def refresh(self, llm=None, **kwargs) -> dict
# Computes (NLP or LLM), persists snapshot, prunes old rows. Returns snapshot dict.

def load(self) -> dict | None
# Most recent snapshot or None.

def get_or_compute(self, llm=None, **kwargs) -> dict
# Returns cached snapshot if exists, else calls refresh().
```

**Snapshot dict shape:**
```python
{
    "computed_at": str,           # ISO datetime
    "days": int,
    "min_source_families": int,   # NLP only
    "min_items": int,             # NLP only
    "total_items_scanned": int,
    "method": str,                # "nlp" (implicit, absent) or "llm"
    "topics": [
        {
            "topic": str,
            "score": float,       # NLP only
            "item_count": int,
            "source_count": int,
            "sources": list[str],
            "source_families": list[str],
            "velocity": float,    # NLP only
            "summary": str,       # LLM only
            "items": list[dict],  # up to 3 representative items
        }
    ]
}
```

#### Invariants

- `MAX_ROWS=20` snapshots retained; older rows deleted after each `refresh()`.
- `min_sources` parameter in `compute()` is accepted for backward compat but silently ignored — `min_source_families` takes effect.
- Empty intel DB returns a valid snapshot dict with `"topics": []`.

#### Error Handling

- `compute_llm()`: any exception during LLM call or JSON parsing → logs WARNING, falls back to `compute()`.
- `load()`: `json.JSONDecodeError` or `TypeError` → returns `None`.

#### Configuration

| Key | Default |
|-----|---------|
| Days look-back | `7` |
| Min source families | `2` |
| Min item mentions | `4` |
| Max topics | `15` (NLP), `10` (LLM) |
| Score weights | `{freq: 0.35, diversity: 0.35, velocity: 0.3}` |
| Collocation threshold | `15.0` (Dunning score) |
| Velocity hot window | `24` hours |
| Batch cluster window | `30` min |
| LLM article limit | `500` |
| Max stored snapshots | `20` |

#### Caveats

- Velocity scoring can return `1.0` (neutral) when no timestamps are available — not a signal of trending.
- Collocation detection requires `n >= 4` words total across all titles; returns `{}` below this.

---

### GoalIntelMatchStore

**File:** `src/intelligence/goal_intel_match.py`
**Status:** Experimental

#### Behavior

SQLite persistence for goal-intel match results in `goal_intel_matches` table. Deduplicates on `(goal_path, url)` within a 7-day window.

**Schema:**

| Column | Type |
|--------|------|
| `id` | INTEGER PK |
| `goal_path` | TEXT NOT NULL |
| `goal_title` | TEXT NOT NULL |
| `url` | TEXT NOT NULL |
| `title` | TEXT NOT NULL |
| `summary` | TEXT |
| `score` | REAL NOT NULL |
| `urgency` | TEXT NOT NULL (`"high"` / `"medium"` / `"low"`) |
| `match_reasons` | TEXT NOT NULL (JSON array) |
| `created_at` | TIMESTAMP |
| `llm_evaluated` | INTEGER NOT NULL DEFAULT 0 |

Indexes on `goal_path` and `created_at`. `llm_evaluated` column added via idempotent `ALTER TABLE`.

#### Inputs / Outputs

```python
def save_matches(self, matches: list[dict]) -> int
# Returns count inserted. Deduplicates (goal_path, url) within 7 days.

def get_matches(self, goal_paths: list[str] | None = None,
                min_urgency: str | None = None, limit: int = 20) -> list[dict]
# Ordered: urgency (high→medium→low) then score desc.
# match_reasons deserialized from JSON.

def get_latest_match_ts(self) -> datetime | None
# MAX(created_at). Returns UTC-aware datetime.

def cleanup_old(self, days: int = 30) -> int
# Returns count deleted.
```

`get_matches()` urgency filter maps `min_urgency` to a set of allowed values using the order `high(1) < medium(2) < low(3)`.

---

### GoalIntelMatcher

**File:** `src/intelligence/goal_intel_match.py`
**Status:** Experimental

#### Behavior

Keyword + semantic scoring of recent intel against user goals. Keyword matching uses `score_profile_relevance()` from `intelligence.search`. Semantic matching queries `IntelEmbeddingManager`.

```python
def __init__(self, intel_storage: IntelStorage,
             match_store: GoalIntelMatchStore | None = None,
             embedding_manager: IntelEmbeddingManager | None = None)
```

**Keyword extraction (`_extract_goal_keywords()`):** title + tags + goal file body (first 1000 chars) → tokenize `[a-z][a-z0-9\-]+` → filter `_STOPWORDS` (39 words) → prefer longer tokens → cap at 30.

**Urgency thresholds:**

| Score | Urgency |
|-------|---------|
| `>= 0.15` | `"high"` |
| `>= 0.08` | `"medium"` |
| `>= 0.04` | `"low"` |
| `< 0.04` | `None` (filtered) |

**Semantic fusion (`_merge_semantic_into_keyword()`):** `SEMANTIC_WEIGHT=0.4`. For URL overlaps: `blended = kw_score * 0.6 + sem_score * 0.4`. For semantic-only hits: `scaled = sem_score * 0.4`; must pass urgency threshold after scaling. Semantic hits with `sem_score < 0.3` are discarded regardless.

**Adaptive recency window (`_compute_days_window()`):** if `match_store` available, uses days since last match, clamped to `[7, 30]`. Falls back to 30 days on first run (no prior matches).

#### Inputs / Outputs

```python
def match_goal(self, goal: dict, intel_items: list[dict]) -> list[dict]
# Keyword-only match for a single goal. Returns matches above urgency threshold.

def match_all_goals(self, goals: list[dict], days: int | None = None,
                    limit: int = 100) -> list[dict]
# Keyword + optional semantic for all goals. Returns top-100 by score.
```

Match dict shape: `{goal_path, goal_title, url, title, summary (<=300 chars), score, urgency, match_reasons: list[str]}`.

#### Invariants

- `match_all_goals()` fetches up to 500 recent items from `intel_storage.get_recent()`.
- Semantic search is not date-bounded (ChromaDB searches all indexed items).
- `score_profile_relevance` is called with `skills=keywords, goal_keywords=keywords` (same list for both fields) — effective max score ~0.45.

#### Error Handling

- `_semantic_match_goal()`: `embedding_manager.query()` exception → logs WARNING, returns `[]`.
- `_get_item_by_id()`: any exception → returns `None`.
- `_extract_goal_keywords()`: goal file parse exception → silently skips file content.

---

### WatchlistStore

**File:** `src/intelligence/watchlist.py`
**Status:** Experimental

#### Behavior

JSON-backed persistence for user-defined watchlist items. The store is path-scoped so web can use a per-user file under `~/coach/users/{safe_user_id}/`, while CLI and MCP can use a single-user file adjacent to `intel_db`.

**Item shape:**

| Field | Type | Notes |
|------|------|-------|
| `id` | TEXT | Stable opaque id |
| `label` | TEXT | Primary watched entity or theme |
| `kind` | TEXT | e.g. `company`, `person`, `technology`, `theme`, `event`, `role` |
| `aliases` | JSON array | Optional alternate spellings / phrases |
| `why` | TEXT | Optional reason shown in "Why this matters to you" |
| `priority` | TEXT | `high` / `medium` / `low` |
| `tags` | JSON array | Free-form grouping labels |
| `goal` | TEXT | Optional linked goal path or title |
| `time_horizon` | TEXT | e.g. `now`, `quarter`, `year`, `someday` |
| `source_preferences` | JSON array | Optional preferred source names |
| `created_at` | ISO timestamp | UTC |
| `updated_at` | ISO timestamp | UTC |

Normalized label de-duplication is case-insensitive and whitespace-insensitive; save/update performs upsert semantics when the same normalized label already exists.

#### Inputs / Outputs

```python
def list_items(self) -> list[dict]

def save_item(self, item: dict) -> dict

def update_item(self, item_id: str, updates: dict) -> dict | None

def delete_item(self, item_id: str) -> bool
```

Returned items are sorted by `priority` (`high → medium → low`) then `updated_at DESC`.

---

### WatchlistMatcher

**File:** `src/intelligence/watchlist.py`
**Status:** Experimental

#### Behavior

Annotates intel items with watchlist matches and computes a ranking boost.

**Match inputs:** title, summary, first 1000 chars of content, tags, and source name.

**Candidate terms per watchlist item:** `label + aliases + tags` after lowercasing and whitespace normalization.

**Output annotations added to an intel item when matched:**

| Field | Type | Notes |
|------|------|-------|
| `watchlist_matches` | list[dict] | Top matches with `watchlist_id`, `label`, `priority`, `matched_terms`, `why`, `score` |
| `watchlist_score` | float | strongest match score |
| `why_this_matters` | str | uses `why` when present, otherwise synthesizes from `label` + matched terms |

**Ranking rule:** watchlist matches sort ahead of generic items when scores are otherwise close. Route handlers use `(has_watchlist_match, watchlist_score, profile_relevance, recency)` ordering instead of pure recency.

#### Inputs / Outputs

```python
def annotate_items(items: list[dict], watchlist_items: list[dict]) -> list[dict]

def find_evidence_for_text(text: str, annotated_items: list[dict], limit: int = 2) -> list[str]
```

`find_evidence_for_text()` returns short evidence strings suitable for recommendation / insight payloads.

#### Invariants

- Matching is best-effort and deterministic — no LLM calls.
- Multiple watchlist hits on one intel item are preserved, but only the strongest match drives rank ordering.
- Empty watchlists are a no-op; items pass through unchanged.

---

### IntelFollowUpStore

**File:** `src/intelligence/watchlist.py`
**Status:** Experimental

#### Behavior

JSON-backed persistence for saved or annotated intel items. Entries are keyed by intel URL and scoped to the same user path as the watchlist file.

| Field | Type |
|------|------|
| `url` | TEXT |
| `title` | TEXT |
| `saved` | BOOL |
| `note` | TEXT |
| `watchlist_ids` | JSON array |
| `created_at` | ISO timestamp |
| `updated_at` | ISO timestamp |

If `saved=False` and `note` is empty, the entry is removed instead of persisted as inert state.

#### Inputs / Outputs

```python
def get(self, url: str) -> dict | None

def upsert(self, *, url: str, title: str, saved: bool, note: str = "", watchlist_ids: list[str] | None = None) -> dict

def list_items(self) -> list[dict]
```

---

### GoalIntelLLMEvaluator

**File:** `src/intelligence/goal_intel_match.py`
**Status:** Experimental

#### Behavior

LLM-based post-processing of keyword matches to drop false positives and adjust urgency. Processes in batches of `BATCH_SIZE=20`. Uses `create_cheap_provider()`.

**Prompt format:** grouped by `goal_title`, numbered `ITEM_N_RELEVANT: yes|no` / `ITEM_N_URGENCY: high|medium|low|drop`. `"drop"` removes the match entirely.

**`is_available()`** — static method. Checks any env var from `llm.factory._PROVIDER_ENV_KEYS`.

#### Inputs / Outputs

```python
@staticmethod
def is_available() -> bool

def evaluate(self, matches: list[dict]) -> list[dict]
# Returns surviving matches with updated urgency and llm_evaluated=1.
# On batch failure: keeps batch unchanged (no llm_evaluated flag set).
```

#### Error Handling

- Per-batch `except Exception`: logs WARNING, appends batch unchanged (no LLM flag). Does not abort remaining batches.

---

### HeartbeatFilter

**File:** `src/intelligence/heartbeat.py`
**Status:** Experimental

#### Behavior

Scores intel items against goals using keyword overlap + recency + source affinity. Returns items exceeding a composite threshold.

```python
def __init__(self, goals: list[dict], threshold: float = 0.3,
             weights: dict | None = None, preferred_sources: list[str] | None = None)
# Default weights: keyword_overlap=0.35, recency=0.35, source_affinity=0.3
```

Pre-extracts keywords per goal on init (same logic as `GoalIntelMatcher._extract_goal_keywords()` minus file reading — title + tags only, cap 30).

**Recency score:** `max(0.0, 1.0 - hours_since / 48.0)`. Default `0.5` if no `scraped_at`.

**Source affinity:** `1.0` if source in `preferred_sources`, else `0.5`.

**`filter()`:** scores each item against each goal; keeps best-scoring goal match per URL; sorts descending by composite score.

#### Inputs / Outputs

```python
def score_item_against_goal(self, item: dict, goal: dict) -> ScoredItem
def filter(self, items: list[dict]) -> list[ScoredItem]
```

`ScoredItem` fields: `intel_item`, `keyword_score`, `recency_score`, `source_affinity_score`, `composite_score`, `matched_goal_path`, `matched_goal_title`.

---

### HeartbeatEvaluator

**File:** `src/intelligence/heartbeat.py`
**Status:** Experimental

#### Behavior

Optional LLM refinement of `ScoredItem` list → `ActionBrief` list. Falls back to heuristic-only when `budget=0` or LLM unavailable.

```python
def __init__(self, provider=None, budget: int = 5)
```

**Heuristic urgency:** composite `> 0.7` → `"high"`, `> 0.5` → `"medium"`, else `"low"`. Suggested action: `"Review this item"`.

**LLM mode:** batches up to `budget` items. Same `ITEM_N_RELEVANT/URGENCY/ACTION/REASON` structured format as `GoalIntelLLMEvaluator`. Items beyond `budget` get heuristic briefs appended.

`ActionBrief.notification_hash` = SHA-256 of `f"{intel_url}|{related_goal_id}"`, truncated to 16 hex chars.

#### Inputs / Outputs

```python
def evaluate(self, scored_items: list[ScoredItem]) -> list[ActionBrief]
```

#### Error Handling

- LLM call exception → logs WARNING, falls back to heuristic for all items.

---

### ActionBriefStore

**File:** `src/intelligence/heartbeat.py`
**Status:** Experimental

#### Behavior

SQLite persistence for heartbeat notifications and run history.

**`save_briefs()` dedup:** checks `notification_hash` within `cooldown_hours` window (default 4h) before inserting. Returns count saved.

**`dismiss()`** sets `dismissed_at = CURRENT_TIMESTAMP`. Returns `True` if found.

**`get_active()`** returns rows where `dismissed_at IS NULL`, ordered by `created_at DESC`.

#### Inputs / Outputs

```python
def save_briefs(self, briefs: list[ActionBrief], cooldown_hours: int = 4) -> int
def get_active(self, limit: int = 20) -> list[dict]
def dismiss(self, notification_id: int) -> bool
def log_run(self, stats: dict) -> None
def get_last_run_at(self) -> datetime | None
def get_runs(self, limit: int = 10) -> list[dict]
def cleanup_old(self, days: int = 30) -> int
```

---

### HeartbeatPipeline

**File:** `src/intelligence/heartbeat.py`
**Status:** Experimental

#### Behavior

Orchestrates one heartbeat cycle: fetch → filter → evaluate → store. Determines lookback window from last run timestamp.

```python
def __init__(self, intel_storage, goals: list[dict],
             db_path: str | Path, config: dict | None = None)
```

**Lookback:** uses `ActionBriefStore.get_last_run_at()` as `since`; falls back to `now - lookback_hours` (default 2h).

Fetches up to 200 items via `intel_storage.get_items_since(since, limit=200)`.

Returns stats dict: `{started_at, finished_at, items_checked, items_passed, briefs_saved, llm_used}`.

#### Configuration

Config keys (from `heartbeat` section):

| Key | Default |
|-----|---------|
| `heuristic_threshold` | `0.3` |
| `llm_budget_per_cycle` | `5` |
| `notification_cooldown_hours` | `4` |
| `lookback_hours` | `2` |
| `weights.keyword_overlap` | `0.35` |
| `weights.recency` | `0.35` |
| `weights.source_affinity` | `0.3` |
| `preferred_sources` | `[]` |

---

### IntelScheduler

**File:** `src/intelligence/scheduler.py`
**Status:** Stable

#### Behavior

APScheduler `BackgroundScheduler` wrapper. Orchestrates scraper runs, research, recommendations, signal detection, heartbeat, goal-intel matching, trending radar, and weekly summaries.

```python
def __init__(
    self, storage: IntelStorage, config: dict | None = None,
    journal_storage=None, embeddings=None, full_config: dict | None = None,
    on_error: Callable | None = None,
)
```

Delegates: `ResearchRunner` (wraps `DeepResearchAgent`), `RecommendationRunner` (wraps `AdvisorEngine`).

**`_init_scrapers()`** — rebuilds `self._scrapers` list from `config["enabled"]` (default `["hn_top", "rss_feeds"]`). Key behaviors:
- HN skipped if `"hn"` in `rss_covered_sources` (auto-dedup).
- arXiv and Reddit similarly skipped if covered by an RSS feed.
- Semantic dedup: shared `IntelEmbeddingManager` created if `config["semantic_dedup"] = True`, attached to all scrapers.
- User RSS feeds from `web.user_store.get_all_user_rss_feeds()` merged in (silently skipped if web module unavailable).

**`_run_async()`** — runs all scrapers concurrently via `asyncio.gather`. Per scraper:
- Checks `should_skip()` (backoff) first.
- `asyncio.wait_for(scraper.scrape(), timeout=60.0)`.
- Records success/failure to `ScraperHealthTracker`.
- Logs `scraper_run` event to `web.user_store` (best-effort, swallowed on ImportError).
- Returns `{scraped, new, deduped}` dict per source.

Correlation ID (`run_id`) bound to structlog context for entire run, unbound in `finally`.

**`start_with_research()`** registers all jobs. Job schedule defaults:

| Job | Default cron/interval |
|-----|----------------------|
| `intel_gather` | `0 6 * * *` (6am daily) |
| `refresh_capability_model` | same as scrape cron |
| `deep_research` | `0 21 * * 0` (Sun 9pm) |
| `weekly_recommendations` | `0 8 * * 0` (Sun 8am) |
| `signal_detection` | `0 9 * * *` (9am daily) |
| `autonomous_actions` | `0 10 * * *` (10am daily) |
| `trending_radar` | every 6 hours (interval) |
| `heartbeat` | every 30 min (interval) |
| `goal_intel_matching` | `0 */4 * * *` (every 4h) |
| `weekly_summary` | `0 8 * * 1` (Mon 8am) |

`start()` (scrape only) registers just `intel_gather`. `start_with_research()` is the full version.

**`run_now()`** calls `asyncio.run(_run_async())` — sync entry point for the scheduler job.

#### Inputs / Outputs

```python
def run_now(self) -> dict           # {source_name: {scraped, new, deduped} | {error} | {skipped}}
def start(self, cron_expr: str = "0 6 * * *") -> None
def stop(self) -> None
def start_with_research(self, scrape_cron: str = "0 6 * * *",
                        research_cron: str = "0 21 * * 0") -> None

# Delegated methods:
def run_research_now(self, topic: str | None = None) -> list[dict]
def get_research_topics(self) -> list[dict]
def run_recommendations_now(self) -> dict
def run_signal_detection(self) -> list
def run_autonomous_actions(self) -> list
def run_heartbeat(self) -> None
def run_goal_intel_matching(self) -> None
def run_trending_radar(self) -> None
def run_weekly_summary(self) -> None
def refresh_capability_model(self) -> dict
```

#### Invariants

- `_init_scrapers()` is called fresh at the start of each `_run_async()` — scraper list not cached between runs.
- `trending_radar` and `heartbeat` jobs use `coalesce=True, max_instances=1` — skips if previous instance still running.
- `capability_model` refresh only scheduled when `ai_capabilities` or `capability_horizon` enabled.

#### Error Handling

- Per-scraper: `asyncio.TimeoutError` → records `"timeout"` failure. `Exception` → records error string.
- `asyncio.gather` exceptions (should not happen with inner try/except) → logged, counted as `"unknown"` source failure.
- `_default_error_handler`: writes `~/.coach/last_run_status.json` with error details on APScheduler job failure.
- All `run_*` methods: bare `except Exception` → logs ERROR, returns empty/error result. Never raises.

#### Configuration

Key `config` keys (from `sources` section of `config.yaml`):

| Key | Default | Effect |
|-----|---------|--------|
| `enabled` | `["hn_top", "rss_feeds"]` | which scrapers to activate |
| `rss_feeds` | `[]` | list of RSS feed URLs |
| `semantic_dedup` | `False` | enable ChromaDB semantic dedup |
| `semantic_dedup_threshold` | `0.92` | similarity threshold |
| `deduplicate_rss_sources` | `True` | skip dedicated scraper if RSS covers it |
| `github_trending.enabled` | `False` | |
| `arxiv.enabled` | `False` | |
| `reddit.enabled` | `False` | |
| `ai_capabilities.enabled` | `False` | |

Per-scraper config keys follow pattern: `{scraper_key}.enabled`, `{scraper_key}.max_items`, etc. See scheduler source for full list.

---

## Scrapers

All scrapers inherit `BaseScraper`. All `scrape()` methods are decorated with `@http_retry` (tenacity, retries on `HTTPStatusError`/`ConnectError`/`RequestError`). Grouped below by implementation pattern.

### Pattern A: HTML scrape (async fetch → BeautifulSoup)

**HackerNewsScraper** (`sources/hn.py`)
- `source_name`: `"hackernews"` (from `IntelSource.HACKERNEWS`)
- API: `https://hacker-news.firebaseio.com/v0/topstories.json` → top story IDs → concurrent detail fetches via semaphore (`concurrency=10`).
- Tags via `detect_hn_tags()` (from `intelligence.utils`).
- Defaults: `max_stories=30`.
- Skipped by scheduler if `"hn"` is a detected tag in any configured RSS feed URL.

**GitHubTrendingScraper** (`sources/github.py`)
- `source_name`: `"github_trending"`
- Scrapes `https://github.com/trending/{language}?since={timeframe}` via BeautifulSoup.
- Defaults: `languages=["python"]`, `timeframe="daily"`.

**ProductHuntScraper** (`sources/producthunt.py`)
- `source_name`: `"producthunt"`
- Scrapes Product Hunt today page. Defaults: `max_items=20`.

**YCJobsScraper** (`sources/yc_jobs.py`)
- `source_name`: `"yc_jobs"`
- Scrapes YC jobs board. Defaults: `max_items=30`.

**IndeedHiringLabScraper** (`sources/indeed_hiring_lab.py`)
- `source_name`: `"indeed_hiring_lab"`
- Scrapes Indeed Hiring Lab reports. Only emits items where metric change exceeds `change_threshold` (default `5.0`%). Defaults: `max_items=8`.

---

### Pattern B: API / structured feed

**ArxivScraper** (`sources/arxiv.py`)
- `source_name`: `"arxiv"`
- Atom API: `http://export.arxiv.org/api/query` with `sortBy=submittedDate`.
- Parses XML with `xml.etree.ElementTree`.
- Default categories: `["cs.AI", "cs.LG", "cs.CL", "cs.SE"]`. `max_results=30`.
- Skipped by scheduler if `"arxiv"` in `rss_covered_sources`.

**RedditScraper** (`sources/reddit.py`)
- `source_name`: `"reddit"`
- Uses Reddit JSON API (`/r/{sub}/top.json`). No auth required.
- Default subreddits: from profile or config. `limit=25`, `timeframe="day"`.
- Skipped if `"reddit"` in `rss_covered_sources`.

**RSSFeedScraper** (`sources/rss.py`)
- `source_name`: `f"rss:{name}"` where name is extracted from domain.
- Uses `feedparser` to parse Atom/RSS. Async HTTP fetch then `feedparser.parse(content)`.
- Notifies `RSSFeedHealthTracker` on success/failure.
- `_detect_source_tag()` maps known RSS URLs to `"hn"`, `"reddit"`, `"arxiv"`, `"github"` for dedup logic.

**GooglePatentsScraper** (`sources/google_patents.py`)
- `source_name`: `"google_patents"`
- Fetches patent RSS feeds. Default: well-known AI-related patent feeds. `max_per_feed=15`.

**CrunchbaseScraper** (`sources/crunchbase.py`)
- `source_name`: `"crunchbase"`
- Crunchbase API (requires `api_key`). `days_back=7`, `max_items=20`.
- Returns empty list if no API key configured.

**GoogleTrendsScraper** (`sources/google_trends.py`)
- `source_name`: `"google_trends"`
- Uses `pytrends` library. Only emits items where trend spike exceeds `spike_threshold` (default `20.0`). `timeframe="today 1-m"`.

---

### Pattern C: Multi-source aggregator

**EventScraper** (`sources/events.py`)
- `source_name`: `"events"`
- Combines `confs.tech` scraping + optional event RSS feeds.
- Accepts `topics` list and `location_filter` string (loaded from user profile if `location_filter=True` in config).
- `rss_feeds` list from `events.rss_feeds` config key.

**GitHubIssuesScraper** (`sources/github_issues.py`)
- `source_name`: `"github_issues"`
- GitHub REST API. Searches for `good-first-issue` / `help-wanted` labels.
- `languages` from config or user profile `languages_frameworks[:5]`. Auth via `token`.

**AICapabilitiesScraper** (`sources/ai_capabilities.py`)
- `source_name`: `"ai_capabilities"`
- Orchestrates multiple sub-sources: `["metr", "chatbot_arena", "helm"]` by default. `max_items_per_source=10`.

---

### Pattern D: Capability horizon scrapers (always co-scheduled with AICapabilitiesScraper)

Five dedicated scrapers in `sources/ai_capabilities.py`:

| Class | `source_name` | Target |
|-------|---------------|--------|
| `METRScraper` | `"metr"` | METR task complexity evals |
| `EpochAIScraper` | `"epoch_ai"` | Epoch AI compute/training trends |
| `AIIndexScraper` | `"ai_index"` | Stanford AI Index reports |
| `ARCEvalsScraper` | `"arc_evals"` | ARC evals benchmark data |
| `FrontierEvalsGitHubScraper` | `"frontier_evals_github"` | GitHub frontier eval repos (needs `token`) |

All five are instantiated together by `IntelScheduler.refresh_capability_model()` and `_init_scrapers()` when capability horizon is enabled.

---

### CapabilityHorizonModel

**File:** `src/intelligence/capability_model.py`
**Status:** Experimental

#### Behavior

Aggregates scraper output into structured AI capability estimates per domain. Uses a cheap LLM to update domain estimates from raw intel items. Falls back to `_STATIC_FALLBACK` data when LLM unavailable or scrape data insufficient.

**10 capability domains:** `software_engineering`, `data_analysis`, `creative_writing`, `scientific_research`, `legal_reasoning`, `medical_diagnosis`, `customer_service`, `physical_world_interaction`, `long_horizon_planning`, `multimodal_understanding`.

Domain model (Pydantic): `{domain, current_level (0-1), months_to_next_threshold, confidence, key_signals, last_updated}`.

**`refresh(items)`** — passes scraped `IntelItem` list to LLM with structured prompt requesting per-domain JSON updates. Validates with Pydantic. Persists updated domains to `capability_model` table in SQLite. Falls back to static data per domain on parse/validation failure.

#### Inputs / Outputs

```python
def __init__(self, db_path: str | Path)

def refresh(self, items: list[IntelItem]) -> None
# Updates self.domains. LLM call + DB persist.

def get_domain(self, domain: str) -> CapabilityDomain | None
def load(self) -> None  # loads from DB into self.domains
```

#### Error Handling

- LLM call failure → falls back to static data for all domains, logs ERROR.
- Pydantic `ValidationError` per domain → falls back to static for that domain, logs WARNING.

---

## Cross-Cutting Concerns

**Deduplication layers (in order):**
1. URL uniqueness — `UNIQUE` constraint on `intel_items.url` → `INSERT OR IGNORE`.
2. Content hash — `hash_exists()` check before insert (7-day window).
3. Semantic near-duplicate — `IntelEmbeddingManager.find_similar()` + `mark_duplicate()`.

**All three layers must pass** for an item to count as `new_count += 1` in `save_items()`.

**WAL mode:** All SQLite access uses `wal_connect()` from the `db` module. Not thread-safe for concurrent writes from multiple processes (APScheduler runs jobs in threads — single writer at a time via GIL + WAL).

**RSS dedup with dedicated scrapers:** `deduplicate_rss_sources=True` (default) prevents running both an RSS feed covering HN and the `HackerNewsScraper`. Detection via `_detect_source_tag()` matching well-known domains.

**Scraper timeout:** 60 seconds per scraper (in `_run_async()`). Individual HTTP requests time out at 30s (httpx client default).

**Correlation IDs:** `run_id` bound to structlog context for each `_run_async()` call.

---

## Test Expectations

- `IntelStorage.save()`: verify URL dedup, hash dedup, and `duplicate_of` linking all produce correct `None`/`int` returns.
- `IntelStorage.fts_search()`: mock `OperationalError` to verify LIKE fallback.
- `BaseScraper.save_items()`: mock `embedding_manager.find_similar()` to exercise semantic dedup + canonical linking paths.
- `ScraperHealthTracker`: verify backoff formula and `should_skip()` state transitions.
- `TrendingRadar.compute()`: test with synthetic items across multiple sources; verify `min_source_families` gating; verify bigram collocation dedup removes constituent unigrams.
- `_velocity_score()`: test batch-spread normalization (all items in 30-min window) vs genuine velocity (items distributed across window).
- `GoalIntelMatcher.match_all_goals()`: mock `intel_storage.get_recent()` + `embedding_manager.query()`. Verify semantic-only hits, blended hits, and urgency threshold filtering.
- `HeartbeatPipeline.run()`: mock `intel_storage.get_items_since()`, verify lookback falls back to `now - lookback_hours` when no prior run.
- `IntelScheduler._init_scrapers()`: verify `rss_covered_sources` logic disables HN/arXiv/Reddit scrapers when relevant RSS feeds configured.
- All scrapers: mock `httpx.AsyncClient` responses. Test empty response handling. No real HTTP in tests.
- `CapabilityHorizonModel.refresh()`: mock LLM provider. Verify per-domain static fallback on parse failure.

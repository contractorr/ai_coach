# Advisor

## Overview

The advisor module is the LLM orchestration layer. It exposes two modes via `AdvisorEngine.ask()`: classic RAG (single-shot retrieval + LLM call) and agentic (tool-calling loop where the LLM decides what to look up). It owns prompt construction, context assembly, caching, dynamic journal/intel weighting, document-grounded retrieval from the user's Library, and delegates to sub-engines for recommendations, skill analysis, learning paths, and action briefs.

## Dependencies

**Depends on:** `llm`, `journal`, `intelligence`, `profile`, `memory`, `research`, `library`, `cli`
**Depended on by:** `web` (routes call `AdvisorEngine`), `cli` (Click commands call `AdvisorEngine`), `coach_mcp` (MCP tools call advisor sub-components directly)

---

## Components

### AdvisorEngine

**File:** `src/advisor/engine.py`
**Status:** Stable

#### Behavior

Main entry point for advice generation. Constructor creates two LLM instances (expensive + cheap), optionally wires up an `AgenticOrchestrator`, and attaches a `ContextCache` to `rag` if not already set.

```python
def __init__(
    self,
    rag: RAGRetriever,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    client=None,              # injectable for testing
    use_tools: bool = False,
    components: Optional[dict] = None,
    rag_config: dict | None = None,
)
```

**Constructor logic:**

1. Cache attachment: if `rag.cache` is falsy, creates `ContextCache("~/coach/context_cache.db")`. Failure is silently swallowed.
2. LLM init: `create_llm_provider(...)` → `self.llm`; `create_cheap_provider(...)` → `self.cheap_llm`. `BaseLLMError` is re-raised as `APIKeyMissingError`.
3. Orchestrator init: only when `use_tools=True AND components is not None`. Builds goals summary (up to 8 active goals, formatted as `"- {title} ({status}, {pct}% done{stale}) — {fname}"`), calls `PromptTemplates.build_agentic_system(goals_summary)`, constructs `AgenticOrchestrator`. Broken goals are silently swallowed.

**`ask()` dispatch:**

- If `self._orchestrator` is set → delegates entirely to `AgenticOrchestrator.run()`. `advice_type`, `include_research` are ignored in agentic mode.
- Otherwise → classic RAG mode.

**Classic RAG mode decision tree:**

`use_extended` is `True` when any of `structured_profile`, `inject_memory`, `inject_recurring_thoughts`, `inject_documents`, `xml_delimiters` are truthy in `_rag_config`, or when the current turn supplies `attachment_ids`.

| `use_extended` | Research available | Method |
|---|---|---|
| False | any | `rag.get_combined_context()` + `get_profile_context()` + `get_prompt(advice_type)` |
| True | any | `rag.build_context_for_ask()` + `get_prompt("general", extended=True, xml_delimiters=..., with_research=...)` |

Research context: fetched via `rag.get_research_context(question)` only if `include_research=True` and `rag` has `get_research_context`. Passed to prompt only if non-empty after strip.

When `attachment_ids` are provided, document-grounded retrieval should be treated as first-class context assembly rather than optional post-processing. The current-turn attachment set is the highest-priority document source.

In non-extended mode, `profile_ctx` is prepended to `journal_context` slot: `profile_ctx + journal_ctx`.

#### Inputs / Outputs

```python
def ask(
    self,
    question: str,
    advice_type: str = "general",      # general, career, goals, opportunities
    include_research: bool = True,
    attachment_ids: list[str] | None = None,
    conversation_history: list[dict] | None = None,
    event_callback: Callable[[dict], None] | None = None,
) -> str

def weekly_review(self, journal_storage=None) -> str
def detect_opportunities(self) -> str
def analyze_goals(self, specific_goal: Optional[str] = None) -> str
def analyze_skill_gaps(self) -> str
def generate_milestones(
    self,
    goal_path: Path,
    journal_storage: JournalStorage | None = None,
) -> list[str]
# Deprecated — will be removed in Phase 2:
# def generate_learning_path(
#     self, skill, lp_dir, current_level, target_level,
# ) -> Path
def generate_recommendations(
    self,
    category: str,           # learning, career, entrepreneurial, investment, all
    db_path: Path,
    config: Optional[dict] = None,
    max_items: int = 3,
) -> list
def generate_action_brief(
    self,
    db_path: Path,
    journal_storage=None,
    max_items: int = 5,
    min_score: float = 6.0,
    save: bool = False,
) -> str
```

**`weekly_review()` context:**
- `rag.get_recent_entries(days=7)` — journal
- `rag.get_intel_context("weekly industry trends", max_chars=2000)` — intel
- Optional stale goals (up to 5) appended to journal slot
- `rag.get_recurring_thoughts_context()` appended to journal slot
- `rag.get_profile_context()` prepended to journal slot
- Uses `PromptTemplates.WEEKLY_REVIEW`, `max_tokens=1500`

**`detect_opportunities()` context:**
- Journal: `get_journal_context("skills interests goals projects work", max_entries=8, max_chars=5000)`
- Intel: `get_intel_context("opportunities trends hiring funding", max_chars=3000)`
- Profile prepended to journal slot
- Uses `PromptTemplates.OPPORTUNITY_DETECTION`

**`analyze_goals()` context:**
- Journal: `get_journal_context(query, max_chars=6000)` — query is `specific_goal` or `"goals objectives targets plans"`
- Uses `PromptTemplates.GOAL_ANALYSIS`

**`generate_recommendations(category="all")`:**
- Calls `engine.generate_all(max_per_category=max_items)`, flattens all category lists, sorts by `score` descending.

#### Invariants

- `self.llm` and `self.cheap_llm` are always set after successful construction or `APIKeyMissingError` is raised.
- `self._orchestrator` is `None` when `use_tools=False` or `components` is `None`.
- `rag.cache` is attached if not already present; failure does not prevent construction.
- Not thread-safe for concurrent `ask()` calls sharing one instance.

#### Error Handling

- `BaseLLMError` during LLM init → `APIKeyMissingError` (re-raised, callers must handle).
- `_call_llm` / `_call_cheap_llm`: wraps `BaseLLMError` as `LLMError`; decorated with `@_llm_retry` (3 attempts, `wait_exponential(min=2, max=30)`, on `LLMRateLimitError` and `BaseLLMError`).
- Goals summary build failures silently swallowed (broken goals must not prevent startup).
- Cache attachment failure silently swallowed.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `rag_config.structured_profile` | `False` | caller |
| `rag_config.inject_memory` | `False` | caller |
| `rag_config.inject_recurring_thoughts` | `False` | caller |
| `rag_config.inject_documents` | `False` outside document-aware surfaces | caller |
| `rag_config.xml_delimiters` | `False` | caller |
| LLM retry attempts | `3` | `cli.retry.llm_retry` |
| LLM retry wait min | `2.0` s | hardcoded |
| LLM retry wait max | `30.0` s | hardcoded |
| cache path | `~/coach/context_cache.db` | hardcoded |
| goals summary cap | `8` | hardcoded |
| stale goals cap | `5` | hardcoded |

---

### RAGRetriever

**File:** `src/advisor/rag.py`
**Status:** Stable

#### Behavior

Assembles LLM context from journal, intel, memory, recurring thoughts, research, and Library documents. Wraps `JournalSearch`, optionally `IntelSearch`, and a user-scoped Library retrieval layer. All retrieval results are cached via `ContextCache` (if set). Dynamic journal/intel budget splitting via `compute_dynamic_weight()`.

```python
def __init__(
    self,
    journal_search: JournalSearch,
    intel_db_path: Optional[Path] = None,
    intel_search: Optional[IntelSearch] = None,
    max_context_chars: int = 8000,
    journal_weight: float = 0.7,
    profile_path: Optional[str] = None,    # default: "~/coach/profile.yaml"
    users_db_path: Optional[Path] = None,
    user_id: Optional[str] = None,
    cache=None,
    fact_store=None,
    memory_config: Optional[dict] = None,
    thread_store=None,
    library_index=None,
)
```

#### Inputs / Outputs

```python
def get_profile_context(self, structured: bool = False) -> str
# structured=False → "\nUSER PROFILE: {profile.summary()}\n"
# structured=True  → "\n{profile.structured_summary()}\n"
# Returns "" on any exception

def get_profile_keywords(self) -> list[str]
# Skills[:8] names + languages[:6] + technologies_watching[:6]
# + industries[:4] + interests[:4] + active_projects[:3] (first 3 words each)
# Returns [] on any exception

def build_context_for_ask(
    self,
    query: str,
    rag_config: dict | None = None,
    attachment_ids: list[str] | None = None,
) -> AskContext
# AskContext fields: journal, intel, profile, memory="", thoughts="", documents=""
# Flags: structured_profile, inject_memory, inject_recurring_thoughts, inject_documents, xml_delimiters

def get_journal_context(
    self, query: str, max_entries: int = 5, max_chars: int = 6000,
    entry_type: Optional[str] = None,
) -> str
# Delegates to journal_search.get_context_for_query(); cached by (type="journal", query, max_entries, max_chars)

def get_intel_context(
    self, query: str, max_items: int = 5, max_chars: int = 3000,
) -> str
# Uses IntelSearch if available, else keyword fallback on SQLite; cached by (type="intel", query, max_items, max_chars)

def get_filtered_intel_context(
    self, query: str, max_items: int = 5, max_chars: int = 3000, min_relevance: float = 0.05,
) -> str
# Two-stage: profile-augmented retrieval → re-rank by profile term overlap
# Falls back to get_intel_context if intel_search not set or profile empty

def get_combined_context(
    self, query: str, journal_weight: Optional[float] = None,
) -> tuple[str, str]
# Returns (journal_ctx, intel_ctx)
# Weight priority: explicit arg > compute_dynamic_weight() (if users_db_path+user_id set) > self.journal_weight
# journal_chars = int(total * weight); intel_chars = total - journal_chars
# Combined result cached by (type="combined", query, weight, total_chars)

def compute_dynamic_weight(self, user_id: Optional[str] = None) -> float
# Reads engagement_events from users DB (last 30 days)
# Formula: 0.7 + 0.15 * (journal_ratio - 0.5), clamped [0.5, 0.85]
# Falls back to self.journal_weight if <10 total events or on any exception

def get_memory_context(self, query: str = "") -> str
# Returns <user_memory> XML block or ""
# Merges: high_confidence_facts (>= threshold) + semantic search results, dedup by ID, cap at max_facts
# Returns "" if no fact_store

def get_document_context(
    self, query: str, attachment_ids: list[str] | None = None, max_items: int = 4, max_chars: int = 4000,
) -> str
# Returns <user_documents> XML block or ""
# Prioritizes explicit attachment_ids first, then falls back to Library search for relevant indexed documents
# Uses title / filename / snippet blocks, bounded by max_chars

def get_recurring_thoughts_context(self, max_threads: int = 3) -> str
# Returns <recurring_thoughts> XML block or ""
# Threads sorted by recent_count (entries in last 30 days), top 3
# Returns "" if all top threads have recent_count == 0

def get_recent_entries(self, days: int = 7, max_chars: int = 6000) -> str
# list_entries(limit=20), filters by ISO created >= cutoff
# Format per entry: "--- {title} ({type}) ---\n{content}\n"
# Returns "No journal entries from the past week." if none

def get_research_context(
    self, query: str, max_entries: int = 3, max_chars: int = 4000,
) -> str
# entry_type="research"; semantic_search if available, else most-recent fallback
# Per entry: "[Research: {title}]\n{content[:1500]}\n"
# Returns "" if no research entries

def get_full_context(self, query: str, include_research: bool = True) -> tuple[str, str, str]
# Returns (journal_ctx, intel_ctx, research_ctx)

def get_capability_context(self) -> str
# Loads CapabilityHorizonModel from intel_db_path; returns "" on failure

def get_ai_capabilities_context(self, query: str, max_chars: int = 1500) -> str
# Static KB summary (~500 chars) + intel search for "AI capabilities benchmarks..."
# Intel section only added if remaining > 100 chars and result doesn't start with "No"
```

**`AskContext` dataclass:**

```python
@dataclass
class AskContext:
    journal: str
    intel: str
    profile: str
    memory: str = ""
    thoughts: str = ""
    documents: str = ""
```

**`_format_memory_block()` display order:**
`Current Context → Goal Context → Preferences → Skills → Constraints → Patterns`
Within each section: sorted by `confidence` descending.

**`get_intel_context()` keyword fallback logic:**
1. `LIKE` search on `title` and `summary` with `%{query}%`, order by `scraped_at DESC`, limit `max_items * 2`.
2. If no results → fallback: most recent `max_items` rows with no filter.
3. Items truncated at `max_chars` (cumulative), summary preview `[:200]`.

**`compute_dynamic_weight()` engagement events:**
- Positive events: `{"opened", "saved", "acted_on", "feedback_useful"}`
- `journal_ratio = journal_score / (journal_score + intel_score)`
- Returns `self.journal_weight` if denom == 0 or total < 10

#### Invariants

- Cache keys are SHA256 hashes; collisions are theoretically possible but not guarded against.
- `get_combined_context()` combined cache stores JSON `{"journal": ..., "intel": ...}`; individual `get_journal_context()` and `get_intel_context()` calls inside it also write their own cache entries.
- Document retrieval cache keys must include the explicit `attachment_ids` set when present, otherwise current-turn uploads can collide with generic query-only cache entries.
- Not thread-safe for concurrent writes to the same cache db.
- `intel_db_path` is expanded with `.expanduser()` at construction; `None` stays `None`.

#### Error Handling

- `get_profile_context`: any exception → debug log, returns `""`.
- `get_profile_keywords`: any exception → returns `[]`.
- `get_memory_context`: any exception → debug log, returns `""`.
- `get_document_context`: any exception → debug log, returns `""`.
- `get_recurring_thoughts_context`: any exception → debug log, returns `""`.
- `get_recent_entries`: per-entry `(OSError, ValueError)` → warning log, skip entry.
- `get_research_context`: per-entry `(OSError, ValueError)` → warning log, skip entry.
- `get_intel_context` keyword fallback: `sqlite3.OperationalError` → returns `"No external intelligence available."`.
- `compute_dynamic_weight`: any exception → debug log, returns `self.journal_weight`.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `max_context_chars` | `8000` | constructor |
| `journal_weight` | `0.7` | constructor |
| `profile_path` | `"~/coach/profile.yaml"` | constructor |
| document retrieval max items | `4` | retrieval helper |
| document retrieval max chars | `4000` | retrieval helper |
| dynamic weight min | `0.5` | hardcoded |
| dynamic weight max | `0.85` | hardcoded |
| dynamic weight formula slope | `0.15` | hardcoded |
| engagement lookback | `30 days` | hardcoded |
| min events for dynamic weight | `10` | hardcoded |
| memory `max_context_facts` | `25` | `memory_config` |
| memory `high_confidence_threshold` | `0.9` | `memory_config` |
| recurring threads max | `3` | `get_recurring_thoughts_context` param |
| recent entries limit | `20` | hardcoded |
| research content preview | `1500` chars | hardcoded |
| AI KB budget | `1500` chars | param default |

---

### AgenticOrchestrator

**File:** `src/advisor/agentic.py`
**Status:** Stable

#### Behavior

Runs a synchronous LLM tool-calling loop. On each iteration, calls `llm.generate_with_tools()`; if the response has `finish_reason == "stop"` or no tool calls, returns the content. Otherwise, appends the assistant + tool result messages and continues. Stops after `max_iterations` and returns whatever content is available, or a fallback string.

```python
def __init__(
    self,
    llm: LLMProvider,
    registry: ToolRegistry,
    system_prompt: str,
    max_iterations: int = 10,
)
```

#### Inputs / Outputs

```python
def run(
    self,
    user_message: str,
    conversation_history: list[dict] | None = None,
    event_callback: Callable[[dict], None] | None = None,
) -> str
```

**Message construction per iteration:**

1. Start: `messages = list(conversation_history or []) + [{"role": "user", "content": user_message}]`
2. LLM responds with `ToolCallResponse(finish_reason, content, tool_calls)`.
3. If stopping: fire `event_callback({"type": "answer", "content": content})`, return `content or ""`.
4. If tool calls: append assistant message `{"role": "assistant", "tool_calls": [...], "content": ...}` (content only included if non-empty).
5. For each tool call: fire `event_callback({"type": "tool_start", "tool": name})`, execute via `registry.execute()`, detect error via `'"error"' in result_text[:50]`, fire `event_callback({"type": "tool_done", ...})`, append `{"role": "tool", "tool_call_id": id, "name": name, "content": result_text, "is_error": bool}`.

**Max iterations fallback:** returns `response.content` if set, else `"I wasn't able to complete that request within the allowed steps."`.

#### Invariants

- `event_callback` is always optional; its absence does not change control flow.
- Tool calls within one iteration are executed sequentially (not concurrently).
- `response.content` in the assistant message is only included when non-falsy.

#### Error Handling

- Tool execution errors are captured by `ToolRegistry.execute()` and returned as `{"error": ...}` JSON — the loop continues.
- LLM errors from `generate_with_tools()` propagate out of `run()` uncaught.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `max_iterations` | `10` | constructor |

---

### ToolRegistry

**File:** `src/advisor/tools.py`
**Status:** Stable

#### Behavior

Registers and dispatches all tools available to `AgenticOrchestrator`. Initialized with a per-user `components` dict. All handlers are closures capturing components at registration time. Tool results are truncated to `TOOL_RESULT_MAX_CHARS = 4000`. Document-aware advisor flows should expose Library search/read capabilities through this same registry.

```python
def __init__(self, components: dict)
# components keys: storage, embeddings, intel_storage, rag, profile_path,
#                  recommendations_dir, library_index, user_id (optional)
```

**`_register_all()` registers 7 tool groups:**
`_register_journal_tools`, `_register_goal_tools`, `_register_intel_tools`,
`_register_library_tools`, `_register_rss_tools`, `_register_web_search_tools`, `_register_misc_tools`

#### Inputs / Outputs

```python
def get_definitions(self) -> list[ToolDefinition]
def execute(self, name: str, arguments: dict) -> str   # JSON string, truncated to 4000 chars
```

**Registered tools (19 total target shape):**

| Tool | Group | Key params | Notes |
|------|-------|-----------|-------|
| `journal_search` | journal | `query`, `limit=5` | semantic search via `embeddings.query()`; content `[:300]` |
| `journal_list` | journal | `entry_type`, `tag`, `limit=20` | preview `[:300]` |
| `journal_read` | journal | `filename` | path traversal check; reads `journal_dir / filename` |
| `journal_create` | journal | `content`, `entry_type="daily"`, `title`, `tags` | syncs embeddings after create; embed errors swallowed |
| `goals_list` | goal | `include_inactive=False` | enriched with `get_progress()`; preview `[:200]` |
| `goals_add` | goal | `title`, `description`, `check_days=14`, `tags` | writes `check_in_days` to frontmatter only if `!= 14` |
| `goals_check_in` | goal | `goal_path`, `notes` | calls `tracker.check_in_goal()` |
| `goals_update_status` | goal | `goal_path`, `status` | enum: active/paused/completed/abandoned |
| `goal_next_steps` | goal | `goal_path` | path traversal check; returns progress + intel matches (limit 5) + related journal (limit 5, excludes `type=goal`) |
| `intel_search` | intel | `query`, `limit=10` | keyword search; summary `[:500]` |
| `intel_get_recent` | intel | `days=7`, `limit=50`, `source` | source filter applied in Python after fetch |
| `library_search` | library | `query`, `limit=5`, `source_kind` | searches indexed Library text, returns snippets |
| `library_read` | library | `report_id`, `max_chars=2000` | returns bounded body or extracted text for one item |
| `intel_list_rss_feeds` | rss | — | only registered if `user_id` in components |
| `intel_add_rss_feed` | rss | `url`, `name`, `reason` | validates scheme (http/https), fetches + checks `<rss`/`<feed`/`<channel` in first 2048 bytes, persists, one-shot scrape |
| `web_search` | web | `query`, `max_results=5` | mutates `search_client.max_results`; content `[:500]` |
| `recommendations_list` | misc | `limit=20`, `category`, `status` | `list_by_category` if category else `list_recent(days=90)` |
| `profile_get` | misc | — | returns `summary()` + `is_stale()` |
| `get_context` | misc | `query`, `max_chars=8000` | calls `rag.get_combined_context()`; both sliced to `max_chars` |

**`intel_add_rss_feed` validation details:**
- URL scheme check: `parsed.scheme not in ("http", "https")` → `{"error": ...}`
- Feed validity: checks lowercase first 2048 bytes for `<rss`, `<feed`, `<channel`
- HTTP errors: returns `{"error": f"Failed to fetch feed: {e}"}` on `httpx.HTTPError`
- One-shot scrape failure is warned but not propagated; `items_scraped=0` returned

**`journal_read` / `goal_next_steps` path traversal guard:**
`filepath.resolve().relative_to(journal_dir.resolve())` — raises `ValueError` → returns `{"error": "Invalid path"}`

#### Invariants

- `_register_rss_tools()` is a no-op if `user_id` not in `components`.
- `web_search` creates a single `WebSearchClient()` at registration time (shared across calls).
- `goals_add` only writes `check_in_days` frontmatter field when the value differs from the default `14`.
- Result truncation is applied after `json.dumps()`, meaning JSON may be syntactically invalid after truncation.

#### Error Handling

- `execute()`: any exception in handler → `logger.error`, returns `json.dumps({"error": str(e)})`.
- Unknown tool name → returns `json.dumps({"error": f"Unknown tool: {name}"})`.
- `journal_create` embed sync: bare `except Exception` → silently swallowed.
- `goals_add` embed sync: bare `except Exception` → silently swallowed.
- `goal_next_steps` intel + journal sub-fetches: bare `except Exception` → silently swallowed, fields return `[]`.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `TOOL_RESULT_MAX_CHARS` | `4000` | module constant |
| journal search content preview | `300` chars | hardcoded |
| goal intel match limit | `5` | hardcoded |
| goal related journal limit | `5` | `embeddings.query(n_results=5)` |
| RSS feed snippet check | `2048` bytes | hardcoded |
| web search content preview | `500` chars | hardcoded |
| recommendations list default days | `90` | hardcoded |

---

### InsightStore

**File:** `src/advisor/insights.py`
**Status:** Experimental

#### Behavior

SQLite-backed store for proactive insights. Persists to the `insights` table in `~/coach/intel.db`. Deduplicates on content hash at save time. TTL-based expiry (14 days default) with no acknowledge step — insights simply expire.

```python
class InsightType(str, Enum):
    topic_emergence      = "topic_emergence"
    goal_stale           = "goal_stale"
    goal_complete        = "goal_complete"
    deadline_urgent      = "deadline_urgent"
    journal_gap          = "journal_gap"
    learning_stalled     = "learning_stalled"
    research_trigger     = "research_trigger"
    recurring_blocker    = "recurring_blocker"
    pattern_blind_spot   = "pattern_blind_spot"
    pattern_blocker_cycle = "pattern_blocker_cycle"
    intel_match          = "intel_match"
```

#### Inputs / Outputs

```python
def save(self, insight: dict) -> None
# Computes SHA256 hash of (type + title + description); skips insert on collision (dedup).
# Sets created_at = now(); expires_at = now() + ttl_days * 86400.

def get_active(
    self,
    type: InsightType | None = None,
    min_severity: int = 1,
    limit: int = 20,
) -> list[dict]
# Returns insights where expires_at > now() and severity >= min_severity.
# Optional type filter. Ordered by severity DESC, created_at DESC.
```

#### Invariants

- No acknowledge — insights are read-only after save; removal is TTL-only.
- Hash dedup operates on (type, title, description) only; different severity for the same insight is silently dropped.
- `get_active()` never returns expired rows; expiry is enforced at query time via `WHERE expires_at > ?`.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `ttl_days` | `14` | constructor |
| `db_path` | `~/coach/intel.db` | constructor |

---

### ContextCache

**File:** `src/advisor/context_cache.py`
**Status:** Stable

#### Behavior

SQLite-backed key/value cache with TTL. Keys are SHA256 hashes. Uses WAL mode via `wal_connect`. Schema initialized on construction.

```python
def __init__(self, db_path, default_ttl: int = 86400)
# Creates context_cache table: (key TEXT PK, value TEXT, created_at REAL)
```

#### Inputs / Outputs

```python
def get(self, cache_key: str, ttl: int | None = None) -> str | None
# Returns value if not expired; deletes and returns None if expired
# ttl overrides default_ttl for this lookup if provided

def set(self, cache_key: str, value: str)
# UPSERT: ON CONFLICT DO UPDATE value + created_at

def make_key(self, context_type: str, query: str, **params) -> str
# SHA256 of JSON {"type": context_type, "query": query, **params} (sort_keys=True)

def invalidate(self, cache_key: str)
# Public alias for _delete()

def invalidate_by_prefix(self, prefix: str)
# DELETE FROM context_cache WHERE key LIKE '{prefix}%'

def clear_expired(self)
# DELETE WHERE created_at < time.time() - default_ttl

def _delete(self, cache_key: str)
# Internal: called on expired get
```

**TTL check:** `time.time() - created_at > self.default_ttl` — lazy deletion on read; no background sweep.

#### Invariants

- `set()` always updates `created_at` to current time on upsert.
- Expiry is checked per `get()` call; stale entries accumulate until `clear_expired()` or a matching `get()`.
- `make_key()` is deterministic for the same inputs (sort_keys=True, no randomness).

#### Error Handling

- No explicit error handling; SQLite errors propagate to caller.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `default_ttl` | `86400` s (24h) | constructor |

---

### PromptTemplates

**File:** `src/advisor/prompts.py`
**Status:** Stable

#### Behavior

Pure class of string constants and factory methods. No state. All templates use Python `.format()` substitution with named slots.

**Templates inventory:**

| Name | Slots | Used by |
|------|-------|---------|
| `SYSTEM` | — | `_call_llm` system arg |
| `CAREER_ADVICE` | journal_context, intel_context, question | `ask(advice_type="career")` |
| `WEEKLY_REVIEW` | journal_context, intel_context | `weekly_review()` |
| `GOAL_ANALYSIS` | journal_context, question | `analyze_goals()` |
| `OPPORTUNITY_DETECTION` | journal_context, intel_context | `detect_opportunities()` |
| `GENERAL_ASK` | journal_context, intel_context, research_context, question | `ask()` non-extended |
| `GENERAL_ASK_WITH_RESEARCH` | same | `ask()` non-extended + research |
| `GENERAL_ASK_EXTENDED` | profile_context, journal_context, intel_context, memory_context, thoughts_context, research_context, question | `ask()` extended |
| `GENERAL_ASK_EXTENDED_WITH_RESEARCH` | same | extended + research |
| `GENERAL_ASK_XML` | same (XML-wrapped) | extended + xml_delimiters |
| `GENERAL_ASK_XML_WITH_RESEARCH` | same | extended + xml_delimiters + research |
| `UNIFIED_RECOMMENDATIONS` | profile_context, journal_context, intel_context, category, max_items | `RecommendationEngine` |
| `UNIFIED_RECOMMENDATIONS_WITH_AI` | + ai_capabilities_section | `RecommendationEngine` with AI context |
| `TOP_PICKS` | profile_context, all_recommendations, max_picks, weekly_hours, rank, category, title, original_score | `RecommendationEngine` |
| `WEEKLY_ACTION_BRIEF` | journal_context, intel_context, recommendations, date | `ActionBriefGenerator` |
| `ACTION_PLAN` | title, category, description, rationale, journal_context | `RecommendationEngine` |
| `INTEL_CONTRADICTION_CHECK` | title, description, rationale, recent_intel | `RecommendationEngine` |
| `ADVERSARIAL_CRITIC` | profile_context, title, description, rationale, premortem, intel_summary, intel_contradictions | `RecommendationEngine` |
| `TOP_PICK_CONTRARIAN` | profile_context, title, description, rationale, critic_challenge, recent_intel | `RecommendationEngine` |
| `AGENTIC_SYSTEM` | — | legacy/unused (superseded by `build_agentic_system()`) |
| `AI_CAPABILITIES_SECTION` | ai_capabilities_context | injected into `UNIFIED_RECOMMENDATIONS_WITH_AI` |
| `SKILL_GAP_ANALYSIS` | profile_context, journal_context | `SkillGapAnalyzer` (also used as advisor prompt mode) |
| `MILESTONE_GENERATION` | goal_title, goal_content, goal_type, profile_context | `AdvisorEngine.generate_milestones()` |
| `LEARNING_PATH_GENERATION` | profile_context, skill_name, current_level, target_level, learning_style, weekly_hours | DEPRECATED — replaced by `MILESTONE_GENERATION` for `type="learning"` goals |
| `PROJECT_RECOMMENDATIONS` | journal_context, intel_context | `RecommendationEngine` |
| `SIDE_PROJECT_IDEAS` | profile_context, journal_context | `RecommendationEngine` |
| `EVENT_RECOMMENDATIONS` | journal_context, intel_context | `RecommendationEngine` |
| `CHECK_IN_ANALYSIS` | skill, module_number, module_title, action, check_in_history, completed, total | DEPRECATED — `LearningPathGenerator` removed |
| `DEEP_DIVE_GENERATION` | skill, module_title, module_content | DEPRECATED — `LearningPathGenerator` removed |

#### Inputs / Outputs

```python
@classmethod
def get_prompt(
    cls,
    prompt_type: str,          # career, weekly_review, goals, opportunities, general, action_plan
    with_research: bool = False,
    xml_delimiters: bool = False,
    extended: bool = False,
) -> str
# Selection logic:
# 1. If type="general" AND extended=True:
#    - xml_delimiters + research → GENERAL_ASK_XML_WITH_RESEARCH
#    - xml_delimiters           → GENERAL_ASK_XML
#    - research                 → GENERAL_ASK_EXTENDED_WITH_RESEARCH
#    - otherwise                → GENERAL_ASK_EXTENDED
# 2. If type="general" AND with_research=True (not extended): → GENERAL_ASK_WITH_RESEARCH
# 3. Otherwise: lookup in dict; unknown types → GENERAL_ASK

@classmethod
def build_agentic_system(cls, goals_summary: str = "") -> str
# Base coaching-oriented system prompt; appends "\n\nACTIVE GOALS:\n{goals_summary}" if non-empty

@classmethod
def _build_user_prompt(
    cls,
    *,
    template: str,
    journal_context: str,
    intel_context: str,
    profile_context: str = "",
    memory_context: str = "",
    thoughts_context: str = "",
    research_context: str = "",
    question: str,
) -> str
# Calls template.format(**kwargs), then collapses 3+ consecutive newlines to 2
```

**`UNIFIED_RECOMMENDATIONS` scoring formula** (documented in template):
`SCORE = 0.5 * RELEVANCE + 0.2 * FEASIBILITY + 0.3 * IMPACT`

Recs with `RELEVANCE < 6` are skipped by the LLM per prompt instruction.

#### Invariants

- All methods are classmethods; no instance state.
- `_build_user_prompt` is non-destructive: collapses whitespace but does not strip leading/trailing newlines.
- `get_prompt` falls back to `GENERAL_ASK` for unknown `prompt_type` values.

#### Caveats

- `xml_delimiters=True` only affects `extended=True` + `type="general"` path; ignored for all other types.
- `with_research=True` on non-general types has no effect (dict lookup returns the non-research template).
- `AGENTIC_SYSTEM` constant is superseded by `build_agentic_system()` and not used in production paths.

---

## Cross-Cutting Concerns

**Dual-LLM pattern:**
`AdvisorEngine` maintains two LLM instances. `self.llm` (expensive) handles primary advice generation. `self.cheap_llm` (cheap) handles critic/scoring in `RecommendationEngine` via `cheap_llm_caller`. Both share the same `provider`, `api_key` but use different model tiers via `create_cheap_provider()`.

**Mode selection summary:**

| Condition | Mode | Entry point |
|-----------|------|-------------|
| `use_tools=True` AND `components` provided | Agentic | `AgenticOrchestrator.run()` |
| Any `rag_config` flag set, or `attachment_ids` present | Extended RAG | `rag.build_context_for_ask()` |
| Default | Classic RAG | `rag.get_combined_context()` |

**Caching layers:**

| Layer | Scope | TTL |
|-------|-------|-----|
| `ContextCache` | per (type, query, params) | 24h |
| Combined cache | `get_combined_context` | 24h (same cache) |
| Document cache | `get_document_context` by query + attachment set | 24h (same cache namespace) |

**Error class hierarchy:**
```
AdvisorError
├── APIKeyMissingError  (LLM init failure)
└── LLMError            (LLM call failure, wrapped from BaseLLMError)
```

---

## Test Expectations

- `AdvisorEngine.ask()` in classic mode: mock `rag.get_combined_context()` + `rag.get_profile_context()`; verify prompt contains journal/intel sections; verify `_call_llm` called with `PromptTemplates.SYSTEM`.
- `AdvisorEngine.ask()` extended mode: set any `rag_config` flag or provide `attachment_ids`; verify `build_context_for_ask(..., attachment_ids=...)` called; verify correct template variant selected.
- `AdvisorEngine.ask()` agentic mode: set `use_tools=True` + `components`; verify `AgenticOrchestrator.run()` called; verify `advice_type` is ignored.
- `APIKeyMissingError` raised on LLM init failure: mock `create_llm_provider` to raise `BaseLLMError`.
- `RAGRetriever.compute_dynamic_weight()`: requires mock `users_db_path` with engagement data; verify formula clamps to [0.5, 0.85]; verify fallback on < 10 events.
- `RAGRetriever.get_memory_context()`: mock `fact_store`; verify high-conf + semantic merge + dedup; verify empty string when no facts.
- `RAGRetriever.get_document_context()`: mock `library_index`; verify explicit attachments are prioritized, snippets are bounded, and empty string is returned on failure.
- `RAGRetriever.get_combined_context()` cache hit: set cache, verify no downstream calls.
- `ContextCache`: verify TTL expiry on `get()`; verify upsert updates `created_at`; verify `make_key()` is deterministic.
- `AgenticOrchestrator.run()`: mock LLM to return tool call then stop; verify message sequence; verify `event_callback` fired; verify max-iterations fallback.
- `ToolRegistry.execute()`: unknown tool → error JSON; exception in handler → error JSON; result truncated at 4000 chars.
- `ToolRegistry` library tools: wrong-user or missing `report_id` should return structured error JSON rather than raw tracebacks.
- `ToolRegistry` `journal_read` / `goal_next_steps`: path traversal attempt → `{"error": "Invalid path"}`.
- `ToolRegistry` `intel_add_rss_feed`: non-http scheme → error; feed without RSS markers → error; HTTP failure → error.
- Mocks required: `LLMProvider`, `JournalSearch`, `IntelSearch`, `EmbeddingManager`, `JournalStorage`, `IntelStorage`, `FactStore`, `ThreadStore`, `httpx.Client` (for RSS validation).


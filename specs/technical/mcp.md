# MCP Server

## Overview

The `coach_mcp` package exposes 40 tools across 12 modules via a stdio-transport MCP server named `"stewardme"`. Tools are loaded lazily on first use and dispatched synchronously. The server enforces a strict no-LLM-in-MCP-layer rule: all reasoning is delegated to the calling Claude Code instance; the MCP layer only retrieves data and returns raw context. The one exception is `research_run`, which transitively invokes an LLM inside the research module's synthesis step (not in the MCP layer itself). Bootstrap initializes shared components once as a singleton, skipping advisor/LLM setup entirely via `skip_advisor=True`.

## Dependencies

**Depends on:** `journal` (JournalStorage, EmbeddingManager, JournalSearch), `intelligence` (IntelStorage, IntelScheduler, TrendingRadar, GoalIntelMatchStore), `advisor` (RAGRetriever, GoalTracker, InsightStore), `memory` (FactStore), `research` (via IntelScheduler.run_research_now), `profile` (ProfileStorage), `cli.utils` (get_components bootstrap), `mcp` SDK

**Depended on by:** Claude Code (external MCP client via stdio transport)

---

## Components

### Server
**File:** `src/coach_mcp/server.py`

#### Behavior

- Creates a single `Server("stewardme")` instance at module load time.
- Two module-level cache globals: `_tool_defs: list[Tool] | None` and `_handlers: dict | None`, both `None` until first use.
- `_load_tools()` imports 12 tool modules in this order: `journal, goals, intelligence, recommendations, research, reflect, profile, projects, insights, brief, memory, threads`. For each module it iterates `TOOLS` (a list of `(name, schema, handler)` tuples) and builds a `Tool(name=name, description=schema["description"], inputSchema=schema)` object plus a `handlers[name] = handler` entry.
- `list_tools()` — async, `@app.list_tools()` decorated. Calls `_load_tools()` on first invocation; returns cached `_tool_defs` subsequently.
- `call_tool(name, arguments)` — async, `@app.call_tool()` decorated. Triggers lazy load if `_handlers` is `None`. Dispatches to `handler(arguments)` synchronously. Serializes result with `json.dumps(result, default=str)`. Returns `list[TextContent]`.
- `run()` — async. Opens stdio streams via `stdio_server()`, runs `app.run(read_stream, write_stream, app.create_initialization_options())`.
- `main()` — sync entry point, calls `asyncio.run(run())`. Invoked by `python -m coach_mcp` and the `coach_mcp` CLI entrypoint.

#### Inputs / Outputs

- `list_tools()` → `list[Tool]` (MCP Tool objects with name, description, inputSchema).
- `call_tool(name: str, arguments: dict)` → `list[TextContent]` where each item has `type="text"` and `text` is a JSON string.

#### Invariants

- Tool loading is lazy and cached — `_load_tools()` is called at most once per process lifetime (unless `_tool_defs` is reset).
- All tool responses are JSON strings wrapped in `list[TextContent]` — never raw Python objects.
- Handler exceptions are caught and returned as error JSON — the MCP connection is never dropped due to a handler crash.
- Tool dispatch is synchronous — no async handlers exist in any tool module.
- `call_tool()` always returns `list[TextContent]`, even for errors.

#### Error Handling

- **Unknown tool**: returns `[TextContent(type="text", text='{"error": "Unknown tool: <name>"}')]` immediately without raising.
- **Handler exception**: caught in `call_tool`, logs `logger.error("tool_error", tool=name, error=str(e))`, returns `{"error": str(e), "traceback": traceback.format_exc()}` as JSON text.

#### Configuration

None — server name `"stewardme"` is hard-coded. Transport is always stdio.

---

### Bootstrap
**File:** `src/coach_mcp/bootstrap.py`

#### Behavior

- Single module-level global `_components = None`.
- `get_components() -> dict` — lazy singleton. On first call logs `"mcp_bootstrap_init"` then calls `cli.utils.get_components(skip_advisor=True)`. Subsequent calls return the cached dict.
- `skip_advisor=True` skips LLM provider and `AdvisorEngine` initialization. This is the architectural enforcement of the no-LLM-in-MCP-layer rule.

#### Inputs / Outputs

Returns a dict with keys:

| Key | Value |
|---|---|
| `"storage"` | `JournalStorage` |
| `"embeddings"` | ChromaDB embeddings wrapper |
| `"search"` | `JournalSearcher` |
| `"rag"` | `RAGRetriever` |
| `"intel_storage"` | `IntelStorage` (SQLite) |
| `"intel_search"` | `IntelSearcher` |
| `"config"` | raw config dict |
| `"config_model"` | Pydantic config model |
| `"paths"` | path dict |

#### Invariants

- `get_components()` is a true singleton — returns the same dict reference on every call after initialization.
- `skip_advisor=True` is hardcoded — the MCP layer can never access the `AdvisorEngine` through bootstrap.
- The only way to reset the singleton in tests is `bootstrap._components = None` — no public reset method.
- Bootstrap failure is fatal — the MCP server cannot start without successful component initialization.

#### Error Handling

Any exception from `cli.utils.get_components()` propagates uncaught — bootstrap failure is fatal.

#### Configuration

- **Test reset pattern**: tests set `bootstrap._components = None` directly to reset the singleton between runs. No dedicated reset function exists in the module.

---

### Tool Convention
**File:** `src/coach_mcp/tools/*.py`

#### Behavior

Every tool module exports a `TOOLS` constant:

```python
TOOLS: list[tuple[str, dict, Callable[[dict], dict]]]
# (tool_name, json_schema_dict, handler_function)
```

- `tool_name`: MCP tool name string.
- `json_schema_dict`: must contain `"description"` (used by `server.py`), `"type": "object"`, `"properties"`, and `"required"` keys.
- `handler_function`: synchronous `(args: dict) -> dict`. Called directly by `call_tool`. Any asyncio work inside uses `asyncio.get_event_loop().run_until_complete()`.

All handlers are sync. No async handlers exist in any tool module.

---

## Tool Modules

### 1. Journal
**File:** `src/coach_mcp/tools/journal.py`
**Status:** Stable

**Internal helpers:**
- `_get_proactive_context(args)`: builds the proactive daily brief; each section (signals, patterns, goals, journal health) is individually wrapped in `try/except`, returning empty lists/dicts on failure. Signals failures also set `_signal_error` key.
- `_detect_thread(c, entry_id)`: post-write thread detection; uses `asyncio.get_event_loop().run_until_complete()`; returns `None` if threads disabled, embedding missing, `match_type == "unthreaded"`, or any exception occurs.

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `journal_get_context` | — | `query`, `mode` (`"rag"`), `journal_weight` (0.7), `max_chars` (8000), `include_research` (True), `max_signals` (10) | RAG context or proactive daily brief. `mode="rag"` mutates `rag.journal_weight` and `rag.max_context_chars` if args provided, returns `{journal_context, intel_context, research_context}`. `mode="proactive"` returns `{_instruction, signals, patterns, stale_goals, active_goals_summary, journal_health}` |
| `journal_create` | `content` | `entry_type` (`"daily"`), `title`, `tags` | Creates markdown entry + syncs ChromaDB embedding. If no title, attempts auto-generation via `llm.create_cheap_provider()` (silently ignored on failure). `entry_type="goal"` auto-adds goal metadata via `get_goal_defaults()`. Runs thread detection post-write. Returns `{path, filename, title, type}` + optional `thread` dict |
| `journal_list` | — | `entry_type`, `tag`, `limit` (20) | Lists entries metadata. Returns `{entries: [...], count}` |
| `journal_read` | `filename` | — | Reads full content + frontmatter. Returns `{path, filename, title, type, created, tags, content, metadata}` |
| `journal_search` | `query` | `limit` (5) | Semantic search. Returns `{results: [...], count}` with `preview` truncated to 300 chars |
| `journal_delete` | `filename` | — | Removes embedding via `embeddings.remove_entry()` then deletes file. Returns `{deleted, filename}` |

**Valid `entry_type` values:** `daily`, `project`, `goal`, `reflection`, `insight`, `note`, `research`, `action_brief`

Note: `shared_types.EntryType` also defines `quick`, but it is intentionally excluded from the MCP schema enum. The `quick` type is only used by the web `POST /api/journal/quick` route.

#### Error Handling

- `journal_read` and `journal_delete`: path traversal check — resolves path and checks `filepath.is_relative_to(journal_dir)`; returns `{"error": "Path escapes journal directory"}` on failure.
- `journal_read` and `journal_delete`: returns `{"error": "Entry not found: <filename>"}` if file missing.

---

### 2. Goals
**File:** `src/coach_mcp/tools/goals.py`
**Status:** Experimental (all tools prefixed `[Experimental]` in description)

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `goals_list` | — | `include_inactive` (False) | Lists goals with staleness info, progress, milestones. Returns `{goals: [...], count}`. Each goal includes `path`, `filename`, `title`, `status`, `created`, `last_checked`, `check_in_days`, `days_since_check`, `is_stale`, `tags`, `progress`, `preview` |
| `goals_add` | `title` | `description`, `check_days` (14), `tags`, `type` (`"general"`) | Creates goal via `journal._create` with `entry_type="goal"`. Writes `check_in_days` to frontmatter only if `check_days != 14`. `type` field: `career`, `learning`, `project`, `general` |
| `goals_check_in` | `goal_path` | `notes` | Records check-in timestamp. Returns `{success, goal_path}` |
| `goals_update_status` | `goal_path`, `status` | — | `status` enum: `active`, `paused`, `completed`, `abandoned`. Returns `{success, goal_path, status}` |
| `goals_add_milestone` | `goal_path`, `title` | — | Adds milestone. Returns `{success, goal_path, progress}` |
| `goals_complete_milestone` | `goal_path`, `milestone_index` | — | `milestone_index` is 0-based integer. Returns `{success, goal_path, progress}` |

---

### 3. Intelligence
**File:** `src/coach_mcp/tools/intelligence.py`
**Status:** Stable

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `intel_search` | `query` | `limit` (10) | Semantic search over scraped items. `summary` truncated to 500 chars. Returns `{results: [...], count}` |
| `intel_get_recent` | — | `days` (7), `limit` (50), `source` | Recent items from SQLite. `source` filter applied client-side after query. Returns `{items: [...], count}` |
| `intel_scrape_now` | — | — | Runs all configured scrapers via `IntelScheduler.run_now()`, then syncs intel embeddings. Returns `{scrape_results, embeddings_synced: {added, removed}}` |
| `events_upcoming` | — | `days` (90), `limit` (20) | Upcoming tech events ranked by profile relevance. Loads profile best-effort (silently ignores failure). Returns `{events: [...], count}` with `title`, `url`, `score`, `event_date`, `location`, `cfp_deadline`, `online` |
| `intel_trending_radar` | — | `days` (7), `min_sources` (2), `max_topics` (15) | Cross-source trending topics via `TrendingRadar`. Truncates to top-1 item per topic for MCP context budget. Returns the `snapshot` dict directly |
| `watchlist_list` | — | — | Lists watchlist items from the single-user watchlist store. Returns `{items, count}` |
| `watchlist_upsert` | `label` | `item_id`, `kind`, `aliases`, `why`, `priority`, `tags`, `goal`, `time_horizon`, `source_preferences` | Creates or updates a watchlist item. Returns `{item}` |
| `watchlist_delete` | `item_id` | — | Deletes a watchlist item. Returns `{success, item_id}` |

---

### 4. Recommendations
**File:** `src/coach_mcp/tools/recommendations.py`
**Status:** Stable

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `recommendations_list` | — | `limit` (20), `category`, `status` | Lists recs from last 90 days. If `category` provided, uses `list_by_category(category, status, limit)`; otherwise `list_recent(days=90, status, limit)`. Returns `{recommendations: [...], count}` |
| `recommendations_update_status` | `rec_id` (int), `status` | — | `status` enum: `suggested`, `in_progress`, `completed`, `dismissed`. Returns `{success, rec_id, status}` |
| `recommendations_rate` | `rec_id` (int), `rating` (int 1–5) | `comment` | Calls `rec_storage.add_feedback(rec_id, rating, comment=comment)`. Returns `{success, rec_id, rating}` |

---

### 5. Research
**File:** `src/coach_mcp/tools/research.py`
**Status:** Experimental (both tools prefixed `[Experimental]`)

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `research_topics` | — | — | Auto-suggested topics from journal/goals via `IntelScheduler.get_research_topics()`. No LLM call. Returns `{topics: [...], count}` |
| `research_run` | — | `topic` | Triggers deep research via `IntelScheduler.run_research_now(topic=topic)`. Auto-selects topic if omitted. **This is the one tool that transitively calls an LLM** (in the research synthesis layer, not the MCP layer). `summary` truncated to 1000 chars. Returns `{reports: [...], count}` |

---

### 6. Reflect
**File:** `src/coach_mcp/tools/reflect.py`
**Status:** Stable

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `get_reflection_prompts` | — | `days` (14) | Returns `{journal_context, goal_context, instruction}`. `journal_context` from `rag.get_recent_entries(days)`. `goal_context` lists active goals as `"- <title> (<status>)\n"` or `"(No goals set)"`. `instruction` = `"Generate 3-5 targeted coaching questions based on the journal context and goal status. Reference specific entries and goals."` No LLM call — Claude Code does the generation |

---

### 7. Profile
**File:** `src/coach_mcp/tools/profile.py`
**Status:** Stable

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `profile_get` | — | — | Returns `{exists: True, profile: model_dump(), summary, is_stale}` or `{exists: False, profile: null}` if no profile file |
| `profile_update_field` | `field`, `value` | — | Updates single field. List fields (`interests`, `languages_frameworks`) auto-split on comma if `value` is a string. Returns `{success: True, profile: model_dump()}` or `{success: False, error: ...}` on `ValueError` |

**Valid field names:** `skills`, `interests`, `career_stage`, `current_role`, `aspirations`, `location`, `languages_frameworks`, `learning_style`, `weekly_hours_available`

**Profile path config:** `config["profile"]["path"]`, default `~/coach/profile.yaml`

---

### 8. Projects
**File:** `src/coach_mcp/tools/projects.py`
**Status:** Stable

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `projects_discover` | — | `limit` (20), `days` (14) | Finds matching open-source GitHub issues ranked by profile match score via `get_matching_issues()`. Profile loaded best-effort. `summary` truncated to 300 chars. Returns `{issues: [...], count}` |
| `projects_ideas` | — | — | Returns `{profile, journal_context, instruction}`. Journal query: `"frustration problem idea project build wish"`, `max_entries=10`, `max_chars=5000`. No LLM in MCP layer |
| `projects_list` | — | `days` (14) | Lists raw `github_issues`-sourced intel items (no match scoring), limit 50. Returns `{issues: [...], count}` |

---

### 9. Insights
**File:** `src/coach_mcp/tools/insights.py`
**Status:** Experimental

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `get_insights` | — | `type`, `min_severity` (1), `limit` (20) | Active insights from `InsightStore.get_active()`. Returns `{insights: [...], count}` |

**InsightType enum:** `topic_emergence`, `goal_stale`, `goal_complete`, `deadline_urgent`, `journal_gap`, `learning_stalled`, `research_trigger`, `recurring_blocker`, `pattern_blind_spot`, `pattern_blocker_cycle`, `intel_match`

**Severity range:** 1–10 (integer). DB path from `config["paths"]["intel_db"]`, default `~/coach/intel.db`.

---

### 10. Brief
**File:** `src/coach_mcp/tools/brief.py`
**Status:** Stable

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `get_daily_brief` | — | — | Time-budgeted daily action plan. Fetches stale goals (threshold=7 days), top 5 recs by score, and uses profile weekly-hours context (default `5`). Returns `{items: [...], budget_minutes, used_minutes, generated_at}` |

Each item has: `kind`, `title`, `description`, `time_minutes`, `action`, `priority`.

---

---

### 11. Memory
**File:** `src/coach_mcp/tools/memory.py`
**Status:** Stable

`FactStore` initialized with `db_path` from `config["paths"]["intel_db"]` (default `~/coach/intel.db`) and `chroma_dir` from `config["paths"]["chroma_dir"]` (default `~/coach/chroma`).

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `memory_list_facts` | — | `category`, `limit` (50) | Lists active facts. If `category` provided, validates against `FactCategory` enum; returns `{"error": "Invalid category: ..."}` on invalid value. Returns `{facts: [...], count}` |
| `memory_search_facts` | `query` | `limit` (10) | Semantic search. Empty `query` returns `{"error": "query is required"}`. Returns `{facts: [...], count}` |
| `memory_delete_fact` | `fact_id` | — | Soft-delete with `reason="mcp_delete"`. Empty `fact_id` returns `{"error": "fact_id is required"}`. Missing fact returns `{"error": "Fact not found: <fact_id>"}`. Returns `{deleted: True, fact_id}` on success |
| `memory_get_stats` | — | — | Returns `store.get_stats()` directly (fact counts by category) |

**Fact category enum:** `preference`, `skill`, `constraint`, `pattern`, `context`, `goal_context`

---

### 12. Threads
**File:** `src/coach_mcp/tools/threads.py`
**Status:** Stable

Thread DB path: `intel_db.parent / "threads.db"` (sibling of `intel.db`). All asyncio calls use `asyncio.get_event_loop().run_until_complete()`.

Default thresholds (used when `config_model` is absent):

```python
similarity_threshold = 0.78
candidate_count = 10
min_entries_for_thread = 2
```

| Tool | Required args | Optional args (defaults) | Description |
|---|---|---|---|
| `threads_list` | — | `min_entries` (2) | Lists active threads. Returns `{threads: [...], count}` with `id`, `label`, `entry_count`, `first_date`, `last_date`, `status` per thread |
| `threads_get_entries` | `thread_id` (str) | — | Returns `{thread: {id, label, entry_count}, entries: [...]}`. Entry `similarity` rounded to 3 decimal places. Returns `{"error": "Thread not found: <thread_id>"}` if missing |
| `threads_reindex` | — | — | Full rebuild via `ThreadDetector.reindex_all()`. Uses config thresholds if `config_model` available, else defaults above. Returns stats dict directly |

---

---

## No-LLM-in-MCP-Layer Rule

#### How It Is Enforced

The rule is enforced architecturally in `bootstrap.py`:

```python
_components = _get(skip_advisor=True)
```

`skip_advisor=True` causes `cli.utils.get_components` to skip all LLM provider and `AdvisorEngine` initialization. No LLM instance is available to any tool handler.

Tools that need reasoning-intensive outputs (project ideas, reflection prompts, and similar context-first helpers) instead return raw context plus an `"instruction"` string:

```python
# Context-first MCP tools return raw data plus an instruction string
# for Claude Code to reason over.
```

The calling Claude Code instance receives the raw data and the instruction, then performs the reasoning itself.

#### The One Exception

`research_run` calls `IntelScheduler.run_research_now()`, which invokes an LLM inside the research module's synthesis step. The LLM call is in the research layer, not the MCP layer — the MCP layer only calls a scheduler method and returns the result. The tool description explicitly notes: `"Uses configured LLM for synthesis."` The LLM is initialized by `IntelScheduler` directly from env/config, not from the bootstrap component dict.

---

## Error Handling Patterns

| Pattern | Where | Behavior |
|---|---|---|
| Unknown tool | `server.call_tool` | Returns `{"error": "Unknown tool: <name>"}` as JSON text immediately |
| Handler exception | `server.call_tool` | Catches all exceptions, logs `logger.error("tool_error", ...)`, returns `{"error": str(e), "traceback": traceback.format_exc()}` |
| Path traversal | `journal_read`, `journal_delete` | Resolves filepath, checks `filepath.is_relative_to(journal_dir)`, returns `{"error": "Path escapes journal directory"}` |
| Not found | Most tools | Returns `{"error": "... not found"}` inline, does not raise |
| Invalid enum value | `memory_list_facts` (category) | Returns `{"error": "Invalid category: <value>"}` inline |
| Empty required string | `memory_search_facts` (query), `memory_delete_fact` (fact_id) | Returns `{"error": "query is required"}` / `{"error": "fact_id is required"}` |
| Sub-component failure in proactive brief | `journal_get_context` mode=proactive | Each section (signals, patterns, goals, journal health) wrapped individually; returns empty list/dict + optional `_signal_error` key on failure |
| Profile load failure | `events_upcoming`, `projects_discover`, `projects_ideas`, `get_daily_brief` | Profile loaded best-effort inside `try/except`; handler continues with `profile=None` or empty string |
| Thread not found | `threads_get_entries` | Returns `{"error": "Thread not found: <thread_id>"}` |
| Profile field ValueError | `profile_update_field` | Returns `{"success": False, "error": str(e)}` |
| Thread detection failure | `journal_create` (post-write) | `_detect_thread` catches all exceptions, logs debug, returns `None`; entry creation still succeeds |

---

## Configuration Knobs and Defaults

| Config key | Default | Used by |
|---|---|---|
| `config["profile"]["path"]` | `~/coach/profile.yaml` | `profile_get`, `profile_update_field`, `projects_discover`, `projects_ideas`, `events_upcoming` |
| `config["paths"]["intel_db"]` | `~/coach/intel.db` | `get_insights`, `memory_*`, `threads_*` |
| `config["paths"]["chroma_dir"]` | `~/coach/chroma` | `memory_list_facts`, `memory_search_facts`, `memory_delete_fact`, `memory_get_stats` |
| `journal_weight` arg default | `0.7` | `journal_get_context` (rag mode) |
| `max_chars` arg default | `8000` | `journal_get_context` (rag mode) |
| `config_model.threads.similarity_threshold` | `0.78` | `threads_reindex`, `journal_create` thread detection |
| `config_model.threads.candidate_count` | `10` | `threads_reindex`, `journal_create` thread detection |
| `config_model.threads.min_entries_for_thread` | `2` | `threads_reindex`, `journal_create` thread detection |
| `config_model.threads.enabled` | (must be truthy) | `journal_create` thread detection skipped if False or absent |
| `goals_add` `check_days` default | `14` | `goals_add` (written to frontmatter only when non-default) |
| `DailyBriefBuilder` stale threshold | `7` days | `get_daily_brief` |
| `DailyBriefBuilder` weekly_hours fallback | `5` | `get_daily_brief` |
| `recommendations_list` lookback | `90` days (hard-coded) | `recommendations_list` |
| `intel_trending_radar` items-per-topic cap | `1` (hard-coded) | `intel_trending_radar` |

---

## Experimental vs. Stable Tool Tagging

Tools marked `[Experimental]` carry the prefix in their MCP description string. All other tools are implicitly stable.

| Status | Tools |
|---|---|
| Experimental | `goals_list`, `goals_add`, `goals_check_in`, `goals_update_status`, `goals_add_milestone`, `goals_complete_milestone`, `research_topics`, `research_run`, `get_insights` |
| Stable | All remaining 28 tools across `journal`, `intelligence`, `recommendations`, `reflect`, `profile`, `projects`, `brief`, `memory`, `threads` |
---

## Test Expectations

- `server.call_tool()`: verify unknown tool returns `{"error": "Unknown tool: ..."}` (not exception); verify handler exception returns `{"error": ..., "traceback": ...}`.
- `bootstrap.get_components()`: verify singleton — second call returns same dict without re-initializing; verify `_components = None` reset pattern works in tests.
- `journal_read` / `journal_delete`: verify path traversal check rejects `../` paths; verify "Entry not found" on missing file.
- `journal_create`: mock cheap LLM for title generation; verify thread detection failure doesn't prevent entry creation.
- `memory_list_facts`: verify invalid category returns `{"error": "Invalid category: ..."}`.
- `profile_update_field`: verify `ValueError` on unknown field returns `{"success": False, "error": ...}`.
- `research_run`: this is the one tool that calls an LLM transitively — mock `IntelScheduler.run_research_now`.
- All tests: reset `bootstrap._components = None` between runs (conftest fixture).
- Mocks required: all storage backends, LLM providers, filesystem.

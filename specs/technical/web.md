# Web

## Overview

FastAPI + Next.js web layer for multi-user access to the AI coach. FastAPI backend handles JWT auth (via NextAuth), Fernet-encrypted per-user secrets, and per-user data isolation under `~/coach/users/{safe_user_id}/`. 19 route modules expose JSON REST endpoints and one SSE streaming endpoint. Intel DB stays global (shared across all users).

## Dependencies

**Depends on:** `advisor`, `journal`, `intelligence`, `research`, `profile`, `memory`, `llm`, `cli` (config + paths)
**Depended on by:** Next.js frontend (`web/`), MCP server indirectly (shares data paths)

---

## Components

### FastAPI App
**File:** `src/web/app.py`
**Status:** Stable

#### Behavior

Creates `FastAPI(title="AI Coach", version="0.1.0")` with an async lifespan that:
1. Calls `init_db()` to create SQLite tables.
2. Calls `_verify_secret_key()` — Fernet encrypt+decrypt roundtrip canary. **Raises `RuntimeError` and aborts startup** if `SECRET_KEY` is missing or canary fails.
3. Best-effort starts the intel scheduler unless `DISABLE_INTEL_SCHEDULER` is truthy.
4. Logs `web.startup`.

20 routers mounted via `app.include_router(...)`. CORS middleware configured from `FRONTEND_ORIGIN` env var (default `http://localhost:3000`); allows credentials, all methods, all headers.

`GET /api/health` returns `{"status": "ok"}` — unauthenticated.

#### Inputs / Outputs

No public API beyond ASGI app object. All configuration via env vars.

#### Invariants

- `SECRET_KEY` must be a valid 32-byte url-safe base64 Fernet key; startup fails otherwise.
- `NEXTAUTH_SECRET` must match the value used by the Next.js frontend; JWT decode will fail on every request otherwise.
- All routers are mounted with `/api/` prefix prefix (each router defines its own sub-prefix).

#### Error Handling

- Missing/invalid `SECRET_KEY`: raises `RuntimeError` at startup, server does not start.
- Router-level errors: each route handles independently (see route sections).

#### Configuration

| Key | Default | Source |
|---|---|---|
| `SECRET_KEY` | required | env var |
| `NEXTAUTH_SECRET` | required | env var |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | env var |
| `DISABLE_INTEL_SCHEDULER` | unset / false | env var |

---

### JWT Auth
**File:** `src/web/auth.py`
**Status:** Stable

#### Behavior

`get_current_user` is a FastAPI dependency used by all protected routes. Extracts Bearer token from `Authorization` header, decodes JWT with `NEXTAUTH_SECRET` (HS256), validates `sub` field exists, upserts user via `get_or_create_user()`, and returns `{"id", "email", "name"}`.

**Auto-registration:** Every authenticated request upserts the user into the `users` SQLite table. First login creates the user; subsequent logins may update `email`/`name`. Secrets are migrated from duplicate user IDs (same email) on each auth call.

`get_admin_user` wraps `get_current_user`. Checks `ADMIN_USER_IDS` env var (comma-separated). Raises HTTP 403 if user not in list or list is empty.

#### Inputs / Outputs

```python
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict
async def get_admin_user(user: dict = Depends(get_current_user)) -> dict
```

Return: `{"id": str, "email": str | None, "name": str | None}`

#### Invariants

- `user["id"]` is always the JWT `sub` claim; never empty (HTTP 401 if missing).
- Every authenticated request is a potential upsert; `users` table is always in sync.

#### Error Handling

| Condition | Response |
|---|---|
| No Bearer token | HTTP 403 (FastAPI HTTPBearer auto-rejects) |
| JWT decode failure / expired | HTTP 401 `"Invalid or expired token"` |
| Missing `sub` claim | HTTP 401 `"Invalid token: missing sub"` |
| `NEXTAUTH_SECRET` not set | HTTP 500 `"NEXTAUTH_SECRET not configured"` |
| User not admin | HTTP 403 `"Admin access required"` |

#### Configuration

| Key | Default | Source |
|---|---|---|
| `NEXTAUTH_SECRET` | required | env var |
| `ADMIN_USER_IDS` | `""` (no admins) | env var, comma-separated |

---

### Fernet Crypto
**File:** `src/web/crypto.py`
**Status:** Stable

#### Behavior

Two layers:

**Value-level (primary, used by UserStore):**
- `encrypt_value(fernet_key, plaintext) -> str` — Fernet-encrypts a string, returns base64 token.
- `decrypt_value(fernet_key, token, key_name="") -> str | None` — Decrypts; returns `None` on `InvalidToken` or any exception (logs warning with `key_name`). Never raises.

**File-level (legacy, CLI/migration):**
- `load_secrets(secret_key) -> dict` — Decrypts `~/coach/secrets.enc` as JSON dict. Returns `{}` on missing file or any decrypt/parse error.
- `save_secrets(secret_key, data)`, `get_secret`, `set_secret`, `delete_secret` — File-backed secret store. Used by legacy CLI, not web routes.

`SECRET_KEY` must be a valid 32-byte url-safe base64 string (Fernet requirement).

#### Invariants

- `decrypt_value` never raises; all failures return `None` + log warning.
- Encrypted values are opaque base64 tokens; never stored in plaintext.
- File-level and value-level encryption use the same key format and Fernet instance.

#### Error Handling

`decrypt_value`: catches `InvalidToken` and all other exceptions; returns `None`; logs `crypto.decrypt_failed` with `key_name` and reason.
`load_secrets`: catches `InvalidToken`, `JSONDecodeError`, and all exceptions; returns `{}`.

---

### UserStore
**File:** `src/web/user_store.py`
**Status:** Stable

#### Behavior

Multi-user SQLite store at `~/coach/users.db` (override via `COACH_HOME` env or `db_path` param). Uses WAL mode via `db.wal_connect`. All functions open+close a connection per call (no connection pooling).

**Schema** (created by `init_db()`):

| Table | Key columns | Notes |
|---|---|---|
| `users` | `id TEXT PK`, `email`, `name`, `created_at` | |
| `user_secrets` | `(user_id, key) PK`, `value TEXT` | Fernet-encrypted values |
| `conversations` | `id TEXT PK`, `user_id FK`, `title`, `created_at`, `updated_at` | CASCADE delete |
| `conversation_messages` | `id TEXT PK`, `conversation_id FK`, `role CHECK(user/assistant)`, `content`, `created_at` | CASCADE delete |
| `conversation_message_attachments` | `id TEXT PK`, `message_id FK`, `library_item_id`, `file_name`, `mime_type` | Per-message attachment linkage to user Library items |
| `onboarding_responses` | `id AUTOINCREMENT`, `user_id FK`, `turn_number`, `role`, `content` | |
| `engagement_events` | `id AUTOINCREMENT`, `user_id FK`, `event_type CHECK(...)`, `target_type`, `target_id`, `metadata_json` | 6 valid event types |
| `usage_events` | `id AUTOINCREMENT`, `event`, `user_id`, `metadata` | Fail-silent analytics |
| `user_rss_feeds` | `id AUTOINCREMENT`, `(user_id, url) UNIQUE` | Per-user RSS subscriptions |

**`get_or_create_user(user_id, email, name)`** — Upsert: if user exists, updates email/name (COALESCE); if new, inserts. After either path, calls `_migrate_secrets()` if `email` provided.

**`_migrate_secrets(conn, target_id, email)`** — Finds other users with same email, moves their secrets to `target_id` (skipping keys target already has), then deletes old user's secrets, conversations, and user record. Used to merge accounts created under different OAuth provider IDs.

**`log_event(event, user_id, metadata)`** — Fail-silent: wraps entire insert in try/except that swallows all exceptions. Never propagates.

**`get_usage_stats(days)`** — Admin analytics: chat queries, avg latency (from `metadata.latency_ms`), active users (7d window hardcoded), event counts, recommendation feedback, scraper health, page views. Returns structured dict.

**`delete_user(user_id)`** — Manually deletes all rows across all tables (secrets, onboarding, engagement, usage, rss_feeds, users). Does not rely on CASCADE for most tables. Returns `True` if user existed.

#### Inputs / Outputs

Key functions:
```python
def init_db(db_path=None) -> None
def get_or_create_user(user_id, email=None, name=None, db_path=None) -> dict
def get_user_secret(user_id, secret_key, fernet_key, db_path=None) -> str | None
def get_user_secrets(user_id, fernet_key, db_path=None) -> dict[str, str]
def set_user_secret(user_id, secret_key, value, fernet_key, db_path=None) -> None
def delete_user_secret(user_id, secret_key, db_path=None) -> None
def log_engagement(user_id, event_type, target_type, target_id, metadata=None) -> None
def get_engagement_stats(user_id, days=30) -> dict
def log_event(event, user_id=None, metadata=None) -> None
def get_usage_stats(days=30) -> dict
def delete_user(user_id) -> bool
def add_user_rss_feed(user_id, url, name=None, added_by="user") -> dict
def remove_user_rss_feed(user_id, url) -> bool
def get_all_user_rss_feeds() -> list[dict]
```

#### Invariants

- `get_user_secrets` skips (and counts) any secret that fails decryption; logs `user_store.secrets_skipped` if any skipped.
- `set_user_secret` uses `INSERT ... ON CONFLICT DO UPDATE` (upsert by `(user_id, key)`).
- `add_user_rss_feed` uses `INSERT ... ON CONFLICT DO UPDATE SET name = COALESCE(excluded.name, name)` (upsert by `(user_id, url)`).
- `log_event` never raises under any condition.

#### Error Handling

- `get_user_secret` / `get_user_secrets`: decrypt failures → `None` / skipped entry (via `decrypt_value`'s fail-silent behavior).
- `log_event`: all exceptions swallowed.
- All other functions: propagate `sqlite3` errors to caller.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `COACH_HOME` | `~/coach` | env var |
| DB path | `$COACH_HOME/users.db` | derived |

---

### ConversationStore
**File:** `src/web/conversation_store.py`
**Status:** Stable

#### Behavior

Thin wrapper over `users.db` `conversations` + `conversation_messages` tables (reuses `_get_conn` from `user_store`). Conversations are keyed by `uuid4().hex` IDs. `get_messages` uses a subquery: fetches last N by `DESC`, returns `ASC` (oldest-first for LLM history).

For document-aware chat, `conversation_message_attachments` lets each user turn retain zero or more Library attachment references without inlining binary data into message rows.

`conversation_belongs_to(conv_id, user_id)` is used as an ownership check before operations; returns bool (no exception).

`add_message` updates `conversations.updated_at` in the same transaction.

#### Inputs / Outputs

```python
def create_conversation(user_id, title, db_path=None) -> str          # returns conv_id (hex UUID)
def list_conversations(user_id, limit=50) -> list[dict]               # newest-first
def get_conversation(conv_id, user_id) -> dict | None                 # includes messages
def add_message(conv_id, role, content, attachments=None) -> str      # returns msg_id
def get_messages(conv_id, limit=20) -> list[dict]                     # oldest-first, last N
def delete_conversation(conv_id, user_id) -> bool
def conversation_belongs_to(conv_id, user_id) -> bool
```

`list_conversations` returns: `{id, title, updated_at, message_count}` (LEFT JOIN count).

Attachment-aware `get_messages()` / `get_conversation()` return message objects with optional `attachments: list[{library_item_id, file_name, mime_type, title?, source_kind?}]`.

#### Invariants

- Title truncated to 80 chars on create.
- `get_messages` returns at most `limit` messages, always in chronological order.
- `delete_conversation` cascade-deletes messages (FK ON DELETE CASCADE).
- Attachment rows must be deleted when their parent message is deleted.
- Cross-user access is prevented at query level (`WHERE id = ? AND user_id = ?`).

---

### Deps (Dependency Injection)
**File:** `src/web/deps.py`
**Status:** Stable

#### Behavior

`get_config()` — `@lru_cache`: loads `~/coach/config.yaml` once per process. Not invalidated on config file changes.

`get_user_paths(user_id) -> dict` — Returns per-user path dict, creating `base/` and `base/journal/` if missing. Keys:

| Key | Path | Notes |
|---|---|---|
| `journal_dir` | `~/coach/users/{safe_id}/journal/` | |
| `data_dir` | `~/coach/users/{safe_id}/` | Parent directory for library, memory db, and other user-scoped stores |
| `chroma_dir` | `~/coach/users/{safe_id}/chroma/` | |
| `recommendations_dir` | `~/coach/users/{safe_id}/recommendations/` | |
| `profile` | `~/coach/users/{safe_id}/profile.yaml` | |
| `intel_db` | `~/coach/intel.db` (global, not per-user) | |

`safe_user_id(user_id)` — Replaces `:` with `_` (for OAuth IDs like `google:12345`).

`get_api_key_with_source(user_id) -> (key, source)` — Priority order:
1. User's encrypted `llm_api_key` secret → source `"user"`
2. `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` env vars → source `"shared"`
3. `config.llm.api_key` → source `"shared"`
4. `(None, None)` if nothing found

`get_settings_mask_for_user(user_id)` — Returns non-sensitive settings dict with bool flags (`*_set`), last-4-char hints (`*_hint`), and `using_shared_key` / `has_own_key` flags. Raw keys never returned.

`SHARED_LLM_MODEL = "claude-haiku-4-5"` — Hardcoded model forced on shared-key users.

#### Invariants

- `intel_db` always points to the global `~/coach/intel.db`, not per-user paths.
- `get_user_paths` creates dirs as a side effect on every call.
- `get_config()` is cached for process lifetime; restart required to pick up config changes.

#### Caveats

- `get_config()` LRU cache means config file changes require process restart.
- Legacy single-user functions (`get_decrypted_secrets`, `get_settings_mask`, `get_api_key_for_provider`) use the file-based crypto (`~/coach/secrets.enc`). These are only used by old tests and are not in the active web path.

---

### Rate Limiter
**File:** `src/web/rate_limit.py`
**Status:** Stable

#### Behavior

In-memory sliding window rate limiter for shared-key (lite mode) users. State in `_request_log: dict[str, list[float]]` — resets on deploy/restart.

`check_shared_key_rate_limit(user_id)`:
1. Prunes timestamps older than 24h.
2. **Burst check**: if last request was within `BURST_INTERVAL` (10s) → HTTP 429 with `Retry-After`.
3. **Daily check**: if `len(log) >= DAILY_LIMIT` (30) → HTTP 429 with `Retry-After` (time until oldest entry expires).
4. Records current timestamp.

`reset_rate_limits()` — Clears all state. Used in tests.

#### Configuration

| Constant | Value |
|---|---|
| `DAILY_LIMIT` | 30 requests per rolling 24h |
| `WINDOW_SECONDS` | 86400 (24h) |
| `BURST_INTERVAL` | 10.0 seconds |

#### Caveats

State is process-local; multiple worker processes do not share rate limit counters. Acceptable for current single-process deployment.

---

### Route Modules
**File:** `src/web/routes/*.py`
**Status:** Stable (settings, journal, advisor, profile, user, engagement, pageview, admin) / Experimental (goals, intel, research, briefing, recommendations, insights, memory, threads, onboarding, greeting, suggestions)

#### Behavior

All routes require `Depends(get_current_user)` except `GET /api/health` (in `app.py`). All use `get_user_paths(user["id"])` for per-user data isolation.

**Pattern: simple CRUD wrapping a storage class**
Used by: `journal`, `goals`, `profile`, `recommendations`, `memory`, `threads`

Each route: resolves user paths → instantiates storage class with per-user path → delegates to storage method → maps result to Pydantic response model. Path traversal protection on file-based routes via `_validate_journal_path()` (checks resolved path is inside `journal_dir`).

**Pattern: advisor (non-trivial)**
`POST /api/advisor/ask` — Creates or reuses a `conversation_id`, loads last 20 messages (trimmed to 64k chars), saves user message, calls `AdvisorEngine.ask()` in `asyncio.to_thread`, saves assistant response, logs `chat_query` usage event. Builds a fresh `AdvisorEngine` instance per request. The JSON request accepts `attachment_ids` so chat turns can reference already-uploaded Library items.

`POST /api/advisor/ask/stream` — SSE streaming variant. Uses `asyncio.Queue` as producer-consumer between engine thread and SSE generator. Engine runs in `loop.run_in_executor`. Events emitted: `tool_start`, `tool_done`, `answer`, `error`. `answer` event emitted by SSE generator only if agentic callback didn't already emit one. Returns `StreamingResponse(media_type="text/event-stream")`. The JSON request accepts `attachment_ids` referencing uploaded Library items.

`library.py`:
- `POST /api/library/reports/upload` validates and stores PDFs, extracts text, indexes content, and returns a Library item that chat can attach immediately.
- `GET /api/library/reports/{report_id}/file` streams the original uploaded file back through an ownership-checked path.

**Shared-key constraints** (applied in `advisor` and `onboarding`):
- `check_shared_key_rate_limit(user_id)` called before LLM operations.
- Shared-key users: model forced to `SHARED_LLM_MODEL` (`claude-haiku-4-5`), `use_tools=False` (agentic disabled).

**Journal post-create hooks** (`_run_post_create_hooks`):
Fired as `asyncio.create_task` (background, best-effort) after journal create/quick:
1. ChromaDB embed via `EmbeddingManager.add_entry`.
2. Thread detection via `ThreadDetector.detect` (requires `config.threads.enabled` and successful embed).
3. Memory extraction via `MemoryPipeline.process_journal_entry` (requires `config.memory.enabled`).
Each step is independent try/except; step 2 is skipped if step 1 fails (needs embedding).

**Current implementation caveats:**
- `DELETE /api/journal/{filepath}` removes the markdown file only; unlike CLI and MCP delete paths, it does not currently remove embeddings or FTS rows.
- `memory.py` currently instantiates `FactStore` against global `intel.db`, while journal/advisor flows write and read per-user extracted memory from `~/coach/users/{safe_id}/memory.db`.
- `threads.py` currently expects `get_user_paths(user_id)["data_dir"]`, but `get_user_paths()` does not return that key, so the web thread routes are currently broken.

**Admin route** (`admin.py`):
`GET /api/admin/stats?days=30` requires `get_admin_user` (admin-only). Returns `get_usage_stats(days)`. Days param: 1–365.

**Insights route** (`insights.py`):
`GET /api/insights` — Queries `InsightStore.get_active()`. Query params: `type` (optional `InsightType`), `min_severity` (int, default 1), `limit` (int, default 20). Returns `list[InsightResponse]` where each item mirrors an `insights` table row. Backed by `InsightStore` in `~/coach/intel.db`.

**Settings route** (`settings.py`):
`GET /api/settings` — Returns `SettingsResponse` with bool mask (no raw keys exposed).
`PUT /api/settings` — Encrypts each field via `set_user_secret`. Accepted fields: `llm_provider`, `llm_model`, `llm_api_key`, `tavily_api_key`, `github_token`, `eventbrite_token`.
`POST /api/settings/test-llm` — Instantiates LLM provider with stored key, calls `generate("ping")` with `max_tokens=5`. Returns `{ok, provider, response}`.

**Pageview / engagement / user routes:**
`POST /api/pageview` — Records `page_view` usage event (fail-silent analytics).
`POST /api/engagement` — Records engagement event in `engagement_events` table (validated event type).
`GET /api/engagement/stats` — Returns `get_engagement_stats(user_id, days=30)`.
`GET /api/user/me` — Returns `{name, email}` from JWT.
`PUT /api/user/me` — Updates display name in `users` table.

#### Route Summary Table

| Module | Prefix | Key Routes |
|---|---|---|
| `settings` | `/api/settings` | `GET/PUT` settings, `POST /test-llm` |
| `journal` | `/api/journal` | list/create/read/update/delete + `POST /quick`; post-create hooks |
| `advisor` | `/api/advisor` | `POST /ask`, `POST /ask/stream`, conversation CRUD, attachment-aware chat turns |
| `library` | `/api/library` | report CRUD, PDF upload, file download, search-backed Library browsing |
| `goals` | `/api/goals` | list/create, check-in, status, milestones, progress |
| `intel` | `/api/intel` | recent/search/health, RSS feeds, watchlist CRUD, follow-ups, trending, scrape |
| `research` | `/api/research` | List topics, `POST /run` |
| `onboarding` | `/api/onboarding` | Chat interview, profile-status, feeds (see profile.md) |
| `briefing` | `/api/briefing` | Daily briefing, recommendations |
| `recommendations` | `/api/recommendations` | List/get/update recommendations |
| `engagement` | `/api/engagement` | Log events, get stats |
| `profile` | `/api/profile` | `GET/PATCH` profile |
| `user` | `/api/user` | `GET/PUT /me` |
| `pageview` | `/api/pageview` | `POST` page view |
| `greeting` | `/api/greeting` | Cached personalized greeting for chat-first home |
| `admin` | `/api/admin` | `GET /stats` (admin only) |
| `insights` | `/api/insights` | `GET` active insights |
| `memory` | `/api/memory` | list/get/delete facts, stats |
| `threads` | `/api/threads` | list/detail routes; currently miswired |
| `suggestions` | `/api/suggestions` | merged brief + recommendation suggestions |

#### Invariants

- Per-user data isolation: all storage operations use `get_user_paths(user["id"])`, never shared paths except `intel_db`.
- `AdvisorEngine` is instantiated fresh per request (no singleton).
- Path traversal check: `resolved.is_relative_to(storage.journal_dir)` on all file-path route params.
- `asyncio.to_thread` used for all synchronous blocking operations (LLM calls, file I/O).
- Conversation ownership verified via `conversation_belongs_to` before all conversation operations.
- Attachment IDs passed into advisor routes must resolve to Library items owned by the same user.

#### Error Handling

Common patterns:

| Condition | Response |
|---|---|
| Missing API key for LLM routes | HTTP 400 or 422 `"No API key configured"` |
| Conversation not found / wrong user | HTTP 404 |
| Attachment not found / wrong user | HTTP 404 |
| Invalid PDF upload | HTTP 400 with validation detail |
| Path traversal attempt | HTTP 400 `"Invalid path"` |
| Entry not found | HTTP 404 `"Entry not found"` |
| ValueError from storage | HTTP 400 with detail |
| LLM call failure (onboarding) | HTTP 502 `"LLM call failed"` |
| Rate limit exceeded | HTTP 429 with `Retry-After` header |
| General exception (advisor) | HTTP 500 with exception string |

Post-create hooks (embed, threads, memory): all exceptions caught and logged as warnings; never propagate to HTTP response.

---

## Cross-Cutting Concerns

### Data Isolation Model

```
~/coach/
  intel.db          ← global (shared across all users)
  context_cache.db  ← greeting cache + RAG context cache
  users.db          ← users, secrets, conversations, engagement
  users/
    {safe_user_id}/
      journal/      ← markdown files (includes goals with goal_type field)
      chroma/       ← ChromaDB embeddings
      recommendations/
      library/
      profile.yaml
      memory.db     ← per-user extracted memory used by journal/advisor flows
      threads.db    ← per-user recurring-thought storage used by journal/advisor flows
```

`safe_user_id` replaces `:` → `_` (OAuth provider prefix separator).

### Secret Storage Model

User secrets flow:
1. Plaintext value arrives in `PUT /api/settings` body.
2. `set_user_secret(user_id, key, value, fernet_key)` → `encrypt_value(fernet_key, value)` → stored in `user_secrets` table.
3. `get_api_key_for_user(user_id)` decrypts on demand.
4. `SettingsResponse` never exposes raw values — only bool flags and last-4-char hints.

Fernet key = `SECRET_KEY` env var. Must be stable across deploys; changing it makes all stored secrets unreadable.

### Shared Key / Lite Mode

Users without their own LLM API key use a server-side shared key. Constraints:
- Model forced to `claude-haiku-4-5`
- Agentic tools disabled (`use_tools=False`)
- Rate limit: 30 req/24h + 1 req/10s burst
- Error message: `"Lite mode limit reached — add your own API key in Settings for unlimited access"`

Detection: `get_api_key_with_source(user_id)[1] == "shared"`.

### Startup Sequence

1. SQLite `init_db()` — creates tables if absent.
2. `_verify_secret_key()` — canary encrypt/decrypt. Hard fail on any issue.
3. First request — `get_config()` cached, user auto-registered via `get_or_create_user`.

---

## Test Expectations

- JWT auth: test with valid token, expired token, missing sub, missing secret.
- `get_or_create_user`: test new user creation, existing user update, secret migration from duplicate email.
- `encrypt_value` / `decrypt_value`: roundtrip, wrong key returns None, never raises.
- `check_shared_key_rate_limit`: daily limit enforcement, burst enforcement, window pruning.
- Journal routes: CRUD, path traversal rejection, post-create hooks mocked (not executed in tests).
- Advisor route: mock `AdvisorEngine.ask`, test conversation creation, history trimming, rate limiting.
- Settings route: verify raw keys never returned in response, `SettingsResponse` only has bool/hint.
- Admin route: test 403 for non-admin, 200 for admin.
- `get_user_paths`: verify per-user isolation (different users → different paths).
- SSE streaming: hard to test end-to-end; mock queue behavior.
- Mock: LLM calls, ChromaDB, filesystem (use temp dirs from conftest).
- Multi-user isolation: `tests/web/conftest.py` provides two JWT users; key behaviors must be tested with both users to verify no cross-contamination.

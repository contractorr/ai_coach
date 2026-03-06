# Greeting Cache

## Overview

Pre-computed personalized greeting for the chat-first home page. Uses cheap LLM (Haiku) to generate a 3-5 sentence opening from current user state, cached in SQLite with 4h TTL and event-driven invalidation. Replaces the `BriefingPanel` dashboard as the primary home page experience.

## Dependencies

**Depends on:** `advisor/context_cache`, `web/deps`, `profile/storage`, `advisor/goals`, `advisor/recommendation_storage`, `intelligence/scraper`, `llm`
**Depended on by:** `web/routes/greeting` (API), `web/routes/journal` (invalidation), `web/routes/goals` (invalidation), `intelligence/scheduler` (invalidation)

---

## Components

### GreetingGenerator

**File:** `src/advisor/greeting.py`
**Status:** Stable

#### Behavior

Generates a personalized greeting string from assembled briefing context. Uses cheap LLM with 200 max tokens. Context is lighter than full `/api/briefing` — only profile name, stale goals (top 3), top recommendations (2), and recent intel (2).

- `GREETING_TTL = 14400` (4 hours)
- `STATIC_FALLBACK` — hardcoded string for first-visit / LLM failure
- `make_greeting_cache_key(user_id)` → `f"greeting_v1_{safe_user_id(user_id)}"` (unhashed, enables LIKE-based bulk invalidation)
- `_build_greeting_prompt(briefing_ctx: dict) -> str` — assembles user-turn from context fields
- `generate_greeting(briefing_ctx: dict, cheap_llm) -> str` — calls LLM, 200 max tokens
- `get_cached_greeting(user_id, cache) -> str | None` — reads from ContextCache with TTL override
- `cache_greeting(user_id, cache, text)` — writes to ContextCache
- `invalidate_greeting(user_id, cache)` — deletes single user's greeting
- `GREETING_PROMPT_SYSTEM` — system prompt instructing 3-5 sentence personalized opening

#### Inputs / Outputs

| Function | Params | Returns |
|----------|--------|---------|
| `make_greeting_cache_key` | `user_id: str` | `str` |
| `_build_greeting_prompt` | `briefing_ctx: dict` (keys: `name`, `stale_goals`, `recommendations`, `intel`) | `str` |
| `generate_greeting` | `briefing_ctx: dict`, `cheap_llm: LLMProvider` | `str` |
| `get_cached_greeting` | `user_id: str`, `cache: ContextCache` | `str \| None` |
| `cache_greeting` | `user_id: str`, `cache: ContextCache`, `text: str` | `None` |
| `invalidate_greeting` | `user_id: str`, `cache: ContextCache` | `None` |

#### Invariants

- Greeting generation never blocks the HTTP response
- Greeting cache is per-user (keyed by safe_user_id)
- Scraper invalidation is all-users (prefix-based delete)
- LLM failure → static fallback cached for 5min (avoids retry storm)
- Missing profile/goals/intel → greeting with available data only

#### Error Handling

- LLM call fails → catch, log warning, cache `STATIC_FALLBACK` with 5min TTL
- Missing context fields → prompt built from available data only, no error raised

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `GREETING_TTL` | `14400` (4h) | Hardcoded constant |
| `GREETING_ERROR_TTL` | `300` (5min) | Hardcoded constant |
| Max tokens | `200` | Hardcoded in `generate_greeting()` |

---

### ContextCache Extensions

**File:** `src/advisor/context_cache.py`
**Status:** Stable

#### Behavior

Two new public methods:
- `invalidate(cache_key: str)` — public alias for `_delete()`
- `invalidate_by_prefix(prefix: str)` — `DELETE FROM context_cache WHERE key LIKE ?` with `prefix%` pattern

`get()` gains optional `ttl: int | None = None` param to override default TTL per call.

---

### Greeting API

**File:** `src/web/routes/greeting.py`
**Status:** Stable

#### Behavior

- `GET /api/greeting` → `GreetingResponse(text: str, cached: bool, stale: bool)`
- Cache check → return cached greeting (`cached=True, stale=False`)
- No cache → return `STATIC_FALLBACK` (`cached=False, stale=True`) + spawn background task to generate & cache
- `_generate_and_cache_greeting(user_id)` — async background task: assemble context, call cheap LLM, cache result
- `_assemble_greeting_context(user_id)` — lightweight reads: `ProfileStorage`, `GoalTracker` (stale goals top 3), `RecommendationStorage` (top 2), `IntelStorage.get_recent(limit=2)`

#### Inputs / Outputs

| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/greeting` | GET | `{"text": str, "cached": bool, "stale": bool}` |

#### Error Handling

- Any assembly/LLM failure → static fallback, `stale=True`
- Background task exceptions caught and logged, never propagated

---

### Cache Invalidation Triggers

| Trigger | File | Hook point | Scope |
|---------|------|------------|-------|
| Journal create/update | `src/web/routes/journal.py` | End of `_run_post_create_hooks()` | Single user |
| Goal check-in | `src/web/routes/goals.py` | After `tracker.check_in_goal()` | Single user |
| Scraper batch complete | `src/intelligence/scheduler.py` | End of `_run_async()` | All users (prefix) |

---

### Frontend

**File:** `web/src/app/(dashboard)/page.tsx`
**Status:** Stable

#### Behavior

Full-page inline chat replacing `BriefingPanel` + `ChatSheet`:
- Fetches `GET /api/greeting` + `GET /api/user/me` on mount
- Greeting pre-populated as first assistant message bubble
- SSE streaming for advisor asks (pattern from `BriefInlineChat.tsx`)
- Mode toggle: ask (Send icon) vs capture (PenLine icon → `POST /api/journal/quick`)
- Full-height layout, no dashboard sections
- If `stale === true`, retry greeting fetch once after 5s

#### Deleted Files

- `web/src/components/BriefingPanel.tsx` — only import was `page.tsx`

#### Retained Files

- `ChatSheet.tsx` — advisor page uses it
- `BriefInlineChat.tsx` — may be used elsewhere
- `src/web/routes/briefing.py` + `src/advisor/daily_brief.py` — MCP compat

---

## Test Expectations

- `tests/advisor/test_greeting.py`: prompt building from context, cache key format, generate with mocked LLM, static fallback on LLM error
- `tests/web/test_greeting_routes.py`: cached return (200, cached=True), stale fallback (200, stale=True), invalidation via journal/goal hooks
- Mock: LLM provider, ContextCache, ProfileStorage, GoalTracker, IntelStorage

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Python (primary) and TypeScript (frontend). Python uses uv/uvx for package management with virtual environments (not conda). TypeScript uses npm with Node.js 18+.

## Commands

```bash
# Activate venv (do this first)
source .venv/bin/activate

# Install
pip install -e ".[dev]"              # dev deps
pip install -e ".[all-providers]"    # all LLM providers
pip install -e ".[web]"             # FastAPI backend
pip install -e ".[dev,all-providers,web]"  # everything (matches CI)

# Test
pytest                                          # all tests
pytest tests/advisor/test_engine.py::test_ask_advice -v  # single test
pytest tests/web/ -v                            # web API only
pytest --cov=src --cov-report=term-missing -v   # with coverage (fail_under=55)

# Lint & format
ruff check src tests
ruff format src tests

# Type check (advisory, not enforced in CI)
mypy src/ --ignore-missing-imports

# Web app
uvicorn src.web.app:app --reload --port 8000  # backend
cd web && npm install && npm run dev            # frontend (port 3000)
```

Tests require `ANTHROPIC_API_KEY=test-key` in env. Async tests use `pytest-asyncio` with `asyncio_mode = "auto"` globally. Ruff ignores `E501`.

### Test patterns

Root `conftest.py` provides temp dirs, mock LLM provider, sample data, and httpx mocks. Web tests (`tests/web/conftest.py`) provide a `TestClient` with patched env + two JWT users for multi-user isolation. MCP tests auto-reset `bootstrap._components` singleton between runs. Check conftest files for available fixtures.

## Architecture

RAG-based personal AI advisor. Journal entries + external intelligence scrapers feed a retrieval-augmented generation pipeline. Runs as CLI (`coach`), FastAPI+Next.js web app, or MCP server.

### Core modules (all under `src/`)

- **advisor/** — `AdvisorEngine` with two modes and dual LLM instances (see below)
- **journal/** — Markdown files with YAML frontmatter, ChromaDB embeddings, semantic+keyword search, KMeans trend detection, sentiment analysis, entry templates
- **intelligence/** — 14 source files in `sources/` (19 scraper classes — `ai_capabilities.py` contains 6) inheriting `BaseScraper` (HN, GitHub, arXiv, Reddit, RSS, Product Hunt, YC Jobs, Google Patents, AI capabilities, events, GitHub issues, Crunchbase, Google Trends, Indeed). Only HN+RSS enabled by default. SQLite storage with URL+content-hash dedup, APScheduler
- **research/** — Deep research: topic selection → web search (Tavily or DuckDuckGo fallback) → LLM synthesis → reports
- **llm/** — Provider factory with auto-detection from env vars. Unified `LLMProvider` interface: Claude/OpenAI/Gemini
- **profile/** — `UserProfile` Pydantic model (YAML-backed). `ProfileInterviewer` for LLM-driven onboarding (5-7 turns, force-extraction fallback). Two rendering modes: `summary()` (compact) and `structured_summary()` (multi-section XML)
- **cli/** — Click CLI (`coach` command). Pydantic config validation. Structlog logging
- **memory/** — Standalone memory package for persistent user memory (facts, context)
- **library/** — Content library management
- **services/** — Shared service layer
- **web/** — FastAPI backend: JWT auth (python-jose), Fernet-encrypted secret storage, per-user data isolation at `~/coach/users/{safe_user_id}/`. Global intel DB stays shared. 24 route modules. `get_or_create_user()` auto-registers on first request
- **curriculum/** — Structured learning system: content scanner, SQLite store, SM-2 spaced repetition, LLM question generation, Bloom's taxonomy grading, teach-back prompts, pre-reading questions, cross-guide chapter connections (ChromaDB embeddings)
- **coach_mcp/** — 52 MCP tools across 13 modules (journal, goals, intel, recommendations, research, reflect, profile, projects, insights, brief, memory, threads, curriculum)

### Advisor deep dive

Two modes in `AdvisorEngine.ask()`:
- **Agentic** (`use_tools=True`) — `AgenticOrchestrator` + `ToolRegistry`, LLM decides what to look up via tool calls
- **Classic RAG** — single-shot `RAGRetriever.get_combined_context()` + LLM

Dual LLM instances: `self.llm` (expensive) + `self.cheap_llm` (critic/scoring). Dynamic journal:intel weighting (default 70:30, adjusted from engagement data via `compute_dynamic_weight()`). SQLite-backed `ContextCache`. Memory (`<user_memory>` XML) and recurring thoughts (`<recurring_thoughts>` XML) injected into prompts.

### Web frontend (`web/`)

Next.js 16 + React 19 + TypeScript + Tailwind v4 + shadcn/ui. NextAuth v5 beta (GitHub/Google OAuth). JWT from NextAuth passed as `Authorization: Bearer` to FastAPI backend — `NEXTAUTH_SECRET` must match both sides. Middleware protects all routes except login/privacy/terms/api/auth.

### Data flow

1. Journal entries → markdown files in `~/coach/journal/` + ChromaDB embeddings + sentiment
2. Scrapers → SQLite `~/coach/intel.db` with dedup
3. Recommendations → markdown files in `~/coach/recommendations/`
4. Query → RAG retrieval (journal+intel, dynamic weighting) → profile + memory + threads context → LLM → advice
5. Background: scheduler runs scrapes + weekly reviews via `coach daemon`

### Cross-cutting

- **Retries:** Tenacity exponential backoff on HTTP/LLM calls (`cli/retry.py`)
- **Rate limiting:** Token bucket per source (`cli/rate_limit.py`)
- **Security:** Path traversal protection, URL scheme validation, API key redaction, content length limits, Fernet encryption for user secrets in web mode
- **Observability:** `observability.py` counters/timers, structlog correlation IDs

## Specs

Two-tier system under `specs/`. See [`specs/README.md`](specs/README.md) for full index.

- **`specs/functional/`** — PM-authored, user-facing: problem, desired behavior, acceptance criteria, edge cases. No code.
- **`specs/technical/`** — Implementation reference: component signatures, invariants, error paths, config.

**Workflow for ALL changes (mandatory order):**

1. Update or create the functional spec in `specs/functional/` first
2. Update or create the technical spec in `specs/technical/` second
3. Implement code changes last

Never skip steps or reorder. Even small changes must flow: functional spec → technical spec → code. When modifying existing behavior, update the relevant functional spec for acceptance criteria and edge cases before touching technical spec or code.

## Feature Status

Core (stable): journal, intelligence scrapers, RAG retrieval, advisor Q&A, recommendations, conversation storage, library (reports + PDF uploads)
Experimental (enabled by default): goal tracking, deep research, trend clustering, memory, threads, insights, suggestions, signals, engagement scoring, nudges (CLI), trending radar, goal-intel matching, AI capabilities KB, capability horizon model, query analysis/decomposition, thread inbox state machine, curriculum/learn (SM-2 spaced repetition, Bloom's taxonomy quizzes, 327 chapters across 50 guides)
Infrastructure: heartbeat (invisible), pageview tracking, feed catalog, user deletion, onboarding feeds, attachments
Removed: mood analysis, burnout detection, momentum detection, predictions, skill gap analyzer (merged into advisor prompt mode)
Legacy config present: `learning_paths` key in config.example.yaml + migration file (`advisor/migrate_learning_paths.py`) — feature merged into goal milestones

## Adding a new intelligence source

1. Create scraper in `src/intelligence/sources/` inheriting `BaseScraper`
2. Implement `source_name` property + `scrape()` async method
3. Register in `scheduler.py` → `_init_scrapers()`

## MCP Server

`src/coach_mcp/` exposes 52 tools across 13 modules. Claude Code does the reasoning; MCP server provides data + context retrieval only — no LLM calls in the MCP layer. Tool convention: `TOOLS = [(name, schema_dict, handler_fn), ...]` per module, loaded lazily and cached in `server.py`.

```bash
python -m coach_mcp  # stdio transport, configured in .mcp.json for auto-discovery
```

## Config

`~/coach/config.yaml` (see `config.example.yaml`). Pydantic-validated. Supports env var interpolation (`${ANTHROPIC_API_KEY}`). Lookup order: `./config.yaml` → `~/.coach/config.yaml` → `~/coach/config.yaml`.

Notable config: `llm.extended_thinking`, `sources.deduplicate_rss_sources` (auto-disables dedicated scrapers when RSS equivalents exist), `agent.autonomous.*` for agentic features, `memory.*` and `threads.*` for context persistence.

## CI

- **test.yml** — Python 3.11 + 3.12 matrix, `pytest --cov-fail-under=50`, Codecov on 3.12
- **lint.yml** — `ruff check` + `ruff format --check` + `mypy` (continue-on-error). Separate job: `npm ci && npm run lint && npm run build` in `web/`
- **deploy.yml** — push to main triggers test then SSH docker compose deploy
- **validate-deploy.yml** — validates docker-compose files have required volume mounts (curriculum content, etc.)

## Deployment

**Pre-deployment validation:**
```bash
./scripts/validate-deployment.sh
```

**Critical docker-compose requirements:**
- Backend MUST mount `./content:/app/content:ro` for curriculum guides
- Both `docker-compose.yml` and `docker-compose.prod.yml` must have identical backend volume mounts
- Run validation script before any deployment to catch missing mounts

**Remote deployment:**
```bash
ssh root@<server> "cd /root/stewardme && git pull && docker compose -f docker-compose.prod.yml up -d --build"
```

## Output Conventions

When writing large documents (specs, reports, analyses), write in incremental chunks of ~150 lines using Write followed by Edit/append. Never output an entire large file in a single response.

## Remote Server Access

When the user mentions a 'remote server' or 'production', always ask for or confirm SSH connection details (host, user, key path) before attempting to connect. Check CLAUDE.md env vars or prior session context first.

## Data Access

For data queries, always clarify the data source FIRST: local DuckDB/SQLite, remote database via SSH, Snowflake, or another tool. Do not assume one over another.

## Development Workflow

After implementing changes from a GitHub issue or plan, always: 1) run the full test suite, 2) run lint, 3) commit with a descriptive message referencing the issue number, 4) push to remote. Do not stop at implementation without committing unless told otherwise.

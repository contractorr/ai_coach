# Contributing to StewardMe

## Getting started

```bash
git clone https://github.com/contractorr/stewardme.git
cd stewardme
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,web,all-providers]"
pre-commit install

# Frontend
cd web && npm install && cd ..

# Verify
ANTHROPIC_API_KEY=test-key pytest
ruff check src tests
pre-commit run --all-files
```

## Project structure

```
src/
├── journal/        # Markdown storage, ChromaDB embeddings, search, trends
├── advisor/        # LLM + RAG orchestration, recommendations, goals
├── intelligence/   # Async scrapers, SQLite storage, scheduler
├── research/       # Deep research agent
├── llm/            # Provider factory (Claude/OpenAI/Gemini)
├── profile/        # User profile
├── memory/         # Persistent user memory (facts, context)
├── library/        # Content library management
├── services/       # Shared service layer
├── coach_mcp/      # MCP server (46 tools across 12 modules)
├── web/            # FastAPI backend
├── cli/            # Click CLI + config
web/                # Next.js frontend
specs/              # Functional + technical specs
tests/              # Mirrors src/ structure
```

## Workflow

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Update or create the **functional spec** in `specs/functional/` (acceptance criteria, edge cases)
4. Update or create the **technical spec** in `specs/technical/` (component signatures, invariants)
5. Implement code changes
6. Run checks: `pre-commit run --all-files && ANTHROPIC_API_KEY=test-key pytest`
7. Commit with a descriptive message
8. Open a PR against `main`

> **Spec-first rule:** All changes follow functional spec → technical spec → code, in that order. Even small changes need spec updates if they affect behavior.

## Code style

- **Python:** Ruff for linting and formatting (E501 ignored — no line length cap)
- **TypeScript:** Next.js defaults, Tailwind CSS for styling
- **Git hooks:** `pre-commit` runs Ruff and frontend ESLint before each commit
- **Tests:** pytest with `asyncio_mode = "auto"`. Tests use `ANTHROPIC_API_KEY=test-key`
- **Types:** mypy is advisory (not enforced in CI), but appreciated

## What to work on

Check [GitHub Issues](https://github.com/contractorr/stewardme/issues) — look for `good first issue` labels.

Some areas that could use help:

- **New intelligence scrapers** — inherit `BaseScraper`, implement `scrape()`. See `src/intelligence/sources/` for examples
- **Frontend polish** — empty states, loading skeletons, mobile responsiveness
- **Testing** — increase coverage, add integration tests
- **Documentation** — usage guides, screenshots, video walkthroughs
- **New LLM providers** — implement `LLMProvider` interface in `src/llm/`
- **Performance** — ChromaDB query optimization, scraper parallelism

## Adding a scraper

1. Create `src/intelligence/sources/my_source.py`
2. Inherit `BaseScraper`, implement `source_name` property and `async scrape()` method
3. Register in `src/intelligence/scheduler.py` → `_init_scrapers()`
4. Add tests in `tests/intelligence/`

## Adding an LLM provider

1. Create `src/llm/my_provider.py`
2. Implement the `LLMProvider` interface
3. Register in `src/llm/factory.py`
4. Add tests

## Pull request guidelines

- Keep PRs focused — one feature or fix per PR
- Include tests for new functionality
- Update docs if the change affects user-facing behavior
- CI must pass (tests + lint)

## Running the full stack locally

```bash
# Terminal 1: backend
source .venv/bin/activate
cp .env.example .env  # fill in values
uvicorn src.web.app:app --reload --port 8000

# Terminal 2: frontend
cd web && npm run dev

# Terminal 3: tests (optional)
ANTHROPIC_API_KEY=test-key pytest --watch
```

## Questions?

Open a [GitHub Discussion](https://github.com/contractorr/stewardme/discussions) or file an issue.

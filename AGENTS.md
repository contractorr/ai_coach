# AGENTS.md

Agent-facing repo guide for StewardMe. Use this file as the canonical starting point for Codex, Claude Code, and similar tools.

## First read

- Canonical developer workflow lives in `docs/development.md`.
- Machine-readable feature ownership and validation hints live in `specs/manifest.yaml`.
- Product behavior is defined in `specs/functional/`.
- Implementation expectations live in `specs/technical/`.
- Shared UX rules live in `specs/foundations/`.
- For behavior changes, follow: functional spec -> technical spec -> code.

## Canonical setup

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1 -WithWeb -WithAllProviders
```

Cross-platform, manual:

```bash
uv sync --frozen --extra dev --extra web --extra all-providers
npm ci --prefix web
```

Prefer `uv`-based commands because CI uses them.

## Canonical commands

- Fast backend tests: `uv run pytest -m "not slow and not web and not integration" --durations=20`
- Coverage slice: `uv run pytest -m "not slow and not web and not integration" --cov=src --cov-report=term-missing --durations=20`
- Web tests: `uv run pytest tests/web/ -q`
- Extended suites: `uv run pytest -m "web or integration or slow" --durations=20`
- Lint: `uv run ruff check src tests`
- Format: `uv run ruff format src tests`
- Type check: `uv run mypy src/ --ignore-missing-imports`
- Frontend lint: `npm --prefix web run lint`
- Frontend build: `npm --prefix web run build`

If `just` is installed, these are wrapped in the root `justfile`.

## Review workflow

For any non-trivial change:

1. Read the relevant functional spec.
2. Read the matching technical spec.
3. Inspect the narrowest affected module(s) before editing.
4. Prefer targeted tests over broad reruns while iterating.
5. Before finishing, run the smallest meaningful validation slice plus lint if code changed materially.

## Repo map

- `src/advisor/`: advisor orchestration, RAG, prompts, recommendations
- `src/curriculum/`: learning catalog, progress, assessments, review logic
- `src/intelligence/`: scrapers, storage, scheduler, radar, signals
- `src/journal/`: markdown storage, search, embeddings, trends, threads
- `src/memory/`: persistent fact memory and consolidation
- `src/research/`: research planning and synthesis
- `src/web/`: FastAPI models, deps, routes, backend app
- `web/`: Next.js frontend
- `tests/`: mirrors major backend areas, plus web and integration suites

## Hotspots

These files have high blast radius and should be edited carefully:

- `src/web/routes/curriculum.py`
- `src/curriculum/store.py`
- `src/memory/store.py`
- `src/advisor/recommendations.py`
- `src/web/models.py`

When working in these areas, prefer small diffs and run targeted tests immediately.

## Contract changes

Backend and frontend payload contracts are exported from FastAPI for frontend use.
When changing request or response payloads:

- update the backend schema in `src/web/models.py`
- regenerate contracts with `just contracts-generate`
- update any workspace-specific frontend type under `web/src/types/` that extends or narrows the generated transport shape
- run at least the relevant route tests and a frontend build if the change is user-facing

## Test notes

- Tests use markers: `unit`, `web`, `integration`, `slow`, `serial`.
- The default fast slice is the same one used in CI.
- Some local environments use `venv/`; the preferred repo-local environment going forward is `.venv`, but `uv run ...` avoids activation assumptions.

## Pull requests

Use the pull request template. It asks for:

- linked issue/specs
- summary of behavior changes
- validation performed
- explicit acknowledgement of spec and test impact

## Avoid

- broad refactors mixed with feature work
- changing generated or contract-heavy payloads without updating both backend and frontend consumers
- editing multiple large hotspot modules in one pass unless the change truly requires it

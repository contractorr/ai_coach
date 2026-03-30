default:
    @just --list

bootstrap:
    powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1

bootstrap-web:
    powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1 -WithWeb

bootstrap-full:
    powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1 -WithWeb -WithAllProviders

sync:
    uv sync --frozen --extra dev --extra web --extra all-providers

test-fast:
    uv run pytest -m "not slow and not web and not integration" --durations=20

specs-check:
    uv run pytest tests/test_repo_manifest.py tests/test_specs_harness.py -q

test-advisor:
    uv run pytest tests/advisor/ tests/web/test_advisor_routes.py -q

test-curriculum:
    uv run pytest tests/curriculum/ tests/web/test_curriculum_routes.py -q

test-intelligence:
    uv run pytest tests/intelligence/ tests/web/test_intel_routes.py -q

test-journal:
    uv run pytest tests/journal/ tests/web/test_journal_routes.py tests/web/test_journal_mind_map_routes.py -q

test-memory:
    uv run pytest tests/memory/ tests/web/test_memory_routes.py -q

test-settings:
    uv run pytest tests/web/test_settings.py tests/web/test_settings_toggles.py tests/web/test_profile_routes.py tests/web/test_user_store.py -q

test-web:
    uv run pytest tests/web/ -q

test-extended:
    uv run pytest -m "web or integration or slow" --durations=20

coverage:
    uv run pytest -m "not slow and not web and not integration" --cov=src --cov-report=term-missing --durations=20

lint:
    uv run ruff check src tests

format:
    uv run ruff format src tests

typecheck:
    uv run mypy src/ --ignore-missing-imports

frontend-install:
    npm ci --prefix web

frontend-lint:
    npm --prefix web run lint

frontend-typecheck:
    npm --prefix web run typecheck

frontend-build:
    npm --prefix web run build

e2e-smoke:
    npm --prefix web run test:e2e

contracts-export:
    uv run python scripts/export_openapi.py web/openapi.json

contracts-generate:
    just contracts-export
    npm --prefix web run contracts:generate

contracts-check:
    uv run python scripts/check_contracts.py

verify:
    just specs-check
    just lint
    just typecheck
    just test-fast

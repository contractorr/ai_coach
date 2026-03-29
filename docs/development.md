# Development Workflow

Canonical setup, validation, and contract commands live here. Keep this file,
`AGENTS.md`, and `justfile` aligned.

## Canonical Setup

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1 -WithWeb -WithAllProviders
```

Cross-platform:

```bash
uv sync --frozen --extra dev --extra web --extra all-providers
npm ci --prefix web
```

## Canonical Validation

- Fast backend slice: `just test-fast`
- Targeted advisor slice: `just test-advisor`
- Targeted curriculum slice: `just test-curriculum`
- Targeted intelligence slice: `just test-intelligence`
- Targeted journal slice: `just test-journal`
- Targeted memory slice: `just test-memory`
- Targeted settings/profile slice: `just test-settings`
- Web API slice: `just test-web`
- Python lint: `just lint`
- Python type check: `just typecheck`
- Frontend lint: `just frontend-lint`
- Frontend type check: `just frontend-typecheck`
- Frontend build: `just frontend-build`
- E2E smoke: `just e2e-smoke`

## Contract Workflow

When backend request or response payloads change:

1. Update the backend schema.
2. Regenerate exported contracts:

```bash
just contracts-generate
```

3. Validate freshness:

```bash
just contracts-check
```

Generated artifacts:

- `web/openapi.json`
- `web/src/types/api.generated.ts`

Existing manual types under `web/src/types/` still exist for workspace-specific
frontend models. Prefer the generated API contract for new transport-layer work.

## Navigation Aids

- Feature-to-code map: `specs/manifest.yaml`
- Functional specs: `specs/functional/`
- Technical specs: `specs/technical/`
- Shared UX rules: `specs/foundations/`

## Working Rules

- Follow functional spec -> technical spec -> code.
- Prefer the narrowest validation slice that covers the edited files.
- Treat hotspot files as split candidates, not default extension points.

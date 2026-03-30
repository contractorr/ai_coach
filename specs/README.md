# Specs

This directory is the canonical spec system for StewardMe.

Use it in this order:

1. `specs/catalog.yaml`
2. `specs/manifest.yaml`
3. `specs/functional/`
4. `specs/technical/`
5. `specs/foundations/`

`catalog.yaml` tells agents and reviewers which specs are canonical and how the
spec tree is classified. `manifest.yaml` maps tracked features to code, tests,
and validation commands.

## Structure

```text
specs/
  HARNESS.md          # Agent workflow for spec-driven development
  catalog.yaml        # Machine-readable catalog of the spec tree
  manifest.yaml       # Machine-readable feature -> code/test/validation map
  functional/         # Product behavior: what users should experience
  technical/          # Implementation expectations: how the system should work
  foundations/        # Shared UX and design rules
```

## Workflow

For any non-trivial behavior change:

1. Find the tracked feature in `catalog.yaml` or `manifest.yaml`.
2. Read the matching functional spec.
3. Read the linked technical spec or specs.
4. Inspect the affected code paths.
5. Implement and validate.
6. Update specs if the behavior, architecture, ownership, or validation slice
   changed.

## Status Model

Tracked feature statuses:

- `draft`
- `ready_for_review`
- `approved`
- `partially_implemented`
- `implemented`
- `stable`
- `experimental`
- `archived`

Tracked module statuses:

- `draft`
- `stable`
- `updated`
- `experimental`
- `deprecated`
- `archived`

## Authoring Rules

- Functional specs stay user-facing and implementation-light.
- Technical specs describe architecture, contracts, invariants, and validation.
- Supporting specs refine a tracked feature or tracked module.
- Archive or delete retired specs instead of leaving them in the active tree as
  ambiguous references.

## Templates

- Functional template: `specs/functional/TEMPLATE.md`
- Technical template: `specs/technical/TEMPLATE.md`

Use the templates for new work. Existing older specs do not all follow the same
section layout yet, but the templates define the forward standard.

## Validation

Run these checks whenever the spec tree changes:

- `just specs-check`
- `uv run pytest tests/test_repo_manifest.py tests/test_specs_harness.py -q`

If a spec file is added, removed, moved, or archived, update both
`specs/catalog.yaml` and any affected `specs/manifest.yaml` entries in the same
change.

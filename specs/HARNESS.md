# AI Harness

This repo is set up for spec-driven development with AI agents, but the harness
only works if agents treat the spec files as first-class inputs instead of
optional background reading.

## Canonical Inputs

Read these in order for any non-trivial change:

1. `specs/catalog.yaml`
2. `specs/manifest.yaml`
3. relevant files under `specs/functional/`
4. matching files under `specs/technical/`
5. `docs/development.md`

Use `specs/catalog.yaml` to locate the authoritative spec set. Use
`specs/manifest.yaml` to jump from a tracked feature to the code paths, tests,
and validation commands that matter for implementation.

## Workflow

For behavior changes:

1. Identify the tracked feature in `specs/catalog.yaml` or `specs/manifest.yaml`.
2. Read the matching functional spec to confirm product intent.
3. Read the linked technical spec or specs to confirm implementation shape.
4. Inspect the narrowest affected code paths.
5. Implement.
6. Update specs if behavior, scope, ownership, or validation changed.
7. Run `just specs-check` plus the smallest relevant code validation slice.

For spec-only work:

1. Decide whether the doc is a tracked feature, tracked module, or supporting spec.
2. Update `specs/catalog.yaml` if you add, remove, move, or archive a spec file.
3. Update `specs/manifest.yaml` when a tracked feature changes code ownership,
   tests, or validation commands.
4. Keep templates aligned with the current authoring standard.

## What Counts As Complete

A repo change is not spec-driven unless all of these are true:

- A user-facing behavior change is reflected in the relevant functional spec.
- Implementation expectations are reflected in the relevant technical spec.
- Tracked features have an up-to-date manifest entry with code paths, tests, and
  validation commands.
- The spec catalog still matches the actual file layout under `specs/`.
- Validation includes `just specs-check` and the smallest meaningful runtime
  slice for the code touched.

## How To Classify Spec Files

- `tracked feature`: primary feature spec that agents should route to first for
  behavior changes
- `supporting spec`: cross-cutting or subordinate design doc that refines a
  tracked feature or module
- `tracked module`: primary technical spec for a code area or delivery surface
- `archived`: no longer authoritative for current implementation

Do not create duplicate tracked features for the same behavior area. Prefer
updating the existing feature spec and linking supporting docs.

## When To Move Or Remove Specs

Move a spec out of the main active set when:

- it documents a retired product shape
- it was replaced by a newer canonical spec
- it is now only historical context

When that happens:

- move the file into an archive location or delete it if the content is
  duplicated elsewhere
- remove or reclassify it in `specs/catalog.yaml`
- remove stale references from `specs/manifest.yaml`, README files, and PR
  guidance

## Authoring Rules

- Functional specs describe user-visible behavior, scope, and acceptance
  criteria. They should not depend on code-level implementation details.
- Technical specs describe architecture, invariants, contracts, data flow, and
  validation expectations.
- Supporting specs should say which tracked feature or module they refine.
- If a spec is superseded, mark it as archived in the catalog before it stops
  being referenced elsewhere.

## Required Guardrails

The following checks should stay green:

- `just specs-check`
- `tests/test_repo_manifest.py`
- `tests/test_specs_harness.py`

If these checks fail, the repo is no longer reliably navigable by AI agents.

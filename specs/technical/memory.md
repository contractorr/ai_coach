# Memory

**Status:** Updated for the simplified product model

## Overview

Memory remains the durable personalization layer. The main user-facing affordance is now the `What I know about you` section in Settings.

## Key Modules

- `src/web/routes/memory.py`
- memory extraction and storage services
- `web/src/app/(dashboard)/settings/page.tsx`

## Interfaces

- `GET /api/memory/facts?limit=50`
- `GET /api/memory/stats`
- `DELETE /api/memory/facts/{id}`

## Simplified Product Notes

- Memory stays transparent and user-controllable from Settings.
- Memory continues to inform advisor, suggestions, and prioritization behind the scenes.

## Confidence Lifecycle

- Facts persist in `steward_facts` with a mutable `confidence` score.
- Duplicate detections (`NOOP` with an `existing_id`) reinforce the active fact by `+0.05`, capped at `1.0`.
- Resolver-driven `UPDATE` and `DELETE` flows decay the old fact by `0.15` before setting `superseded_by`.
- `updated_at` doubles as the last-reinforced timestamp; optional time decay uses it as the staleness signal.

## Current Implementation Notes

- Reinforcement is applied in `MemoryPipeline._execute(...)` by calling `FactStore.reinforce(...)` for `NOOP` resolutions.
- `FactStore.update(...)` accepts the new fact confidence and writes a decayed confidence to the superseded row before creating the replacement row.
- `FactStore.delete(...)` writes the decayed confidence to the soft-deleted row before removing it from active retrieval.
- `FactStore.apply_time_decay(...)` exists as an opt-in maintenance hook and is not scheduled by default.

## Cross-System Reinforcement

- Advisor retrieval computes a small temporary confidence bonus for facts whose `source_id` belongs to a strong recurring thread.
- This bonus affects retrieval ordering only; it does not create hidden undeletable facts or bypass Settings controls.

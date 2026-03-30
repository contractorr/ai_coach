---
id: memory-threads
category: tracked_feature
status: experimental
technical_specs:
- specs/technical/memory.md
- specs/technical/recurring-thread-inbox.md
foundations:
- specs/foundations/ux-guidelines.md
last_reviewed: '2026-03-30'
---

# Memory and Threads

**Status:** Updated for the simplified product model

## Purpose

Two internal capabilities are surfaced in simple places: durable memory facts in Settings and recurring threads in Radar. Users benefit from both without needing to learn them as standalone products.

## Product Placement

- Memory lives in `Settings` under `What I know about you`
- Threads live in `Radar` under the `Threads` tab
- Both support better capture, advice, and prioritization across the app

## Current Behavior

- Memory facts are inspectable and deletable from Settings.
- Threads cluster related journal activity and present clear next actions.
- A thread can be converted into a goal, research run, dossier, or dismissal from Radar.
- Repeated facts from later journal or feedback inputs reinforce the existing memory fact instead of creating duplicates.
- Contradicted facts lose confidence before they are superseded or deleted so history reflects weakening evidence.
- Strong recurring threads slightly strengthen related memory facts during advisor retrieval even though memory remains user-controllable from Settings.

## Memory Confidence Lifecycle

- New extracted facts start with the extractor-provided confidence.
- Near-duplicate restatements reinforce the active fact by `+0.05`, capped at `1.0`.
- Resolver-driven `UPDATE` and `DELETE` flows decay the previous fact by `0.15` before superseding it.
- Optional time decay exists as an implementation hook, but it is not scheduled by default in the current product.

## User Flows

- Open Settings to inspect and remove memory facts.
- Open Radar > Threads to review recurring themes.
- Turn a promising thread into action without leaving Radar.

## Key System Components

- `web/src/app/(dashboard)/settings/page.tsx`
- `web/src/app/(dashboard)/radar/page.tsx`
- `src/web/routes/memory.py`
- `src/web/routes/threads.py`

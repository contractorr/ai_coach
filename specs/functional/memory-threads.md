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

## User Flows

- Open Settings to inspect and remove memory facts.
- Open Radar > Threads to review recurring themes.
- Turn a promising thread into action without leaving Radar.

## Key System Components

- `web/src/app/(dashboard)/settings/page.tsx`
- `web/src/app/(dashboard)/radar/page.tsx`
- `src/web/routes/memory.py`
- `src/web/routes/threads.py`

# Capture Receipts

**Status:** Updated for the simplified product model

## Purpose

Capture receipts explain what the system learned from a note and suggest the next obvious action without overwhelming the user with internal jargon.

## Product Placement

- Surfaces: `Home` and the deeper Journal flow
- Related destinations: `Focus`, `Radar`, and the Journal shortcut
- Primary job: confirm capture and guide the next step

## Current Behavior

- Receipts stay short and plain-language.
- A receipt can mention extracted threads, memory facts, or follow-up actions.
- Where a thread is linked, the follow-up should point into Radar's `Threads` tab.

## User Flows

- Save a note from Home or Journal.
- Review what the system extracted.
- Jump into the most relevant follow-up action.

## Key System Components

- `src/web/routes/journal.py`
- `src/web/routes/memory.py`
- `src/web/routes/threads.py`
- Home and Journal receipt surfaces

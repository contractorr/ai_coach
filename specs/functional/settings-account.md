# Settings and Account

**Status:** Updated for the simplified product model

## Purpose

Settings owns account-level and advanced configuration tasks so everyday work can stay in Home, Focus, Radar, and Library.

## Product Placement

- Workspace: `Settings`
- Primary job: manage account, profile, model access, tracked topics, and memory facts
- Not intended as the primary day-to-day work surface

## Current Behavior

- Settings includes profile and key management.
- Tracked-topic configuration remains here as an advanced control.
- The `What I know about you` section shows memory facts, stats, and delete controls.

## User Flows

- Update account or model-access settings.
- Add or edit a tracked topic.
- Review and delete memory facts.

## Key System Components

- `web/src/app/(dashboard)/settings/page.tsx`
- `src/web/routes/settings.py`
- `src/web/routes/intel.py`
- `src/web/routes/memory.py`

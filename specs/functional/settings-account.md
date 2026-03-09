# Settings and Account

**Status:** Updated for the simplified product model

## Purpose

Settings owns account-level and advanced configuration tasks so everyday work can stay in Home, Focus, Radar, and Library. It is also where users manage model access, connect multiple AI providers, and control whether steward can use a multi-model council for higher-stakes questions.

## Product Placement

- Workspace: `Settings`
- Primary job: manage account, profile, model access, council preferences, tracked topics, and memory facts
- Not intended as the primary day-to-day work surface

## Current Behavior

- Settings includes profile and model-access management.
- Users can save separate API keys for multiple supported LLM providers without overwriting the others.
- Each provider entry has its own masked key state, replace/remove actions, and connection test.
- Settings explains when steward may use a multi-provider council for important or open-ended prompts, including the expected tradeoff of better deliberation versus higher latency and cost.
- Users can keep a default provider for normal fast answers while still allowing council mode when multiple working providers are available.
- Tracked-topic configuration remains here as an advanced control.
- The `What I know about you` section shows memory facts, stats, and delete controls.

## User Flows

- Add, replace, test, or remove one provider key without affecting the others.
- Review which providers are available for normal answers versus council-assisted answers.
- Update account or model-access settings.
- Add or edit a tracked topic.
- Review and delete memory facts.

## Key System Components

- `web/src/app/(dashboard)/settings/page.tsx`
- `web/src/components/SettingsSheet.tsx`
- `src/web/routes/settings.py`
- `src/web/routes/advisor.py`
- `src/llm/`
- `src/web/routes/intel.py`
- `src/web/routes/memory.py`

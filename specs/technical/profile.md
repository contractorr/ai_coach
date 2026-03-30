---
id: profile
category: tracked_module
status: stable
implements:
- profile-onboarding
- settings-account
code_paths:
- src/profile
- src/web/routes/onboarding.py
- src/web/routes/profile.py
- tests/profile
last_reviewed: '2026-03-30'
---

# Profile

**Status:** Updated for the simplified product model

## Overview

Profile data powers onboarding personalization, greeting text, recommendation grounding, and Settings-based account editing.

## Key Modules

- `src/web/routes/onboarding.py`
- `src/user_state_store.py`
- `src/web/routes/profile.py`
- `src/web/routes/user.py`
- `web/src/app/(dashboard)/onboarding/page.tsx`
- `web/src/app/(dashboard)/settings/page.tsx`

## Interfaces

- `POST /api/onboarding/start`
- `POST /api/onboarding/chat`
- `GET /api/onboarding/profile-status`
- `GET/PATCH /api/user/me`
- profile-dependent greeting and recommendation generation
- Settings-based profile editing

## Simplified Product Notes

- Onboarding captures only the profile context needed to personalize Home quickly.
- Additional profile refinement belongs in Settings, not the first-run flow.
- Blank onboarding messages are rejected server-side before they are persisted or counted toward the turn limit.
- Same-user onboarding requests are serialized in-process, and forced completion always clears the in-memory session even if the second LLM/save step fails.

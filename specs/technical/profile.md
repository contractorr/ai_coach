# Profile

**Status:** Updated for the simplified product model

## Overview

Profile data powers onboarding personalization, greeting text, recommendation grounding, and Settings-based account editing.

## Key Modules

- `src/web/routes/profile.py`
- `src/web/routes/user.py`
- `web/src/app/(dashboard)/onboarding/page.tsx`
- `web/src/app/(dashboard)/settings/page.tsx`

## Interfaces

- `GET/PATCH /api/user/me`
- profile-dependent greeting and recommendation generation
- Settings-based profile editing

## Simplified Product Notes

- Onboarding captures only the profile context needed to personalize Home quickly.
- Additional profile refinement belongs in Settings, not the first-run flow.

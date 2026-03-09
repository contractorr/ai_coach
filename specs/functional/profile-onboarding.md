# Profile and Onboarding

**Status:** Updated for the simplified product model

## Purpose

Onboarding should get the user to a personalized Home quickly. The goal is enough context to personalize Home, Focus, and Radar without forcing a long setup flow.

## Product Placement

- Entry path: onboarding flow
- Destination: `Home`
- Advanced setup remains reachable later in `Settings`

## Current Behavior

- The default path is name, model-access choice, onboarding chat, feed-topic selection, then Home.
- Users can continue in shared or lite mode without providing a personal API key.
- Topic selection configures the first Radar and recommendation experience.

## User Flows

- Save a display name.
- Choose model-access mode and complete the onboarding chat.
- Pick feed topics and land directly on Home.

## Key System Components

- `web/src/app/(dashboard)/onboarding/page.tsx`
- `src/web/routes/onboarding.py`
- `src/web/routes/settings.py`
- `src/web/routes/user.py`

---
id: profile-onboarding
category: tracked_feature
status: stable
technical_specs:
- specs/technical/profile.md
- specs/technical/web.md
foundations:
- specs/foundations/design-system.md
- specs/foundations/ux-guidelines.md
last_reviewed: '2026-03-30'
---

# Profile and Onboarding

**Status:** Updated for the simplified product model

## Purpose

Onboarding should get the user to a personalized Home quickly. The goal is enough context to personalize Home, Goals, and Radar without forcing a long setup flow.

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

## Feed Catalog and Onboarding Feeds

### Feed Catalog (`src/web/feed_catalog.py`)

A static catalog of curated RSS feeds organized into 11 categories:

- AI/ML
- Web Dev
- Systems/Infra
- Security
- Startups/VC
- Data Science
- DevOps/Cloud
- Mobile
- General Tech
- Open Source
- Blockchain/Web3

Each category carries a set of match keywords used for profile-based auto-selection.

### Profile Matching

`match_categories_to_profile(profile)` tokenizes the user's profile fields (interests, industries, technologies) and scores them against each category's keywords. `general_tech` is always included regardless of match score. The result is the subset of categories relevant to the user's background.

`feeds_for_categories(categories)` collects feeds for the matched categories, deduplicates by URL, and pads the list to a minimum of `MIN_FEEDS=5` using General Tech feeds if needed.

### Onboarding Routes

- `GET /api/onboarding/feed-categories` — returns the full catalog with categories pre-selected based on the current user's profile. Requires an existing profile; selection is advisory (user can change before confirming).
- `POST /api/onboarding/feeds` — accepts a list of selected category slugs and bulk-inserts the corresponding RSS feeds into `user_rss_feeds` for the authenticated user. Duplicate URLs are ignored.

### Onboarding Chat

The onboarding chat is LLM-driven and multi-turn:

- Maximum 15 turns before force-extraction fallback.
- Sessions are in-memory (keyed by user ID); no DB persistence during the conversation.
- Collects 13 profile fields (name, role, goals, interests, industries, technologies, etc.) plus 1–3 concrete near-term goals.
- At max turns the LLM is prompted to extract whatever has been collected so far and write the profile, even if incomplete.

# Settings & Account

**Status:** Implemented
**Author:** -
**Date:** 2026-03-07

## Problem

Users need a safe place to manage API keys, understand whether they are on shared/lite mode, update account-facing identity details, and delete their account data when needed.

## Users

All authenticated web users.

## Desired Behavior

### Managing AI settings

1. User can view whether provider settings and secret keys are configured.
2. Secrets are never returned in raw form; the product shows masked state only.
3. User can save or update LLM and research-related credentials.
4. User can test LLM connectivity after saving a key.
5. Long settings pages keep save progress visible even when the primary save action would otherwise fall below the fold.

### Lite mode

1. If the user has no personal LLM key, the product can fall back to shared/lite mode.
2. Lite mode is clearly explained in the UI.
3. Lite mode still supports the core product, but certain higher-cost capabilities remain limited.

### Radar inputs

1. User can add and remove custom RSS feeds for the intel radar.
2. User can maintain a watchlist of companies, technologies, roles, and themes.
3. Watchlist items capture a label, optional rationale, priority, and lightweight tags.

### Profile context

1. User can review and edit structured profile fields from settings without rerunning onboarding.
2. Stale profile state is surfaced inline.
3. User can restart onboarding from settings when a full refresh is easier than field-by-field editing.

Current interface scope:
- Settings is organized as a long-form workspace with section jump chips at the top.
- When provider or key settings change, a sticky bottom save bar appears so the user can save without scrolling to the page end.
- Account deletion remains isolated in a dedicated danger zone.

### Account identity

1. User can view and edit their display name.
2. The product prefers the app-level display name over the raw OAuth name when available.

### Account deletion

1. User can delete their account.
2. Account deletion removes stored user metadata and attempts best-effort cleanup of per-user filesystem data.

## Acceptance Criteria

- [ ] Settings endpoints return masked state rather than raw secrets.
- [ ] User can update settings and test LLM connectivity from the web product.
- [ ] Lite/shared mode is surfaced in the UI when the user lacks a personal key.
- [ ] User can manage custom RSS feeds and watchlist entries from settings.
- [ ] User can edit structured profile fields from settings and see stale-state messaging.
- [ ] Unsaved settings changes surface through a persistent save affordance.
- [ ] User can edit their display name.
- [ ] User can delete their account from the product.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User saves an invalid LLM key | Connectivity test fails with a clear error |
| User has no personal key | Product can continue in lite/shared mode |
| User edits settings near the top of the page | Sticky save bar keeps save/discard actions available without a full scroll |
| Name update fails | Settings UI remains usable; user can retry |
| File cleanup during delete partially fails | Account deletion succeeds and cleanup is logged as best effort |

## Out of Scope

- Billing and subscription management
- Multi-account switching in one session
- Secret export or key escrow features

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
- View estimated LLM cost breakdown by model for the last 30 days.
- Update account or model-access settings.
- Add or edit a tracked topic.
- Review and delete memory facts.

## User Deletion

Users can permanently delete their account and all associated data via a single self-service action.

### Behavior

- `DELETE /api/user/me` — authenticated endpoint, no request body required.
- Before deletion, an `account_deleted` event is logged for audit purposes.
- DB records are removed in FK-safe order: `user_secrets` → `onboarding_responses` → `engagement_events` → `usage_events` → `user_rss_feeds` → `users`.
- Filesystem cleanup (`shutil.rmtree($COACH_HOME/users/{safe_user_id}/)`) is best-effort; failure does not block the response. Path resolved via `get_coach_home()` (respects `COACH_HOME` env var).
- Returns `204 No Content` on success.
- After deletion the JWT is invalid; subsequent requests with the same token receive `401`.

### Re-onboarding After Deletion

- When a deleted user logs back in, `get_or_create_user()` auto-creates a new DB row with `onboarded=false`.
- The dashboard onboarding gate (`DashboardShell.tsx`) checks `has_profile` from `GET /api/settings`.
- `has_profile` is backed by the `users.onboarded` DB column — not filesystem state.
- If `has_profile` is false, the user is redirected to `/onboarding` regardless of API key / shared key status.
- On onboarding completion, `mark_onboarded()` sets the flag to true.

### User Flow Addition

- Delete account and all associated data from the Settings page.

## API Key Validation During Onboarding

Invalid API keys must never trap the user in a broken state.

### Behavior

- **Key entry:** After saving a key, a connectivity test (`POST /api/settings/test-llm`) runs. The onboarding chat phase is only entered on success. On failure, the user stays on the welcome/key-entry screen with an error toast.
- **Re-login with stale key:** When returning to onboarding with `llm_api_key_set: true`, the key is verified via test-llm before auto-advancing. If the stored key is invalid, `hasApiKey` is set to false and the user is routed to the welcome phase.
- **Mid-chat LLM failure:** If the onboarding chat auto-start or send fails (e.g. 502, bad key), the user is reset to the welcome phase with messages and turn cleared. Error toast explains the issue.

### Acceptance Criteria

- Entering an invalid API key does not advance past the welcome phase.
- A previously-saved invalid key does not auto-skip to chat on re-login.
- LLM errors during onboarding chat bounce the user back to welcome for key re-entry.
- Valid keys continue to work as before (save → test → advance to chat).

## Key System Components

- `web/src/app/(dashboard)/settings/page.tsx`
- `web/src/components/SettingsSheet.tsx`
- `src/web/routes/settings.py`
- `src/web/routes/advisor.py`
- `src/llm/`
- `src/web/routes/intel.py`
- `src/web/routes/memory.py`

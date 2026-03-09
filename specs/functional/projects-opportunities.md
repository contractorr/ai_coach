# Projects & Opportunities

**Status:** Implemented
**Author:** -
**Date:** 2026-03-07

## Problem

Users want help turning their profile and current market signals into concrete project opportunities, especially open-source issues to contribute to and project ideas they could pursue next.

## Users

Users who want practical opportunities derived from their skills, interests, and current intelligence.

## Desired Behavior

### Matching issues

1. User can request GitHub issues that match their profile.
2. System uses profile context plus recent intelligence to rank issue opportunities.
3. Each result includes title, URL, summary, tags, source, and a match score.

### Project ideas

1. User can request generated project ideas.
2. System uses profile, journal, and broader retrieval context to produce idea suggestions.
3. Generated ideas are returned as a lightweight list rather than a full project-management board.

Current interface scope:
- Web now exposes a dedicated `/projects` workspace in the dashboard navigation.
- The projects workspace supports two complementary tracks:
  - `Issue matches` for tactical open-source opportunities sourced from tracked GitHub issue intel
  - `Project ideas` for broader AI-generated bets based on profile and journal context
- Issue matches can be refreshed and narrowed by recent-day window and result count.
- Idea generation renders as a lightweight markdown artifact in-page rather than a full planning board.
- If idea generation cannot run because model access is unavailable or misconfigured, the workspace keeps the rest of the page usable and surfaces a clear inline error.

## Acceptance Criteria

- [ ] User can fetch matching issues from the product API.
- [ ] User can generate project ideas from the product API.
- [ ] User can review matching issues in a dedicated web workspace.
- [ ] User can filter issue matches by recency window and result count.
- [ ] User can review generated project ideas in-page.
- [ ] Matching uses available profile context when present.
- [ ] Missing profile data degrades gracefully rather than crashing the feature.
- [ ] Empty and error states keep the workspace understandable instead of leaving a blank screen.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No profile exists | Return weaker but still valid matches or ideas |
| No LLM key exists for idea generation | Product returns a clear configuration error |
| Matching pipeline fails | Feature returns an empty or error state without breaking the rest of the app |
| No recent GitHub issue intel exists | Workspace shows an actionable empty state and keeps idea generation available |

## Out of Scope

- Full project planning boards
- Automatic issue application or PR submission
- Persistent project-idea storage and editing UI

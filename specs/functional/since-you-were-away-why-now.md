# Since-You-Were-Away + Why-Now Surfaces

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

The product already produces suggestions, insights, and recommendation signals, but returning users still need help understanding what changed since they last engaged. Separately, recommendations can feel opaque when the user cannot immediately see why something is being surfaced now.

## Overview

This feature adds two related explanatory surfaces:

- `Since you were away` return briefings that summarize what changed during a user's absence
- `Why now` evidence chips on suggestions and recommendations that expose the immediate trigger behind each surfaced item

Together, these features make the product feel more alive, timely, and explainable.

## Users

Returning users who do not open the app every day, and users who want higher trust in recommendation timing and prioritization.

## User Stories

- As a returning user, I want a quick summary of what changed while I was gone so I can re-enter my workflow fast.
- As a user, I want each suggestion or recommendation to show the concrete reason it is being surfaced now.
- As a user, I want to expand an evidence chip when I need the deeper reasoning chain.
- As a user, I do not want a long briefing every time I come back after a short gap.

## Dependencies

- Builds on greeting and proactive surfaces from `specs/functional/ask-advice.md` and `specs/functional/recommendations.md`.
- Reuses signals from threads, dossiers, goals, and intelligence feed.
- Can incorporate outcomes from `specs/functional/outcome-harvester.md` when that feature exists.
- Depends on last-seen or recent-activity tracking from existing analytics and engagement plumbing.
- Current implementation includes a return-briefing aggregator, a dedicated home-surface return brief card, and expandable why-now chips. Durable cross-session last-briefed state is still a follow-up item.

## Detailed Behavior

### Return briefing trigger

1. A `Since you were away` briefing is shown when a user returns after a meaningful absence.
2. For web, meaningful absence means no authenticated activity for at least 72 hours.
3. If the user returns sooner than that, the app can continue using the normal home greeting without a dedicated return briefing.
4. The threshold should be configurable over time, but the user should experience a stable default.

### Return briefing content

When shown, the return briefing can summarize:

1. elapsed time since the user's last session
2. notable new intel matched to goals or watchlist items
3. specialized pipeline updates such as company movements, hiring signals, regulatory alerts, or assumption changes when available
4. recurring thread changes or newly active threads
5. dossier updates or newly changed change-summaries
6. stale-goal or check-in reminders when relevant
7. a short set of suggested next actions

The briefing should be selective and short rather than an exhaustive digest.

### Return briefing placement

1. The briefing appears on the home or chat-first surface near the top of the page.
2. It should feel like a distinct briefing card or first assistant message, not a generic notification toast.
3. The briefing is dismissible.
4. The user can expand it to inspect linked supporting items.

### Why-now evidence chips

1. Suggestions and recommendations can show one or more inline evidence chips.
2. An evidence chip is a short reason label such as:
   - `stale goal`
   - `2 new watchlist matches`
   - `thread active again`
   - `dossier changed`
   - `acted on similar advice`
3. Chips should be shown when the system has a concrete, user-comprehensible reason for surfacing the item now.
4. Chips should be hidden when the reason is too generic, too weak, or would create noise without helping the user decide.

### Evidence chip expansion

1. User can expand a chip to view a fuller reasoning chain.
2. The expanded view can include linked journal snippets, goal references, thread labels, dossier updates, or matched intel items.
3. The expanded view should explain timing, not dump raw scoring internals.
4. The user should be able to jump from the expanded chip to the underlying source item when available.

## Acceptance Criteria

- [ ] Returning users who have been away for a meaningful interval can receive a return briefing.
- [ ] The return briefing summarizes changed items across goals, intel, threads, and dossiers when available.
- [ ] The return briefing appears as a dedicated home-surface briefing rather than a transient toast only.
- [ ] Suggestions and recommendations can display why-now evidence chips when specific reasons are available.
- [ ] Evidence chips remain hidden when no specific or strong reason exists.
- [ ] Users can expand a why-now chip to inspect the fuller reasoning chain.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User returns after less than the absence threshold | No dedicated return briefing is required |
| User was away, but nothing meaningful changed | Briefing can say there were no major changes rather than inventing urgency |
| A suggestion has multiple valid reasons | Show a small number of the strongest chips rather than every possible chip |
| A chip points to an unavailable source surface | Expanded reasoning still explains the trigger in plain language |
| User dismisses the return briefing | It should stay dismissed for that session unless materially refreshed |

## Success Metrics

- Increase in returning-user re-engagement after absences
- Increase in clicks or expansions on why-now evidence chips
- Increase in suggestion or recommendation follow-through when reasons are visible
- Reduction in user confusion about why items surfaced now

## Out of Scope

- Full email or push re-engagement campaigns
- Exhaustive daily digests for every user session
- Exposing raw ranking formulas or internal score weights directly in the UI
- Real-time collaborative briefings across users

## Open Questions

- Should the absence threshold be based only on web activity, or also on journal creation and API activity from other surfaces?
- Should a return briefing ever replace the normal greeting completely, or always appear alongside it?

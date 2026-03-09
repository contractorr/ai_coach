# Dossier Escalation Engine

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

Users can journal repeatedly about a topic and the system can already detect threads, but the bridge from repeated reflection into active monitored research still needs to be selective and trustworthy. The product now has a dossier-escalation path, but it still needs tuning so strategically important topics graduate reliably without noisy prompts.

## Overview

Dossier Escalation Engine proactively suggests promoting a topic into a live dossier when it appears repeatedly across personal and external signals. The feature should feel selective and high-signal, not like a generic prompt to create more objects.

## Users

Users who journal regularly, follow external intelligence, and benefit from ongoing monitoring of companies, markets, technical decisions, career paths, or strategic bets.

## User Stories

- As a user, I want the product to notice when a recurring topic has become important enough to monitor actively.
- As a user, I want a suggested dossier to come prefilled with the right context so I do not have to restate everything.
- As a user, I want to snooze or dismiss noisy suggestions so the system respects my attention.
- As a user, I want the app to suggest dossiers only when there is meaningful cross-signal evidence.

## Dependencies

- Depends on recurring threads from `specs/functional/recurring-thread-inbox.md` and dossier creation from `specs/functional/research-dossiers.md`.
- Can surface in suggestions alongside `specs/functional/recommendations.md` and in return briefings from `specs/functional/since-you-were-away-why-now.md`.
- Can be seeded by extraction receipts from `specs/functional/extraction-receipt.md`.
- Reuses watchlist, intel matching, and research context from `specs/functional/intelligence-feed.md` and `specs/functional/deep-research.md`.
- Current implementation includes escalation scoring, persisted escalation rows, dismiss/snooze/accept flows, and suggestion/briefing surfacing. Follow-up work is mainly threshold tuning and richer suppression heuristics.

## Detailed Behavior

### Escalation signals

An escalation suggestion should require more than a single repeated journal phrase. Candidate signals include:

1. Personal repetition
   - repeated journal mentions over a recent time window
   - an active recurring thread
2. External movement
   - fresh intel items relevant to the same topic
   - cross-source convergence rather than one isolated article when possible
3. Strategic relevance
   - linkage to an active goal, project, or watchlist item
   - recent research activity or repeated advisor questions on the same topic
4. Eligibility guardrails
   - no existing active dossier already covering the topic
   - no active snooze or recent dismissal for the same normalized topic

The engine should prefer topics that combine personal recurrence with external movement.

### Suggestion surfaces

1. Dossier escalation suggestions can appear in the suggestions feed, thread inbox, and extraction receipt next-step area.
2. Suggestions should be non-blocking and dismissible.
3. Each suggestion should state clearly why the topic is being surfaced now.
4. The user should never be forced into dossier creation before continuing normal journaling or chat.

### Accepting an escalation

1. When the user accepts a suggestion, the product opens dossier creation with pre-populated context.
2. The pre-populated dossier should include, when available:
   - topic
   - draft scope
   - starter questions
   - linked goals or projects
   - related recurring thread
   - recent supporting intel items
   - relevant assumptions already visible in user context
3. Accepting the suggestion creates the dossier through the normal dossier flow rather than inventing a separate dossier object type.

### Dismissing and snoozing

1. User can dismiss a suggestion if the topic is not useful.
2. User can snooze a suggestion if the timing is wrong but the topic is still potentially relevant.
3. Dismissed or snoozed topics should not immediately reappear on the next refresh.
4. The suppression window should be long enough to reduce noise but short enough to allow reappearance when evidence materially changes.

### Noise control

1. The engine should create at most a small number of active escalation suggestions at one time.
2. The same topic should not be suggested repeatedly while an earlier suggestion is still active.
3. Topics backed only by weak or low-confidence evidence should not generate proactive suggestions.
4. If the user already has an active dossier on the topic, the engine should favor updating that dossier rather than suggesting a new one.

## Acceptance Criteria

- [ ] The product can suggest escalating a topic into a dossier when personal recurrence and external relevance are both present.
- [ ] Suggestions are surfaced non-blockingly in user-visible surfaces such as suggestions, threads, or receipts.
- [ ] Accepting a suggestion opens a dossier create flow with pre-populated topic context.
- [ ] Dismissing or snoozing a suggestion suppresses immediate re-suggestion of the same topic.
- [ ] The engine avoids suggesting topics already covered by active dossiers.
- [ ] Low-confidence or low-signal topics are filtered out rather than producing noisy prompts.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Topic repeats in journals but has no external movement | Topic may remain a thread, but dossier escalation stays conservative |
| Topic has fresh intel but no personal relevance | It can appear in intel or suggestions without automatically becoming a dossier escalation |
| User already has an active dossier on the topic | No new escalation is suggested; existing dossier remains the source of truth |
| User dismisses a suggestion and then the topic changes materially | A later escalation can reappear after the suppression window or material evidence shift |
| User has no goals or watchlist items | Escalation can still occur based on threads and external movement alone if strong enough |

## Success Metrics

- Acceptance rate of dossier escalation suggestions
- Share of accepted suggestions that lead to repeated dossier opens or updates
- Low repeat-dismissal rate for the same topic within the suppression window
- Increase in dossiers created from recurring personal context rather than only manual topic entry

## Out of Scope

- Fully automatic dossier creation without user confirmation
- Creating multiple competing dossier suggestions for near-identical topics at once
- Replacing one-off deep research for topics that do not need ongoing monitoring
- Shared dossier escalation across multiple users

## Open Questions

- What should count as a material evidence shift large enough to override a prior dismissal?
- Should an accepted escalation automatically mute the originating thread from future dossier suggestions?

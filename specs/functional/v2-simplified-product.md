# V2 Simplified Product

**Status:** Draft
**Author:** Codex
**Date:** 2026-03-09

## Problem

StewardMe already supports a rich set of workflows, but the current product language and workspace model ask users to learn too many concepts too early. Users should not need to understand the distinction between recommendations, suggestions, action plans, threads, dossiers, watchlists, research modes, and monitoring pipelines before they can get value.

The v2 product experience should keep all currently implemented capabilities available while simplifying how the app is organized, how actions are named, and how much decision-making is pushed onto the user.

## Users

- New users who need to reach first value quickly
- Returning users who want a clear sense of what matters now
- Regular users who want the app to feel like one coherent assistant rather than a collection of specialist tools
- Power users who still need access to advanced capabilities without those capabilities dominating the default experience

## Desired Behavior

### Product model

The product should present four clear user jobs:

1. `Capture` - save thoughts, notes, files, and reflections quickly
2. `Ask` - ask one question and get grounded help
3. `Focus` - decide what to do next and move goals forward
4. `Monitor` - stay aware of important changes without manual checking

The user should not need to learn internal product concepts before completing these jobs.

### Primary navigation

The default web navigation should be organized around a small number of workspaces:

1. `Home`
   - serves as the main entry point for `Capture` and `Ask`
   - shows a short personalized briefing, one main input, and the top next steps
2. `Focus`
   - combines goals, suggested next steps, weekly planning, and opportunities that are ready for action
3. `Radar`
   - combines personalized monitoring, saved intel, and tracked topics in one place
4. `Library`
   - stores durable documents, reports, and research artifacts
5. `Settings`
   - manages account, profile, keys, and advanced controls

Existing capabilities that do not need their own top-level mental model should remain available through these workspaces instead of appearing as separate first-run concepts.

### Home

Home should be the simplest possible starting point.

1. User lands on Home after onboarding and on most return visits.
2. Home shows one primary input field with plain-language guidance such as `Ask a question or drop a quick note`.
3. The system should infer whether the user is asking for advice or capturing a note, while still giving the user a lightweight way to correct the interpretation.
4. Home shows a short personalized briefing near the top.
5. If the user has been away long enough for a return briefing, that briefing should replace or absorb the normal greeting instead of creating two separate summary surfaces.
6. Home shows at most three clearly prioritized next steps.
7. Home can show attached files in the current conversation without making document handling feel like a separate workflow.

Current implemented capabilities should map into Home as follows:

- advisor chat remains available, but the product does not foreground internal mode choices
- quick capture remains available, but it does not require a separate mode toggle by default
- extraction receipt can appear as a non-blocking follow-up after note capture
- `why now` reasoning appears only when it helps the user decide what to do next

### Capture

Capture should optimize for speed first and structure second.

1. User can save a note, reflection, journal entry, or attached document from Home or from dedicated journal/library surfaces.
2. The default capture flow should ask only for the content itself.
3. Optional metadata such as title, type, and tags should stay secondary.
4. After saving, the system can surface a lightweight extraction receipt that explains what was learned in plain language.
5. The receipt should help the user take one obvious next step when useful, rather than presenting a large menu of system concepts.

Current implemented capabilities should be simplified as follows:

- journal entry types remain supported, but default capture should not force users to choose among many types up front
- extraction receipts can expose themes, memory, threads, and next steps, but only the most useful items should be expanded by default
- recurring threads discovered from capture should usually appear later as a follow-up in `Focus` or `Radar`, not as a concept the user must understand during every save

### Ask

Asking for help should feel like one workflow.

1. User asks a free-text question from Home or any embedded chat surface.
2. User can attach relevant files without leaving the conversation.
3. System chooses the best available retrieval and response strategy automatically.
4. Advanced response framing can still exist, but the default product should not require the user to choose among internal advice modes before asking.
5. Answers should make the next action obvious when there is a practical recommendation.

Current implemented capabilities should be simplified as follows:

- classic and agentic paths remain available behind the scenes, but are not primary user-facing decisions
- advice types remain available as optional refinement controls rather than required front-door choices
- research-backed or document-grounded answers should feel like stronger answers, not separate products

### Focus

Focus should be the place where the user decides what to do next.

1. Focus combines active goals, suggested next steps, weekly planning, and opportunities worth acting on.
2. The default view emphasizes current goals and a small number of actionable items.
3. Suggestions, recommendations, and action plans should be presented as one connected workflow rather than separate categories the user must understand.
4. When a suggested next step is accepted, it becomes part of the user's plan without forcing them into a separate project-management mental model.
5. Opportunities such as matched issues or generated project ideas should appear in Focus when they are actionable, rather than feeling like an isolated workspace.
6. Goal-linked work should stay visually connected to the relevant goal.

Current implemented capabilities should map into Focus as follows:

- goals remain the anchor structure for ongoing work
- recommendation cards and action items are presented as `Suggested next steps`
- weekly plan remains visible, but as a concise planning aid rather than a separate planning system
- projects and opportunities appear as tactical or strategic opportunities inside Focus
- thread-driven actions such as `make goal`, `run research`, or `start dossier` should be reframed as a simpler action such as `Investigate` or `Turn into plan`, with the product choosing the best matching downstream workflow

### Radar

Radar should be the single place for monitoring and follow-up.

1. Radar shows a personalized feed by default.
2. The main default views should be simple, such as `For you`, `Saved`, and `Tracked topics`.
3. Saving, annotating, and following up on an item should happen in context.
4. Tracked topics should be understandable without requiring users to learn every watchlist subtype.
5. The product can still use richer internal watchlist and monitoring models, but the default UI should keep those distinctions lightweight.
6. Specialized signals should feel like part of one monitoring system, not like unrelated pipelines.

Current implemented capabilities should map into Radar as follows:

- watchlists remain supported, but the default add flow should start from simple topics such as companies, themes, and places to watch
- company movement, hiring activity, regulatory alerts, and assumption monitoring should surface as specialized alert types within Radar instead of as separate conceptual products
- saved intel, follow-up notes, and related evidence should stay in one continuous flow
- recurring threads and dossier updates can appear in Radar when they represent something newly worth noticing

### Library

Library should remain the durable artifact workspace.

1. User can upload, revisit, and manage documents and reports.
2. Library should emphasize durable assets and traceability.
3. Research reports, dossier outputs, and uploaded files should feel related because they are all reusable reference material.
4. Users should be able to move from a library item back into Ask, Focus, or Radar when they want to act on it.

Current implemented capabilities should map into Library as follows:

- uploaded documents remain durable private assets
- research reports remain searchable and reusable
- dossier materials remain accessible, but dossiers should behave like pinned ongoing research rather than a separate first-run concept

### Settings

Settings should stay advanced and explicit.

1. Settings manages account identity, profile editing, keys, and advanced monitoring controls.
2. Settings should not be the main place where users experience everyday product value.
3. Profile editing and onboarding refresh remain available here for users who want more control.
4. Advanced source controls and detailed watch configuration can live here without complicating the default product flow.

### Onboarding

Onboarding should reach value faster while preserving existing capabilities.

1. The onboarding flow should focus on only the minimum information needed to personalize the app.
2. The first goal is to get the user to a useful Home experience quickly.
3. Deep profile detail, feed tuning, and advanced setup should happen later when context makes them easier to understand.
4. Lite/shared mode should remain supported, but should be explained in plain language and not dominate the early flow.

Current implemented capabilities should be reframed as follows:

- conversational onboarding remains available, but the interview should feel short and adaptive
- initial goals can still be created from onboarding answers
- feed setup can still happen, but should feel optional or auto-seeded rather than mandatory configuration work

### Progressive disclosure

Advanced capabilities should remain available without becoming mandatory parts of the default experience.

1. Users can start with simple actions and only discover more specialized workflows when needed.
2. Threads, dossiers, assumptions, advanced watch configuration, and deeper reasoning views should appear as secondary layers, drawers, expanded cards, or advanced controls.
3. The product should prefer simple action labels over internal system labels.
4. Users who never learn the full product vocabulary should still be able to get sustained value.

### Existing capability mapping

The v2 simplification should preserve currently implemented functionality while changing how it is framed:

- `advisor`, `quick capture`, and `return briefing` all live primarily in `Home`
- `goals`, `recommendations`, `action plans`, and `projects/opportunities` live primarily in `Focus`
- `intel feed`, `watchlist`, `company movement`, `hiring activity`, `regulatory alerts`, and `assumption watchlist` live primarily in `Radar`
- `deep research`, `dossiers`, uploaded files, and durable reports live primarily in `Library`
- `profile management`, keys, account controls, and advanced monitoring setup live in `Settings`

## Acceptance Criteria

- [ ] The product can be explained to a new user using the four jobs `Capture`, `Ask`, `Focus`, and `Monitor`.
- [ ] The default web navigation uses a small set of workspaces with clear user-purpose labels.
- [ ] Home presents one primary input and a short prioritized briefing rather than multiple competing starting points.
- [ ] Users can ask questions and capture notes without first choosing between internal system modes.
- [ ] Goals, recommendations, action items, and opportunities are presented as one connected execution workflow in `Focus`.
- [ ] Monitoring behaviors appear as one unified `Radar` experience even when different alert types or signal families are involved.
- [ ] Advanced capabilities remain reachable without being required for first-run comprehension.
- [ ] Existing implemented capabilities remain available somewhere in the product even when their framing or entry point changes.
- [ ] Settings remains the place for explicit account and advanced configuration tasks, not the primary surface for everyday work.
- [ ] Onboarding reaches useful product value before asking the user to configure advanced details.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| New user has no API key and chooses lite/shared mode | User still reaches a useful Home experience quickly and understands what remains available |
| User prefers structured journaling | Dedicated journal and library surfaces still support richer editing without complicating default capture |
| User is a power user who depends on watchlists, dossiers, or assumptions | Advanced workflows remain reachable through contextual entry points or settings |
| User returns after a long absence and many things changed | Home shows a concise briefing with the strongest items rather than multiple overlapping summaries |
| User has no active goals yet | Focus still provides suggested next steps and opportunities without feeling empty |
| User tracks multiple specialized signal types | Radar still feels like one monitoring surface, with specialized alert labels only when helpful |
| User wants to inspect deeper reasoning | Expanded evidence and drill-down views remain available without cluttering the default card state |

## Out of Scope

- Removing existing implemented capabilities from the product entirely
- Hiding advanced functionality so deeply that power users cannot reach it
- Rewriting technical architecture or implementation details
- Replacing functional specs for individual features with a single monolithic spec

## Open Questions

- Should `Home` fully replace a distinct advisor workspace in primary navigation, or should advisor remain as a secondary deep-link destination?
- Should `Journal` remain a top-level navigation item for users who capture frequently, or should it live as a deeper workspace under `Home` and `Library`?
- Should `Library` explicitly include dossiers in its language, or should dossiers be described only as ongoing research?

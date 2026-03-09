# V2 Simplified Product

**Status:** Accepted
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

The product should present five clear user jobs that map 1:1 to the primary navigation:

1. `Capture + Ask` (Home) — save thoughts or get grounded help from one input
2. `Focus` — decide what to do next and move goals forward
3. `Monitor` (Radar) — stay aware of important changes without manual checking
4. `Reference` (Library) — find, reuse, and manage durable documents and research
5. `Configure` (Settings) — manage account, profile, keys, and advanced controls

The user should not need to learn internal product concepts before completing these jobs.

### Primary navigation

The default web navigation has five workspaces. Each maps to exactly one user job:

1. `Home` — Capture + Ask
   - the main entry point; one input, personalized briefing, top next steps
   - journal shortcut pinned in the sidebar for quick access to full journal view
2. `Focus` — decide what to do next
   - goals, suggested next steps, weekly planning, actionable opportunities
3. `Radar` — monitor and follow up
   - personalized intel feed, tracked topics, recurring threads, active dossiers, pipeline alerts
4. `Library` — reference material
   - uploaded documents, research reports, completed dossier outputs, saved artifacts
5. `Settings` — account and advanced controls
   - profile, keys, source config, advanced watch configuration, memory management

Existing capabilities that do not need their own top-level mental model should remain available through these workspaces instead of appearing as separate first-run concepts.

### Home

Home should be the simplest possible starting point.

1. User lands on Home after onboarding and on most return visits.
2. Home shows one primary input field with plain-language guidance such as `Write a note or ask a question`.
3. The system defaults to capture (lower stakes if misclassified). After saving, a non-blocking `Get advice on this?` affordance appears, letting the user upgrade a note into a question. Explicit question syntax (e.g., starting with a question word, ending with `?`) routes directly to the advisor. The user can also toggle mode manually before submitting.
4. Home shows a short personalized briefing near the top.
5. If the user has been away 7+ days, the return briefing replaces the normal greeting. For shorter absences, the return briefing appears alongside it.
6. Home shows at most three clearly prioritized next steps.
7. Home can show attached files in the current conversation without making document handling feel like a separate workflow.
8. A persistent journal shortcut (sidebar icon or pinned link) provides one-tap access to the full journal workspace with type filters, tags, search, and templates — without requiring journal to be a top-level nav item.

Current implemented capabilities should map into Home as follows:

- advisor chat remains available, but the product does not foreground internal mode choices
- quick capture remains available, but it does not require a separate mode toggle by default
- extraction receipt can appear as a non-blocking follow-up after note capture
- `why now` reasoning appears only when it helps the user decide what to do next

### Capture

Capture should optimize for speed first and structure second.

1. User can save a note, reflection, journal entry, or attached document from Home or from the journal workspace.
2. The default capture flow should ask only for the content itself.
3. Optional metadata such as title, type, and tags should stay secondary.
4. After saving, the system can surface a lightweight extraction receipt that explains what was learned in plain language.
5. The receipt should help the user take one obvious next step when useful, rather than presenting a large menu of system concepts.

Journal is the product's primary data flywheel — journal entries feed embeddings, threads, memory, extraction receipts, sentiment, and trend detection. Capture friction directly degrades every downstream feature. The journal workspace must remain fast to reach even though it is not a top-level nav item:

- Home input defaults to capture, so the most common path has zero navigation cost
- A persistent sidebar shortcut opens the full journal workspace (type filters, tag chips, search, templates, entry list) in one tap
- The journal workspace is also reachable from Library as a content type filter

Current implemented capabilities should be simplified as follows:

- journal entry types remain supported, but default capture should not force users to choose among many types up front
- extraction receipts can expose themes, memory, threads, and next steps, but only the most useful items should be expanded by default
- recurring threads discovered from capture should usually appear later as a follow-up in `Radar`, not as a concept the user must understand during every save

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

#### Visual hierarchy

Focus must avoid becoming a wall of mixed content. The default view uses a strict visual hierarchy:

1. **What to do next** — a short ranked list of at most 3 suggested next actions (drawn from recommendations, action items, thread-driven actions, and opportunity matches). Each item shows a one-line reason and a primary action button. This section is always visible at the top.
2. **Active goals** — goal cards with inline milestones, linked action items, and check-in status. This is the anchor structure for ongoing work.
3. **Everything else** — weekly plan, opportunities, and lower-ranked suggestions live in collapsible secondary sections below goals. They are accessible but do not compete for attention on first load.

#### Behavior

1. Focus combines active goals, suggested next steps, weekly planning, and opportunities worth acting on.
2. The default view emphasizes the top next actions and current goals only; secondary content is collapsed.
3. Suggestions, recommendations, and action plans should be presented as one connected workflow rather than separate categories the user must understand.
4. When a suggested next step is accepted, it becomes part of the user's plan without forcing them into a separate project-management mental model.
5. Opportunities such as matched issues or generated project ideas should appear in Focus when they are actionable, rather than feeling like an isolated workspace.
6. Goal-linked work should stay visually connected to the relevant goal.

Current implemented capabilities should map into Focus as follows:

- goals remain the anchor structure for ongoing work
- recommendation cards and action items are presented as `Suggested next steps`
- weekly plan remains visible as a collapsible planning aid, not a separate planning system
- projects and opportunities appear as a collapsible `Opportunities` section inside Focus
- thread-driven actions such as `make goal`, `run research`, or `start dossier` should be reframed as a simpler action such as `Investigate` or `Turn into plan`, with the product choosing the best matching downstream workflow

### Radar

Radar should be the single place for monitoring and follow-up.

#### Default views

Radar uses a small set of tabs or filters as its primary organization:

1. **For you** — personalized feed ranked by relevance. Mixes intel items, pipeline alerts (company, hiring, regulatory), assumption updates, recurring thread activity, and active dossier updates into one stream. Each item carries a type badge but the stream is unified.
2. **Threads** — recurring threads detected from journal entries. Shows active threads with label, last updated, entry count, and recent activity. Thread card actions: view entries, create goal, run research, start dossier, dismiss. Dismissed threads resurface when new matching entries arrive.
3. **Dossiers** — active dossiers with topic, status, last updated, change summary, and open questions. Dossier card actions: view detail, trigger research, archive. Completed/archived dossiers move to Library automatically.
4. **Saved** — bookmarked intel items with user notes and follow-up status.
5. **Tracked topics** — the user's watchlist presented as simple topic cards (companies, themes, sectors, geographies). Adding a topic starts from plain language, not from watchlist subtype selection. Advanced watch configuration (priority, aliases, preferred sources, linked goals) available via expand or Settings.

#### Behavior

1. Radar shows the `For you` feed by default.
2. Saving, annotating, and following up on an item should happen in context.
3. Tracked topics should be understandable without requiring users to learn every watchlist subtype.
4. The product can still use richer internal watchlist and monitoring models, but the default UI should keep those distinctions lightweight.
5. Specialized signals should feel like part of one monitoring system, not like unrelated pipelines.

Current implemented capabilities should map into Radar as follows:

- watchlists remain supported, but the default add flow should start from simple topics such as companies, themes, and places to watch
- company movement, hiring activity, regulatory alerts, and assumption monitoring should surface as specialized alert types within the `For you` feed
- saved intel, follow-up notes, and related evidence should stay in one continuous flow
- recurring threads have a dedicated `Threads` tab with full CRUD (replaces the standalone recurring-thread-inbox workspace)
- active dossiers have a dedicated `Dossiers` tab; completed dossier outputs migrate to Library
- dossier escalation suggestions surface in the `For you` feed and on thread cards as contextual prompts

### Library

Library should remain the durable artifact workspace.

1. User can upload, revisit, and manage documents and reports.
2. Library should emphasize durable assets and traceability.
3. Research reports, completed dossier outputs, and uploaded files should feel related because they are all reusable reference material.
4. Users should be able to move from a library item back into Ask, Focus, or Radar when they want to act on it.
5. Library supports content type filters: `Documents`, `Reports`, `Dossiers`, `Journal` — where the Journal filter opens the full journal workspace.

Current implemented capabilities should map into Library as follows:

- uploaded documents remain durable private assets
- research reports remain searchable and reusable
- completed/archived dossier outputs live here; active dossiers live in Radar
- journal entries are accessible via a Library filter that opens the journal workspace

### Settings

Settings should stay advanced and explicit.

1. Settings manages account identity, profile editing, keys, and advanced monitoring controls.
2. Settings should not be the main place where users experience everyday product value.
3. Profile editing and onboarding refresh remain available here for users who want more control.
4. Advanced source controls and detailed watch configuration can live here without complicating the default product flow.
5. Memory management lives in Settings under a `What I know about you` section — listing active memory facts by category with inspect/delete controls and a stats summary. This provides transparency into the system's learned model of the user.

### Onboarding

Onboarding should reach value faster while preserving existing capabilities.

#### First 5 minutes

The onboarding sequence has one goal: get the user to a useful Home experience with a personalized greeting. The minimum path is:

1. **Display name** — one field, required
2. **API key or lite mode** — binary choice with plain-language explanation
3. **Two-sentence self-description** — free text: "Tell us about yourself in a sentence or two." This seeds the profile enough for a personalized greeting.
4. **Done** — user lands on Home with a greeting that references their self-description. A `Tell me more about yourself` prompt in the chat invites deeper profiling conversationally, on the user's terms.

#### First week

The product introduces depth through contextual nudges, not upfront configuration:

- After the first journal entry: extraction receipt explains what was learned, offers `Get advice on this?`
- After the third entry: Focus suggests a first goal based on detected themes
- After the first question: the answer includes a `Save to Library` affordance
- After the first goal: Focus populates with suggested next steps
- Radar auto-seeds a `For you` feed from profile interests; a nudge invites the user to add their first tracked topic

#### Existing capabilities

- conversational onboarding remains available, but the interview should feel short and adaptive
- initial goals can still be created from onboarding answers
- feed setup can still happen, but should feel optional or auto-seeded rather than mandatory configuration work

### Progressive disclosure

Advanced capabilities should remain available without becoming mandatory parts of the default experience.

1. Users can start with simple actions and only discover more specialized workflows when needed.
2. Threads, dossiers, assumptions, advanced watch configuration, and deeper reasoning views should appear as secondary layers, drawers, expanded cards, or advanced controls.
3. The product should prefer simple action labels over internal system labels.
4. Users who never learn the full product vocabulary should still be able to get sustained value.

### Empty states

Every workspace must guide the user toward a first action when unpopulated:

| Workspace | Empty State |
|-----------|-------------|
| Home | Personalized greeting + prompt: "Write your first note or ask a question" |
| Focus | "No goals yet. Start by writing a few notes — we'll suggest goals as patterns emerge." + manual create-goal action |
| Radar > For you | Auto-seeded feed from profile interests. If no profile interests: "Add a topic to start monitoring" |
| Radar > Threads | "Threads appear automatically as you journal. Write a few entries to get started." |
| Radar > Dossiers | "No active research. Start a dossier from any intel item, thread, or question." |
| Library | "Upload a document, generate a report, or save something from chat." |

### Existing capability mapping

The v2 simplification should preserve currently implemented functionality while changing how it is framed:

- `advisor`, `quick capture`, `return briefing`, and `journal shortcut` all live primarily in `Home`
- `goals`, `recommendations`, `action plans`, and `projects/opportunities` live primarily in `Focus`
- `intel feed`, `watchlist`, `company movement`, `hiring activity`, `regulatory alerts`, `assumption watchlist`, `recurring threads`, and `active dossiers` live primarily in `Radar`
- `deep research` outputs, `completed dossiers`, uploaded files, and durable reports live primarily in `Library`
- `profile management`, `memory management`, keys, account controls, and advanced monitoring setup live in `Settings`

## Acceptance Criteria

- [ ] The product can be explained to a new user using the five jobs: Capture+Ask, Focus, Monitor, Reference, Configure.
- [ ] Each primary nav item maps to exactly one user job.
- [ ] Home presents one primary input and a short prioritized briefing rather than multiple competing starting points.
- [ ] Home input defaults to capture; explicit question syntax routes to advisor; user can upgrade a note to a question after saving.
- [ ] Journal is reachable in one tap from a persistent sidebar shortcut and as a Library content filter.
- [ ] Users can ask questions and capture notes without first choosing between internal system modes.
- [ ] Focus shows at most 3 suggested next actions at the top; goals below; everything else collapsed.
- [ ] Goals, recommendations, action items, and opportunities are presented as one connected execution workflow in `Focus`.
- [ ] Monitoring behaviors appear as one unified `Radar` experience even when different alert types or signal families are involved.
- [ ] Recurring threads have a dedicated tab in Radar with full CRUD (view, create goal, research, dossier, dismiss).
- [ ] Active dossiers have a dedicated tab in Radar; completed dossiers appear in Library.
- [ ] Memory facts are inspectable and deletable from a `What I know about you` section in Settings.
- [ ] Advanced capabilities remain reachable without being required for first-run comprehension.
- [ ] Existing implemented capabilities remain available somewhere in the product even when their framing or entry point changes.
- [ ] Every workspace has a useful empty state that guides toward a first action.
- [ ] Onboarding reaches a personalized Home in 4 steps or fewer.
- [ ] Settings remains the place for explicit account and advanced configuration tasks, not the primary surface for everyday work.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| New user has no API key and chooses lite/shared mode | User still reaches a useful Home experience quickly and understands what remains available |
| User prefers structured journaling | Journal workspace (via sidebar shortcut or Library filter) still supports richer editing, type filters, tags, templates without complicating default capture |
| User is a power user who depends on watchlists, dossiers, or assumptions | Advanced workflows remain reachable through Radar tabs, contextual entry points, or Settings |
| User returns after a long absence (7+ days) | Home replaces greeting with a concise return briefing with the strongest items |
| User returns after a short absence (< 7 days) | Return briefing appears alongside normal greeting |
| User has no active goals yet | Focus shows "No goals yet" guidance and still provides suggested next steps from profile/intel |
| User tracks multiple specialized signal types | Radar `For you` feed unifies all signal types with type badges; `Tracked topics` tab shows simple topic cards |
| User wants to inspect deeper reasoning | Expanded evidence and drill-down views remain available without cluttering the default card state |
| User writes ambiguous input in Home | System defaults to capture; shows `Get advice on this?` affordance after save |
| User journals frequently and needs fast access | Sidebar shortcut opens full journal workspace in one tap from any page |
| Active dossier completes | Dossier moves from Radar > Dossiers to Library automatically; user notified |
| User wants to see what the system knows about them | Settings > "What I know about you" shows all memory facts with delete controls |

## Out of Scope

- Removing existing implemented capabilities from the product entirely
- Hiding advanced functionality so deeply that power users cannot reach it
- Rewriting technical architecture or implementation details
- Replacing functional specs for individual features with a single monolithic spec
- Global search (important for friction reduction but warrants its own spec)

## Resolved Questions

- **Home vs advisor nav?** Home fully replaces advisor; advisor is just a mode within Home.
- **Journal navigation?** Journal lives as a deeper workspace accessible via a persistent sidebar shortcut and as a Library content filter, not top-level nav. One-tap access preserved.
- **Dossier language in Library?** Explicit — Library UI names dossiers directly as a content type.
- **Dossier lifecycle split?** Active dossiers live in Radar; completed/archived dossier outputs live in Library.
- **Recurring thread inbox?** Threads live as a dedicated tab in Radar, not a standalone workspace. The `recurring-thread-inbox.md` spec should be updated to reflect this placement.
- **Capture/Ask ambiguity?** Default to capture. Explicit question syntax routes to advisor. Post-save affordance lets user upgrade to a question.
- **Memory management placement?** Settings, under a `What I know about you` section with inspect/delete/stats.

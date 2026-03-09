# Goal Tracking

**Status:** Approved
**Author:** —
**Date:** 2026-03-02

## Problem

Users set career and learning goals but lack a structured way to track progress, break them into milestones, and get accountability. Goals mentioned in journal entries aren't actionable without explicit tracking.

## Users

Users who set explicit goals during onboarding or manually. Most useful for mid-to-senior professionals with deliberate growth plans.

## Desired Behavior

### Creating goals

1. User creates a goal with a title and optional description
2. System stores as a markdown file with YAML frontmatter in journal directory
3. Goal gets a status (`active` by default) and 0% progress
4. Goal has a `type` field: `career`, `learning`, `project`, or `general` (default `general`)

Current interface scope:
- CLI and web goal creation currently default to `general`
- MCP goal creation can set `type` explicitly
- Learning-path migration also produces `type="learning"` goals

### Milestones

1. User adds milestones to a goal (sub-tasks with titles)
2. User marks milestones complete as they progress
3. Completing milestones updates the goal's progress percentage

### Auto-milestone generation

1. User asks the advisor to "break down" any goal
2. Advisor generates ordered milestones based on goal type, profile context, and journal history
3. For `learning` goals, milestones correspond to learning steps (replaces the separate learning path system)
4. Skill gap detection is an advisor prompt mode — user asks "what skills should I work on?" and advisor creates `learning`-type goals with auto-generated milestones

### Check-ins

1. User records a check-in on a goal with a text note
2. Check-in is timestamped and appended to the goal's history
3. System tracks check-in frequency for staleness detection

### Goal status

- `active` — in progress
- `completed` — all milestones done or manually marked complete
- `paused` — temporarily deprioritized
- `abandoned` — explicitly dropped

### Web goals workspace

1. The web goals page defaults to a focus view that shows `active` and `paused` goals.
2. Stale goals can be isolated with a dedicated `Needs check-in` filter.
3. `Completed` and `abandoned` goals remain visible in an archived view instead of crowding the default working list.
4. The web UI supports quick status transitions from each expanded goal card:
   - `active` -> `paused`, `completed`, or `abandoned`
   - `paused` -> `active`, `completed`, or `abandoned`
   - `abandoned` -> `active`
5. The web goals page includes title search across the loaded goal list.
6. The web goals page surfaces a weekly-plan summary so users can see remaining capacity for the current week.
7. Recommendation action items linked to a goal render inline on that goal card.
8. Action items without a goal link remain visible in a separate section so they do not disappear.
9. Recommendation cards on the goals page support inline 1-5 usefulness ratings with optional notes.

### Goal analysis

1. Advisor can analyze progress on a specific goal or all goals
2. Analysis considers: milestone completion %, time since last check-in, journal entries mentioning the goal, relevant intel
3. Stale goals (no check-in for extended period) are flagged

### Goal-intel matching

1. System matches incoming intel items against active goals
2. Matched items surface in heartbeat notifications
3. Up to 8 active goals are summarized in the agentic advisor's system prompt

### Learning path migration

Existing learning paths are auto-migrated to goals on first startup post-upgrade:
1. Each learning path becomes a goal with `type="learning"`
2. Path modules become milestones, preserving completion status
3. One-time migration script; original learning path files left as-is for rollback

## Acceptance Criteria

- [ ] User can create goals, update status, record check-ins, and manage milestones
- [ ] Direct goal deletion is not currently exposed in CLI, web, or MCP
- [ ] Goals persist a `goal_type` field (`career`, `learning`, `project`, `general`)
- [ ] MCP can set goal type on create; CLI and web currently create `general` goals unless migrated or edited out-of-band
- [ ] Goals support milestones with completion tracking
- [ ] The web goals page defaults to a focus view and lets users filter to stale, archived, or all goals
- [ ] The web goals page supports title search across loaded goals
- [ ] The web goals page surfaces weekly-plan capacity and linked recommendation action items
- [ ] The web UI exposes quick abandon and reactivate goal actions
- [ ] Advisor can auto-generate milestones for any goal on request
- [ ] Check-ins are timestamped and persisted
- [ ] Progress percentage reflects milestone completion
- [ ] Advisor can analyze goal progress with journal + intel context
- [ ] Stale goals are flagged (no recent check-in)
- [ ] Active goals are injected into agentic advisor context
- [ ] Skill gap detection available as advisor prompt mode
- [ ] Existing learning paths migrated to `learning`-type goals preserving progress
- [ ] Available via CLI, web, and MCP

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Goal with no milestones | Progress is 0% until manually updated or milestones added; advisor can auto-generate |
| Learning path migration fails | Original files untouched; user can retry migration or manually recreate |
| All milestones completed | Goal progress is 100%; status remains `active` until user marks complete |
| No active goals | Goal analysis returns empty; agentic prompt has no goals section |
| Stale filter has no matches | Web UI shows a reassuring empty state instead of an empty list |
| Search/filter returns no results | Web UI keeps filters visible and offers a reset action |
| Goal file corrupted | Silently skipped in listings; error on direct access |
| 8+ active goals | Only first 8 shown in advisor context |

## Out of Scope

- Goal templates or pre-built goal libraries
- Deadline tracking or calendar integration
- Goal sharing or accountability partners
- Automatic goal completion (always user-initiated)
- Standalone learning path system (merged into goals; see deprecated `learning-paths.md`)

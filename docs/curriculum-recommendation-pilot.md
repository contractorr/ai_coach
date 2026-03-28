# Curriculum Recommendation Pilot

This document scopes the next-step recommendation pilot for Learn. The current `/api/curriculum/next`
logic is momentum- and graph-aware, but it still needs explicit ranking signals for users with
different roles, goals, industries, and time budgets. The same pilot also exposes a lightweight
applied-assessment plan so the recommendation surface points toward transfer, not just content
consumption.

## Pilot objective

Keep the current momentum-first behavior, but personalize what comes next when the system needs to
choose between multiple valid guides or modules.

## Candidate pool

The pilot should continue to use the existing candidate buckets:

1. next chapter in last-read active guide
2. next chapter in another enrolled incomplete guide
3. ready-to-start guide (all prerequisites complete)
4. entry-point guide with no prerequisites

The pilot changes ranking inside those buckets instead of inventing a separate recommendation
system.

## Recommendation inputs

- Graph state: last-read chapter, enrolled guides, unlocked guides, and entry points.
- Profile context: current role, short/long-term goals, industries watching, active projects, and weekly time budget.
- Curriculum context: manifest-backed learning programs, program outcomes, and applied industry modules.

## Recommendation rules

### Rule 1: preserve momentum first

- If the learner has an active guide with a natural next chapter, keep recommending that chapter.
- Only break momentum when the current path is clearly mismatched with stated goals or constraints.

### Rule 2: rank enrolled guides by context fit

When there is more than one enrolled incomplete guide, rank them by:

1. goal match
2. industry or role match
3. program fit
4. time-budget fit

### Rule 3: rank ready-to-start guides before generic entry points

- Ready guides still beat cold-start entry points.
- Within ready guides, apply the same context-fit scoring so the learner sees the most relevant unlocked option, not just the first one in DAG order.

### Rule 4: personalize entry-point suggestions

- When the learner has no active or ready guides, choose an entry-point guide that best fits role, industry, goals, and time budget.
- Industry capstones should never be recommended as true entry points; they remain late-stage applied modules.

## Context signals

### Goal match

- Primary source: active goals from `GoalTracker`
- Secondary source: `goals_short_term`, `goals_long_term`, `aspirations`, and `active_projects` from `UserProfile`
- Use: prioritize guides whose program outcomes or role descriptions align with the learner's explicit near-term direction

### Industry match

- Primary source: `industries_watching` from `UserProfile`
- Secondary source: current role string, active projects, and program mapping for industry modules
- Use: rank applied modules and sector-adjacent guides higher when the learner is clearly targeting a sector

### Role match

- Primary source: `current_role` and `career_stage` from `UserProfile`
- Secondary source: program audience descriptions in `content/curriculum/skill_tree.yaml`
- Use: prefer programs that match the learner's operating context

### Time-budget fit

- Primary source: `constraints.time_per_week`
- Fallback: `weekly_hours_available`
- Use: prefer lighter recommendations when time is scarce and longer cold-start guides when the learner has more available study time

## Scoring shape

The pilot does not need a machine-learned ranker. A transparent weighted score is enough:

- `momentum_bonus`
- `goal_match`
- `industry_or_role_match`
- `program_fit`
- `time_budget_fit`

Suggested first-pass interpretation:

- low time budget: `<= 3` hours/week
- medium time budget: `4-7` hours/week
- high time budget: `>= 8` hours/week

## Applied assessment types

- `teach_back`
  - Stage: `chapter_completion`
  - Output: short note or voice memo translating a chapter into applied language
  - Use: checks comprehension and transfer after each chapter
- `decision_brief`
  - Stage: `review`
  - Output: one-page recommendation with assumptions, trade-offs, and a clear call
  - Use: turns spaced review into applied reasoning instead of recall only
- `scenario_analysis`
  - Stage: `scenario_practice`
  - Output: base/stress cases with leading indicators and response triggers
  - Use: pressure-tests frameworks mid-guide against realistic uncertainty
- `case_memo`
  - Stage: `capstone`
  - Output: 1-2 page memo with recommendation, rationale, execution plan, and failure modes
  - Use: serves as the guide/program capstone artifact

## Required data dependencies

| Dependency | Current source | Why it is needed | Fallback |
|---|---|---|---|
| active guide state | `CurriculumStore.get_last_read_chapter()`, `get_enrollments()`, `get_next_chapter()` | preserve momentum and know what can be continued now | DAG-only behavior |
| ready guides | `CurriculumStore.get_ready_guides()` | preserve prerequisite safety while still personalizing | entry-point suggestions |
| guide metadata | `CurriculumStore.list_guides()` and `get_guide()` | chapter count, reading-time estimate, track, prerequisites | omit time-fit nuance |
| learning programs | `content/curriculum/skill_tree.yaml` `programs` section | connect guides/modules to target outcomes and audiences | use track only |
| fuller guide roles | `docs/curriculum-program-map.md` | optional richer mapping for non-program guides during pilot tuning | rely on manifest-only programs |
| profile role and stage | `UserProfile.current_role`, `career_stage` | distinguish operator, specialist, founder, investor, etc. | no role weighting |
| industry intent | `UserProfile.industries_watching` | rank sector modules and adjacent guides | infer weakly from goals/projects |
| goal intent | `GoalTracker.get_goals()` plus `UserProfile.goals_short_term`, `goals_long_term`, `aspirations` | match Learn to what the user is actually trying to achieve | use only curriculum progress |
| time budget | `UserProfile.constraints.time_per_week` or `weekly_hours_available` | avoid recommending heavy cold starts to constrained learners | assume medium budget |

## Pilot surface area

- Backend
  - Extend `/api/curriculum/next` to return recommendation signals, matched programs, and assessment previews.
  - Extend guide detail payloads to expose the same assessment plan.
- Frontend
  - Show a visible personalized "Next up" card even when the next action is guide enrollment.
  - Show recommendation chips or explanation signals on Learn landing.
  - Show the assessment pilot on Learn landing and guide detail views.

## Pilot rollout

### Phase 1

- Add structured recommendation signals to `/api/curriculum/next`.
- Personalize ready-guide and entry-point selection using profile and goals.

### Phase 2

- Personalize ranking across multiple enrolled incomplete guides.
- Add frontend explanation chips so users can see why a guide is being suggested now.

### Phase 3

- Tune weights using real usage and completion feedback.
- Expand beyond manifest-backed programs only after the program-map metadata is stable.

# Action Plans

## Overview

Action plans extend recommendation storage with a structured execution artifact while reusing the existing recommendation markdown files as the source of truth. The feature stays lightweight by treating each tracked action as metadata on a recommendation and linking it to an existing goal path when relevant.

**Functional spec:** `specs/functional/action-plans.md`

## Dependencies

**Depends on:** `advisor.recommendation_storage`, `advisor.scoring`, `web.routes.recommendations`, `web.models`, `web app/(dashboard)/goals`
**Depended on by:** `recommendation ranking`, `goals UI`, `weekly planning UI`

---

## Components

### Recommendation Execution Metadata

**Files:** `src/advisor/recommendation_storage.py`, `src/shared_types.py`
**Status:** Stable

#### Behavior

- Each recommendation may carry one optional `action_item` object in its frontmatter metadata.
- The action item is created idempotently from an existing recommendation.
- If the recommendation already has freeform `action_plan` markdown, the storage layer derives sensible defaults from it; otherwise it falls back to recommendation title, description, and rationale.
- Goal linkage is represented by `goal_path` and `goal_title` inside the action item.
- Weekly planning reads action items directly from recommendation storage rather than creating a second database.

#### Action Item Shape

| Field | Type | Notes |
|------|------|-------|
| `objective` | `str` | Defaults to recommendation title |
| `next_step` | `str` | Derived from action-plan text or description |
| `effort` | `small \| medium \| large` | Defaults to `medium` |
| `due_window` | `today \| this_week \| later` | Defaults to `this_week` |
| `blockers` | `list[str]` | Defaults to empty list |
| `success_criteria` | `str` | Derived from action-plan text or rationale |
| `status` | `accepted \| deferred \| blocked \| completed \| abandoned` | Defaults to `accepted` |
| `review_notes` | `str \| null` | Optional manual notes |
| `goal_path` | `str \| null` | Optional validated goal link |
| `goal_title` | `str \| null` | Convenience copy for UI |
| `created_at` | `ISO-8601 str` | Set on first creation |
| `updated_at` | `ISO-8601 str` | Updated on every mutation |

#### Invariants

- At most one action item exists per recommendation.
- Action item writes stay within the recommendation markdown file; no separate action-item file is created.
- Weekly plan selection is deterministic for the same stored recommendations.

#### Error Handling

- Unknown recommendation id: returns `None` in storage; route translates to `404`.
- Invalid enum values: normalized to defaults in storage and rejected by route models.
- Missing goal path: route rejects with `404` when the supplied goal does not exist for the current user.

### Recommendation Ranking Feedback

**File:** `src/advisor/scoring.py`
**Status:** Stable

#### Behavior

- Existing engagement and rating boosts remain unchanged.
- A new execution boost uses recent action-item outcomes from recommendation storage.
- Completed actions provide positive signal.
- Deferred, blocked, and abandoned actions provide negative signal.
- Accepted-but-not-finished actions contribute a small positive signal so active follow-through is rewarded without equaling completion.

#### Configuration

| Constant | Default | Purpose |
|---------|---------|---------|
| `MIN_EXECUTION_EVENTS_FOR_BOOST` | `2` | Minimum outcomes before a category gets an execution boost |
| `MAX_EXECUTION_BOOST` | `1.0` | Maximum score delta from execution history |

### Web API Surface

**Files:** `src/web/routes/recommendations.py`, `src/web/models.py`
**Status:** Stable

#### Endpoints

- `GET /api/recommendations`
  - Existing list endpoint now includes optional `action_item` payload per recommendation.
- `POST /api/recommendations/{rec_id}/action-item`
  - Creates or returns a tracked action item for a recommendation.
- `PUT /api/recommendations/{rec_id}/action-item`
  - Updates status, effort, due window, review notes, blockers, and goal linkage.
- `GET /api/recommendations/actions`
  - Lists tracked action items, optionally filtered by status or goal.
- `GET /api/recommendations/weekly-plan`
  - Returns a capacity-limited plan assembled from accepted actions.

#### Security

- Goal linkage is validated against the current user’s journal directory.
- Recommendation reads and writes remain per-user through `get_user_paths()`.

### Goals UI Integration

**File:** `web/src/app/(dashboard)/goals/page.tsx`
**Status:** Stable

#### Behavior

- Goal-contextual recommendations can be converted directly into goal-linked action items.
- The page shows tracked actions grouped into a weekly focus section and under linked goals.
- Users can change action status, effort, due window, and review notes without leaving the goals page.
- Recommendations display whether they are still suggestions or already tracked for execution.

---

## Cross-Cutting Concerns

- **Persistence strategy:** markdown remains the single source of truth for recommendations and execution state.
- **Backwards compatibility:** recommendations without action items continue to work unchanged.
- **Explainability:** UI exposes the execution state directly so users can see which advice became action.

## Test Expectations

- Storage creates and updates structured action items without duplicating them.
- Weekly plan respects due-window order and capacity points.
- Execution stats feed recommendation scoring.
- Recommendation routes validate goal linkage and expose action items in list responses.
- Goals UI can render both goal-linked and unlinked tracked actions from API responses.

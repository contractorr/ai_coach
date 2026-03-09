# Action Plans

**Status:** Implemented
**Author:** —
**Date:** 2026-03-06

## Problem

Recommendations are useful, but they often stop at advice. Users need a lightweight way to turn a suggestion into a concrete follow-through loop inside the app, especially when that work should stay connected to an existing goal.

## Users

Users who already receive recommendations or suggestions and want help translating them into real progress without adopting a separate project-management tool.

## Desired Behavior

### Converting advice into action

1. User sees a recommendation in the app.
2. User can convert that recommendation into a tracked action item.
3. When the recommendation is viewed from a goal context, the action item can be attached to that goal.
4. The action item is created with a lightweight execution artifact that includes:
   - objective
   - next step
   - estimated effort
   - due window (`today`, `this_week`, `later`)
   - blockers
   - success criteria

### Managing action items

1. User can update an action item’s status.
2. Supported statuses are `accepted`, `deferred`, `blocked`, `completed`, and `abandoned`.
3. User can adjust the effort estimate and due window after creation.
4. User can add review notes once they have tried or completed the action.

### Weekly planning

1. The app assembles a small weekly plan from accepted action items.
2. The weekly plan respects a simple capacity budget so the user is not overloaded.
3. Higher-priority windows (`today`, then `this_week`, then `later`) are considered first.

### Learning from execution

1. The system distinguishes between recommendations that stayed as suggestions and recommendations that became tracked action items.
2. The system distinguishes between action items that completed versus drifted, deferred, or were abandoned.
3. Those execution outcomes influence future recommendation ranking in addition to explicit ratings.

### Goal linkage

1. Goal-linked action items appear as part of the goal workflow rather than as a separate standalone project board.
2. Users can see which recommendations are helping a specific goal move forward.

## Acceptance Criteria

- [ ] Any recommendation can be converted into a tracked action item.
- [ ] Action items support status, effort estimate, due window, blockers, success criteria, and review notes.
- [ ] Goal-contextual recommendations can be converted into goal-linked action items.
- [ ] The app can assemble a weekly plan from accepted actions using a simple capacity budget.
- [ ] Users can see which recommendations led to execution versus drift.
- [ ] Execution outcomes influence future recommendation ranking alongside existing rating feedback.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Recommendation has no existing generated action-plan text | System still creates a usable action item with sensible defaults |
| User converts the same recommendation twice | Existing tracked action item is shown instead of creating duplicates |
| Recommendation is linked from a goal card | New action item is attached to that goal automatically |
| User has no goals yet | Recommendation can still become an unlinked action item |
| Weekly plan capacity is too small for every accepted action | App selects a small, prioritized subset instead of overflowing the plan |
| An action becomes blocked or abandoned | It remains visible in history and counts as execution feedback rather than disappearing |

## Out of Scope

- Calendar syncing, reminders, or external task-manager integrations
- Multi-user collaboration, assignment, or project boards
- Nested sub-tasks beyond the single lightweight action item artifact
- Automatic completion of actions without user input

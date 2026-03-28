# Curriculum Recommendation Pilot

This pilot defines the minimum viable personalization and applied-assessment model for Learn.

## Recommendation Inputs

- Graph state: last-read chapter, enrolled guides, unlocked guides, and entry points.
- Profile context: current role, short/long-term goals, industries watching, active projects, and weekly time budget.
- Curriculum context: manifest-backed learning programs, program outcomes, and applied industry modules.

## Recommendation Priority Rules

1. Continue an active guide when a next unread chapter exists.
2. Otherwise rank enrolled incomplete guides by:
   - program/goal overlap
   - industry overlap
   - time-budget fit
3. Otherwise rank unlocked guides with the same context signals.
4. Otherwise rank entry-point guides with the same context signals.

The current pilot keeps progress momentum as the top priority, but it no longer picks new guides based only on DAG readiness order.

## Applied Assessment Types

- `teach_back`
  - Stage: `chapter_completion`
  - Output: short note or voice memo translating a chapter into workplace language
  - Use: checks comprehension and transfer after each chapter
- `decision_brief`
  - Stage: `review`
  - Output: one-page recommendation with assumptions, trade-offs, and a clear call
  - Use: turns spaced review into applied reasoning instead of recall only
- `scenario_analysis`
  - Stage: `scenario_practice`
  - Output: base/stress cases with leading indicators and response triggers
  - Use: pressure-tests frameworks mid-guide against realistic operating uncertainty
- `case_memo`
  - Stage: `capstone`
  - Output: 1-2 page memo with recommendation, rationale, execution plan, and failure modes
  - Use: serves as the guide/program capstone artifact

## Pilot Surface Area

- Backend
  - Extend `/api/curriculum/next` to return recommendation signals, matched programs, and assessment previews.
  - Extend guide detail payloads to expose the same assessment plan.
- Frontend
  - Show a visible personalized "Next up" card even when the next action is guide enrollment.
  - Show the assessment pilot on Learn landing and guide detail views.

This keeps the pilot inside the existing Learn system while defining a stable contract for later chapter-level implementation.

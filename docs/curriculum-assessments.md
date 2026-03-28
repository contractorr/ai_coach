# Applied Assessment Modes For Learn

Learn already supports quizzes, teach-back, pre-reading prompts, and placement bypass. Those are
useful, but they still skew toward short-answer recall and explanation. Professional learning
needs heavier assessment modes that test judgment, transfer, and synthesis.

## Assessment catalog

### 1. Extended teach-back

- **Learner job:** Explain the concept, state its boundary conditions, and transfer it to a fresh context.
- **Format:** 1 structured response with sections such as concept, limits, and application.
- **Rubric:** accuracy, completeness, transfer quality, clarity.
- **Best placement:** conceptually dense chapter completions and occasional review refreshers.

### 2. Scenario analysis

- **Learner job:** Read a changed situation, identify the real problem, and choose a defensible response.
- **Format:** short scenario prompt plus 1-3 paragraph response or structured bullets.
- **Rubric:** diagnosis, trade-off reasoning, recommended action, risk awareness.
- **Best placement:** chapter checkpoints for operational or policy-heavy material; optional review follow-ups.

### 3. Decision brief

- **Learner job:** Make a recommendation among competing options and justify it with course frameworks.
- **Format:** structured memo with recommendation, reasoning, risks, and metrics to watch.
- **Rubric:** recommendation quality, support from models, treatment of uncertainty, communication quality.
- **Best placement:** end-of-guide checkpoints and lighter industry-capstone submissions.

### 4. Case memo

- **Learner job:** Synthesize multiple chapters into a longer, realistic analysis of a sector, company, policy, or operating situation.
- **Format:** 500-1000 word memo or equivalent structured response with evidence and conclusion.
- **Rubric:** synthesis across concepts, evidence use, judgment, counterargument handling, clarity.
- **Best placement:** industry capstones and the end of multi-chapter guides.

## Placement by flow

| Learn flow | Assessment types | Notes |
|---|---|---|
| Chapter completion | Quiz, extended teach-back, scenario analysis | Default chapter-level applied modes should stay short enough to complete in one sitting. |
| Spaced review | Quiz, teach-back, short scenario refresh | Review should favor compact items; long memos do not belong in normal SM-2 sessions. |
| Guide checkpoint | Scenario analysis, decision brief | Use when a guide needs judgment beyond concept recall. |
| Industry capstone | Decision brief, case memo | Capstones should end in a real operating or sector judgment task. |
| Placement bypass | Placement quiz only | Placement remains a separate test-out path, not a longform assessment flow. |

## Recommended pairing rules

- Use **extended teach-back** when the chapter turns on one durable mental model.
- Use **scenario analysis** when the chapter teaches operating, policy, or strategy trade-offs.
- Use **decision briefs** when the learner must choose between options and defend a course of action.
- Use **case memos** when the learner must synthesize several chapters or complete an applied module.

## Minimum pilot path

The pilot should not attempt every new mode at once. The smallest credible rollout is:

1. Keep existing quizzes and teach-back unchanged for the general corpus.
2. Add **scenario analysis** for a small set of selected chapters.
3. Add **decision briefs** for selected guide finales and industry capstones.
4. Treat **case memos** as defined but deferred until the pilot proves submission UX and grading quality.

## Minimum implementation requirements

### Backend

- Extend curriculum assessment typing beyond `quiz`, `teachback`, and `pre_reading`.
- Add assessment metadata for prompt template, rubric, expected response shape, and whether the item belongs in SM-2 review.
- Reuse the current generate/grade pattern from teach-back, but generalize it into assessment generation and grading endpoints.
- Persist longform submissions and rubric feedback so capstone work is reviewable later.

### Frontend

- Replace the teach-back-only card assumption with a generic assessment card that can render prompt, rubric, response box, and grading feedback.
- Support short-answer and longform layouts without creating separate one-off components for every mode.
- Show assessment type labels clearly so users know whether they are explaining, analyzing, or recommending.

### Content / authoring

- Allow chapters and capstones to opt into assessment modes intentionally rather than generating them for every page.
- Tie each applied assessment back to chapter objectives, checkpoints, or capstone role so it does not feel bolted on.

## Proposed pilot sequence

### Phase 1

- Add generic assessment type support and a reusable assessment card.
- Pilot `scenario_analysis` on selected chapters from strategy, policy, or operations-heavy guides.

### Phase 2

- Pilot `decision_brief` on guide finales and industry capstones.
- Capture rubric scores plus learner submission text for review and iteration.

### Phase 3

- Add `case_memo` only after the submission flow, grading rubric, and UI affordances are proven.

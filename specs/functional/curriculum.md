# Curriculum / Learn

**Status:** Implemented

## Purpose

Learn is the app's structured study workspace. It turns the curriculum corpus into a guided,
tracked learning system with active recall, spaced repetition, personalized next-step
recommendations, and authoring QA.

## Product Placement

- Workspace: `Learn`
- Primary job: help the user study, retain, and revisit structured material
- Primary framing: a daily learning workflow organized around outcome-based programs, not only a guide library
- Cross-system handoffs:
  - guide enrollment can create a linked `learning` goal with chapter milestones
  - completed chapters can trigger reflection prompts and best-effort memory extraction
  - advisor context can include active curriculum progress
  - due reviews can surface on Home and in the main Learn workspace

## Current Behavior

- The shipped curriculum is scanned from `content/curriculum/`.
- Guides are organized by a manifest-driven graph in `skill_tree.yaml`:
  - tracks
  - prerequisite edges
  - canonical guide aliases
  - outcome-based learning programs
- Learn supports both legacy markdown and schema-first `MDX + frontmatter`.
- The primary learner surfaces are:
  - Home `Today in Learn` card
  - `/learn` Today queue
  - `/learn` program-path cards
  - `/learn` grid view
  - `/learn` tree view
  - guide detail
  - chapter reader
  - review session
- `/learn` is now organized as:
  - a prioritized daily queue
  - outcome-based program paths
  - a secondary library/map section
- The current study loop includes:
  - pre-reading prompts
  - chapter completion
  - inline reflection writing
  - free-form chapter quiz answers with grading feedback
  - teach-back prompts
  - SM-2 review scheduling
  - placement / test-out for advanced users
- Recommendation UX is profile-aware:
  - role
  - goals
  - industries
  - time budget
  - learning-program overlap
- Recommendation ranking also now consumes live learning-performance signals:
  - weak-item density from recent review history
  - applied-deliverable grades
  - revision backlog on active deliverables
- The recommendation logic now also feeds a `Today in Learn` workflow payload:
  - primary action for the current block
  - due-review task when recall is waiting
  - applied-practice prompt for active guides
  - active/recommended program-path cards with progress counts
- Guide and recommendation payloads also expose an applied-assessment pilot:
  - teach-back note
  - decision brief
  - scenario analysis
  - case memo
- Applied assessments are no longer view-only:
  - guide detail can create a persisted draft in Journal
  - launch also creates a linked learning goal for the deliverable
  - existing drafts reopen from guide detail and the Today queue
  - Journal drafts can be edited and submitted for rubric feedback
  - stronger submissions close the loop; weaker ones stay active for revision
- Learn now closes a weak-recall loop:
  - the Today queue can surface `retry weak items`
  - `/learn/review?mode=retry` focuses on recently weak recall items
- Curriculum visuals are no longer markdown-only:
  - typed visual blocks render as web-native components
  - legacy ASCII diagrams and plain data tables still fall back safely

## User Flows

### Discover and choose

- User opens Home or `/learn`.
- They first see a `Today in Learn` queue rather than only a generic catalog.
- They can open the primary task immediately, clear due reviews, or jump into a recommended program path.
- They can still browse a guide grid or switch to a tree view.
- Grid view supports search, category filtering, and sort modes.
- Tree view supports:
  - track filters
  - learning-program filters
  - prerequisite edges
  - progress/mastery-aware guide nodes
- Program-path cards summarize:
  - whether the path is active, recommended, or merely available
  - completed/in-progress/ready guide counts
  - path outcomes
  - a direct link into the tree view filtered to that path
- The daily queue can recommend:
  - continuing a chapter
  - clearing due reviews
  - retrying recently weak review items
  - starting an unlocked guide
  - opening applied-practice work for the current guide or its existing draft

### Enroll and orient

- User opens a guide detail page.
- Guide detail shows:
  - chapter list
  - difficulty
  - reading-time estimate
  - learning-program membership
  - applied-assessment pilot cards
  - placement/test-out action when the guide is not already complete
- Each applied-assessment card can:
  - create a draft artifact in Journal
  - create a linked learning goal with default milestones
  - reopen an existing draft instead of duplicating it
  - show status and latest feedback when the deliverable has already been reviewed
- Enrolling in a guide persists enrollment and can auto-create a linked learning goal with
  non-glossary chapters as milestones.

### Read and complete a chapter

- User opens a chapter reader.
- Chapter content renders through the curriculum renderer.
- Internal curriculum links resolve to in-app `/learn/...` routes.
- Reading time is synced periodically.
- On completion:
  - chapter progress is updated
  - a reflection prompt may be returned
  - the learner can write their own reflection and save it to the journal
  - memory extraction is attempted best-effort

### Active recall and review

- Before reading, a pre-reading card can show priming questions.
- After or during reading, the learner can generate a chapter quiz.
- Quiz flow supports:
  - inline answer fields
  - free-form submission
  - grading feedback
  - correct/missing points
  - retry/resubmit flow
- After completion, teach-back can be generated and graded separately.
- Due items appear in `/learn/review` and are scheduled using SM-2.
- Recently weak recall items can be retried in a separate retry-mode review session.
- Applied deliverables can be edited in Journal and submitted for rubric feedback.
- Feedback keeps weaker deliverables active for revision and marks stronger submissions complete.

### Test out

- Guide detail can offer "Test out".
- Placement questions are generated across the guide's non-glossary chapters.
- Passing placement marks the guide complete.
- Failing placement returns per-question grading without mutating guide completion.

### Authoring and QA

- Maintainers can lint curriculum content.
- Maintainers can migrate legacy markdown to schema-first MDX.
- Maintainers can audit thin guides and applied modules for rewrite planning.
- Manifest QA checks cover:
  - missing guides
  - missing prerequisites
  - missing track assignment
  - duplicate track assignment
  - program references
  - cycles
  - alias-target validity

## Acceptance Criteria

- [x] Home and `/learn` both surface a `Today in Learn` workflow rather than only a passive recommendation card.
- [x] `/learn` exposes both grid and tree views for the curriculum as secondary library surfaces.
- [x] `/learn` surfaces outcome-based program paths with progress counts and direct navigation into filtered tree views.
- [x] Guides can be enrolled and tracked persistently.
- [x] Guide enrollment can create linked learning goals with chapter milestones.
- [x] Chapter reading progress accumulates across sessions.
- [x] Chapter completion can return an inline reflection prompt.
- [x] Learners write and save their own reflection text rather than saving prompt text directly.
- [x] Chapter quizzes support free-form answers, grading feedback, and retry flow.
- [x] Teach-back prompts can be generated and graded for completed chapters.
- [x] Pre-reading prompts can be generated separately from review scheduling.
- [x] SM-2 review sessions surface due items and reschedule them after grading.
- [x] Placement/test-out exists for non-completed guides.
- [x] Guide graph data comes from curated manifest metadata rather than only directory ordering.
- [x] Canonical guide aliases are resolved so deprecated guide IDs do not remain in the active graph.
- [x] Learning programs are data-driven from the manifest.
- [x] `/api/curriculum/next` is profile-aware and not only prerequisite-aware.
- [x] `/api/curriculum/next` also reacts to weak recall, deliverable grades, and revision backlog within the existing candidate buckets.
- [x] `/api/curriculum/today` assembles a ranked learning queue plus active/recommended program paths.
- [x] Recommendation and guide payloads surface applied-assessment pilot data.
- [x] Applied-assessment cards can create persisted Journal drafts and linked learning goals.
- [x] Existing applied-assessment drafts reopen instead of creating duplicate artifacts.
- [x] Applied-assessment drafts can be edited in Journal and submitted for rubric feedback.
- [x] Strong applied-assessment submissions complete their linked learning goal.
- [x] Recently weak review items can resurface through a retry-specific review queue.
- [x] Typed visual blocks render as web-native visuals.
- [x] Legacy markdown diagrams and data blocks still degrade gracefully.
- [x] Internal curriculum links navigate correctly inside the app.
- [x] Curriculum lint, migration, and audit commands exist for maintainers.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Content directory missing or empty | Sync returns no guides; Learn shows empty or reduced state without crashing |
| Guide requested via deprecated alias | API resolves to canonical guide ID |
| Alias-based old user progress exists | Sync reconciles stale alias enrollment/progress/review rows into canonical IDs |
| Chapter has legacy markdown only | Scanner and renderer still support it |
| Chapter has schema-first MDX | Scanner prefers MDX over same-stem markdown |
| External links in chapter content | Render normally; lint ignores them for curriculum-reference validation |
| No LLM available for question generation | Generation degrades or returns empty outputs rather than breaking the rest of Learn |
| Memory extraction fails | Progress update still succeeds |
| Goal creation fails on enroll | Enrollment still succeeds |
| Guide has no assessable non-glossary chapters | Placement generation rejects cleanly |
| Related-chapter search has too little context | Related card returns empty state / no content rather than error |

## Related Design Docs

- `docs/curriculum-authoring.md`
- `docs/curriculum-redesign-roadmap.md`
- `docs/curriculum-recommendation-pilot.md`
- `docs/curriculum-assessments.md`
- `docs/curriculum-industry-capstones.md`

## Out of Scope

- Strict prerequisite gating or locking
- Automatic corpus-wide content rewrites
- Treating industry capstones as full multi-chapter textbooks by default
- Replacing all legacy markdown immediately before migration

## Key System Components

- `web/src/app/(dashboard)/learn/page.tsx`
- `web/src/app/(dashboard)/home/page.tsx`
- `web/src/app/(dashboard)/learn/[guideId]/page.tsx`
- `web/src/app/(dashboard)/learn/[guideId]/[chapterId]/page.tsx`
- `web/src/app/(dashboard)/learn/review/page.tsx`
- `web/src/components/curriculum/`
- `web/src/components/home/LearningSnapshotCard.tsx`
- `src/web/routes/curriculum.py`
- `src/curriculum/content_schema.py`
- `src/curriculum/scanner.py`
- `src/curriculum/store.py`
- `src/curriculum/question_generator.py`
- `src/curriculum/personalization.py`
- `src/curriculum/spaced_repetition.py`
- `src/curriculum/embeddings.py`
- `src/coach_mcp/tools/curriculum.py`
- `content/curriculum/skill_tree.yaml`

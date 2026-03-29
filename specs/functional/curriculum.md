# Curriculum / Learn

**Status:** Proposed Simplification

## Purpose

Learn is the app's lightweight learning workspace. Its job is simple:

- help the user pick something worth learning
- help them continue where they left off
- help them remember the important parts

It should feel calm, obvious, and low-friction. It should not feel like a learning operating
system.

## Product Principles

- One clear next step: every visit should make it obvious what to do next.
- Fewer concepts: users should only need to understand `guide`, `chapter`, and `review`.
- Reading first: the core value is reading and retaining useful material, not managing a learning framework.
- Progressive disclosure: advanced structure can exist in the system, but it should not dominate the core UI.
- Optional reflection: writing and deeper exercises can help, but they must never block progress.

## Product Placement

- Workspace: `Learn`
- Guide catalog: `Guide Library`
- Primary job: study practical material in small steps
- Core question answered: `What should I learn next?`
- Relationship to Home: Home can surface the next learning step, but the full learning workflow lives in `/learn`
- Relationship to the rest of the app:
  - learning should not require Goals to make sense
  - learning should not require Journal to make sense
  - learning should not require Radar or Research context to make sense

## Simplified Product Model

The learning experience should be built around just three things:

1. A guide
2. A chapter
3. A review queue

Everything else is secondary or deferred.

### Guide

- A guide is a short structured unit of learning on one topic.
- A guide has:
  - title
  - short summary
  - estimated effort
  - chapter list
  - simple progress state

### Chapter

- A chapter is the primary unit of progress.
- A chapter supports:
  - reading
  - marking complete
  - optional recap or reflection

### Review

- Review is a lightweight queue for recall after reading.
- Review should feel like a single simple follow-up flow, not a separate product mode with multiple subtypes.

## Desired User Experience

### Home

- Home shows one learning card.
- That card contains:
  - one primary next action
  - a small reviews-due count when relevant
  - a single link into the Guide Library
- Home should not expose multiple learning concepts at once.

### Learn landing page

The Learn page should have only three primary sections:

1. `Next up`
2. `Reviews`
3. `Guide Library`

#### Next up

- Show one primary action:
  - continue current chapter
  - start the next chapter
  - clear due reviews
  - start a selected guide if nothing is in progress
- Include one short explanation line if helpful.
- Do not show multiple recommendation systems, signal chips, or competing CTAs.

#### Reviews

- Show a small summary when reviews are due.
- Use one review entry point: `Start review`.
- Do not split the user into different review concepts such as normal review vs retry review in the main UI.

#### Guide Library

- Show a simple searchable guide list.
- Keep filtering lightweight.
- Support one lightweight topic filter based on broad guide category.
- Support one simple order control:
  - `Recommended order`
  - `A-Z`
- Prioritize:
  - in-progress guides first
  - then guides the user can start now
  - then later guides with unmet prerequisites
- The primary browse goal is choosing a guide, not understanding a graph.

### Guide detail

Guide detail should answer only:

- What is this guide about?
- How long is it?
- Where should I start or continue?

Guide detail should include:

- guide title and summary
- chapter list
- simple progress
- one obvious CTA:
  - `Start`
  - `Continue`
  - `Review`

Guide detail should not be a control panel.

### Chapter reader

The chapter reader should focus on finishing the chapter with minimal distraction.

Visible actions should be kept to:

- `Mark complete`
- `Start review` or `Review later`
- previous / next chapter navigation

Optional support can exist below the core reading flow, but it must stay secondary.

### Review session

- Review should be one lightweight session flow.
- The user enters, answers a small batch, and exits.
- Completion should feel satisfying and quick.
- The system can keep richer scheduling logic internally, but the UI should present one simple review concept.

## Core User Flows

### Start learning

- User opens Learn.
- They see one obvious next step.
- If nothing is in progress, they browse guides and start one.

### Continue learning

- User opens Learn.
- They see the chapter they should continue.
- One click takes them back into reading.

### Finish a chapter

- User reads a chapter.
- User marks it complete.
- The system can optionally offer a short recap question or reflection.
- Completion moves the user forward without requiring extra work.

### Review material

- When reviews are due, Learn highlights that clearly.
- User starts one review session.
- User completes the batch and returns to Learn.

### Browse and switch

- User can browse guides with search.
- Switching guides should be easy, but the product should gently favor one active guide at a time.

## What We Should Keep

- Guide catalog
- Guide detail
- Chapter reading
- Enrollment / progress tracking
- Simple review queue
- Home handoff into learning
- Basic search across guides

## What We Should Simplify Hard

- Collapse the current `Today` workflow into one primary next action instead of a ranked task stack.
- Replace multiple recommendation labels and learning signal badges with plain-language copy.
- Reduce metrics on the main page to the minimum needed for orientation.
- Make review feel like one mode, not a family of modes.
- Keep the primary landing page readable without needing to understand programs, tracks, or remediation logic.

## Deferred / Out of Scope For The Minimalist Version

- Program paths as a primary concept
- Tree / graph view in the main learning flow
- Track filters and prerequisite visualization
- Applied assessments and deliverable workflows
- Automatic goal creation from learning actions
- Journal draft creation as part of the core loop
- Teach-back as a primary workflow
- Pre-reading prompts as a primary workflow
- Placement / test-out
- Related chapter suggestions in the primary flow
- Retry-specific review mode in the main UI
- User-authored guide generation and guide extensions
- Complex performance signals exposed directly in the UI

These may remain technically possible, but they should not shape the core experience until the
minimal loop proves useful.

## Acceptance Criteria

- [ ] Home shows one learning CTA, not multiple learning decisions.
- [ ] `/learn` has at most three primary sections: `Next up`, `Reviews`, and `Guide Library`.
- [ ] `/learn` can be understood without knowing what a program, path, track, or assessment is.
- [ ] A user can start or continue learning from the landing page in one click.
- [ ] A guide detail page has one obvious primary action.
- [ ] A chapter reader keeps the reading flow primary and secondary tools visually subordinate.
- [ ] Reviews are entered through one simple entry point.
- [ ] Progress can advance without requiring reflection, quiz completion, or Journal usage.
- [ ] Guide Library supports lightweight topic filtering and a clear recommended order without exposing tracks or trees.
- [ ] Search is sufficient for finding guides in the normal case.
- [ ] Learning does not auto-create goals or drafts as part of the default flow.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User has one active guide and due reviews | The page chooses one recommended next step and still shows the other option clearly |
| User has no active guide | Learn defaults to a simple browse-and-start state |
| User has no reviews due | Review section stays quiet and does not create dead space |
| User returns after a long gap | Learn still shows one obvious next action rather than a dense dashboard |
| User wants a deeper exercise | The app can link outward, but the default learning flow stays lightweight |
| Content is missing or sync fails | The page degrades to a simple empty or reduced state without exposing internal complexity |

## Design Notes

- Prefer plain language:
  - use `Next up`, `Guide`, `Chapter`, `Review`, and `Guide Library`
  - avoid `program path`, `placement`, `teach-back`, `assessment`, and `retry mode` in the main flow
- Prefer one strong CTA over several equal CTAs.
- Avoid dashboards full of badges, counts, and status cues unless they change the next action.
- Favor vertical reading flow over control-heavy layouts.

## Key System Components

- `web/src/app/(dashboard)/learn/page.tsx`
- `web/src/app/(dashboard)/home/page.tsx`
- `web/src/app/(dashboard)/learn/[guideId]/page.tsx`
- `web/src/app/(dashboard)/learn/[guideId]/[chapterId]/page.tsx`
- `web/src/app/(dashboard)/learn/review/page.tsx`
- `src/web/routes/curriculum.py`
- `src/curriculum/store.py`
- `src/curriculum/personalization.py`

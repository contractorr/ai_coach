# Curriculum / Learn

**Status:** Implemented

## Purpose

Learn is a structured study workspace that turns a corpus of markdown guides into a tracked learning system with spaced repetition, active recall testing, and progress tracking.

## Product Placement

- Workspace: `Learn`
- Primary job: read, study, and retain knowledge from curated guides
- Cross-system handoffs: completed chapters create memory facts (auto-extracted), guide enrollment auto-creates goals with milestones, review reminders surface in recommendations, advisor RAG injects `<curriculum_progress>` context

## Current Behavior

- 327 markdown chapters across ~50 guides ship with the app in `content/curriculum/`.
- Guides span 7 categories: science, humanities, business, technology, industry, social science, professional.
- Users enroll in guides, read chapters, track progress, and take quizzes.
- SM-2 spaced repetition schedules review items for long-term retention.
- Questions generated at Bloom's taxonomy levels: remember → understand → apply → analyze → evaluate → create.
- ASCII diagrams render faithfully as styled monospace blocks.

## User Flows

### Browse & enroll
- User opens `/learn` and sees a grid of all guides with category badges, difficulty indicators, and estimated reading time.
- User can filter by category, search by title, and sort by recommended/alpha/progress/difficulty.
- User clicks a guide to see chapters and enrolls to start tracking.
- On enrollment, a learning goal is auto-created with chapter titles as milestones. Opt-out via `create_goal=false` query param.

### Read
- User opens a chapter. Content renders as rich markdown with styled diagram blocks and tables.
- When a diagram or table contains parseable numeric data, a chart toggle (bar chart icon) appears top-right. Clicking it renders an interactive Recharts overlay (bar, line, or scatter). Clicking again returns to ASCII view.
- Reading time is tracked automatically (IntersectionObserver + 30s periodic sync).
- User marks chapter complete and navigates prev/next.
- On chapter completion, a reflection prompt card appears inline suggesting a brief reflection. User can write a journal reflection or dismiss.

### Quiz
- After reading, user starts a quiz. System generates 5 questions at varying Bloom's levels.
- User submits free-form answers. REMEMBER questions graded by keyword matching; higher levels graded by LLM.
- Questions cached per chapter content hash — regenerated only on content changes.

### Spaced repetition review
- User opens `/learn/review` to see due review items (SM-2 scheduled).
- Flashcard UI: question → answer → self-grade (0-5 mapped to labels: Blackout through Perfect).
- Session pulls up to 20 items. After session, summary shows count reviewed and average grade.

### Continue reading
- Dashboard shows "continue reading" card with last chapter and "reviews due" card with count.
- `/api/curriculum/next` returns advisor-recommended next chapter based on enrollment and last read.

## Acceptance Criteria

- [ ] `/learn` lists all guides with correct category, difficulty, chapter count, and reading time
- [ ] Enrolling in a guide tracks it persistently; progress survives page reload
- [ ] Chapter reader renders markdown content including ASCII diagrams and tables
- [ ] Reading time accumulates across sessions (not resets)
- [ ] Marking all non-glossary chapters complete auto-completes the guide
- [ ] Quiz generates questions at specified Bloom's levels
- [ ] SM-2 scheduling correctly increases intervals on successful recall, resets on failure
- [ ] Review session shows due items and advances to next after grading
- [ ] Content sync picks up new/changed chapters and regenerates questions for changed content
- [ ] MCP tools expose curriculum data for Claude Code integration
- [ ] Numeric tables/diagrams show interactive chart toggle; renders Recharts overlay
- [ ] Enrolling in a guide creates a learning goal with chapter milestones
- [ ] Completing a chapter shows inline reflection prompt; memory facts auto-extracted
- [ ] Advisor queries include `<curriculum_progress>` context when user has active enrollments

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No content dirs exist | Sync returns 0, dashboard shows empty state with sync button |
| Chapter markdown has no H1 | Title derived from filename |
| Content changes (re-scan) | content_hash mismatch triggers question regeneration |
| All chapters completed | Guide marked complete, excluded from "next" recommendations |
| Chapter has no numeric data | Chart toggle does not appear |
| Goal creation fails on enroll | Enrollment succeeds; goal creation is best-effort |
| Memory extraction fails | Progress update succeeds; extraction is best-effort |
| No LLM available for quiz | Keyword matching fallback for grading |
| Industry guide naming | `Industries/Healthcare/` → guide ID `industry-healthcare` |

### Teach-back / Feynman prompts
- After completing a chapter, user sees a "Teach-back" card prompting them to explain the key concept in their own words.
- Generated lazily on first request: LLM identifies the single most important concept from chapter content.
- Prompt: "Explain {concept} as if teaching someone with no background."
- User writes a free-form explanation in a large textarea.
- On submit, expensive LLM grades on 3 dimensions: accuracy (0-5), completeness (0-5), clarity (0-5), plus overall grade (0-5).
- Teach-back items enter SM-2 cycle alongside quiz items (bloom_level=CREATE).
- One teach-back per chapter; cached after first generation.
- Toggled via `curriculum.teachback_enabled` (default true).

### Pre-reading questions
- Before reading a chapter, user sees a collapsible "Before you read" card with 2-3 attention-priming questions.
- Questions cannot be answered without reading the chapter; they direct attention to key concepts.
- Generated alongside quiz questions in the same LLM call. Stored as review items but never enter SM-2 cycle.
- After chapter completion, header changes to "Check your understanding" (same questions).
- No input fields, no grading — read-only priming.
- Toggled via `curriculum.pre_reading_enabled` (default true).

### Cross-guide chapter connections
- After quiz section, user sees a "Related from other guides" card with 2-3 links to chapters from other enrolled guides covering similar topics.
- Uses ChromaDB embeddings to find semantically related chapters, post-filtered to exclude same guide and limit to enrolled guides.
- Each link shows "{chapter_title} — {guide_title}" and navigates to that chapter.
- Empty state: renders nothing (e.g., single enrolled guide = no results).
- Toggled via `curriculum.cross_guide_connections` (default true).

## Acceptance Criteria (Deep Processing Features)

- [ ] Completing a chapter shows teach-back card; user can submit explanation and see 3-dimension grading
- [ ] Teach-back items appear in SM-2 review sessions with "Teach-back" badge and larger textarea
- [ ] Pre-reading card appears above chapter content with 2-3 priming questions (collapsed by default)
- [ ] Pre-reading questions never appear in review sessions
- [ ] After chapter completion, pre-reading header changes to "Check your understanding"
- [ ] Related chapters card shows cross-guide connections below quiz section
- [ ] Related chapters only shows results from other enrolled guides
- [ ] All three features respect their config toggles

## Edge Cases (Deep Processing Features)

| Scenario | Expected Behavior |
|----------|-------------------|
| Chapter not completed | Teach-back card not shown |
| Teach-back already generated | Returns cached item |
| No LLM for teach-back grading | Keyword fallback grading |
| Pre-reading with no LLM | No pre-reading card shown |
| Single enrolled guide | Related chapters card renders nothing |
| Glossary chapter | No pre-reading or teach-back generated |
| Hash-based fallback embedder | Higher distance threshold (0.5) for related chapters |

## Out of Scope

- Cross-domain synthesis questions — requires 3+ active guides

## Key System Components

- `web/src/app/(dashboard)/learn/page.tsx` — dashboard
- `web/src/app/(dashboard)/learn/[guideId]/page.tsx` — guide detail
- `web/src/app/(dashboard)/learn/[guideId]/[chapterId]/page.tsx` — chapter reader
- `web/src/app/(dashboard)/learn/review/page.tsx` — review session
- `web/src/components/curriculum/` — GuideCard, ChapterList, CurriculumRenderer, ReviewCard, etc.
- `src/web/routes/curriculum.py` — 16 API endpoints
- `src/curriculum/` — scanner, store, spaced_repetition, question_generator, models
- `src/coach_mcp/tools/curriculum.py` — 5 MCP tools
- `content/curriculum/` — 327 markdown chapters

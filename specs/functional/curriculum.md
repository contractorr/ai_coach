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

### Authoring QA
- Maintainers run `coach curriculum lint --path content/curriculum` before shipping guide changes.
- The lint report surfaces broken curriculum references, missing frontmatter fields, missing objectives/checkpoints, thin chapters, chapter-order gaps, duplicate chapter concepts inside a guide, and manifest graph issues such as missing guides, missing prerequisites, duplicate track assignments, and prerequisite cycles.
- Maintainers run `coach curriculum audit --path content/curriculum` to rank thin guides and applied modules for rewrite planning.
- Lint output is available in text and JSON so CI or scripts can consume it directly.

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
- [ ] `coach curriculum lint` reports broken references, missing frontmatter metadata, missing objectives/checkpoints, thin chapters, and chapter-order/path coherence problems
- [ ] `coach curriculum lint` reports manifest graph problems clearly, including missing guide references and prerequisite cycles
- [ ] `coach curriculum audit` ranks thin guides and applied industry modules for rewrite planning

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

| External URL in chapter body | Ignored by curriculum lint |
| Alias in `skill_tree.yaml` | QA resolves alias to canonical guide before graph checks |
| Guide present in content but absent from tracks | Lint flags missing track assignment |

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

### Skill tree

- `/learn` organizes guides into **tracks** — thematic groupings with curated prerequisite chains.
- 6 tracks: Foundations, Natural Sciences, Human Sciences, Business & Economics, Technology, Industry.
- Each guide belongs to exactly one track. Prerequisites are hand-curated per guide (not auto-inferred from directory numbering).
- A **mastery score** (0-100) is computed per guide from completion + review performance. Displayed on guide cards and aggregated per track.
- Tracks and prerequisites are **informational only** — no gating or locking. Users can start any guide regardless of prerequisite completion.
- Track view shows aggregate stats: guides completed, average mastery, completion percentage.
- MCP `curriculum_list_guides` accepts optional `track` filter.

#### Acceptance Criteria (Skill Tree)

- [ ] Every guide belongs to exactly one track
- [ ] Guide cards show mastery score
- [ ] `/api/curriculum/tracks` returns 6 tracks with aggregate stats
- [ ] Prerequisites come from curated manifest, not directory numbering
- [ ] Incomplete prerequisites do not block enrollment or reading
- [ ] MCP tool filters by track
- [ ] `GET /api/curriculum/tree` returns full DAG: tracks, nodes (with position hints), and edges
- [ ] Each node includes status, mastery, progress, and layout position (x, y, depth)
- [ ] Entry-point guides have `is_entry_point: true` and `depth: 0`
- [ ] Cross-track prerequisite edges are included
- [ ] Layout positions computed via topological sort (longest path from root)
- [ ] `/learn` page has Grid/Tree tabs; Grid tab shows existing guide grid, Tree tab shows DAG view
- [ ] Tree view groups nodes by depth tier with SVG edges connecting prerequisites
- [ ] Track filter badges in tree view filter nodes by track
- [ ] Node cards show status (color-coded), mastery, progress, and track color border
- [ ] Clicking a tree node navigates to guide detail page
- [ ] Tree view scrolls horizontally on narrow screens

#### Edge Cases (Skill Tree)

| Scenario | Expected Behavior |
|----------|-------------------|
| Guide not in manifest | Empty track, empty prerequisites, mastery still computed |
| Manifest file missing | Falls back to auto-inferred prereqs from directory ordering |
| Duplicate guides (34-game-theory, 35-engineering) | Each appears in its natural track with appropriate prereqs |
| No reviews for a guide | Mastery = completion_pct * 0.4 |
| No progress at all | Mastery = 0 |

### Enhanced recommendations (DAG-aware)

- `/api/curriculum/next` uses DAG-aware priority: (1) continue last-read, (2) next enrolled incomplete, (3) ready-to-start guide (all prereqs completed, not yet enrolled), (4) entry-point guide (no prereqs, not enrolled), (5) fallback message.
- Ready-to-start suggestions return `action: "enroll"` so the frontend can offer one-click enrollment.
- `/api/curriculum/ready` returns all guides whose prerequisites are fully completed but the guide itself is not enrolled.
- MCP `curriculum_skill_tree` tool returns tree data + edges for Claude Code integration.
- MCP `curriculum_recommend_next` uses same DAG-aware priority as web route.

#### Acceptance Criteria (Enhanced Recommendations)

- [ ] `/next` returns a ready-to-start guide when no active reading exists but prereqs are met
- [ ] `/next` returns an entry-point guide when no enrolled or ready guides exist
- [ ] Ready-to-start suggestions include `action: "enroll"` field
- [ ] `/ready` returns guides with all prereqs completed, excludes already-enrolled
- [ ] MCP `curriculum_skill_tree` returns nodes and edges matching web `/tree` endpoint
- [ ] MCP `curriculum_recommend_next` suggests DAG-aware guides

#### Edge Cases (Enhanced Recommendations)

| Scenario | Expected Behavior |
|----------|-------------------|
| No prereqs completed | `/ready` returns empty list; `/next` suggests entry points |
| All guides enrolled | `/ready` returns empty; `/next` uses enrolled-incomplete logic |
| Circular prereqs (shouldn't exist) | Guide never appears in ready list |
| Guide prereq points to nonexistent guide | Guide excluded from ready list |

### Personalized next-step recommendations (planned)

- The next-step flow should remain DAG-aware, but it should rank valid candidates using learner context such as role, industry intent, goals, and time budget.
- The pilot should stay inside the existing Learn entry points: `/api/curriculum/next`, the Learn landing card, and guide-detail enrollment CTAs.
- Recommendation explanations should be user-visible so the system can justify why a guide is suggested now.
- The current pilot scope and data dependencies live in `docs/curriculum-recommendation-pilot.md`.

### Placement bypass (test-out)

- Advanced users can "test out" of a guide by taking a placement quiz covering all chapters.
- Placement generates 2 questions per non-glossary chapter (capped at 15 total) at APPLY/ANALYZE/EVALUATE Bloom's levels.
- Questions are ephemeral — never stored in review_items or SM-2 cycle.
- Server caches questions for 1 hour; client never sees expected answers.
- If average grade >= threshold (default 3.5/5): guide auto-completed (all chapters + guide marked done).
- If average grade < threshold: user sees per-question grades and a "Start reading instead" CTA.
- "Test out" button visible on guide detail when guide is NOT completed.
- Toggled via `curriculum.placement_enabled` (default true).

#### Acceptance Criteria (Placement Bypass)

- [ ] "Test out" button visible on guide detail for non-completed guides
- [ ] Placement generates questions at APPLY+ Bloom's levels, not REMEMBER/UNDERSTAND
- [ ] Client receives questions without expected answers
- [ ] Passing placement marks all chapters + guide as completed in one transaction
- [ ] Failing placement does NOT modify any progress
- [ ] Cached questions expire after 1 hour (410 on stale submit)
- [ ] `placement_enabled=false` config disables the feature (400 response)
- [ ] Placement-completed guide shows as completed in tree view and stats

#### Edge Cases (Placement Bypass)

| Scenario | Expected Behavior |
|----------|-------------------|
| Guide already completed | Generate endpoint rejects (400) |
| Guide has 1 chapter | 2 questions generated, cap doesn't apply |
| Guide has 20 chapters | Capped at 15 questions total |
| All glossary chapters | No questions generated, endpoint returns error |
| Cache expired on submit | 410 Gone response |
| No LLM available | 500 with error message |

### Applied assessments (planned)

- Learn should expand beyond quizzes and short teach-back prompts into applied modes such as extended teach-back, scenario analysis, decision briefs, and case memos.
- Chapter completions can use short applied tasks; guide endings and industry capstones should use heavier decision-oriented submissions.
- Normal SM-2 review should keep only compact items; longform memos should remain outside the standard review queue.
- The current design and pilot scope live in `docs/curriculum-assessments.md`.

## Out of Scope

- Cross-domain synthesis questions — requires 3+ active guides

## Key System Components

- `web/src/app/(dashboard)/learn/page.tsx` — dashboard
- `web/src/app/(dashboard)/learn/[guideId]/page.tsx` — guide detail
- `web/src/app/(dashboard)/learn/[guideId]/[chapterId]/page.tsx` — chapter reader
- `web/src/app/(dashboard)/learn/review/page.tsx` — review session
- `web/src/components/curriculum/` — GuideCard, ChapterList, CurriculumRenderer, ReviewCard, SkillTree, SkillTreeNode, SkillTreeEdges, etc.
- `src/web/routes/curriculum.py` — 21 API endpoints
- `src/curriculum/` — scanner, store, spaced_repetition, question_generator, models
- `src/coach_mcp/tools/curriculum.py` — 6 MCP tools
- `content/curriculum/` — 327 markdown chapters

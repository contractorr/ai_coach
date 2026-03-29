# Curriculum

**Status:** Implemented

## Overview

The curriculum subsystem powers the Learn workspace. It scans the curriculum corpus, normalizes
content metadata, stores per-user progress and review state, exposes web and MCP surfaces, and
supports richer rendering and recommendation behavior than the original markdown-only reader.

This spec describes the current shipped architecture rather than the earlier prototype.

## Dependencies

**Depends on:** `db`, `llm`, `memory`, `journal`, `profile`, `advisor.rag`, embeddings/chroma utilities  
**Depended on by:** `web.routes.curriculum`, `coach_mcp.tools.curriculum`, `advisor.rag`

## Major Components

### Content Schema and Authoring

**Files:** `src/curriculum/content_schema.py`, `src/frontmatter.py`, `src/cli/commands/curriculum.py`

#### Responsibilities

- Parse both legacy `.md` and schema-first `.mdx` curriculum documents into a normalized
  `CurriculumDocument`.
- Prefer `.mdx` over `.md` when both exist for the same chapter stem.
- Infer missing metadata for legacy content when frontmatter is absent.
- Power maintainer tooling:
  - `coach curriculum lint`
  - `coach curriculum migrate`
  - `coach curriculum audit`

#### Document model

`CurriculumDocument` captures:

- `title`
- `summary`
- `objectives`
- `checkpoints`
- `content_references`
- `body`
- `content_format`
- `schema_version`
- frontmatter presence and raw metadata

#### Lint coverage

- required frontmatter fields
- broken curriculum references
- broken relative chapter links
- broken `/learn/<guide>/<chapter>` references
- thin chapters
- duplicate chapter ordering
- path gaps
- duplicate concepts inside a guide
- manifest graph errors:
  - unknown alias targets
  - unknown guides
  - unknown prerequisites
  - duplicate track assignment
  - missing track assignment
  - unknown program references
  - prerequisite cycles

#### Reporting model

- `CurriculumLintIssue`: `{code, path, message, severity}`
- `CurriculumLintReport`: `{documents_scanned, issues}`
- text output is intended for maintainers
- JSON output is intended for CI and scripted review

#### Audit coverage

`audit_curriculum_root()` produces a rewrite-planning report that:

- ranks thin core guides by rewrite priority
- treats industry guides as applied modules / capstones
- reports superseded aliases
- incorporates dependency leverage and program membership into ranking
- aligns with the rewrite and capstone planning docs in `docs/`

### CurriculumScanner

**File:** `src/curriculum/scanner.py`

#### Responsibilities

- Scan one or more curriculum content roots.
- Discover guide directories and `Industries/*` subdirectories.
- Build `Guide` and `Chapter` records.
- Load manifest-driven graph metadata from `skill_tree.yaml`.

#### Current behavior

- Supports:
  - guide aliases
  - tracks
  - curated prerequisites
  - learning programs
- Canonicalizes guide IDs through alias mappings before graph assignment.
- Loads typed chapter metadata from the content schema layer rather than only from raw markdown.
- Falls back to directory-order prerequisite inference only when no manifest metadata is present.

#### Exposed helpers

- `load_skill_tree()`
- `load_guide_aliases()`
- `load_learning_programs()`
- `build_tree_layout()`
- `CurriculumScanner.get_track_metadata()`
- `CurriculumScanner.get_learning_programs()`
- `CurriculumScanner.get_guide_aliases()`
- `CurriculumScanner.canonicalize_guide_id()`

### CurriculumStore

**File:** `src/curriculum/store.py`

#### Responsibilities

- Persist guides, chapters, enrollment, chapter progress, and review items in SQLite.
- Compute guide, track, and stats views for the Learn UI.
- Apply SM-2 scheduling updates.
- Reconcile deprecated guide aliases into canonical records during sync.

#### Current schema

The store is now on schema version `4`.

Key tables:

- `guides`
- `chapters`
- `user_guide_enrollment`
- `user_chapter_progress`
- `review_items`

Chapter rows persist schema-aware metadata such as:

- `summary`
- `objectives`
- `checkpoints`
- `content_references`
- `content_format`
- `schema_version`

#### Notable behaviors

- progress updates accumulate reading time rather than replacing it
- guide completion ignores glossary chapters
- track and tree aggregation are batched, not computed with per-guide N+1 queries
- alias reconciliation migrates:
  - enrollments
  - chapter progress
  - review items
  - stale alias catalog rows

#### Important methods

- `sync_catalog()`
- `reconcile_guide_aliases()`
- `list_guides()`
- `get_guide()`
- `get_chapter()`
- `enroll()`
- `update_progress()`
- `get_due_reviews()`
- `grade_review()`
- `get_ready_guides()`
- `complete_guide_placement()`
- `list_tracks()`
- `get_tree_data()`
- `get_stats()`

### SM-2 Scheduling

**File:** `src/curriculum/spaced_repetition.py`

Standard SM-2 scheduling is used for quiz and teach-back review items.

Current properties:

- grade range `0-5`
- easiness-factor floor `1.3`
- reset on failing recall
- interval expansion on successful recall
- recently weak items can also be queried separately for retry-mode review sessions

### Question Generation and Grading

**File:** `src/curriculum/question_generator.py`

#### Responsibilities

- Generate chapter quiz questions.
- Grade quiz answers.
- Generate and grade teach-back prompts.
- Generate placement/test-out questions.

#### Current behavior

- quiz generation can also include pre-reading prompts in the same generation flow
- quiz items are persisted as review items
- pre-reading items are stored but excluded from SM-2 review behavior
- placement questions are ephemeral and never persisted as review items
- applied deliverables can be rubric-graded and fall back to heuristic grading when no LLM is
  configured
- grading strategy varies by Bloom level:
  - lower-level fallback logic
  - LLM grading for richer answers

### Personalization and Applied Assessments

**File:** `src/curriculum/personalization.py`

#### Responsibilities

- Score guide candidates against user profile context and curated learning programs.
- Build recommendation signals for `/api/curriculum/next`.
- Assemble a ranked daily workflow payload for `/api/curriculum/today`.
- Generate the applied-assessment pilot payload surfaced in Learn.

#### Current inputs

- role
- goals
- industries
- time budget
- guide metadata
- program metadata
- per-guide learning-performance signals:
  - weak-review counts and density
  - deliverable-grade averages
  - active revision backlog

#### Current outputs

- recommendation score
- explanation signals
- matched programs
- applied-assessment plan:
  - teach-back note
  - decision brief
  - scenario analysis
  - case memo
- ranking-sensitive performance signals surfaced in `/api/curriculum/next` when relevant
- reusable per-guide learning-signal summaries used by both route ranking and advisor context

#### Roadmap references

- `docs/curriculum-recommendation-pilot.md` defines the current ranking rationale and pilot
  rollout for personalized next-step guidance.
- `docs/curriculum-assessments.md` defines the broader applied-assessment expansion beyond the
  currently shipped pilot payload.

### Chapter Embeddings and Related Chapters

**File:** `src/curriculum/embeddings.py`

#### Responsibilities

- index chapter content into a Chroma-backed embedding collection
- find related chapters from other enrolled guides
- skip glossary chapters in sync

This is used by `/api/curriculum/chapters/{chapter_id}/related`.

### Web Routes

**File:** `src/web/routes/curriculum.py`

The web API currently exposes 25 curriculum routes.

#### Core catalog and graph

- `GET /api/curriculum/tracks`
- `GET /api/curriculum/tree`
- `GET /api/curriculum/guides`
- `GET /api/curriculum/guides/{guide_id}`
- `GET /api/curriculum/guides/{guide_id}/chapters/{chapter_id}`
- `POST /api/curriculum/guides/{guide_id}/enroll`
- `POST /api/curriculum/sync`

#### Progress and reviews

- `POST /api/curriculum/progress`
- `GET /api/curriculum/review/due`
- `GET /api/curriculum/review/retry`
- `POST /api/curriculum/review/{review_id}/grade`
- `GET /api/curriculum/stats`
- `GET /api/curriculum/today`

#### Quiz and deep-processing features

- `POST /api/curriculum/quiz/{chapter_id}/generate`
- `POST /api/curriculum/quiz/{chapter_id}/submit`
- `POST /api/curriculum/teachback/{chapter_id}/generate`
- `POST /api/curriculum/teachback/{review_id}/grade`
- `GET /api/curriculum/chapters/{chapter_id}/pre-reading`
- `GET /api/curriculum/chapters/{chapter_id}/related`
- `POST /api/curriculum/guides/{guide_id}/assessments/{assessment_type}/launch`
- `POST /api/curriculum/guides/{guide_id}/assessments/{assessment_type}/submit`

#### Recommendation and placement

- `GET /api/curriculum/ready`
- `GET /api/curriculum/next`
- `POST /api/curriculum/guides/{guide_id}/placement/generate`
- `POST /api/curriculum/guides/{guide_id}/placement/submit`

#### Current route behavior worth documenting

- guide aliases are resolved on guide/chapter/enrollment/placement routes
- `/tree` returns:
  - `tracks`
  - `programs`
  - `nodes`
  - `edges`
- `/guides` hides superseded alias guides unless user enrollment requires visibility
- guide payloads are decorated with:
  - `canonical_guide_id`
  - `learning_programs`
  - `applied_assessments` on guide detail
  - draft metadata for launched applied assessments
- `/next` returns:
  - `recommendation_type`
  - `signals`
  - `matched_programs`
  - `applied_assessments`
- `/next` ranking now blends:
  - profile/program fit
  - weak-review density
  - applied-deliverable grades
  - revision backlog for active deliverables
- `/today` returns:
  - `headline`
  - `summary`
  - `recommended_action`
  - ranked `tasks`
  - `focus_programs`
  - `reviews_due`
  - a retry-review task when recently weak recall exists
- `/today` focus-program ordering now blends:
  - active/recommended/available status
  - revision backlog aggregated across the path
  - weak-review pressure aggregated across the path
  - completion and ready-guide counts
- assessment launch creates:
  - a persisted Journal draft entry
  - a linked learning-goal entry with default milestones
- assessment submission:
  - grades the Journal draft against the assessment rubric
  - writes feedback into Journal metadata
  - leaves weak submissions `active` for revision
  - marks stronger submissions `submitted` and completes the linked goal
- sync runs alias reconciliation after catalog upsert

### Advisor curriculum context

**File:** `src/advisor/retrievers/supplementary.py`

`SupplementaryRetriever.get_curriculum_context()` reads the per-user `curriculum.db` from the user
data directory, joins it with Journal-backed assessment artifacts, and injects compact XML-like
context that includes:

- aggregate `learning_pressure` attributes:
  - due reviews
  - retry reviews
  - weak reviews
  - active revisions
  - submitted assessments
- per-guide attributes when present:
  - progress
  - track
  - weak review count
  - revision backlog count
  - average assessment grade
  - submitted assessment count

### Frontend

#### Pages

- `web/src/app/(dashboard)/home/page.tsx`
- `web/src/app/(dashboard)/learn/page.tsx`
- `web/src/app/(dashboard)/learn/[guideId]/page.tsx`
- `web/src/app/(dashboard)/learn/[guideId]/[chapterId]/page.tsx`
- `web/src/app/(dashboard)/learn/review/page.tsx`

#### Current UX surface

- Home:
  - `Today in Learn` card backed by `/api/curriculum/today`
  - learning metrics alongside the daily queue
  - top program paths now show revision / weak-item / assessment cues from the same backend signals
- Learn landing page:
  - `Today in Learn` primary task
  - supporting queue
  - program-path cards
  - program-path remediation badges driven by aggregated learning signals
  - library/grid/tree section below the workflow surfaces
- guide detail:
  - enrollment
  - chapter list
  - learning-program badges
  - applied-assessment pilot cards
  - create/open/revise draft actions for applied assessments
  - draft status and latest feedback summary for reviewed deliverables
  - placement/test-out
- Journal:
  - reads and updates persisted assessment drafts
  - submits assessment drafts for rubric feedback
  - shows the latest grading feedback block inline with the draft
- chapter reader:
  - renderer
  - pre-reading
  - completion
  - inline reflection textarea
  - teach-back
  - free-form quiz flow with grading feedback
  - related chapters
- review page:
  - due-item session flow
  - retry-mode session flow for recently weak items

#### CurriculumRenderer

**File:** `web/src/components/curriculum/CurriculumRenderer.tsx`

Current renderer behavior:

- ReactMarkdown + GFM
- resolves internal markdown chapter links into `/learn/...` routes
- supports typed visual blocks via fenced code block languages:
  - `diagram`
  - `process-flow`
  - `framework`
  - `comparison-table`
  - `chart`
  - `visual`
- falls back to legacy ASCII/data-table rendering when structured blocks are absent
- still supports chart overlays for parseable legacy blocks

#### Visual block rendering

**Files:** `web/src/components/curriculum/CurriculumVisualBlock.tsx`, `web/src/lib/curriculum-visuals.ts`

Typed visual blocks render as web-native UI rather than plain monospace markdown. This is now
the preferred path for diagrams in the learning content.

### MCP Tools

**File:** `src/coach_mcp/tools/curriculum.py`

Current MCP tools:

- `curriculum_list_guides`
- `curriculum_get_chapter`
- `curriculum_progress`
- `curriculum_due_reviews`
- `curriculum_recommend_next`
- `curriculum_skill_tree`

#### Important note

The MCP curriculum surface is simpler than the web API today. It exposes the core catalog,
chapter, progress, recommendation, and tree data, but it does not yet mirror the full
program-aware and applied-assessment-enriched web payloads.

### Configuration

**File:** `src/cli/config_models.py`

Current curriculum config keys:

- `enabled`
- `extra_content_dirs`
- `questions_per_chapter`
- `review_session_size`
- `cross_domain_questions`
- `interleaving_ratio`
- `teachback_enabled`
- `pre_reading_enabled`
- `pre_reading_count`
- `cross_guide_connections`
- `placement_enabled`
- `placement_pass_threshold`
- `placement_questions_per_chapter`
- `placement_max_questions`

## Test Expectations

The current automated coverage for curriculum behavior spans:

- scanner and manifest handling
- store behavior and alias reconciliation
- schema parsing, linting, migration, and audit
- personalization scoring and applied assessments
- web routes
- placement flow
- skill-tree responses
- review scheduling

Relevant suites include:

- `tests/curriculum/`
- `tests/web/test_curriculum_routes.py`
- `tests/coach_mcp/test_server.py`
- `web/e2e/tests/curriculum.spec.ts`

Key route-level checks now include:

- today queue auto-sync and retry-task coverage
- assessment launch, reopen, and submit flows
- retry review endpoint coverage
- next-step ranking against weak-review and revision-backlog signals

## Known Limitations

- the MCP curriculum tools lag the richer web personalization payloads
- legacy ASCII/chart parsing still exists as fallback and remains heuristic
- some corpus-level content improvements are planned and documented separately, but the platform
  already supports the newer authoring and rendering contract

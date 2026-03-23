# Curriculum

**Status:** Experimental

## Overview

Structured learning system that scans markdown guide directories, tracks per-user reading progress in SQLite, generates quiz questions at Bloom's taxonomy levels via LLM, and schedules spaced repetition reviews using the SM-2 algorithm. Implements the [curriculum functional spec](../functional/curriculum.md).

## Dependencies

**Depends on:** `db` (WAL connect, schema versioning), `llm` (question generation + grading), `memory` (FactSource.CURRICULUM), `journal` (goal creation), `advisor.rag` (curriculum context)
**Depended on by:** `web.routes.curriculum`, `coach_mcp.tools.curriculum`, `advisor.rag` (via get_curriculum_context)

---

## Components

### CurriculumScanner

**File:** `src/curriculum/scanner.py`
**Status:** Stable

#### Behavior
- Constructor: `__init__(content_dirs: list[Path])` — list of directories to scan.
- `scan() -> tuple[list[Guide], list[Chapter]]` — walks each dir, discovers guide dirs and Industry subdirs.
- Guide discovery: any directory containing `.md` files becomes a guide. `Industries/` subdirs get `industry-` prefix.
- Chapter ordering: sorted by filename (expecting `NN-name.md` convention).
- Category inference: keyword matching against dir name → `GuideCategory` enum. Industry dirs always → `INDUSTRY`.
- Difficulty inference: `_ADVANCED_KEYWORDS` → advanced, order ≤ 5 → introductory, else intermediate.
- Prerequisites: previous numbered guide inferred from `NN-` prefix ordering.
- Content analysis per chapter: word count, reading time (250 WPM), diagram detection (box-drawing U+2500-257F, ASCII art `+---+`), table detection (pipe + separator line), formula detection (LaTeX patterns, math symbols).
- Title extraction: first `# ` heading, fallback to filename stem.
- Content hash: SHA-256 prefix (16 chars) for change detection.

#### Inputs / Outputs

| Parameter | Type | Default |
|-----------|------|---------|
| `content_dirs` | `list[Path]` | required |

Returns `(guides: list[Guide], chapters: list[Chapter])` sorted by guide order.

---

### CurriculumStore

**File:** `src/curriculum/store.py`
**Status:** Stable

#### Behavior
- Constructor: `__init__(db_path: str | Path)` — creates SQLite DB with WAL mode.
- Schema version 2: tables `guides`, `chapters`, `user_guide_enrollment`, `user_chapter_progress`, `review_items` (v2 adds `item_type` column).
- `sync_catalog(guides, chapters)` — bulk upsert via `ON CONFLICT DO UPDATE`. Single transaction.
- `update_progress(...)` — upserts chapter progress, accumulates reading time (not replaces), auto-marks guide complete when all non-glossary chapters done.
- `grade_review(review_id, grade)` — applies SM-2 algorithm, updates `next_review`, `easiness_factor`, `interval_days`, `repetitions`.
- `get_stats(user_id)` → `LearningStats` with enrollment counts, completion counts, reading time, review stats, mastery by category, daily activity heatmap data, streak calculation.

#### Schema

| Table | Primary Key | Key Columns |
|-------|-------------|-------------|
| `guides` | `id TEXT` | title, category, difficulty, chapter_count, total_word_count, prerequisites (JSON) |
| `chapters` | `id TEXT` | guide_id (FK), title, filename, order, word_count, content_hash, is_glossary |
| `user_guide_enrollment` | `(user_id, guide_id)` | enrolled_at, completed_at, linked_goal_id |
| `user_chapter_progress` | `(user_id, chapter_id)` | guide_id, status, reading_time_seconds, scroll_position, started_at, completed_at |
| `review_items` | `id TEXT` | user_id, chapter_id, question, expected_answer, bloom_level, easiness_factor, interval_days, repetitions, next_review, content_hash, item_type (quiz/teachback/pre_reading) |

#### Invariants
- Reading time is additive — `update_progress` adds to existing, never replaces.
- Guide auto-completion only counts non-glossary chapters.
- `next_review` is always set (defaults to now for new items).
- Schema version checked on every connect via `ensure_schema_version`.

#### Error Handling
- Missing DB path: parent dirs created automatically.
- Duplicate upserts: `ON CONFLICT` clauses handle re-scans gracefully.

---

### SM-2 Algorithm

**File:** `src/curriculum/spaced_repetition.py`
**Status:** Stable

#### Behavior
`sm2_update(easiness_factor, interval_days, repetitions, grade) -> SM2Result`

- Grade clamped to 0-5.
- EF update: `new_ef = ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))`, floor 1.3.
- Grade < 3 (fail): reset to interval=1, repetitions=0.
- Grade ≥ 3 (pass): rep 1 → interval 1, rep 2 → interval 6, rep 3+ → `round(interval * ef)`.
- Interval floor: 1 day minimum.

---

### QuestionGenerator

**File:** `src/curriculum/question_generator.py`
**Status:** Experimental

#### Behavior
- Constructor: `__init__(llm_provider=None, cheap_llm_provider=None)` — dual LLM pattern.
- `generate_questions(content, chapter_title, guide_title, bloom_levels, count, ...)` → `list[ReviewItem]`
  - Truncates content to ~4000 words for LLM context.
  - Prompts LLM to output JSON array with question, expected_answer, bloom_level.
  - Parses response stripping markdown code fences.
  - Default bloom levels: 3 REMEMBER + 2 UNDERSTAND.
- `grade_answer(question, expected_answer, student_answer, bloom_level)` → `ReviewGradeResult`
  - REMEMBER: keyword matching only (no LLM).
  - UNDERSTAND/APPLY/ANALYZE: cheap LLM grading.
  - EVALUATE/CREATE: expensive LLM with rubric.
  - Keyword grading: set overlap ratio → grade 0-5.

#### Teach-back Generation & Grading
- `generate_teachback(content, chapter_title, guide_title, ...) -> ReviewItem | None` — cheap LLM identifies single most important concept, returns `ReviewItem` with `item_type=TEACHBACK`, `bloom_level=CREATE`.
- `grade_teachback(concept, expected_answer, student_answer, chapter_title, guide_title) -> ReviewGradeResult` — expensive LLM grades on accuracy/completeness/clarity (0-5 each), returns `ReviewGradeResult`.
- Prompt constants: `_TEACHBACK_CONCEPT_PROMPT`, `_TEACHBACK_GRADING_PROMPT`.

#### Pre-reading Question Generation
- `generate_questions()` gains `include_pre_reading: bool = False`, `pre_reading_count: int = 3` params.
- When enabled, `extra_instructions` populated with pre-reading prompt; items with `"pre_reading": true` in LLM response get `item_type=PRE_READING`, `expected_answer=""`, `next_review=None`.

#### Error Handling
- LLM unavailable: returns empty list for generation, keyword fallback for grading.
- JSON parse failure: returns empty list, logs warning.
- Grade result parse failure: returns grade=0 with error feedback.

---

### ChapterEmbeddingManager

**File:** `src/curriculum/embeddings.py`
**Status:** Experimental

#### Behavior
- Wraps `EmbeddingManager(collection_name="curriculum_chapters")`.
- `upsert_chapter(chapter_id, content, guide_id, chapter_title, content_hash)` — truncates to 2000 words, stores with metadata `{guide_id, title, content_hash}`.
- `find_related(chapter_content, current_guide_id, enrolled_guide_ids, n_results=3)` — queries 4×n_results, post-filters (exclude same guide, only enrolled guides, distance < 0.5), returns top n.
- `sync_from_chapters(chapters, content_reader) -> int` — bulk upsert, skips glossary chapters.
- `count() -> int`.

---

## Routes

**File:** `src/web/routes/curriculum.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/curriculum/guides` | GET | List guides with user progress, optional category filter |
| `/api/curriculum/guides/{guide_id}` | GET | Guide detail + chapters + per-chapter progress |
| `/api/curriculum/guides/{guide_id}/chapters/{chapter_id}` | GET | Chapter markdown + progress + prev/next |
| `/api/curriculum/guides/{guide_id}/enroll` | POST | Enroll user in guide |
| `/api/curriculum/progress` | POST | Update chapter reading state |
| `/api/curriculum/review/due` | GET | Due review items (SM-2 scheduled) |
| `/api/curriculum/review/{review_id}/grade` | POST | Grade review answer |
| `/api/curriculum/quiz/{chapter_id}/generate` | POST | Generate quiz (cached) |
| `/api/curriculum/quiz/{chapter_id}/submit` | POST | Submit quiz + receive grading |
| `/api/curriculum/stats` | GET | Learning stats |
| `/api/curriculum/sync` | POST | Re-scan content directories |
| `/api/curriculum/next` | GET | Recommended next chapter |
| `/api/curriculum/teachback/{chapter_id}/generate` | POST | Generate teach-back prompt for completed chapter |
| `/api/curriculum/teachback/{review_id}/grade` | POST | Grade teach-back response |
| `/api/curriculum/chapters/{chapter_id}/pre-reading` | GET | Get/generate pre-reading questions |
| `/api/curriculum/chapters/{chapter_id}/related` | GET | Find related chapters from other guides |

Content resolution: `_content_dirs()` resolves repo-relative `content/curriculum/` + any `config.curriculum.extra_content_dirs`. `_chapter_content_path()` handles both regular and industry guide ID formats.

Auto-sync: `list_guides` triggers catalog sync on first call (empty DB).

### enroll_guide() — auto-goal creation

On `POST /guides/{guide_id}/enroll`, after `store.enroll()`:
- If `create_goal=True` (default): creates a learning goal via `JournalStorage.create()` with `entry_type="goal"`, title `Learn: {guide_title}`, tags `["learning", "curriculum"]`.
- Adds milestones via `GoalTracker.add_milestone()` for each non-glossary chapter.
- Calls `store.enroll(..., linked_goal_id=str(goal_path))` to link back.
- Entire goal block wrapped in try/except — enrollment succeeds regardless.

### update_progress() — reflection + memory

On chapter completion (`status == COMPLETED`):
- **Reflection prompt**: `_generate_reflection_prompt()` returns a context-aware prompt string. Guide-complete prompt differs from chapter-complete prompt. Returned in response as `reflection_prompt`.
- **Memory extraction**: reads chapter content (truncated to 3000 chars), calls `MemoryPipeline.process_document()` with `source_type: "curriculum"`. Gated behind `config.memory.enabled`. Returns `memory_facts_extracted` count in response.
- Both are catch-all guarded — progress update never fails due to these.

---

## MCP Tools

**File:** `src/coach_mcp/tools/curriculum.py`

5 tools: `curriculum_list_guides`, `curriculum_get_chapter`, `curriculum_progress`, `curriculum_due_reviews`, `curriculum_recommend_next`. Follow the standard `TOOLS = [(name, schema, handler)]` pattern.

---

## Configuration

**File:** `src/cli/config_models.py` → `CurriculumConfig`

| Key | Default | Description |
|-----|---------|-------------|
| `curriculum.enabled` | `true` | Feature toggle |
| `curriculum.extra_content_dirs` | `[]` | Additional markdown guide directories |
| `curriculum.questions_per_chapter` | `5` | Questions generated per chapter |
| `curriculum.review_session_size` | `20` | Max items per review session |
| `curriculum.cross_domain_questions` | `true` | Enable cross-domain synthesis questions |
| `curriculum.interleaving_ratio` | `0.3` | Fraction of review items from non-current guide |
| `curriculum.teachback_enabled` | `true` | Enable teach-back / Feynman prompts |
| `curriculum.pre_reading_enabled` | `true` | Enable pre-reading priming questions |
| `curriculum.pre_reading_count` | `3` | Number of pre-reading questions per chapter |
| `curriculum.cross_guide_connections` | `true` | Enable cross-guide chapter connections |

---

## Frontend

### Pages
- `/learn` — Dashboard: stats row, continue reading card, reviews due card, guide grid with filters/search/sort.
- `/learn/[guideId]` — Guide detail: enrollment, chapter list with status icons, progress ring.
- `/learn/[guideId]/[chapterId]` — Chapter reader: sticky header, `CurriculumRenderer`, reading time tracker (30s sync), mark complete, start quiz, prev/next.
- `/learn/review` — Review session: flashcard flow, self-grade buttons (0-5), progress bar, session summary.

### Key Components (`web/src/components/curriculum/`)
- `CurriculumRenderer.tsx` — ReactMarkdown + remarkGfm. Code block override detects ASCII diagrams (box-drawing chars, `+---+`, tree `├──`, arrows) and data tables (aligned columns + separators). Diagrams get monospace 13px, `bg-slate-50`, rounded border. Tables get alternating row backgrounds. Both `DiagramBlock` and `TableBlock` parse their text with `parseChartData()` and show a chart toggle button when data is extractable.
- `ChartOverlay.tsx` — Recharts wrapper accepting `ParsedChartData`. Renders `<BarChart>`, `<LineChart>`, or `<ScatterChart>` in a `<ResponsiveContainer>` (256px height). Uses CSS variables `--chart-1` through `--chart-5` for series colors.
- `chart-parser.ts` (`web/src/lib/`) — Heuristic parser: detects tables with numeric columns (≥70% numeric, ≥3 data rows) → bar/line chart, and axis-labeled diagrams → line/scatter chart. Returns `ParsedChartData | null`.
- `GuideCard.tsx` — Grid card with title, category/difficulty badges, progress bar.
- `ChapterList.tsx` — Chapter list with completion status icons.
- `ReviewCard.tsx` — Question + text input + submit/self-grade.
- `ProgressRing.tsx` — SVG circular progress indicator.
- `DifficultyBadge.tsx` — Colored badge (green/yellow/red).

---

## Advisor Integration

### RAGRetriever.get_curriculum_context()

**File:** `src/advisor/rag.py`

New method on `RAGRetriever` that lazily imports `CurriculumStore`, constructs it from `Path(self.intel_db_path).parent / "curriculum.db"`, and builds a `<curriculum_progress>` XML block with active enrollments (max 5), completion counts, and current chapter titles.

- Added `curriculum_context: str = ""` field to `AskContext` dataclass.
- `build_context_for_ask()` calls `get_curriculum_context(query)` when `inject_curriculum` config flag is true (default true).
- Prompt templates (`GENERAL_ASK_EXTENDED`, `GENERAL_ASK_EXTENDED_WITH_RESEARCH`, `GENERAL_ASK_XML`, `GENERAL_ASK_XML_WITH_RESEARCH`) include `{curriculum_context}` slot.
- `_build_user_prompt()` accepts and passes `curriculum_context` kwarg.
- `engine.py` `_build_advice_prompt()` passes `curriculum_context=ctx.curriculum_context`.
- Returns empty string on any error (catch-all, debug log).

---

## Test Expectations

- Scanner: discovers guides/chapters from temp dir structure, handles Industries/, infers categories/difficulty, detects diagrams, handles missing dirs.
- Store: CRUD for catalog, enrollment, progress tracking, reading time accumulation, guide auto-completion, review item lifecycle, SM-2 scheduling, stats aggregation.
- SM-2: perfect/fail/boundary grades, EF floor 1.3, interval progression, reset on fail.
- Tests: `tests/curriculum/` — 34 tests covering scanner, store, and SM-2.

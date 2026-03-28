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
- Schema version 3: tables `guides`, `chapters`, `user_guide_enrollment`, `user_chapter_progress`, `review_items` (v2 adds `item_type` column, v3 adds `track` column to guides).
- `sync_catalog(guides, chapters)` — bulk upsert via `ON CONFLICT DO UPDATE`. Single transaction.
- `update_progress(...)` — upserts chapter progress, accumulates reading time (not replaces), auto-marks guide complete when all non-glossary chapters done.
- `grade_review(review_id, grade)` — applies SM-2 algorithm, updates `next_review`, `easiness_factor`, `interval_days`, `repetitions`.
- `get_stats(user_id)` → `LearningStats` with enrollment counts, completion counts, reading time, review stats, mastery by category, daily activity heatmap data, streak calculation.

#### Schema

| Table | Primary Key | Key Columns |
|-------|-------------|-------------|
| `guides` | `id TEXT` | title, category, difficulty, chapter_count, total_word_count, prerequisites (JSON), track |
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

### Skill Tree Manifest

**File:** `content/curriculum/skill_tree.yaml`

#### Behavior
- Hand-authored YAML mapping guides to tracks with curated prerequisites.
- `load_skill_tree(content_dir: Path) -> tuple[dict, dict, dict] | None` — returns `(guide_prereqs, guide_tracks, track_metadata)` or `None` on missing/invalid file.
- Scanner loads manifest in `__init__`, stores as `self._skill_tree`.
- `_build_guide()` uses manifest prereqs/track when available; falls back to auto-inferred linear chain.
- `get_track_metadata() -> dict[str, dict]` exposes track titles/descriptions/colors.

#### Track model
`Track`: `id, title, description, color, guide_count, guides_completed, average_mastery, completion_pct, guide_ids`.

#### Mastery formula
```
mastery_score = completion_pct * 0.4 + review_score * 0.6
  completion_pct = chapters_completed / chapters_total * 100
  review_score = clamp((avg_easiness_factor - 1.3) / 1.2 * 100, 0, 100)
  If no reviews: mastery = completion_pct * 0.4
  If no progress: mastery = 0
```

#### Schema v3 migration
- `ALTER TABLE guides ADD COLUMN track TEXT NOT NULL DEFAULT ''`
- `upsert_guide()` and `sync_catalog()` include `track` in column lists.
- `list_guides()` and `get_guide()` compute `mastery_score` per guide.
- `list_tracks(user_id, track_metadata)` groups guides by track, returns aggregate stats. Uses `_batch_guide_data()` to pre-fetch chapter counts, completion counts, enrollments, and avg easiness factors in 4 bulk queries instead of per-guide sub-queries.
- `get_tree_data(user_id)` returns per-guide skill tree data. Also uses `_batch_guide_data()` for O(1) lookups per guide.
- `get_stats()` adds `mastery_by_track` computation. Consolidates enrollment, progress, and review stats into batched queries (3 instead of 7). Uses `_batch_guide_data()` for track mastery instead of per-guide sub-queries. Inlines due review count to avoid separate connection.

---

### Curriculum Content QA

**Files:** `src/curriculum/content_schema.py`, `src/cli/commands/curriculum.py`

#### Responsibilities
- Parse legacy `.md` and schema-first `.mdx` curriculum files into a normalized `CurriculumDocument`.
- Prefer `.mdx` over `.md` when both exist for the same chapter stem in a directory.
- Power `coach curriculum lint`, `coach curriculum migrate`, and `coach curriculum audit`.

#### Lint coverage
- Frontmatter requirements: `title`, `summary`, `objectives`, `checkpoints`.
- Content references: validates `curriculum:` references, `/learn/<guide>/<chapter>` paths, and relative `.md` / `.mdx` links. External URLs are ignored.
- Thin chapter detection: warning when a non-glossary chapter body falls below the configured QA threshold (`500` words).
- Path coherence: detects reused chapter order numbers and gaps in numbered chapter sequences within a guide.
- Duplicate concepts: warns when a guide repeats the same normalized chapter title.
- Manifest graph validation against `skill_tree.yaml`: unknown alias targets, missing guides in tracks, missing prerequisites, duplicate track assignments, missing track assignments for content guides, unknown program references, and prerequisite cycles.

#### Reporting model
- `CurriculumLintIssue`: `{code, path, message, severity}` where severity is `error` or `warning`.
- `CurriculumLintReport`: `{documents_scanned, issues}`.
- `coach curriculum lint --format text` prints a summary with error/warning counts plus one line per issue.
- `coach curriculum lint --format json` emits the raw report payload for CI or scripted review.

#### Audit coverage
- `audit_curriculum_root()` scores thin guides for rewrite priority using chapter count, total word count, downstream dependents, and learning-program membership.
- Industry guides under `content/curriculum/Industries/` are surfaced as applied modules / capstones rather than ranked as normal thin-guide rewrites.

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
| `/api/curriculum/tracks` | GET | List tracks with per-track guide counts and mastery |
| `/api/curriculum/tree` | GET | Full DAG: tracks, nodes with layout positions, edges |

### GET /api/curriculum/tree

Returns `SkillTreeResponse` with full DAG for frontend visualization.

**Response schema:**
```json
{
  "tracks": { "<track_id>": { "title": "...", "description": "...", "color": "#..." } },
  "nodes": [SkillTreeNode],
  "edges": [{ "source": "guide_id", "target": "guide_id" }]
}
```

**SkillTreeNode fields:** `id, title, track, category, difficulty, chapter_count, prerequisites, is_entry_point, status (not_started|enrolled|in_progress|completed), enrolled, progress_pct, mastery_score, chapters_completed, chapters_total, position: {x, y, depth}`.

**Layout algorithm (build_tree_layout):**
1. Build adjacency list from guide_prereqs (prereq → dependents).
2. Entry points = guides with no prerequisites within the DAG.
3. BFS from all entry points computing `depth` = longest path from any root.
4. Within each depth tier, assign `x` = index (left-to-right).
5. `y` = depth. Frontend uses these as relative hints.

**Edge derivation:** For each guide with prerequisites, emit `{source: prereq_id, target: guide_id}`.

**Status derivation:** not_started (no enrollment) → enrolled (enrolled, 0 chapters done) → in_progress (partial) → completed (all non-glossary done).

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

6 tools: `curriculum_list_guides`, `curriculum_get_chapter`, `curriculum_progress`, `curriculum_due_reviews`, `curriculum_recommend_next`, `curriculum_skill_tree`. Follow the standard `TOOLS = [(name, schema, handler)]` pattern.

### curriculum_skill_tree

Returns skill tree DAG data: nodes with progress/mastery/status + edges from prerequisites. Calls `store.get_tree_data("")` and builds edges from each guide's prerequisites list.

### curriculum_recommend_next (updated)

DAG-aware priority: (1) continue last-read, (2) next enrolled incomplete, (3) first ready-to-start guide from `store.get_ready_guides("")`, (4) first entry-point guide (no prereqs, not enrolled), (5) fallback.

---

### CurriculumStore — new methods

#### `get_ready_guides(user_id: str) -> list[dict]`

Returns guides where ALL prerequisites have `completed_at IS NOT NULL` on enrollment, AND the guide itself is NOT enrolled. Entry-point guides (no prereqs) are excluded. Each result dict has `id, title, track, category, difficulty, chapter_count, prerequisites`.

Uses a single query joining guides → user_guide_enrollment for prereqs, filtering by prereq completion.

#### `complete_guide_placement(user_id: str, guide_id: str) -> dict`

Single transaction: (1) auto-enroll via `ON CONFLICT DO NOTHING`, (2) mark all non-glossary chapters as completed, (3) mark guide enrollment as completed. Returns `{guide_id, chapters_marked, completed_at}`.

---

### QuestionGenerator — new method

#### `generate_placement_questions(content, chapter_title, guide_title, count=2) -> list[dict]`

Uses `_PLACEMENT_PROMPT` targeting APPLY/ANALYZE/EVALUATE Bloom's levels. Returns raw dicts `{question, expected_answer, bloom_level, chapter_id}` — NOT ReviewItems (ephemeral, never stored).

---

### Placement Routes

#### `POST /api/curriculum/guides/{guide_id}/placement/generate`

Rejects if placement disabled or guide already completed. Loops non-glossary chapters, calls `generate_placement_questions(count=2)` per chapter, caps at `placement_max_questions`. Caches full questions (with answers) server-side in `_placement_cache[(user_id, guide_id)]` with 1hr TTL. Returns questions WITHOUT `expected_answer`.

#### `POST /api/curriculum/guides/{guide_id}/placement/submit`

Body: `QuizSubmission` (dict of question_id → answer). Looks up cached questions (410 if expired). Grades each answer via `gen.grade_answer()`. If avg grade >= threshold: calls `store.complete_guide_placement()`, clears cache. Returns `{results, average_grade, passed, threshold, completion}`.

#### `GET /api/curriculum/ready`

Returns `store.get_ready_guides(user_id)`.

#### `GET /api/curriculum/next` (updated)

Priority: (1) continue last-read, (2) next enrolled incomplete, (3) first from `get_ready_guides()` with `action: "enroll"`, (4) first entry-point with `action: "enroll"`, (5) fallback.

### Placement cache design

Module-level dict: `_placement_cache: dict[tuple[str, str], dict]` keyed by `(user_id, guide_id)`. Value: `{questions: list[dict], created_at: datetime}`. TTL: 1 hour. Checked on submit; stale entries return 410.

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
| `curriculum.placement_enabled` | `true` | Enable placement bypass (test-out) |
| `curriculum.placement_pass_threshold` | `3.5` | Min avg grade to pass placement |
| `curriculum.placement_questions_per_chapter` | `2` | Placement questions per non-glossary chapter |
| `curriculum.placement_max_questions` | `15` | Hard cap on total placement questions |

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

### Skill Tree View (`web/src/components/curriculum/`)

#### SkillTree.tsx
Main tree view component. Fetches `GET /api/curriculum/tree` via `apiFetch`. State: `selectedTracks: Set<string>` (empty = all), loading, error.

Data flow: fetch → filter nodes/edges by selected tracks → group nodes by `position.depth` → render depth rows → measure node DOM positions via refs → draw SVG edges.

Track filter bar: `Badge` toggles per track, colored with `track.color`. "All" shown when no tracks selected. Same pattern as category badges on grid view.

Container: `overflow-x-auto` for horizontal scroll on narrow screens. `position: relative` to layer SVG behind nodes.

#### SkillTreeNode.tsx
Compact card (~160px wide). Props: `node: SkillTreeNode`, `trackColor: string`.

Visual: 4px left border in track color. Status-based styling:
- `not_started`: `bg-muted text-muted-foreground`
- `enrolled`: `bg-background ring-1 ring-blue-200 border-blue-300`
- `in_progress`: `bg-background ring-1 ring-amber-200 border-amber-300`
- `completed`: `bg-green-50 border-green-300 dark:bg-green-950/30`

Shows: truncated title, mastery score (if > 0), thin progress bar (if enrolled), entry-point diamond icon. Click → `router.push(/learn/${node.id})`.

Ref forwarded for edge measurement.

#### SkillTreeEdges.tsx
SVG overlay. Props: `edges`, `nodePositions: Map<string, DOMRect>`, `containerRect: DOMRect`, `trackColor: (nodeId) => string`.

Per edge: cubic bezier from source center-bottom to target center-top.
`M sx,sy C sx,mid tx,mid tx,ty` where mid = (sy+ty)/2.
Stroke = source track color at 60% opacity, 1.5px width.

Uses ResizeObserver on container for re-measurement.

---

## Test Expectations

- Scanner: discovers guides/chapters from temp dir structure, handles Industries/, infers categories/difficulty, detects diagrams, handles missing dirs.
- Store: CRUD for catalog, enrollment, progress tracking, reading time accumulation, guide auto-completion, review item lifecycle, SM-2 scheduling, stats aggregation, get_ready_guides, complete_guide_placement.
- SM-2: perfect/fail/boundary grades, EF floor 1.3, interval progression, reset on fail.
- Routes: `/ready` returns ready guides, `/next` DAG-aware suggestions, placement generate/submit flow, placement cache expiry (410).
- Tests: `tests/curriculum/` — 47+ tests covering scanner (incl. skill tree), store (incl. mastery, tracks), and SM-2. `tests/web/test_curriculum_routes.py` covers route-level behavior.

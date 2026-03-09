# Extraction Receipt

## Overview

The extraction-receipt feature adds a user-visible, per-entry summary of what the journal post-create pipeline learned from a newly saved entry. It sits between the existing journal/memory/thread systems and the web journal UI, persisting a receipt artifact per journal entry so the web app can render transparent, non-blocking extraction output even when processing completes asynchronously.

## Dependencies

**Depends on:** `journal` (entry create + thread detection), `memory` (fact extraction), `llm` (theme / goal-candidate extraction), `web` (journal routes + models + UI), `db` (WAL SQLite)
**Depended on by:** `web journal workspace`, `recurring-thread-inbox`, `dossier-escalation-engine`

---

## Components

### ExtractionReceiptStore

**File:** `src/journal/extraction_receipts.py`
**Status:** Experimental

#### Behavior

Per-user SQLite store for extraction receipts. The store is path-scoped so web mode uses `~/coach/users/{safe_user_id}/receipts.db`. Receipts are keyed by journal entry path and are overwriteable when an entry is reprocessed.

Uses WAL mode on every connection. Receipt payload is stored mostly as JSON because reads are entry-scoped and the primary UI pattern is `get by entry` rather than cross-receipt analytics.

Suggested schema:

```sql
CREATE TABLE extraction_receipts (
    receipt_id TEXT PRIMARY KEY,
    entry_path TEXT NOT NULL UNIQUE,
    entry_title TEXT NOT NULL,
    status TEXT NOT NULL,
    thread_id TEXT,
    thread_label TEXT,
    thread_match_type TEXT,
    payload_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_extraction_receipts_entry_path ON extraction_receipts(entry_path);
CREATE INDEX idx_extraction_receipts_updated_at ON extraction_receipts(updated_at);
```

`payload_json` holds the receipt body:

```json
{
  "themes": [{"label": "", "confidence": 0.0, "snippet": ""}],
  "memory_facts": [{"fact_id": "", "text": "", "category": "", "confidence": 0.0}],
  "goal_candidates": [{"title": "", "confidence": 0.0, "reason": ""}],
  "next_steps": [{"kind": "view_thread", "label": "View thread", "enabled": true, "target": "..."}]
}
```

#### Inputs / Outputs

```python
def upsert(self, receipt: dict) -> str
def get_by_entry(self, entry_path: str) -> dict | None
def delete_by_entry(self, entry_path: str) -> bool
def list_recent(self, limit: int = 20) -> list[dict]
```

#### Invariants

- At most one active receipt exists per `entry_path`.
- `status` is one of `pending`, `complete`, `partial`, `failed`.
- Receipt storage is per-user; no receipt data is stored in shared `intel.db`.
- Missing optional sections are represented as empty arrays, not omitted keys, once a receipt has been materialized.

#### Error Handling

- SQLite failures propagate to callers creating or reading receipts.
- JSON decode failure on read returns `None` only for the malformed receipt row after logging a warning; it must not crash entry reads.

#### Configuration

| Key | Default | Source |
|---|---|---|
| Receipt DB path | `~/coach/users/{safe_id}/receipts.db` | `get_user_paths()` extension |
| Recent list limit | `20` | hardcoded default |

---

### ReceiptBuilder

**File:** `src/journal/extraction_receipts.py`
**Status:** Experimental

#### Behavior

Builds a receipt artifact from the existing post-create pipeline outputs plus one new summarization step. The builder is invoked after journal save and after any reprocessing flow.

Inputs include:

- journal entry metadata and body excerpt
- memory pipeline results from `MemoryPipeline.process_journal_entry`
- thread detection result from `ThreadDetector.detect`
- optional theme / goal-candidate extraction from a cheap LLM or heuristic fallback

Suggested build order:

1. Seed receipt with `status="pending"` immediately after entry create.
2. Capture memory facts and thread match as existing background tasks complete.
3. Run `ThemeGoalExtractor.extract(...)` using title, tags, first N chars of body, and extracted memory facts.
4. Derive `next_steps` from available output:
   - thread exists → `view_thread`
   - goal candidates above threshold → `make_goal`
   - strategic topic above threshold → `run_research`, `start_dossier`
5. Set final status:
   - `complete` when all enabled steps succeed
   - `partial` when at least one signal is available but a step fails
   - `failed` when no signal is available and the build fails

#### Inputs / Outputs

```python
def seed_pending(self, entry_path: str, entry_title: str) -> str
def finalize(
    self,
    *,
    entry: dict,
    thread_match: dict | None,
    memory_facts: list[dict],
    theme_candidates: list[dict],
    goal_candidates: list[dict],
    warnings: list[str] | None = None,
) -> dict
```

`ThemeGoalExtractor` output shape:

```json
{
  "themes": [{"label": "career uncertainty", "confidence": 0.81, "snippet": "..."}],
  "goal_candidates": [{"title": "Clarify PM career direction", "confidence": 0.77, "reason": "Repeated planning language"}]
}
```

#### Invariants

- Receipt generation never blocks journal save.
- Low-confidence themes or goal candidates never directly create downstream artifacts.
- The receipt always reflects the latest available processing outcome for the entry.

#### Error Handling

- Theme/goal extraction failure logs and yields `[]`; receipt can still be `partial`.
- Missing thread or memory output is not itself an error condition.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `theme_goal_min_confidence` | `0.7` | new config under `journal.receipts` |
| `max_themes` | `3` | new config under `journal.receipts` |
| `max_goal_candidates` | `2` | new config under `journal.receipts` |
| LLM provider | cheap provider | `llm.create_cheap_provider()` |

#### Caveats

- Theme and goal-candidate extraction is a new capability; it does not exist in the current journal stack.
- Receipt quality depends on the completion of best-effort background tasks and may legitimately remain `partial`.

---

### Web API + UI

**Files:** `src/web/routes/journal.py`, `src/web/models.py`, `web/src/components/journal/ExtractionReceiptCard.tsx`, `web/src/app/(dashboard)/journal/*`
**Status:** Experimental

#### Behavior

Adds receipt-aware journal flows:

- `POST /api/journal` and `POST /api/journal/quick` seed a pending receipt after file creation.
- `GET /api/journal/{filepath}/receipt` returns the materialized receipt or a `pending` envelope.
- Entry detail and post-create UI render `ExtractionReceiptCard` inline using shared `Card`, `Badge`, `Button`, and lightweight chip primitives from the design system.

Suggested response model:

```json
{
  "status": "pending|complete|partial|failed",
  "receipt": { ... } | null
}
```

The frontend should poll briefly or revalidate on focus after entry create rather than blocking on synchronous processing.

#### Inputs / Outputs

| Endpoint | Method | Response |
|---|---|---|
| `/api/journal/{filepath}/receipt` | GET | `ExtractionReceiptEnvelope` |

#### Invariants

- Receipt UI is secondary to entry capture speed.
- The UI must visually distinguish generated or inferred content from user-authored journal text.
- Empty or low-confidence sections render with lower emphasis per UX guidelines.

#### Error Handling

- Missing receipt row → `{"status":"pending","receipt":null}` if processing is in-flight, otherwise 404 only when the entry itself is unknown.
- Frontend fetch failures show an inline retry affordance; they must not hide the saved entry.

---

## Cross-Cutting Concerns

### Path model

- `get_user_paths()` gains `receipts_db`.
- Receipt lifecycle is tied to journal entry lifecycle; deleting an entry should delete its receipt.

### UX foundation alignment

- The receipt surface follows the design-system guidance for calm, low-noise cards and the UX rule that AI output should be inspectable and visually distinct from confirmed user data.

## Test Expectations

- `ExtractionReceiptStore`: upsert/get/delete happy path, per-entry uniqueness, malformed JSON handling.
- `ReceiptBuilder`: complete vs partial vs failed state transitions, low-confidence gating, next-step derivation.
- Journal route tests: create/quick create seed pending receipts; receipt fetch returns pending then populated payload.
- Delete path tests: deleting an entry removes the corresponding receipt.
- Frontend tests: pending, partial, complete, and failed card states; retry and empty-section rendering.
- Mock: cheap LLM for theme/goal extraction, memory pipeline, thread detector, filesystem, and SQLite temp paths.

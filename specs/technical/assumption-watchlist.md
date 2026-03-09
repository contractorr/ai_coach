# Assumption Watchlist

## Overview

Assumption Watchlist adds a structured, user-scoped layer for capturing assumptions, matching them against external signals, and surfacing confirmations or invalidations over time. It sits above journal, dossiers, action plans, and the intelligence system, and bridges private planning context with public-world evidence.

## Dependencies

**Depends on:** `journal`, `action-plans`, `research-dossiers`, `intelligence`, `memory`, `web`, `db`, `llm` (cheap extraction and evidence classification)
**Depended on by:** `since-you-were-away-why-now`, future strategic dashboard or planning flows

---

## Components

### AssumptionStore

**File:** `src/advisor/assumptions.py`
**Status:** Experimental

#### Behavior

Per-user SQLite store for assumptions and their latest evidence state.

Suggested path:

- `~/coach/users/{safe_id}/assumptions.db`

Suggested schema:

```sql
CREATE TABLE assumptions (
    id TEXT PRIMARY KEY,
    statement TEXT NOT NULL,
    status TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    extraction_confidence REAL,
    linked_goal_path TEXT,
    linked_dossier_id TEXT,
    linked_entity_json TEXT NOT NULL DEFAULT '[]',
    latest_evidence_summary TEXT NOT NULL DEFAULT '',
    last_evaluated_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE assumption_evidence (
    id TEXT PRIMARY KEY,
    assumption_id TEXT NOT NULL,
    evidence_kind TEXT NOT NULL,
    evidence_state TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    excerpt TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (assumption_id) REFERENCES assumptions(id)
);

CREATE INDEX idx_assumptions_status ON assumptions(status, updated_at DESC);
CREATE INDEX idx_assumption_evidence_assumption ON assumption_evidence(assumption_id, created_at DESC);
```

Suggested `status` values:

- `suggested`
- `active`
- `confirmed`
- `invalidated`
- `resolved`
- `archived`

#### Inputs / Outputs

```python
def create(self, assumption: dict) -> str
def list_active(self, limit: int = 50) -> list[dict]
def get(self, assumption_id: str) -> dict | None
def update_status(self, assumption_id: str, status: str) -> dict | None
def append_evidence(self, assumption_id: str, evidence: dict) -> str
```

#### Invariants

- Assumptions are per-user and never stored in shared `intel.db`.
- `suggested` assumptions do not participate in active monitoring until promoted.
- Evidence rows are append-only; status changes do not delete history.

#### Error Handling

- Unknown `assumption_id` returns `None` or caller-translated 404.
- SQLite failures propagate.

---

### AssumptionExtractor

**File:** `src/advisor/assumptions.py`
**Status:** Experimental

#### Behavior

Extracts candidate assumptions from journals, action plans, and dossier content. V1 should remain narrow and favor precision over recall.

Suggested extraction sources:

- journal entries tagged or classified as planning / reflection
- recommendation action items and review notes
- dossier definitions and updates where assumptions are already present or implied

Output shape:

```json
{
  "statement": "Series A environment will stay favorable this year",
  "confidence": 0.79,
  "source_type": "journal",
  "source_id": "journal/2026-03-08.md",
  "linked_entities": ["venture funding"],
  "linked_dossier_id": null
}
```

Candidates above threshold are stored as `suggested`, not `active`, unless the source already declares an explicit assumption field such as a dossier definition.

#### Inputs / Outputs

```python
def extract_from_journal(self, entry: dict) -> list[dict]
def extract_from_action_item(self, recommendation: dict) -> list[dict]
def extract_from_dossier(self, dossier: dict) -> list[dict]
```

#### Invariants

- Extraction is conservative; speculative or vague text should be skipped.
- Existing explicit dossier assumptions may bypass the `suggested` state and enter directly as `active`.

#### Error Handling

- LLM extraction failure yields `[]`, not an exception.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `assumptions.extract_enabled` | `False` | new config |
| `assumptions.min_confidence` | `0.75` | new config |
| `assumptions.max_candidates_per_source` | `3` | new config |

---

### AssumptionSignalMatcher

**File:** `src/advisor/assumptions.py`
**Status:** Experimental

#### Behavior

Matches active assumptions against external signals from:

- generic intel search
- company movement events
- hiring signals
- regulatory alerts
- dossier updates

The matcher computes whether a signal is confirming, invalidating, or merely relevant context.

Suggested evidence decision inputs:

```text
match_score =
  0.40 * statement_keyword_overlap
  0.25 * linked_entity_match
  0.20 * dossier_or_goal_context_match
  0.15 * source_authority
```

Evidence states:

- `confirming`
- `invalidating`
- `informational`

#### Inputs / Outputs

```python
def evaluate(self, assumption: dict, candidate_signals: list[dict]) -> list[dict]
def run_active(self, limit: int = 100) -> list[dict]
```

Each evidence result includes:

- `evidence_kind`
- `evidence_state`
- `source_ref`
- `excerpt`
- `confidence`

#### Invariants

- Weak matches should remain `informational` rather than flipping status.
- Multiple evidence rows may coexist for the same assumption over time.

#### Error Handling

- Missing company / regulatory / hiring pipelines degrades the matcher to generic intel and dossier signals.
- LLM-based evidence classification failure falls back to keyword/entity matching only.

#### Caveats

- Quality depends heavily on the availability of specialized signal pipelines, which are new capabilities.

---

### MemoryAdapter + Web Routes

**Files:** `src/advisor/assumptions.py`, `src/memory/extractor.py`, `src/web/routes/assumptions.py`, `src/web/models.py`
**Status:** Experimental

#### Behavior

When an assumption is resolved or repeatedly confirmed / invalidated, the feature can emit a durable memory fact. This requires extending `FactSource` with a new value:

- `ASSUMPTION`

`MemoryAdapter` should write only durable outcomes such as:

- `User tends to plan around regulatory risk in fintech`
- `Assumption about employer hiring growth was invalidated in Q3 2026`

Suggested routes:

- `GET /api/assumptions`
- `POST /api/assumptions`
- `PATCH /api/assumptions/{id}`
- `POST /api/assumptions/{id}/activate`
- `POST /api/assumptions/{id}/resolve`
- `POST /api/assumptions/{id}/archive`

#### Invariants

- User-visible assumption state changes and memory writes are separate operations; memory failure must not block state updates.
- Manual assumptions created through the API default to `active` unless otherwise specified.

#### Error Handling

- Unknown assumption id → 404.
- Memory write failure logs and continues without failing the assumption route.

---

## Cross-Cutting Concerns

### Lifecycle model

- `suggested` → user review → `active` → evidence accumulates → `confirmed` / `invalidated` → `resolved` or `archived`

### Relation to dossier assumptions

- Dossier-defined assumptions remain source-of-truth inside dossier metadata; the watchlist mirrors them into active monitored assumptions rather than duplicating dossier authoring.

## Test Expectations

- Store tests: create/list/get/status transitions, evidence append, history preservation.
- Extractor tests: journal/action-item/dossier extraction precision, low-confidence filtering, dossier-explicit assumption import.
- Matcher tests: confirming vs invalidating vs informational evidence, weak-match suppression, degraded behavior when specialized pipelines are unavailable.
- Memory adapter tests: resolved assumptions emit durable facts, memory failure does not break route behavior.
- Route tests: CRUD, activate/resolve/archive flows, manual-entry defaults.
- Mock: cheap LLM extraction/classification, intel search, company/hiring/regulatory signal stores, temp SQLite DBs.

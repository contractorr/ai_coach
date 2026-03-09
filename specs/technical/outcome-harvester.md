# Outcome Harvester

## Overview

Outcome Harvester closes the feedback loop between surfaced advice and later user behavior. It scans later journal entries, goal check-ins, action-item updates, and explicit recommendation feedback, infers a user-visible outcome state, and feeds that state back into recommendation ranking without treating silence as failure.

## Dependencies

**Depends on:** `advisor/recommendation_storage`, `action-plans`, `journal`, `goals`, `memory`, `web` (users DB + routes), `db`, `llm` (cheap inference only when needed)
**Depended on by:** `recommendation scoring`, `goals UI`, `since-you-were-away-why-now`, future `analytics-admin`

---

## Components

### HarvestedOutcomeStore

**File:** `src/advisor/outcomes.py`
**Status:** Experimental

#### Behavior

Per-user SQLite store for harvested recommendation and action outcomes. A dedicated store keeps harvested evidence queryable and auditable without changing recommendation markdown into a noisy append log.

Suggested path:

- `~/coach/users/{safe_id}/outcomes.db`

Suggested schema:

```sql
CREATE TABLE harvested_outcomes (
    id TEXT PRIMARY KEY,
    recommendation_id TEXT NOT NULL,
    action_item_id TEXT,
    state TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_json TEXT NOT NULL,
    source_summary TEXT NOT NULL DEFAULT '',
    user_overridden INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX idx_harvested_outcomes_rec
ON harvested_outcomes(recommendation_id);
```

Suggested `state` values:

- `positive`
- `negative`
- `unresolved`
- `conflicted`

`evidence_json` stores structured supporting evidence:

```json
[
  {"kind": "action_status", "value": "completed", "source_id": "rec_123", "excerpt": ""},
  {"kind": "journal", "value": "positive", "source_id": "journal/2026-03-08.md", "excerpt": "Shipped the memo..."}
]
```

#### Inputs / Outputs

```python
def upsert(self, outcome: dict) -> str
def get(self, recommendation_id: str) -> dict | None
def list_recent(self, limit: int = 50) -> list[dict]
def override(self, recommendation_id: str, state: str, note: str = "") -> dict | None
```

#### Invariants

- At most one current harvested outcome exists per `recommendation_id`.
- User overrides always win over inferred states until explicitly cleared.
- Outcome rows are per-user and never stored in shared `intel.db`.

#### Error Handling

- Unknown `recommendation_id` on `override()` returns `None`.
- SQLite failures propagate to callers.

#### Configuration

| Key | Default | Source |
|---|---|---|
| Outcome DB path | `~/coach/users/{safe_id}/outcomes.db` | `get_user_paths()` extension |

---

### OutcomeHarvester

**File:** `src/advisor/outcomes.py`
**Status:** Experimental

#### Behavior

Scans later user activity for evidence related to a recommendation or tracked action item. It is rules-first and only uses a cheap LLM for ambiguous text classification.

Evaluation order:

1. explicit action-item status
2. explicit recommendation feedback
3. goal check-in / goal progress delta
4. journal evidence within the review window
5. unresolved fallback

Suggested scoring model:

```text
positive_score =
  1.0 if action_status == completed else 0
  + 0.7 if explicit_feedback in {useful, acted_on} else 0
  + 0.5 if goal_progress_delta > 0 else 0
  + journal_signal_score

negative_score =
  1.0 if action_status in {blocked, abandoned} else 0
  + 0.7 if explicit_feedback in {not_useful, thumbs_down} else 0
  + 0.5 if goal_checkin indicates stall or regression else 0
  + journal_failure_score
```

Decision tree:

1. If `user_overridden=1` → use stored override.
2. If `positive_score >= positive_threshold` and `negative_score < conflict_threshold` → `positive`.
3. If `negative_score >= negative_threshold` and `positive_score < conflict_threshold` → `negative`.
4. If both are above threshold → `conflicted`.
5. Else if review window expired with insufficient evidence → `unresolved`.
6. Else no write or keep current unresolved state.

#### Inputs / Outputs

```python
def evaluate_recommendation(self, recommendation: dict) -> dict | None
def run_recent(self, limit: int = 50) -> list[dict]
```

The evaluator consumes:

- recommendation metadata
- optional `action_item` block
- related goal path if present
- recent journal entries
- recent goal check-ins
- prior explicit recommendation feedback

#### Invariants

- Missing evidence does not become `negative` by default.
- Explicit statuses outrank inferred textual evidence.
- The evaluator is conservative; it should emit `conflicted` or `unresolved` rather than overclaim.

#### Error Handling

- Journal or goal lookup failure degrades to fewer signals; it does not abort evaluation.
- LLM classifier failure on ambiguous journal text falls back to neutral / no contribution.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `review_window_today_days` | `3` | new `advisor.outcomes` config |
| `review_window_this_week_days` | `21` | new config |
| `review_window_later_days` | `45` | new config |
| `positive_threshold` | `1.0` | new config |
| `negative_threshold` | `1.0` | new config |
| `conflict_threshold` | `0.8` | new config |

#### Caveats

- This is a new inference layer and does not replace explicit action-item status.
- Recommendation markdown remains the source of truth for action state; harvested outcomes are secondary learned state.

---

### ScoringAdapter + Web Route Extensions

**Files:** `src/advisor/scoring.py`, `src/web/routes/recommendations.py`, `src/web/models.py`
**Status:** Experimental

#### Behavior

Adds harvested outcomes as an additional scoring input alongside explicit ratings and action execution boosts.

Suggested integration:

- `positive` harvested outcomes contribute a bounded positive boost
- `negative` harvested outcomes contribute a bounded negative boost
- `unresolved` contributes no directional score change
- `conflicted` contributes no automatic boost until user confirmation

Route additions:

- `GET /api/recommendations/{id}/outcome`
- `POST /api/recommendations/{id}/outcome/override`

Recommendation list payloads can include:

```json
"harvested_outcome": {
  "state": "positive",
  "confidence": 0.84,
  "source_summary": "Completed action item and positive journal evidence",
  "user_overridden": false
}
```

#### Invariants

- Harvested outcomes are explainability metadata first and ranking input second.
- User override must be visible in API responses.

#### Error Handling

- Missing harvested outcome returns `null`, not an error.
- Outcome override validation rejects unknown states with 422.

---

## Cross-Cutting Concerns

### Memory integration

- The existing memory pipeline already supports `FactSource.FEEDBACK` and `FactSource.GOAL`. Outcome Harvester should reuse those upstream signals where available rather than inventing a separate fact-extraction source immediately.

## Test Expectations

- Store tests: upsert/get/override, per-recommendation uniqueness, user override precedence.
- Evaluator tests: positive from completion, negative from blocked/abandoned, unresolved on no evidence, conflicted on mixed signals.
- Scoring tests: harvested outcomes affect rank within bounded limits and do not override explicit user corrections.
- Route tests: outcome fetch and override endpoints, null outcome behavior.
- Mock: recommendation storage, journal storage, goal tracker, cheap LLM classifier, temp SQLite DBs.

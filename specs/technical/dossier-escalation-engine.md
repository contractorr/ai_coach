# Dossier Escalation Engine

## Overview

Dossier Escalation Engine suggests when a recurring user topic should be promoted into a live dossier. It is deliberately user-scoped and heuristic-first: it combines thread recurrence, journal frequency, recent intel support, and existing user context, then persists a small set of suggestion records that can be accepted, dismissed, or snoozed.

## Dependencies

**Depends on:** `journal` (threads + journal frequency), `intelligence` (recent item search + watchlist context), `research-dossiers` (dossier create / list), `web` (suggestions + routes), `db`
**Depended on by:** `thread inbox`, `suggestions`, `extraction receipt`, `return briefing`

---

## Components

### DossierEscalationStore

**File:** `src/research/escalation.py`
**Status:** Experimental

#### Behavior

Per-user SQLite store for escalation suggestions. Uses a dedicated per-user database file rather than the shared `InsightStore` because escalation suggestions are derived from private journal and goal context.

Suggested path:

- `~/coach/users/{safe_id}/escalations.db`

Suggested schema:

```sql
CREATE TABLE dossier_escalations (
    escalation_id TEXT PRIMARY KEY,
    topic_key TEXT NOT NULL,
    topic_label TEXT NOT NULL,
    score REAL NOT NULL,
    state TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    snoozed_until TEXT,
    dismissed_at TEXT,
    accepted_dossier_id TEXT
);

CREATE UNIQUE INDEX idx_dossier_escalations_topic_active
ON dossier_escalations(topic_key)
WHERE state IN ('active', 'snoozed');
```

Suggested states:

- `active`
- `snoozed`
- `dismissed`
- `accepted`

#### Inputs / Outputs

```python
def upsert_candidate(self, suggestion: dict) -> str
def list_active(self, limit: int = 10) -> list[dict]
def snooze(self, escalation_id: str, until: str) -> bool
def dismiss(self, escalation_id: str) -> bool
def accept(self, escalation_id: str, dossier_id: str) -> bool
```

#### Invariants

- At most one active-or-snoozed suggestion exists per normalized `topic_key`.
- Accepted suggestions retain history through `accepted_dossier_id`.
- Suggestion storage is per-user only.

#### Error Handling

- Unknown `escalation_id` returns `False` to callers; web routes translate to 404.
- SQLite failures propagate.

#### Configuration

| Key | Default | Source |
|---|---|---|
| Escalation DB path | `~/coach/users/{safe_id}/escalations.db` | `get_user_paths()` extension |

---

### DossierEscalationEngine

**File:** `src/research/escalation.py`
**Status:** Experimental

#### Behavior

Heuristic engine that scores candidate topics and refreshes the active suggestion set lazily from user-scoped data. It should run on demand from suggestion-serving surfaces rather than as a new mandatory background scheduler phase.

Candidate sources:

1. active recurring threads
2. repeated journal topic mentions over the last 30 days
3. recent intel items matching the same normalized topic over the last 7 days
4. watchlist or active-goal boosts
5. optional recent research or dossier-adjacent context

Suggested composite score:

```text
score =
  0.35 * thread_recency_score
  0.25 * journal_frequency_score
  0.25 * intel_support_score
  0.10 * goal_or_watchlist_bonus
  0.05 * prior_research_bonus
```

Eligibility gates:

- active thread or repeated journal evidence required
- no active dossier already covering `topic_key`
- no active snooze covering the topic
- score must exceed `min_escalation_score`

The engine writes only the top `max_active_escalations` suggestions after deduping by `topic_key`.

#### Inputs / Outputs

```python
def refresh(self, user_context: dict) -> list[dict]
def build_prefill(self, escalation_id: str) -> dict | None
```

Suggested evidence shape:

```json
{
  "thread_id": "...",
  "recent_mentions": 4,
  "intel_hits": 3,
  "goal_titles": ["..."],
  "watchlist_labels": ["..."]
}
```

#### Invariants

- The engine is conservative by default and must not emit suggestions for single-source weak topics.
- Refresh is deterministic for the same user inputs and thresholds.
- Existing active dossiers suppress new suggestions for the same normalized topic.

#### Error Handling

- Missing optional inputs (watchlist, goals, research) degrade score quality but do not abort refresh.
- Failure in one candidate topic should not abort the rest of the refresh set.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `min_escalation_score` | `0.62` | new `research.escalation` config |
| `max_active_escalations` | `3` | new `research.escalation` config |
| `journal_window_days` | `30` | new config |
| `intel_window_days` | `7` | new config |
| `dismiss_cooldown_days` | `21` | new config |
| `default_snooze_days` | `14` | new config |

#### Caveats

- This is a new capability; no current scheduler job or suggestion route performs this scoring today.
- Topic normalization must be good enough to avoid duplicate suggestions for near-identical labels.

---

### Web Routes + Suggestion Integration

**Files:** `src/web/routes/suggestions.py`, `src/web/routes/research.py`, `src/web/models.py`
**Status:** Experimental

#### Behavior

Suggested additions:

- `GET /api/dossier-escalations`
- `POST /api/dossier-escalations/{id}/dismiss`
- `POST /api/dossier-escalations/{id}/snooze`
- `POST /api/dossier-escalations/{id}/accept`

`accept` resolves through the existing dossier create path and records the resulting dossier id on success. The general suggestions feed can optionally merge active escalation rows into its payload with `source="dossier_escalation"`.

#### Invariants

- Accept is idempotent: if already accepted, return the existing linked dossier.
- Dismiss and snooze never create dossier artifacts.

#### Error Handling

- Accept failure in dossier creation leaves the escalation in `active` state.
- Hidden or stale topic data produces a user-safe error rather than creating an empty dossier shell.

---

## Cross-Cutting Concerns

### Why not InsightStore

- `InsightStore` is persisted in shared `intel.db` and has no user isolation field; escalation suggestions must remain private because they are derived from journal and goal context.

## Test Expectations

- Store tests: unique active topic enforcement, dismiss/snooze/accept transitions, accepted-dossier linkage.
- Engine tests: scoring, active-dossier suppression, cooldown handling, weak-topic filtering.
- Route tests: accept creates dossier on success, accept failure leaves state unchanged, dismiss/snooze endpoints mutate only user-owned rows.
- Suggestions integration tests: escalation rows merge cleanly without duplicating other suggestion types.
- Mock: thread service, intel search, watchlist store, dossier store, user-scoped temp DBs.

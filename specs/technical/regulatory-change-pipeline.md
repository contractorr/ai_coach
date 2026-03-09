# Regulatory Change Pipeline

## Overview

Regulatory Change Pipeline extends the intelligence system with focused monitoring for policy, regulatory, and standards changes tied to watched sectors, topics, and geographies. It normalizes updates into structured regulatory alerts, classifies urgency and relevance, stores public-source events in shared `intel.db`, and attaches user-relevant alerts into dossiers, briefings, and watchlist views.

## Dependencies

**Depends on:** `intelligence` (watchlist, scheduler, storage), `research-dossiers`, `web`, `db`, `llm` (cheap classification or rewrite only when needed)
**Depended on by:** `assumption-watchlist`, `since-you-were-away-why-now`, future sector-risk dossier workflows

---

## Components

### RegulatoryWatchResolver

**File:** `src/intelligence/regulatory.py`
**Status:** Experimental

#### Behavior

Builds monitored regulatory targets from watchlist items representing sectors, topics, geographies, or free-form themes. Targets remain user-scoped at configuration time, but the resulting public events are stored in shared `intel.db` after normalization.

Suggested normalized target shape:

```json
{
  "target_id": "reg_xxx",
  "kind": "sector",
  "label": "digital health",
  "aliases": ["healthtech"],
  "geographies": ["UK", "EU"],
  "watchlist_id": "wl_xxx"
}
```

#### Inputs / Outputs

```python
def from_watchlist_items(self, items: list[dict]) -> list[dict]
```

#### Invariants

- Resolver output is deterministic for the same watchlist items.
- Geography scoping is additive; a target may have topic-only or geography-only matching.

#### Error Handling

- Weak or empty watch targets are skipped with warnings.

---

### RegulatoryAlertStore

**File:** `src/intelligence/regulatory.py`
**Status:** Experimental

#### Behavior

Stores normalized regulatory or standards events in shared `intel.db`.

Suggested schema:

```sql
CREATE TABLE regulatory_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_key TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_family TEXT NOT NULL,
    change_type TEXT NOT NULL,
    urgency TEXT NOT NULL,
    relevance REAL NOT NULL,
    effective_date TEXT,
    source_url TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    dedup_hash TEXT NOT NULL UNIQUE,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_regulatory_alerts_target ON regulatory_alerts(target_key, observed_at DESC);
CREATE INDEX idx_regulatory_alerts_urgency ON regulatory_alerts(urgency, observed_at DESC);
```

`change_type` examples:

- `proposed`
- `finalized`
- `guidance`
- `standard`
- `enforcement`

#### Inputs / Outputs

```python
def save_many(self, alerts: list[dict]) -> int
def get_recent(self, since: datetime, limit: int = 100) -> list[dict]
```

#### Invariants

- Public-source alerts are shared and user-agnostic at storage time.
- Dedup hash collapses repeated reporting of the same underlying change.

#### Error Handling

- Duplicate rows are skipped.
- Invalid urgency or change-type values are rejected before save.

---

### RegulatoryClassifier

**File:** `src/intelligence/regulatory.py`
**Status:** Experimental

#### Behavior

Classifies raw regulatory-source findings into urgency, relevance, and change type. V1 should be rules-first with optional cheap-LLM rewrite to improve the user-facing explanation.

Suggested urgency rules:

- `high` when finalized or enforcement-relevant changes match a user's monitored geography/topic closely
- `medium` when guidance, proposed rules with clear near-term impact, or standards updates are strongly relevant
- `low` for exploratory, distant, or weakly matched updates

Suggested relevance score inputs:

```text
relevance =
  0.45 * keyword_match
  0.30 * geography_match
  0.25 * watched_target_priority
```

#### Inputs / Outputs

```python
def classify(self, raw_item: dict, target: dict) -> dict | None
```

#### Invariants

- Classifier should prefer lower urgency over overstating legal importance.
- Missing effective date is allowed and should not block alert creation.

#### Error Handling

- Unclassifiable items return `None` rather than creating vague alerts.
- LLM rewrite failure falls back to rule-based summary only.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `regulatory.enabled` | `False` | new scheduler config |
| `regulatory.min_relevance` | `0.5` | new config |
| `regulatory.run_cron` | `0 */12 * * *` | new config |

#### Caveats

- Direct agency and standards-body adapters are new capabilities not in the current scraper set.

---

### Scheduler + User Matching + Routes

**Files:** `src/intelligence/scheduler.py`, `src/intelligence/regulatory.py`, `src/web/routes/intel.py`, `src/web/models.py`
**Status:** Experimental

#### Behavior

Adds a `regulatory` scheduler job that:

1. resolves monitored targets from user watchlists
2. runs supported source adapters
3. classifies and stores normalized alerts
4. exposes matched alerts via web routes and dossier attachment points

Suggested routes:

- `GET /api/intel/regulatory-alerts`
- `GET /api/intel/regulatory-alerts/{target_key}`

Alerts can also feed into dossier updates and return briefings by querying recent `high` or `medium` urgency alerts.

#### Invariants

- Matching to user watch targets is view-layer logic; shared alert rows remain user-agnostic.
- Alerts can enrich dossiers without becoming dossier-specific storage.

#### Error Handling

- One failing adapter should not abort the scheduler run.
- No watch targets produce a no-op run result.

---

## Cross-Cutting Concerns

### Assumption Watchlist integration

- Regulatory alerts should expose enough structured metadata for assumption matching later, especially target labels, geographies, urgency, and source-family data.

## Test Expectations

- Resolver tests: sector/topic/geography normalization and weak-target skipping.
- Store tests: dedup, urgency validation, recent retrieval.
- Classifier tests: urgency and relevance assignment for proposed vs final changes, geography-aware relevance, conservative fallback behavior.
- Scheduler tests: no-op on no watch targets, partial adapter failure behavior, route payload shape.
- Mock: source adapters, watchlist items, shared `intel.db`, optional cheap LLM rewrite.

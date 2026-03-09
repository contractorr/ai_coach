# Hiring Activity Pipeline

## Overview

Hiring Activity Pipeline specializes the intelligence system for company- and sector-level hiring signals. It shares company identity and scheduling infrastructure with Company Movement Pipeline, but adds hiring-specific source adapters, baseline tracking, signal clustering, and strategy interpretation.

## Dependencies

**Depends on:** `company-movement-pipeline` (company identity + shared scheduling patterns), `intelligence` (watchlist, scheduler, storage), `web`, `db`, `llm` (cheap interpretation only when needed)
**Depended on by:** `company-movement-pipeline` enrichment, `since-you-were-away-why-now`, future hiring-focused dossier updates

---

## Components

### HiringSignalStore

**File:** `src/intelligence/hiring_signals.py`
**Status:** Experimental

#### Behavior

Stores normalized hiring signals in shared `intel.db`. Signals are derived from public company or sector hiring behavior, so they live in the shared intel layer.

Suggested schema:

```sql
CREATE TABLE hiring_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_key TEXT NOT NULL,
    entity_label TEXT NOT NULL,
    entity_kind TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    interpretation TEXT NOT NULL DEFAULT '',
    significance REAL NOT NULL,
    source_url TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    dedup_hash TEXT NOT NULL UNIQUE,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
```

`entity_kind` examples:

- `company`
- `sector`

`signal_type` examples:

- `hiring_spike`
- `new_role_family`
- `capability_buildup`
- `geography_expansion`
- `seniority_shift`

#### Inputs / Outputs

```python
def save_many(self, signals: list[dict]) -> int
def get_recent(self, entity_key: str | None = None, limit: int = 50) -> list[dict]
```

#### Invariants

- Shared store rows are public and user-agnostic.
- Dedup hash collapses materially identical signals across repeated scrapes.

#### Error Handling

- Invalid or duplicate rows are skipped.

---

### HiringBaselineTracker

**File:** `src/intelligence/hiring_signals.py`
**Status:** Experimental

#### Behavior

Tracks recent posting baselines so the pipeline can distinguish ordinary hiring from meaningful change.

Suggested schema in `intel.db`:

```sql
CREATE TABLE hiring_baselines (
    entity_key TEXT PRIMARY KEY,
    entity_kind TEXT NOT NULL,
    rolling_post_count REAL NOT NULL,
    last_role_family_json TEXT NOT NULL DEFAULT '[]',
    last_geographies_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL
);
```

The tracker updates rolling counts and category sets on each run.

#### Inputs / Outputs

```python
def update(self, entity_key: str, snapshot: dict) -> dict
def get(self, entity_key: str) -> dict | None
```

#### Invariants

- Baselines are approximate heuristics, not exact historical archives.
- Missing baseline means first observation; no spike should be claimed on first sighting alone.

#### Error Handling

- Missing baseline returns `None` and triggers cold-start logic.

---

### HiringSignalDetector

**File:** `src/intelligence/hiring_signals.py`
**Status:** Experimental

#### Behavior

Consumes snapshots from company career pages, ATS-hosted boards, and supported public job sources, then emits hiring signals when change exceeds baseline thresholds.

Suggested detection rules:

- `hiring_spike` when `current_post_count >= rolling_post_count * spike_multiplier` and both exceed minimum counts
- `new_role_family` when a role family absent from baseline appears above `min_family_count`
- `capability_buildup` when clustered roles map repeatedly to the same capability taxonomy
- `geography_expansion` when new location clusters exceed `min_geo_count`

Interpretation can be rule-based first, with optional cheap LLM rewrite into concise user-facing text.

#### Inputs / Outputs

```python
def detect(self, entity: dict, snapshot: dict, baseline: dict | None) -> list[dict]
```

#### Invariants

- The detector should not emit `hiring_spike` on cold-start baselines.
- Interpretation must stay bounded to observed evidence.

#### Error Handling

- Partial source snapshots produce fewer possible signal types but do not abort detection.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `hiring.enabled` | `False` | new scheduler config |
| `hiring.spike_multiplier` | `2.0` | new config |
| `hiring.min_post_count` | `5` | new config |
| `hiring.min_family_count` | `3` | new config |
| `hiring.min_geo_count` | `3` | new config |
| `hiring.run_cron` | `0 */12 * * *` | new config |

#### Caveats

- Company-specific ATS and career-page adapters are new capabilities and not part of the current scraper set.
- LinkedIn is not assumed; no dependency on LinkedIn APIs is introduced in V1.

---

### Shared Company Matching + Web Routes

**Files:** `src/intelligence/hiring_signals.py`, `src/web/routes/intel.py`, `src/web/models.py`
**Status:** Experimental

#### Behavior

Uses watched-company and watched-sector items to filter shared hiring signals back into user-relevant views.

Suggested routes:

- `GET /api/intel/hiring-signals`
- `GET /api/intel/hiring-signals/{entity_key}`

Signals can optionally be promoted into company movement summaries or dossier evidence when both systems are enabled.

#### Invariants

- Shared signal storage remains user-agnostic; view-layer matching is user-specific.

#### Error Handling

- No supported entities configured → empty list.

---

## Cross-Cutting Concerns

### Relationship to Company Movement Pipeline

- Shared: company identity, user matching, scheduling registration, card enrichment.
- Separate: hiring baselines, detection thresholds, role-family taxonomy, interpretation logic.

## Test Expectations

- Baseline tracker tests: cold-start behavior, rolling update behavior.
- Detector tests: spike, new role family, capability buildup, geography expansion, and false-positive suppression.
- Store tests: dedup, retrieval by entity.
- Route tests: watched-company and watched-sector filtering.
- Mock: company resolvers, job snapshots from career/ATS pages, shared `intel.db`, optional cheap LLM interpreter.

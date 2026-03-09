# Competitor / Company Movement Pipeline

## Overview

Company Movement Pipeline adds entity-centric monitoring on top of the existing intelligence system. It resolves watched companies into monitorable identities, runs company-specific collectors, normalizes raw findings into company movement events, stores those events in shared `intel.db`, and then matches them back into per-user watchlists, dossiers, and proactive surfaces.

## Dependencies

**Depends on:** `intelligence` (scheduler, storage, watchlist, heartbeat patterns), `research-dossiers`, `web`, `db`, `llm` (cheap significance summarization only when needed)
**Depended on by:** `hiring-activity-pipeline`, `since-you-were-away-why-now`, future company-specific dossier views

---

## Components

### WatchedCompanyResolver

**File:** `src/intelligence/company_watch.py`
**Status:** Experimental

#### Behavior

Builds monitorable company identities from existing watchlist items where `kind="company"`. It enriches each watched company with aliases and optional source-specific handles.

Suggested normalized shape:

```json
{
  "company_id": "cmp_xxx",
  "label": "OpenAI",
  "aliases": ["OpenAI Inc"],
  "domain": "openai.com",
  "github_org": "openai",
  "ticker": null,
  "watchlist_id": "wl_xxx",
  "priority": 3
}
```

#### Inputs / Outputs

```python
def from_watchlist_items(self, items: list[dict]) -> list[dict]
```

#### Invariants

- Resolver output is derived from user-owned watchlist items but normalized enough for shared scraping.
- Missing optional identifiers do not block monitoring if at least a label exists.

#### Error Handling

- Invalid or weak company records are skipped with warnings.

---

### CompanyMovementStore

**File:** `src/intelligence/company_watch.py`
**Status:** Experimental

#### Behavior

Stores normalized company movement events in shared `intel.db`. Events are public-world intelligence, so they belong in the shared intel layer rather than a per-user store.

Suggested schema:

```sql
CREATE TABLE company_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_key TEXT NOT NULL,
    company_label TEXT NOT NULL,
    movement_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    significance REAL NOT NULL,
    source_url TEXT NOT NULL,
    source_family TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    dedup_hash TEXT NOT NULL UNIQUE,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_company_movements_company ON company_movements(company_key, observed_at DESC);
CREATE INDEX idx_company_movements_significance ON company_movements(significance DESC, observed_at DESC);
```

`movement_type` examples:

- `product`
- `pricing`
- `roadmap`
- `partnership`
- `leadership`
- `github`
- `filing`

#### Inputs / Outputs

```python
def save_many(self, movements: list[dict]) -> int
def get_recent_for_company(self, company_key: str, limit: int = 20) -> list[dict]
def get_since(self, since: datetime, limit: int = 200) -> list[dict]
```

#### Invariants

- Dedup is hash-based over normalized company, movement type, and canonicalized source/title summary.
- Shared store rows do not carry `user_id`; user-specific relevance is computed later.

#### Error Handling

- Duplicate insert returns skip, not failure.
- Invalid movement rows are skipped after validation.

---

### CompanyMovementCollector + SignificanceRanker

**Files:** `src/intelligence/company_watch.py`, `src/intelligence/sources/company_*`
**Status:** Experimental

#### Behavior

Collector orchestrates company-specific adapters such as:

- company RSS / news feeds
- product or pricing page snapshots
- GitHub org release and activity snapshots
- partnership / press pages
- optional filings adapters

Each adapter returns raw findings which are normalized into movement events and ranked.

Suggested significance formula:

```text
significance =
  0.35 * source_authority
  0.25 * novelty
  0.20 * movement_type_weight
  0.20 * corroboration_score
```

`movement_type_weight` can bias launches, pricing, filings, and leadership higher than minor changelog noise.

#### Inputs / Outputs

```python
async def collect(self, companies: list[dict]) -> list[dict]
def rank(self, events: list[dict]) -> list[dict]
```

#### Invariants

- Collector output is normalized before persistence.
- At least one stable company identifier (`company_key`) is attached before save.

#### Error Handling

- One adapter failure should not abort other adapters or companies.
- Missing optional adapters degrade coverage only.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `company_movement.enabled` | `False` | new scheduler config |
| `company_movement.max_events_per_run` | `100` | new config |
| `company_movement.min_significance` | `0.45` | new config |
| `company_movement.run_cron` | `0 */6 * * *` | new config |

#### Caveats

- Pricing-page snapshots and filings adapters are new capabilities, not present in the current scraper set.

---

### User Matching + Web Surfaces

**Files:** `src/intelligence/company_watch.py`, `src/web/routes/intel.py`, `src/web/models.py`
**Status:** Experimental

#### Behavior

Matches shared company movement events back to watched-company items and optionally linked dossiers.

Suggested response card shape:

```json
{
  "company": "OpenAI",
  "movement_type": "pricing",
  "title": "API pricing updated",
  "summary": "...",
  "significance": 0.81,
  "why_it_matters": "Watched company changed a monetization lever",
  "source_refs": [...],
  "linked_dossier_id": null
}
```

Suggested routes:

- `GET /api/intel/company-movements`
- `GET /api/intel/company-movements/{company_key}`

#### Invariants

- User-specific watchlist priority affects ordering, not the shared underlying event row.
- Multiple users may match the same shared event differently.

#### Error Handling

- No watched companies → empty list, not route failure.

---

## Cross-Cutting Concerns

### Shared with Hiring Activity Pipeline

- watched-company resolution
- company identity normalization
- scheduler registration
- dossier attachment and card rendering patterns

## Test Expectations

- Resolver tests: alias handling, weak-record skipping, stable `company_key` generation.
- Store tests: dedup hash behavior, company-specific retrieval, shared-store semantics.
- Collector tests: adapter fan-out, normalization, significance ranking, partial adapter failure.
- Route tests: watched-company filtering, company detail listing, empty-state behavior.
- Mock: watchlist store, adapter outputs, shared intel DB temp path, optional cheap LLM summarizer.

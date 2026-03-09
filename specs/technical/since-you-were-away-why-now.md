# Since-You-Were-Away + Why-Now Surfaces

## Overview

This feature adds two explanatory layers on top of existing greeting, suggestion, recommendation, and dossier infrastructure: a return-brief builder for users coming back after an absence, and a `why now` reasoner that attaches compact evidence chips to surfaced items. The design goal is to make the product's timing legible without turning the UI into a debug console.

## Dependencies

**Depends on:** `greeting-cache`, `web` (greeting + suggestion routes, users DB), `recommendations`, `action-plans`, `research-dossiers`, `journal` (thread summaries), `intelligence`
**Depended on by:** `home page`, `suggestions`, `recommendation cards`, future `outcome-harvester`

---

## Components

### ReturnBriefBuilder

**File:** `src/advisor/return_brief.py`
**Status:** Experimental

#### Behavior

Builds a compact return briefing when a user has been inactive for a configured threshold. The builder reads the user's last meaningful activity from `users.db` event tables, compares that timestamp with current state, and returns a structured briefing payload rather than a freeform string only.

Suggested payload shape:

```json
{
  "active": true,
  "absent_hours": 96,
  "summary": "While you were away, two company movements landed, one assumption changed, and one dossier changed.",
  "sections": [
    {"kind": "intel", "items": [...]},
    {"kind": "company_movements", "items": [...]},
    {"kind": "hiring_signals", "items": [...]},
    {"kind": "regulatory_alerts", "items": [...]},
    {"kind": "threads", "items": [...]},
    {"kind": "dossiers", "items": [...]},
    {"kind": "goals", "items": [...]},
    {"kind": "assumptions", "items": [...]}
  ],
  "next_steps": [ ... ],
  "generated_at": "..."
}
```

`summary` may be heuristic text or cheap-LLM-generated, but sections are structured so the UI can remain calm and inspectable.

#### Inputs / Outputs

```python
def get_last_active_at(self, user_id: str) -> datetime | None
def build(self, user_id: str) -> dict | None
```

#### Invariants

- No return brief is built when absence is below the configured threshold.
- The builder is additive to the greeting system; it does not replace the greeting cache by itself.
- The builder must tolerate missing data from any one subsystem.

#### Error Handling

- Missing last-activity signal → return `None` (first-visit or insufficient data), not an error.
- Partial subsystem failure → omit that section and continue.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `return_brief_absence_hours` | `72` | new `greeting.return_brief` config |
| `max_section_items` | `3` | new config |
| `cache_ttl` | `21600` (6h) | new config |

---

### WhyNowReasoner

**File:** `src/advisor/why_now.py`
**Status:** Experimental

#### Behavior

Attaches compact evidence chips to suggestion and recommendation payloads. The reasoner is deterministic and rules-based in V1 so chip presence is explainable.

Supported chip codes can include:

- `stale_goal`
- `assumption_invalidated`
- `assumption_confirmed`
- `assumption_suggested`
- `assumption_updated`
- `watchlist_match`
- `thread_reactivated`
- `dossier_changed`
- `recent_intel`
- `executed_similar`

Suggested chip shape:

```json
{
  "code": "watchlist_match",
  "label": "2 new watchlist matches",
  "severity": "info",
  "detail": {
    "watchlist_ids": ["..."],
    "source_urls": ["..."]
  }
}
```

The reasoner should emit at most `max_chips_per_item` chips per surfaced item, ordered by usefulness.

#### Inputs / Outputs

```python
def explain_suggestion(self, suggestion: dict, user_context: dict) -> list[dict]
def explain_recommendation(self, recommendation: dict, user_context: dict) -> list[dict]
```

#### Invariants

- No chip is better than a vague chip; emit `[]` when evidence is weak or generic.
- Chip labels are user-facing text, not raw internal score names.
- `detail` is safe for expansion in the UI; it should not expose private scoring internals.

#### Error Handling

- Missing optional context sources yield fewer chips, not route failure.

#### Configuration

| Key | Default | Source |
|---|---|---|
| `max_chips_per_item` | `3` | new `advisor.why_now` config |
| `recent_intel_window_days` | `7` | new config |
| `thread_reactivated_window_days` | `14` | new config |

---

### Greeting + Suggestions Route Extensions

**Files:** `src/web/routes/greeting.py`, `src/web/routes/suggestions.py`, `src/web/routes/recommendations.py`, `src/web/models.py`
**Status:** Experimental

#### Behavior

Route changes:

- `GET /api/greeting` gains optional `return_brief` field.
- `GET /api/suggestions` gains optional `why_now: list[chip]` per item.
- `GET /api/recommendations` can also include `why_now` chips for consistency with goal-card recommendation rendering.

Suggested greeting response shape:

```json
{
  "text": "...",
  "cached": true,
  "stale": false,
  "return_brief": { ... } | null
}
```

The route should reuse the existing greeting fetch path so the home surface does not need multiple startup calls for closely related context.

#### Invariants

- Greeting failure must not prevent `return_brief` from being omitted cleanly.
- `return_brief` is optional; clients must feature-detect its presence.
- Chips are additive metadata and do not change the underlying suggestion ordering logic in V1.

#### Error Handling

- Return-brief build failure → return greeting without `return_brief`.
- Why-now build failure → return item without chips.

---

### Frontend Surfaces

**Files:** `web/src/app/(dashboard)/page.tsx`, `web/src/components/home/ReturnBriefCard.tsx`, `web/src/components/shared/WhyNowChip.tsx`
**Status:** Experimental

#### Behavior

Implements:

- a dedicated `ReturnBriefCard` under the home header / first assistant greeting region
- compact chip rendering on suggestion and recommendation cards
- an expandable sheet, popover, or inline disclosure for chip details

Per the design system and UX guidelines, the surfaces should:

- preserve one clear primary action on the card
- keep chips lightweight and subordinate
- make generated reasoning inspectable without overwhelming the main workflow

#### Invariants

- Return brief is dismissible and non-blocking.
- Chip expansion is optional; core workflows remain usable without opening details.
- Empty-state copy is explicit when the user was away but nothing major changed.

#### Error Handling

- Missing chip detail renders the label only.
- Frontend fetch or parse issues fall back to existing greeting / suggestion UI.

---

## Cross-Cutting Concerns

### Activity source of truth

- `users.db` engagement and page-view events should be used as the primary last-activity signal.
- If multiple event tables exist, `max(timestamp)` across supported event sources should determine inactivity.

### Cache strategy

- Return briefs should be cached per user and activity boundary, not globally. A practical key pattern is `return_brief_v1_{safe_user_id}_{last_active_ts}`.

## Test Expectations

- `ReturnBriefBuilder`: below-threshold no-op, section aggregation, omission of failed sections, stable summary generation.
- `WhyNowReasoner`: chip emission rules, max-chip cap, empty-chip cases, human-readable labels.
- Greeting route tests: `return_brief` included only when threshold exceeded; omission on builder failure.
- Suggestions/recommendations route tests: chips attached when evidence exists, hidden when weak.
- Frontend tests: return-brief card render/dismiss, chip render/expand, empty and error fallback states.
- Mock: users DB engagement reads, suggestion/recommendation stores, dossier summaries, thread summaries, context cache.

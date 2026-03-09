# Research Dossiers

## Overview

Research dossiers extend deep research with a journal-backed persistence layer for long-lived topics. The feature adds a dossier store, dossier-aware synthesis prompts, targeted dossier updates in the research agent, and retrieval hooks so advisor and recommendation flows can consume accumulated dossier state.

## Dependencies

**Depends on:** `journal` (frontmatter-backed persistence, embeddings), `research` (search + synthesis), `intelligence` (intel item storage, scheduler), `advisor` (RAG retrieval, recommendation prompts), `web`, `cli`, `mcp`
**Depended on by:** `research.agent`, `intelligence.scheduler`, `web.routes.research`, `cli.commands.research`, `coach_mcp.tools.research`, `advisor.rag`, `advisor.recommendations`

---

## Components

### `ResearchDossierStore`

**File:** `src/research/dossiers.py`
**Status:** Experimental

#### Behavior

Wraps `JournalStorage` to persist two kinds of `entry_type="research"` journal entries:

- dossier definition entries (`research_kind="dossier"`)
- dossier update entries (`research_kind="dossier_update"`)

The store treats journal frontmatter as the source of truth. Dossier entries hold stable metadata such as `dossier_id`, `topic`, `scope`, `status`, `core_questions`, `assumptions`, `related_goals`, and `tracked_subtopics`. Update entries hold timeline records for the same `dossier_id`, including `change_summary`, `confidence`, `recommended_actions`, `citations`, and `source_urls`.

It does not create a separate database. Listing and lookup scan journal markdown files and parse frontmatter, which is acceptable at current single-user scale.

#### Inputs / Outputs

- `create_dossier(...) -> dict`
- `list_dossiers(include_archived: bool = False, limit: int = 50) -> list[dict]`
- `get_dossier(dossier_id: str) -> dict | None`
- `list_updates(dossier_id: str, limit: int = 20) -> list[dict]`
- `append_update(dossier_id: str, content: str, metadata: dict) -> dict`
- `update_dossier_metadata(dossier_id: str, **fields) -> dict | None`
- `get_active_dossiers(limit: int = 50) -> list[dict]`

#### Invariants

- Every dossier has a stable UUID-like `dossier_id`
- Dossier definitions and dossier updates always use `entry_type="research"`
- Update entries always reference an existing dossier by `dossier_id`
- Archived dossiers remain readable but are excluded from automatic scheduled updates
- The dossier detail shape includes `updates`, `update_count`, `last_updated`, and `latest_change_summary`

#### Error Handling

- Unknown dossier ID returns `None` from read/update helpers; callers convert that to a not-found error where needed
- Malformed research entries are skipped during scans rather than aborting listing
- Missing optional metadata fields normalize to empty strings or empty lists

#### Caveats

- Listing is `O(n)` over journal markdown files
- Ordering is based on frontmatter timestamps and falls back to file ordering when timestamps are missing

---

### `ResearchSynthesizer` dossier update mode

**File:** `src/research/synthesis.py`
**Status:** Experimental

#### Behavior

Adds a dossier-specific synthesis path that compares fresh sources against dossier context. The output is structured markdown with fixed headings:

- `## What Changed`
- `## Why It Matters`
- `## Evidence`
- `## Confidence`
- `## Recommended Actions`
- `## Open Questions`
- `## Sources`

The synthesizer uses prior dossier summary and latest change summary as context so the model can produce a delta rather than a full snapshot. A fallback update template is returned when the LLM call fails.

#### Invariants

- Dossier update outputs always contain the headings above, even in fallback mode
- Citation/source URLs are preserved in the final markdown under `## Sources`

---

### `DeepResearchAgent` dossier integration

**File:** `src/research/agent.py`
**Status:** Experimental

#### Behavior

The agent gains dossier-aware APIs while keeping existing one-off research behavior:

- `create_dossier(...)`
- `list_dossiers(...)`
- `get_dossier(dossier_id)`
- `run(specific_topic: str | None = None, dossier_id: str | None = None)`

Execution order:

1. If `dossier_id` is provided, run one targeted dossier update.
2. Else if `specific_topic` is provided, run the legacy one-off research flow.
3. Else if active dossiers exist, update active dossiers up to `research.max_topics_per_week`.
4. Else fall back to topic auto-selection and one-off reports.

For dossier updates, the agent:

1. loads dossier metadata + latest updates
2. builds personalized context from goals plus dossier scope/questions
3. searches the web using the dossier topic
4. synthesizes a structured update
5. appends the update as a journal `research` entry
6. updates dossier summary metadata (`last_updated`, `update_count`, `latest_change_summary`)
7. stores a corresponding `research://dossier/{id}/{timestamp}` intel item
8. upserts embeddings for both the update entry and dossier definition entry

#### Error Handling

- Unknown `dossier_id` raises `ValueError`
- Empty search results create a failed result record and do not append an update
- Standalone topic research keeps its prior behavior

---

### Interface integrations

**Files:** `src/intelligence/scheduler.py`, `src/web/routes/research.py`, `src/cli/commands/research.py`, `src/coach_mcp/tools/research.py`
**Status:** Experimental

#### Behavior

- Scheduler forwards optional `dossier_id` into the agent and automatically updates active dossiers during unattended runs.
- Web routes add dossier create/list/detail endpoints and allow `/api/research/run` to target `dossier_id`.
- CLI adds dossier subcommands for create/list/view and allows `coach research run --dossier ID`.
- MCP adds `research_dossiers_list` and `research_dossier_create`, and extends `research_run` with optional `dossier_id`.

---

### Retrieval integrations

**Files:** `src/advisor/rag.py`, `src/advisor/recommendations.py`
**Status:** Experimental

#### Behavior

- `RAGRetriever.get_research_context()` continues searching `entry_type="research"`, which now includes dossier definitions and updates.
- Fallback formatting favors dossier entries with richer metadata and includes `change_summary` when present.
- Recommendation generation pulls research context for the category query and appends it to the prompt context so dossier state can influence recommendation output.

#### Caveats

- Recommendation prompts do not yet separate dossier research into its own dedicated section; the context is appended to the existing intel bundle.

---

## Test Expectations

- Store tests cover dossier create/list/get/update behavior, archived filtering, and change-summary propagation
- Agent tests cover targeted dossier updates, auto-updating active dossiers, and legacy standalone research remaining intact
- Route tests cover dossier endpoints plus `/api/research/run` with `dossier_id`
- MCP tests cover dossier list/create and targeted dossier run forwarding
- RAG/recommendation tests cover dossier-backed research context being surfaced to both advisor and recommendation flows

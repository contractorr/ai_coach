# Memory

## Overview

The memory module extracts structured facts about the user from journal entries, uploaded documents, recommendation feedback, and goal events, storing them in a dual-backend (SQLite + ChromaDB) fact store. Facts carry a category, source, and LLM-assigned confidence score. A conflict resolver prevents duplicates by combining a fast Jaccard-similarity auto-NOOP path with an LLM arbitration path. The resulting facts are injected into advisor prompts as a `<user_memory>` XML block, enabling the RAG pipeline to ground responses in persistent, user-specific context across sessions.

## Dependencies

**Depends on:** `db` (WAL connect), `llm` (FactExtractor uses cheap provider, ConflictResolver uses cheap provider), `chromadb` (FactStore optional semantic search), `advisor.rag` (context injection point), `shared_types`, `pydantic` (MemoryConfig)

**Depended on by:** `advisor` (RAGRetriever.get_memory_context injects `<user_memory>` block), `web` (memory routes call MemoryPipeline), `cli` (memory commands), `coach_mcp` (memory tools)

---

## Components

### FactCategory and FactSource enums

**File:** `src/memory/models.py`

#### Behavior

`FactCategory` classifies what kind of information a fact represents. `FactSource` records where the fact was originally observed. Both are `str` enums, so their values serialize directly to/from JSON and SQLite without translation.

`FactCategory` members:

| Value | Member |
|---|---|
| `"preference"` | `PREFERENCE` |
| `"skill"` | `SKILL` |
| `"constraint"` | `CONSTRAINT` |
| `"pattern"` | `PATTERN` |
| `"context"` | `CONTEXT` |
| `"goal_context"` | `GOAL_CONTEXT` |

`FactSource` members:

| Value | Member |
|---|---|
| `"journal"` | `JOURNAL` |
| `"document"` | `DOCUMENT` |
| `"feedback"` | `FEEDBACK` |
| `"profile"` | `PROFILE` |
| `"goal"` | `GOAL` |

#### Inputs / Outputs

Used as typed fields on `StewardFact` and `FactUpdate`. Stored as their string values in SQLite `category` and `source_type` columns. Used as ChromaDB where-clause filter values in `FactStore.search`.

#### Invariants

- Both enums are `StrEnum` — values serialize directly to/from JSON and SQLite without translation.
- `FactCategory` and `FactSource` values are stable strings used in DB columns; renaming them is a breaking migration.

#### Error Handling

No internal error handling. Invalid string values passed to `FactStore.search` categories filter produce a 400 response at the web layer before reaching the store.

#### Configuration

None.

---

### StewardFact and FactUpdate dataclasses

**File:** `src/memory/models.py`

#### Behavior

`StewardFact` is the canonical fact record. A `superseded_by` value of `None` means the fact is active; any non-None value (another fact ID for updates, `"DELETED:{reason}"` for deletions) marks it as inactive.

```python
@dataclass
class StewardFact:
    id: str
    text: str
    category: FactCategory
    source_type: FactSource
    source_id: str
    confidence: float = 0.8
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    superseded_by: str | None = None  # None = active
```

`FactUpdate` is the output of `ConflictResolver` — an instruction to the pipeline about what to do with a candidate fact.

```python
@dataclass
class FactUpdate:
    action: str          # "ADD" | "UPDATE" | "DELETE" | "NOOP"
    candidate: str       # text of the candidate fact
    existing_id: str | None = None
    reasoning: str = ""
```

#### Inputs / Outputs

`StewardFact` instances are produced by `FactExtractor`, persisted by `FactStore`, and consumed by `RAGRetriever.get_memory_context`. `FactUpdate` instances are produced by `ConflictResolver` and consumed by `MemoryPipeline._execute`.

#### Invariants

- `superseded_by = None` means active; any non-None value means inactive. Never check truthiness — check `is None`.
- `superseded_by = "DELETED:{reason}"` is the soft-delete sentinel; it is not a foreign key.
- `StewardFact.confidence` has no validation here — only `FactExtractor._parse_response` enforces the `[0.5, 1.0]` range.
- `FactUpdate.action` must be one of `"ADD"`, `"UPDATE"`, `"DELETE"`, `"NOOP"` — pipeline will silently skip unknown actions.

#### Error Handling

Dataclasses with no internal validation. Confidence capping (`min(1.0, float(confidence))`) and floor filtering (`< 0.5` dropped) happen in `FactExtractor._parse_response`, not here.

#### Configuration

Default confidence: `0.8`.

---

### MemoryConfig

**File:** `src/cli/config_models.py`

#### Behavior

Pydantic model validating the `memory:` section of `~/coach/config.yaml`. All fields are optional with defaults. The config object is accessed at runtime via `config.get("memory", {})` dict lookups in several places, or as a typed `MemoryConfig` object where injected directly.

#### Inputs / Outputs

Read by `FactExtractor.__init__`, `ConflictResolver.__init__`, `MemoryPipeline`, `RAGRetriever.get_memory_context`, and CLI memory commands.

#### Invariants

- `similarity_threshold` is stored but unused in all active code paths — it is a dead config key.
- `backfill_batch_size` is declared but not enforced — pipeline iterates entry-by-entry regardless.
- `enabled=False` gates the entire pipeline; individual components do not check it — the caller (`MemoryPipeline` invoker) must check first.

#### Caveats

- `similarity_threshold` and `backfill_batch_size` exist in the config model but have no effect. Do not rely on them for tuning.

#### Error Handling

Pydantic validation raises on type mismatches at startup.

#### Configuration

| Field | Type | Default | Purpose |
|---|---|---|---|
| `enabled` | `bool` | `True` | Gate for all memory processing; when `False`, pipeline is skipped entirely |
| `model_override` | `Optional[str]` | `None` | Override LLM model used by `FactExtractor` and `ConflictResolver` |
| `max_facts_per_entry` | `int` | `5` | Cap on facts extracted per journal entry |
| `similarity_threshold` | `float` | `0.7` | Stored on `ConflictResolver` but not actively used in any current code path |
| `auto_noop_threshold` | `float` | `0.95` | Jaccard similarity above which auto-NOOP fires without LLM call |
| `max_context_facts` | `int` | `25` | Max facts injected into the advisor prompt |
| `high_confidence_threshold` | `float` | `0.9` | Facts at or above this confidence always included in context regardless of semantic relevance |
| `backfill_batch_size` | `int` | `10` | Declared but not enforced in pipeline; pipeline iterates entry-by-entry |

---

### FactExtractor

**File:** `src/memory/extractor.py`

#### Behavior

Extracts `StewardFact` instances from text using an LLM. Four public entry points cover the supported source types. All paths converge on `_extract` (LLM call) and `_parse_response` (JSON parsing + filtering).

**Constructor:**

```python
def __init__(self, provider=None, max_facts_per_entry: int = 5)
```

Uses `create_cheap_provider()` when `provider` is `None`.

**Journal extraction:**

```python
def extract_from_journal(
    self, entry_id: str, entry_text: str, entry_metadata: dict | None = None
) -> list[StewardFact]
```

- Returns `[]` if `entry_text` is missing or `len(entry_text.strip()) < 20`
- Truncates entry text to first **3000 characters**
- Appends optional metadata (`type`, `tags`) to the LLM prompt
- Calls `_extract` with `FactSource.JOURNAL` and `max_facts = self.max_facts` (from config, default 5)

**Document extraction:**

```python
def extract_from_document(
    self, document_id: str, document_text: str, document_metadata: dict | None = None
) -> list[StewardFact]
```

- Intended for durable user-context documents such as CVs, resumes, role descriptions, and personal planning documents
- Returns `[]` if `document_text` is missing or too short to be useful for stable fact extraction
- Truncates document text before the LLM call using a higher ceiling than journal entries when needed
- Appends optional metadata such as title, filename, and collection to the extraction prompt
- Calls `_extract` with `FactSource.DOCUMENT`
- Should extract only durable user-relevant facts, not every generic sentence from the document

**Feedback extraction:**

```python
def extract_from_feedback(
    self, recommendation_id: str, feedback: str, recommendation_context: dict | None = None
) -> list[StewardFact]
```

- `feedback_type = "positive"` if `feedback in ("useful", "thumbs_up", "acted_on")` else `"negative"`
- Recommendation description truncated to **200 characters**
- Calls `_extract` with `max_facts=3` (hardcoded, ignores `self.max_facts`)
- Source: `FactSource.FEEDBACK`

**Goal extraction:**

```python
def extract_from_goal(self, goal_id: str, goal_data: dict) -> list[StewardFact]
```

- Reads `title`, `event_type` (default `"created"`), up to 5 milestone titles, and tags from `goal_data`
- Calls `_extract` with `max_facts=3` (hardcoded)
- Source: `FactSource.GOAL`

**Internal LLM call:**

```python
def _extract(self, system: str, prompt: str, source_type: FactSource, source_id: str) -> list[StewardFact]
```

- `max_tokens=800`
- On any exception: logs `fact_extraction_failed`, returns `[]`

**Response parsing:**

```python
def _parse_response(self, response: str, source_type: FactSource, source_id: str) -> list[StewardFact]
```

- Strips markdown fences (` ``` `) if present
- Parses JSON array; on `JSONDecodeError` logs `fact_parse_failed`, returns `[]`
- Non-list response → `[]`
- Per item: skips if `category not in VALID_CATEGORIES`, or `confidence < 0.5`, or `fact_text` is empty
- Caps confidence: `min(1.0, float(confidence))`
- IDs: `uuid4().hex[:16]`
- Enforces `items[:self.max_facts]` slice after filtering

#### Inputs / Outputs

Inputs: raw text strings, source IDs, optional metadata dicts.
Outputs: `list[StewardFact]` — may be empty on extraction failure, short text, or all-filtered results.

#### Invariants

- `extract_from_journal()` returns `[]` on short content (< 20 chars) without an LLM call.
- `extract_from_document()` is source-aware and should bias toward durable user facts rather than generic document summarization.
- `extract_from_feedback()` always uses `max_facts=3` regardless of `self.max_facts`.
- Content is always truncated before the LLM call — LLM never sees more than 3000 chars of journal text.
- IDs are `uuid4().hex[:16]` — not deterministic; re-extraction of the same entry produces different IDs.
- `max_facts` cap is applied AFTER filtering — the slice enforces the limit on valid items only.

#### Error Handling

All LLM and parse exceptions are caught and return `[]`. Individual items failing validation (bad category, low confidence, empty text) are silently dropped. No exception propagates to the caller.

#### Configuration

LLM confidence rubric embedded in `_EXTRACTION_SYSTEM` prompt:

| Confidence Range | Meaning |
|---|---|
| 0.9–1.0 | User explicitly stated |
| 0.7–0.89 | Strong inference |
| 0.5–0.69 | Weak signal |
| < 0.5 | Do not extract (filtered out in `_parse_response`) |

---

### ConflictResolver

**File:** `src/memory/resolver.py`

#### Behavior

Determines the correct action for each candidate fact by comparing it against the existing fact store. A fast Jaccard similarity check handles near-duplicates without an LLM call; ambiguous cases are delegated to the LLM.

**Constructor:**

```python
def __init__(
    self,
    fact_store: FactStore,
    provider=None,
    similarity_threshold: float = 0.7,
    auto_noop_threshold: float = 0.95,
)
```

Uses `create_cheap_provider()` when `provider` is `None`. `similarity_threshold` is stored as an attribute but not used in any active code path.

**Batch resolution:**

```python
def resolve(self, candidates: list[StewardFact]) -> list[FactUpdate]
```

For each candidate: calls `store.search(candidate.text, limit=3)`, filters out the candidate itself by ID, then calls `resolve_single`.

**Single resolution:**

```python
def resolve_single(self, candidate: StewardFact, similar: list[StewardFact]) -> FactUpdate
```

- `similar` empty → `FactUpdate(action="ADD", candidate=candidate.text)`
- Auto-NOOP: if `_text_similarity(candidate.text, similar[0].text) > 0.95` AND `candidate.category == similar[0].category` → `FactUpdate(action="NOOP", reasoning="Near-duplicate of existing fact")`
- Otherwise: calls `_llm_resolve`; on any exception → `FactUpdate(action="ADD")` with no reasoning

**LLM resolution:**

```python
def _llm_resolve(self, candidate: StewardFact, similar: list[StewardFact]) -> FactUpdate
```

- Sends up to 3 existing similar facts (ID, date, text, category, confidence) to the LLM
- `max_tokens=200`
- Expected response: `{"action": "ADD|UPDATE|DELETE|NOOP", "existing_id": "<id or null>", "reasoning": "<one sentence>"}`
- On JSON parse failure → `FactUpdate(action="ADD", reasoning="Parse failed")`
- Unknown `action` string → coerced to `"ADD"`

**Jaccard similarity formula:**

```python
@staticmethod
def _text_similarity(a: str, b: str) -> float
```

`|intersection(tokens_a, tokens_b)| / |union(tokens_a, tokens_b)|` on lowercased whitespace-split tokens. Returns `0.0` if either string has no tokens.

Auto-NOOP fires when this value exceeds `0.95` (from `MemoryConfig.auto_noop_threshold`).

#### Inputs / Outputs

Input: `list[StewardFact]` candidates from `FactExtractor`.
Output: `list[FactUpdate]` with one entry per candidate.

#### Invariants

- Auto-NOOP requires BOTH Jaccard ≥ 0.95 AND matching `category` — either condition alone is insufficient.
- `resolve()` always fetches up to 3 similar facts from the store — batch size is hardcoded, not configurable.
- On any LLM failure, action defaults to `"ADD"` — the safe/additive choice.
- `similarity_threshold` attribute is stored but never consulted in any code path.
- `resolve()` outputs one `FactUpdate` per input candidate — length of output equals length of input.

#### Caveats

- The auto-NOOP Jaccard threshold (0.95) is hardcoded at call site, not read from `MemoryConfig.auto_noop_threshold` at construction time — config changes after construction have no effect.

#### Error Handling

LLM call exceptions in `resolve_single` are caught; default `ADD` action is returned. JSON parse failures in `_llm_resolve` return `ADD` with `reasoning="Parse failed"`. Unknown action strings are coerced to `"ADD"`.

#### Configuration

| Parameter | Default | Source |
|---|---|---|
| `auto_noop_threshold` | `0.95` | `MemoryConfig.auto_noop_threshold` |
| `similarity_threshold` | `0.7` | `MemoryConfig.similarity_threshold` (stored, unused) |
| `store.search limit` | `3` | Hardcoded in `resolve()` |
| `_llm_resolve max_tokens` | `200` | Hardcoded |

---

### FactStore

**File:** `src/memory/store.py`

#### Behavior

Dual-backend persistence: SQLite as the authoritative store, ChromaDB as an optional semantic search index. ChromaDB is entirely optional — if `chroma_dir=None` or init fails, all operations degrade gracefully.

**Constructor:**

```python
def __init__(self, db_path: str | Path, chroma_dir: str | Path | None = None)
```

Creates parent directories, initializes SQLite in WAL mode. ChromaDB collection is lazy-initialized on first access.

**SQLite schema (`steward_facts` table):**

| Column | Type | Notes |
|---|---|---|
| `id` | `TEXT PRIMARY KEY` | `uuid4().hex[:16]` |
| `text` | `TEXT NOT NULL` | |
| `category` | `TEXT NOT NULL` | `FactCategory` value |
| `source_type` | `TEXT NOT NULL` | `FactSource` value |
| `source_id` | `TEXT NOT NULL` | |
| `confidence` | `REAL NOT NULL DEFAULT 0.8` | |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | |
| `superseded_by` | `TEXT` | `NULL` = active; fact ID = updated; `"DELETED:{reason}"` = deleted |

Indexes: `idx_facts_active (superseded_by)`, `idx_facts_source (source_type, source_id)`, `idx_facts_category (category)`.

**ChromaDB collection:** name `"steward_facts"`, `hnsw:space = "cosine"`. Init failure is silently swallowed (logs `chroma_init_failed` warning; `_chroma` property returns `None`).

**CRUD:**

`add(fact: StewardFact) -> StewardFact` — Auto-generates `id = uuid4().hex[:16]` if `fact.id` is falsy. Inserts into SQLite, then upserts into ChromaDB with `category` and `confidence` metadata. ChromaDB upsert failure is swallowed (logs `chroma_upsert_failed`).

`update(fact_id: str, new_text: str, new_source_id: str) -> StewardFact` — Raises `ValueError` if `fact_id` not found. Sets `superseded_by = new_id` on the old row, deletes old fact from ChromaDB, creates a new `StewardFact` inheriting `category`, `source_type`, `confidence`, and `created_at`, with `updated_at = now`, then calls `add`.

`delete(fact_id: str, reason: str = "manual") -> None` — Soft-delete only: sets `superseded_by = "DELETED:{reason}"`. Removes from ChromaDB. Does not verify fact existence before writing.

`get(fact_id: str) -> StewardFact | None` — Returns `None` if not found.

**Search:**

`search(query: str, limit: int = 10, categories: list[FactCategory] | None = None) -> list[StewardFact]`

Primary path (ChromaDB):
1. Fetches all active IDs; returns `[]` if none
2. Queries `min(limit * 2, len(active_ids))` results from ChromaDB with optional category where-clause
3. Filters to active IDs only, hydrates from SQLite

Falls back to `_keyword_search` on any exception (logs `chroma_search_failed`).

Fallback (`_keyword_search`): SQL `LIKE %query%` on `text`, `superseded_by IS NULL`, ordered by `confidence DESC`.

Category filter encoding: single value → `{"category": val}`, multiple values → `{"category": {"$in": [...]}}`.

**Bulk read:**

`get_all_active() -> list[StewardFact]` — `WHERE superseded_by IS NULL ORDER BY confidence DESC`.

`get_by_source(source_type, source_id) -> list[StewardFact]` — Returns all facts including superseded.

`get_by_category(category, active_only: bool = True) -> list[StewardFact]` — `active_only=True` adds `superseded_by IS NULL`.

**History:**

`get_history(fact_id: str) -> list[StewardFact]` — Walks backward through the supersession chain by following `superseded_by` pointers in reverse. Uses a `seen` set to guard infinite loops. Returns chain in chronological order (oldest first).

**Stats:**

`get_stats() -> dict` — Returns `{"total_active": int, "total_superseded": int, "by_category": {cat: count}}`. `total_superseded` counts rows where `superseded_by IS NOT NULL` (includes `"DELETED:..."` entries).

**Source cleanup:**

`delete_by_source(source_type, source_id) -> int` — Fetches all facts from source (including superseded), soft-deletes only those where `superseded_by is None` with reason `"source_reextract:{source_id}"`. Returns `len(facts)` (total fetched, not count newly deleted — a known misleading return value).

**Reset:**

`reset() -> int` — Hard-deletes ALL rows from SQLite and removes all IDs from ChromaDB. Returns count before deletion. This is the only hard-delete path.

#### Inputs / Outputs

Inputs: `StewardFact` objects, string queries, fact IDs.
Outputs: `StewardFact` objects or `None`; counts for stats/reset.

#### Invariants

- SQLite is authoritative; ChromaDB is an optional semantic index. All reads fall back to SQLite.
- `delete()` is soft-delete only — rows remain in SQLite with `superseded_by = "DELETED:{reason}"`.
- `reset()` is the ONLY hard-delete path — all other deletes are soft.
- `update()` creates a new fact (new ID) rather than modifying in place — the old fact is superseded.
- `add()` auto-generates an ID when `fact.id` is falsy — callers need not pre-generate IDs.
- `delete_by_source()` returns `len(fetched_facts)` (all facts from source), NOT the count of rows newly soft-deleted.
- `get_by_source()` returns ALL facts including superseded — not filtered to active only.

#### Caveats

- `delete_by_source()` return value is misleading: it returns the total count of facts fetched from the source, not the count actually soft-deleted (which excludes already-superseded rows).

#### Error Handling

ChromaDB failures on init, upsert, delete, and search are all silently swallowed with warning logs. `update` raises `ValueError` on unknown `fact_id`. `delete` and `delete_by_source` do not raise on missing IDs.

#### Configuration

| Parameter | Value | Notes |
|---|---|---|
| SQLite journal mode | WAL | Set on init |
| ChromaDB distance metric | cosine | `hnsw:space = "cosine"` |
| ChromaDB collection name | `"steward_facts"` | Fixed |
| Default search limit | `10` | `search()` parameter default |
| Default delete reason | `"manual"` | `delete()` parameter default |

---

### MemoryPipeline

**File:** `src/memory/pipeline.py`

#### Behavior

Orchestrates the extract → resolve → store sequence. Provides four entry points for different event types and a `backfill` method for processing historical journal data.

**Constructor:**

```python
def __init__(
    self,
    store: FactStore,
    extractor: FactExtractor | None = None,
    resolver: ConflictResolver | None = None,
)
```

Defaults to `FactExtractor()` and `ConflictResolver(store)` when not injected.

**Journal entry processing:**

```python
def process_journal_entry(
    self, entry_id: str, entry_text: str, entry_metadata: dict | None = None
) -> list[FactUpdate]
```

Returns `[]` if no candidates extracted. Logs `memory.journal_processed` with `entry_id`, extracted count, and set of actions taken.

**Feedback processing:**

```python
def process_feedback(
    self, recommendation_id: str, feedback: str, context: dict | None = None
) -> list[FactUpdate]
```

Logs `memory.feedback_processed`.

**Document processing:**

```python
def process_document(
    self, document_id: str, document_text: str, document_metadata: dict | None = None
) -> list[FactUpdate]
```

Runs the same extract → resolve → store path for uploaded Library documents. Intended to be called after PDF text extraction succeeds. Logs `memory.document_processed`.

**Goal event processing:**

```python
def process_goal_event(
    self, goal_id: str, event_type: str, goal_data: dict
) -> list[FactUpdate]
```

Merges `event_type` into a copy of `goal_data` before passing to extractor. Logs `memory.goal_processed`.

**Backfill:**

```python
def backfill(self, journal_entries: list[dict]) -> dict
```

- Sorts entries chronologically by `entry.get("created", "") or ""`
- Skips entries where `content` is missing or `len(content.strip()) < 20`
- Entry dict expected keys: `path` or `id` (used as `entry_id`), `content`, `type`, `tags`, `created`
- Returns `{"entries_processed": int, "facts_extracted": int, "facts_stored": int}`
- Logs `memory.backfill_complete`
- `backfill_batch_size` from `MemoryConfig` is declared but not enforced; pipeline iterates entry-by-entry

**Re-extraction:**

```python
def reextract_entry(
    self, entry_id: str, entry_text: str, entry_metadata: dict | None = None
) -> list[FactUpdate]
```

Calls `store.delete_by_source(FactSource.JOURNAL, entry_id)` to soft-delete existing facts, then calls `process_journal_entry`.

Document re-extraction follows the same pattern using `FactSource.DOCUMENT` when a document is reprocessed or replaced.

**Internal execution (`_execute`):**

Builds a `candidate_map` keyed by `candidate.text`:
- `ADD` → `store.add(candidate)`, increments stored count
- `UPDATE` → `store.update(existing_id, new_text, candidate.source_id)`, increments stored count
- `DELETE` → `store.delete(existing_id, reason=update.reasoning)`
- `NOOP` → no-op

Returns count of stored facts.

#### Inputs / Outputs

Inputs: text strings, event metadata dicts, lists of journal entry dicts for backfill.
Outputs: `list[FactUpdate]` per entry, or summary dict for backfill.

#### Invariants

- `process_journal_entry()` returns `[]` when no candidates extracted — not an error condition.
- `process_document()` returns `[]` when extracted document text does not contain durable user facts — not an error condition.
- `backfill()` processes entries chronologically (sorted by `created` ascending) — ensures consistent supersession order.
- `reextract_entry()` always soft-deletes existing facts before re-extracting — never creates duplicates for the same source.
- `_execute()` maps one `FactUpdate` per candidate; `candidate_map` is keyed by `candidate.text`, not ID — duplicate texts within a batch may collide.
- Pipeline does not check `MemoryConfig.enabled` — callers must gate on it.

#### Error Handling

No top-level exception handling in `MemoryPipeline` itself; errors propagate from store/extractor/resolver. Individual component failures return empty lists or safe defaults as documented in their respective sections.

#### Configuration

Inherits all thresholds from `FactExtractor` and `ConflictResolver`, which read from `MemoryConfig`.

---

### Context Injection via RAGRetriever.get_memory_context

**File:** `src/advisor/rag.py`

#### Behavior

Produces a `<user_memory>` XML block from the fact store for injection into advisor prompts.

```python
def get_memory_context(self, query: str = "") -> str
```

Returns `""` if `self._fact_store` is `None`.

**Retrieval strategy:**
1. Semantic search on `query`, up to `max_context_facts` results
2. Fetch all active facts with `confidence >= high_confidence_threshold` (0.9)
3. Merge both sets, dedup by fact ID, high-confidence facts first, cap total at `max_context_facts`

**Output XML format:**

```xml
<user_memory>
## Current Context
- fact text

## Goal Context
- fact text

## Preferences
- fact text

## Skills
- fact text

## Constraints
- fact text

## Patterns
- fact text
</user_memory>
```

Facts within each section are sorted by `confidence` descending. Sections with no facts are omitted.

**Display order:** Current Context (`context`) → Goal Context (`goal_context`) → Preferences (`preference`) → Skills (`skill`) → Constraints (`constraint`) → Patterns (`pattern`)

**Injection gate:** Only injected when `cfg.get("inject_memory", False)` is truthy in the RAG config. Defaults to not injecting.

#### Inputs / Outputs

Input: optional `query` string for semantic relevance ranking.
Output: `<user_memory>...</user_memory>` XML string, or `""` on failure or missing store.

#### Invariants

- Returns `""` (not `None`) when `_fact_store is None` or any exception occurs — always safe to concatenate.
- High-confidence facts (≥ 0.9) are always included regardless of semantic relevance to `query`.
- Total injected facts are capped at `max_context_facts=25` — semantic + high-confidence facts merged and truncated.
- Injection is gated by `cfg.get("inject_memory", False)` — disabled by default.
- Sections with no facts are omitted from the XML output — the XML block may be minimal.

#### Error Handling

Any exception during retrieval or formatting is caught, logged at DEBUG as `memory_context_failed`, and `""` is returned. Prompt construction is never interrupted by memory failures.

#### Configuration

| Parameter | Default | Source |
|---|---|---|
| `max_context_facts` | `25` | `MemoryConfig.max_context_facts` / `memory_config.get("max_context_facts", 25)` |
| `high_confidence_threshold` | `0.9` | `MemoryConfig.high_confidence_threshold` / `memory_config.get("high_confidence_threshold", 0.9)` |
| `inject_memory` | `False` | RAG config key `cfg.get("inject_memory", False)` |
---

## Test Expectations

- `FactExtractor.extract_from_journal()`: mock cheap LLM; verify `[]` on short content; verify confidence < 0.5 items filtered; verify max_facts cap; verify markdown fence stripping.
- `FactExtractor._parse_response()`: verify non-list JSON → `[]`; verify unknown category dropped; verify confidence cap at 1.0.
- `ConflictResolver.resolve_single()`: verify auto-NOOP fires at Jaccard ≥ 0.95 with matching category; verify LLM called for ambiguous cases; verify fallback ADD on LLM exception.
- `ConflictResolver._text_similarity()`: unit-test Jaccard formula with known token sets; verify 0.0 on empty strings.
- `FactStore.add()`: verify ChromaDB upsert failure is swallowed; verify ID auto-generated when falsy.
- `FactStore.update()`: verify `ValueError` on unknown fact_id; verify old row superseded + new row created.
- `FactStore.delete()`: verify soft-delete only (superseded_by set, row not removed).
- `FactStore.reset()`: verify all rows deleted (hard-delete only path).
- `FactStore.delete_by_source()`: note the misleading return value — returns `len(fetched)` not `len(newly_deleted)`.
- `FactStore.search()`: verify fallback to `_keyword_search` on ChromaDB exception.
- `MemoryPipeline.backfill()`: verify chronological ordering; verify short entries skipped.
- `FactExtractor.extract_from_document()`: verify generic or text-poor documents can yield `[]`, and document metadata is included in the prompt shape.
- `MemoryPipeline.process_document()`: verify document-derived facts are stored with `FactSource.DOCUMENT` and can be superseded by reprocessing the same document.
- `get_memory_context()`: verify empty string returned when `_fact_store` is None; verify high-confidence facts included regardless of semantic relevance; verify section ordering in XML output.
- Mocks required: LLM provider (cheap), ChromaDB client, SQLite (or use tmp path).

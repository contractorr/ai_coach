# Hybrid Retrieval

## Overview

Upgrades the advisor's retrieval pipeline with three capabilities: sub-question decomposition for complex queries, entity graph traversal for relational queries, and unified hybrid search in the agentic tool path. All changes are internal to the retrieval layer — the advisor prompt interface (`AskContext`) and response format are unchanged.

## Dependencies

**Depends on:** `intelligence/search` (IntelSearch, hybrid_search), `intelligence/entity_store` (EntityStore), `advisor/rag` (RAGRetriever), `llm` (cheap LLM for decomposition + classification)
**Depended on by:** `advisor/engine` (AdvisorEngine.ask_result), `advisor/agentic` (tool definitions), `web/routes/advisor` (no changes needed — transparent)

---

## Components

### QueryAnalyzer

**File:** `src/advisor/query_analyzer.py`
**Status:** Draft

#### Behavior

Classifies incoming queries to determine retrieval mode. Two-tier approach: fast heuristic first, optional cheap LLM fallback for ambiguous cases.

Constructor:
```python
QueryAnalyzer(
    llm: LLMProvider | None = None,      # cheap LLM, None = heuristic-only mode
    entity_store: EntityStore | None = None,
)
```

Classification flow:
1. **Entity check:** If `entity_store` is provided, call `entity_store.search_entities(query)`. If matches found, set `has_entities = True`.
2. **Complexity heuristic:** Score the query on:
   - Contains comparison words ("compare", "versus", "vs", "difference between", "how does X relate to Y") → +2
   - Contains conjunctions joining distinct topics ("and", "but also", "as well as") → +1
   - Contains multiple named entities (capitalized multi-word sequences) → +1
   - Word count > 20 → +1
   - Score ≥ 2 → `is_complex = True`
3. **Mode selection:**
   - `is_complex=False, has_entities=False` → `RetrievalMode.SIMPLE`
   - `is_complex=True, has_entities=False` → `RetrievalMode.DECOMPOSED`
   - `is_complex=False, has_entities=True` → `RetrievalMode.ENTITY`
   - `is_complex=True, has_entities=True` → `RetrievalMode.COMBINED`
4. **LLM fallback (optional):** If heuristic score == 1 (ambiguous) and LLM is available, call cheap LLM with `"Is this query complex enough to benefit from being split into sub-questions? Reply YES or NO."` Single-token response.

```python
class RetrievalMode(Enum):
    SIMPLE = "simple"
    DECOMPOSED = "decomposed"
    ENTITY = "entity"
    COMBINED = "combined"
```

#### Inputs / Outputs

```python
def analyze(self, query: str) -> QueryAnalysis

@dataclass
class QueryAnalysis:
    mode: RetrievalMode
    matched_entities: list[dict]    # entity dicts from EntityStore, empty if none
    complexity_score: int           # heuristic score, 0-5
```

#### Invariants

- Heuristic path adds zero LLM latency.
- LLM fallback is at most one cheap LLM call with < 50 tokens.
- If `entity_store` is None, entity modes are never selected.
- If `llm` is None, only heuristic classification is used.

Additional retrieval notes:

- `compute_dynamic_weight()` may apply a small query-aligned adjustment from recommendation engagement categories after the base journal-vs-intel ratio is computed.
- Memory selection may apply a temporary ranking bonus to facts whose source entries belong to strong recurring threads.

#### Error Handling

| Trigger | Action |
|---------|--------|
| entity_store.search_entities raises | Log warning, treat as has_entities=False |
| LLM fallback times out | Fall back to heuristic result |
| LLM returns unexpected response | Treat as heuristic result |

---

### QueryDecomposer

**File:** `src/advisor/query_decomposer.py`
**Status:** Draft

#### Behavior

Splits a complex query into 2–4 sub-questions using the cheap LLM.

Constructor:
```python
QueryDecomposer(
    llm: LLMProvider,    # cheap LLM
    max_sub_questions: int = 4,
)
```

Prompt template:
```
Split this question into 2-{max} independent sub-questions that together cover the full scope.
Each sub-question should be self-contained and searchable.

Question: {query}

Return JSON array of strings. No explanations.
```

#### Inputs / Outputs

```python
async def decompose(self, query: str) -> list[str]
    # Returns 2-4 sub-question strings.
    # On any failure, returns [query] (original query as single-element list).
```

#### Invariants

- Always returns at least 1 sub-question (the original query as fallback).
- Never returns more than `max_sub_questions`.
- Deduplicates sub-questions (case-insensitive exact match).
- Uses cheap LLM only.

#### Error Handling

| Trigger | Action |
|---------|--------|
| LLM returns non-JSON | Return [query] |
| LLM returns empty array | Return [query] |
| LLM returns > max_sub_questions | Truncate to max |
| LLM timeout | Return [query] |

---

### EntityRetriever

**File:** `src/advisor/entity_retriever.py`
**Status:** Draft

#### Behavior

Retrieves entity graph context for a query. Finds matching entities, their relationships, and linked intel items. Formats as structured XML for prompt injection.

Constructor:
```python
EntityRetriever(
    entity_store: EntityStore,
    max_entities: int = 5,
    max_relationships_per_entity: int = 10,
    max_items_per_entity: int = 3,
    max_chars: int = 1600,    # 20% of default 8000 budget
)
```

#### Inputs / Outputs

```python
def retrieve(self, matched_entities: list[dict], query: str) -> str
    # matched_entities: from QueryAnalyzer.analyze().matched_entities
    # Returns XML string or empty string if no entities/extraction disabled.
```

Output format:
```xml
<entity_context>
  <entity name="OpenAI" type="Company">
    <relationships>
      <rel type="COMPETES_WITH" target="Anthropic" evidence="Both building frontier LLMs"/>
      <rel type="ACQUIRED" target="Rockset" evidence="Acquired for vector DB capabilities"/>
    </relationships>
    <recent_items count="3">
      <item source="hackernews" title="..." summary="..." />
    </recent_items>
  </entity>
</entity_context>
```

#### Invariants

- Output never exceeds `max_chars`. Entities are added in order of `item_count` (most-referenced first); truncation drops lowest-count entities.
- Empty `matched_entities` → returns empty string immediately.
- Relationships sorted by `created_at` desc (most recent first).
- Items sorted by `scraped_at` desc.

#### Error Handling

| Trigger | Action |
|---------|--------|
| EntityStore queries fail | Log warning, return empty string |
| Single entity fetch fails | Skip entity, continue with rest |

---

### EnhancedRAGRetriever

**File:** `src/advisor/rag.py` (modifications to existing `RAGRetriever`)
**Status:** Draft

#### Behavior

Extends `RAGRetriever` with new retrieval modes. The existing `get_combined_context()` method is preserved as the `SIMPLE` mode path. New methods handle decomposed and entity-augmented retrieval.

New constructor params (all optional, backward-compatible):
```python
RAGRetriever(
    ...,                          # all existing params
    entity_store: EntityStore | None = None,
    query_analyzer: QueryAnalyzer | None = None,
    query_decomposer: QueryDecomposer | None = None,
    entity_retriever: EntityRetriever | None = None,
)
```

New public method:
```python
def get_enhanced_context(self, query: str) -> AskContext
    # 1. analyzer.analyze(query) → QueryAnalysis
    # 2. Dispatch by mode:
    #    SIMPLE → existing get_combined_context() + empty entity_context
    #    DECOMPOSED → _decomposed_retrieval(query)
    #    ENTITY → existing get_combined_context() + entity_retriever.retrieve()
    #    COMBINED → _decomposed_retrieval(query) + entity_retriever.retrieve()
    # 3. Build AskContext with journal, intel, profile, memory, thoughts, documents, entity_context
```

`_decomposed_retrieval(query)`:
```python
async def _decomposed_retrieval(self, query: str) -> tuple[str, str]:
    sub_questions = await self.query_decomposer.decompose(query)
    # Run get_combined_context(sub_q) for each sub_q concurrently
    # Merge results: parse formatted lines, dedup by URL, re-rank by occurrence count
    # Re-truncate to budget
    return (merged_journal_context, merged_intel_context)
```

**AskContext addition:**
```python
@dataclass
class AskContext:
    journal: str
    intel: str
    profile: str
    memory: str = ""
    thoughts: str = ""
    documents: str = ""
    entity_context: str = ""    # NEW FIELD
```

**Budget allocation (8000 chars default):**

| Mode | Journal | Intel | Entity |
|------|---------|-------|--------|
| SIMPLE | 70% | 30% | 0% |
| DECOMPOSED | 70% | 30% | 0% |
| ENTITY | 56% | 24% | 20% |
| COMBINED | 56% | 24% | 20% |

Entity ceiling is 20% of total budget. Remaining 80% uses existing journal:intel ratio.

#### Invariants

- `get_combined_context()` behavior is unchanged — backward compatible.
- `get_enhanced_context()` is the new entry point; `build_context_for_ask()` calls it when components are available.
- Total context never exceeds `max_context_chars` regardless of mode.
- If all new components are None, `get_enhanced_context()` falls back to `get_combined_context()`.

#### Error Handling

| Trigger | Action |
|---------|--------|
| QueryAnalyzer fails | Fall back to SIMPLE mode |
| Decomposition fails | Fall back to SIMPLE mode (single query) |
| Entity retrieval fails | Continue with text-only context |
| Any sub-question search fails | Merge results from successful searches |

---

### Agentic tool upgrades

**File:** `src/advisor/tools.py` (modifications)
**Status:** Draft

#### Changes to existing `intel_search` tool

Current: calls `self.components["intel_storage"].search(query)` (LIKE search).

New: calls `self.components["intel_search"].hybrid_search(query, n_results=arguments.get("limit", 10))` when `intel_search` component is available, falls back to current LIKE behavior.

#### New `intel_entity_search` tool

```python
{
    "name": "intel_entity_search",
    "description": "Search for entities (companies, people, technologies) and their relationships in the intelligence database",
    "parameters": {
        "query": {"type": "string", "description": "Entity name or search term"},
        "type": {"type": "string", "description": "Entity type filter", "enum": ["Company", "Person", "Technology", "Product", "Sector"]},
        "limit": {"type": "integer", "default": 5}
    },
    "required": ["query"]
}
```

Handler:
```python
def _intel_entity_search(self, arguments: dict) -> str:
    entities = self.components["entity_store"].search_entities(
        query=arguments["query"],
        entity_type=arguments.get("type"),
        limit=arguments.get("limit", 5),
    )
    for entity in entities:
        entity["relationships"] = self.components["entity_store"].get_relationships(entity["id"])
    return json.dumps(entities)[:4000]
```

Only registered when `entity_store` is present in components.

---

### Prompt template additions

**File:** `src/advisor/prompts.py` (modifications)
**Status:** Draft

#### Entity context injection

When `AskContext.entity_context` is non-empty, it is injected into the user prompt between the intel context and the question:

```
{journal_context}

{intel_context}

{entity_context}

Question: {question}
```

System prompt addition (appended to existing system prompts when entity context is present):
```
You have access to structured entity and relationship data from a knowledge graph.
Use entity relationships to answer questions about connections, competition, and trends.
Cite specific relationships when relevant.
```

---

### RRF Utility

**File:** `src/services/ranking.py`
**Status:** Draft

#### Behavior

Shared Reciprocal Rank Fusion implementation replacing three ad-hoc copies.

```python
def rrf_fuse(
    result_lists: list[list[dict]],
    weights: list[float],
    key_fn: Callable[[dict], str],
    k: int = 60,
) -> list[dict]:
```

For each result list `i`, each item at position `rank`:
`score[key_fn(item)] += weights[i] * 1.0 / (k + rank + 1)`

Returns items sorted by descending score. When duplicate keys appear, the first occurrence's dict is kept.

#### Invariants

- `len(result_lists) == len(weights)` (asserted)
- `k >= 0` (smoothing constant; default 60 per standard RRF)
- Empty result lists contribute no scores
- Items with empty string keys are assigned unique keys via `str(id(item))`

---

### Temporal Expression Parser

**File:** `src/services/temporal.py`
**Status:** Draft

#### Behavior

Regex-based temporal expression detection and parsing. Zero LLM calls.

```python
@dataclass
class TemporalFilter:
    start: datetime | None
    end: datetime | None
    original_expr: str

def parse_temporal_expr(query: str) -> TemporalFilter | None:
def strip_temporal(query: str, temporal_filter: TemporalFilter) -> str:
```

Supported patterns (case-insensitive):
- `"last N days/weeks/months/years"` → `start = now - N*period`
- `"last week"` → `start = now - 7d`
- `"last month"` → `start = now - 30d`
- `"past N days/weeks/months"` → same as "last N ..."
- `"yesterday"` → `start = yesterday 00:00, end = yesterday 23:59`
- `"today"` → `start = today 00:00`
- `"this week"` → `start = Monday of current week`
- `"this month"` → `start = 1st of current month`
- `"since <month>"` → `start = 1st of named month in current/previous year`
- `"in <year>"` → `start = Jan 1 of year, end = Dec 31 of year`
- `"recently"` / `"recent"` → `start = now - 7d`
- `"before <date>"` → `end = parsed date`
- `"after <date>"` → `start = parsed date`

`strip_temporal()` removes the matched expression from the query and strips extra whitespace.

#### Error Handling

| Trigger | Action |
|---------|--------|
| No temporal expression detected | Return None |
| Ambiguous/unparseable date | Return None |
| Multiple temporal expressions | Use first match |

---

### Token Counter

**File:** `src/services/tokens.py`
**Status:** Draft

```python
def count_tokens(text: str) -> int:
```

Uses tiktoken `cl100k_base` encoding. Encoding instance cached at module level. Falls back to `len(text) // 4` if tiktoken unavailable.

---

### Cross-Encoder Reranker

**File:** `src/services/reranker.py`
**Status:** Draft

```python
class CrossEncoderReranker:
    MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self) -> None:
        self.available: bool  # True if sentence-transformers installed

    def rerank(self, query: str, passages: list[str], top_k: int = 10) -> list[int]:
        # Returns sorted indices into passages list
```

#### Invariants

- `__init__` never raises. Sets `self.available = False` on ImportError.
- `rerank()` returns `list(range(len(passages)))` unchanged when `not self.available`.
- Empty passages → empty result.

---

### Temporal Search Extensions

**Journal:** `src/journal/search.py` — new `temporal_search()` method:
```python
def temporal_search(
    self,
    query: str,
    start: datetime | None = None,
    end: datetime | None = None,
    n_results: int = 5,
) -> list[dict]:
```
Runs `hybrid_search(query, n_results=n_results*3)` then post-filters by `created` date.

**Intel storage:** `src/intelligence/scraper.py` — new `get_by_date_range()`:
```python
def get_by_date_range(
    self,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 50,
) -> list[dict]:
```
SQL: `WHERE COALESCE(published, scraped_at) BETWEEN ? AND ?`

**Intel search:** `src/intelligence/search.py` — new `temporal_search()`:
```python
def temporal_search(
    self,
    query: str,
    start: datetime | None = None,
    end: datetime | None = None,
    n_results: int = 10,
) -> list[dict]:
```
Gets date-filtered items from storage, then runs semantic reranking on subset.

---

### QueryAnalyzer Extensions

**File:** `src/advisor/query_analyzer.py`

New field on `QueryAnalysis`:
```python
temporal_filter: TemporalFilter | None = None
```

In `analyze()`, call `parse_temporal_expr(query)` before complexity scoring. If temporal filter detected, set on result and use `strip_temporal()` for subsequent analysis.

---

### RAGRetriever Token Budget Refactor

**File:** `src/advisor/rag.py`

New constructor params:
```python
max_context_tokens: int | None = None  # default: derive from max_context_chars // 4
reranker: CrossEncoderReranker | None = None
```

`_get_text_context_for_budget` changes:
- Accept `total_tokens` instead of `total_chars`
- Pass `max_tokens` to journal/intel context methods
- Internal budget tracking uses `count_tokens()` instead of `len()`

`get_enhanced_context` changes:
- If `analysis.temporal_filter` is set, use `journal.temporal_search()` / `intel_search.temporal_search()` with start/end
- If `self.reranker` and `self.reranker.available`, apply reranking as final pass

---

## Cross-Cutting Concerns

**Backward compatibility:** All new components are optional. When not configured, the entire retrieval path falls back to current behavior. No existing tests should break.

**Latency budget:** Sub-question decomposition adds one cheap LLM call (~200ms). Entity lookup adds one SQLite query (~5ms). Parallel sub-question searches run concurrently. Worst case (COMBINED mode): ~200ms decomposition + parallel searches (same as single search if IO-bound) + 5ms entity lookup.

**Concurrency:** `_decomposed_retrieval` uses `asyncio.gather` for parallel sub-question searches. `RAGRetriever` methods are currently sync — will need `async` wrappers or `loop.run_in_executor` for the concurrent path.

**Config integration:**

| Key | Default | Source |
|-----|---------|--------|
| `retrieval.mode` | `"auto"` | config.yaml |
| `retrieval.decomposition_enabled` | `true` | config.yaml |
| `retrieval.entity_budget_ratio` | `0.2` | config.yaml |
| `retrieval.max_sub_questions` | `4` | config.yaml |
| `retrieval.complexity_threshold` | `2` | config.yaml |

`retrieval.mode` overrides: `"auto"` (default), `"simple"`, `"decomposed"`, `"entity"`, `"combined"`.

## Test Expectations

**QueryAnalyzer:**
- Simple query ("latest AI news") → SIMPLE mode
- Complex query ("compare OpenAI and Anthropic hiring trends vs product releases") → DECOMPOSED or COMBINED
- Query mentioning known entity → ENTITY or COMBINED mode
- No entity_store → entity modes never selected
- Heuristic score boundary cases (score=1 with/without LLM fallback)

**QueryDecomposer:**
- Known complex query → 2-4 sub-questions
- LLM failure → returns [original_query]
- Duplicate sub-questions are deduplicated
- Mock: LLM calls

**EntityRetriever:**
- Known entities → formatted XML with relationships and items
- Empty entity list → empty string
- Output respects max_chars budget
- Mock: EntityStore

**EnhancedRAGRetriever:**
- SIMPLE mode → identical to current get_combined_context()
- DECOMPOSED mode → merged results from sub-questions, deduped by URL
- ENTITY mode → text context + entity XML block
- COMBINED mode → both decomposed + entity context
- Budget never exceeded in any mode
- All-None components → falls back to get_combined_context()
- Mock: LLM calls, IntelSearch, EntityStore, JournalSearch

**Agentic tools:**
- `intel_search` uses hybrid_search when IntelSearch component available
- `intel_search` falls back to LIKE when IntelSearch unavailable
- `intel_entity_search` returns entities with relationships
- `intel_entity_search` not registered when entity_store missing
- Mock: IntelSearch, EntityStore

**RRF Utility (Phase 2):**
- Two overlapping lists with equal weights → items in both lists score higher
- Disjoint lists → interleaved by individual scores
- Custom k parameter changes ranking spread
- Empty result lists handled gracefully

**Temporal Parser (Phase 2):**
- "last 3 days" → start = now - 3d, end = None
- "since January" → start = Jan 1, end = None
- "yesterday" → start/end = yesterday bounds
- "recently" → start = now - 7d
- No temporal expression → returns None
- strip_temporal removes matched expression from query

**Temporal Search (Phase 2):**
- Journal temporal_search returns only entries within date range
- Intel temporal_search filters by COALESCE(published, scraped_at)
- Items with NULL published fall back to scraped_at
- QueryAnalyzer sets temporal_filter on QueryAnalysis
- RAGRetriever routes to temporal search methods when filter present

**Token Budgets (Phase 2):**
- count_tokens returns accurate token count via tiktoken
- RAGRetriever respects token budget, not char budget
- Backward compat: max_context_chars still accepted (divided by 4)

**Reranker (Phase 2):**
- CrossEncoderReranker.available=False when sentence-transformers missing
- rerank() returns identity ordering when not available
- RAGRetriever skips reranking when reranker is None or unavailable

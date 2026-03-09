# Entity Extraction

## Overview

Post-ingestion pipeline that extracts structured entities and relationships from intelligence items using the cheap LLM. Stores results in new SQLite tables alongside `intel_items`. Provides query APIs for the advisor retrieval layer and Radar UI. Inspired by MiroFish's ontology-guided GraphRAG approach, adapted to work without external graph DB dependencies — pure SQLite.

## Dependencies

**Depends on:** `intelligence` (IntelStorage, IntelItem), `llm` (cheap LLM provider), `db` (wal_connect, schema versioning)
**Depended on by:** `advisor/rag` (entity context retrieval), `web/routes/intel` (entity tags in Radar), `advisor/tools` (entity search tool)

---

## Components

### EntityExtractor

**File:** `src/intelligence/entity_extractor.py`
**Status:** Draft

#### Behavior

Extracts entities and relationships from intel items via LLM prompt. Operates in batch mode — receives a list of intel item dicts, processes in configurable batch sizes.

Constructor:
```python
EntityExtractor(
    llm: LLMProvider,            # cheap LLM instance
    storage: IntelStorage,
    entity_store: EntityStore,
    batch_size: int = 10,
    max_content_chars: int = 2000,
)
```

Extraction flow per item:
1. Build prompt: title + summary + content[:max_content_chars] + existing entity types as schema hint.
2. Call `llm.generate()` with JSON mode requesting `{entities: [{name, type, aliases}], relationships: [{source, target, type, evidence}]}`.
3. Parse JSON response. On malformed JSON: log warning, skip item, continue.
4. Normalize entity names: lowercase, strip whitespace, collapse multiple spaces.
5. Deduplicate against existing entities in `EntityStore` by (normalized_name, type) pair.
6. Insert new entities, merge aliases into existing entities, insert relationships, insert item-entity links.

Prompt template (system):
```
Extract entities and relationships from the following intelligence item.

Entity types: Company, Person, Technology, Product, Sector
Relationship types: COMPETES_WITH, BUILDS, WORKS_AT, ACQUIRED, PARTNERS_WITH, FUNDS

Return JSON: {
  "entities": [{"name": "...", "type": "...", "aliases": ["..."]}],
  "relationships": [{"source": "...", "target": "...", "type": "...", "evidence": "..."}]
}

Only extract entities explicitly mentioned. Do not infer. Keep evidence to one sentence.
```

#### Inputs / Outputs

```python
async def extract_batch(self, items: list[dict]) -> ExtractionResult
    # items: list of intel_items rows (dict with id, title, summary, content, ...)
    # Returns ExtractionResult

async def extract_item(self, item: dict) -> ItemExtractionResult
    # Single item extraction, called by extract_batch

async def backfill(self, since_days: int = 90, limit: int = 500) -> ExtractionResult
    # Re-extract from historical items not yet processed
```

```python
@dataclass
class ItemExtractionResult:
    item_id: int
    entities: list[dict]        # [{name, type, aliases, entity_id}]
    relationships: list[dict]   # [{source_id, target_id, type, evidence}]
    error: str | None = None

@dataclass
class ExtractionResult:
    processed: int
    entities_created: int
    entities_merged: int        # alias matches into existing entities
    relationships_created: int
    errors: int
```

#### Invariants

- Never calls the expensive LLM — only cheap instance.
- A single item extraction failure does not abort the batch.
- Entity (normalized_name, type) is unique. Duplicate inserts merge aliases.
- Relationships are directional: (source_id, target_id, type) is unique.
- Items already processed (exist in `entity_item_links`) are skipped in `extract_batch`.

#### Error Handling

| Trigger | Action |
|---------|--------|
| LLM returns non-JSON | Log warning with item_id, set `error` on ItemExtractionResult, continue |
| LLM returns JSON missing required keys | Treat as partial: extract what's present, skip missing |
| LLM timeout | Retry once (tenacity), then skip item |
| Unknown entity type in LLM response | Map to nearest known type or discard entity |
| SQLite constraint violation on insert | Log, skip duplicate, continue |

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `entity_extraction.enabled` | `true` | config.yaml |
| `entity_extraction.batch_size` | `10` | config.yaml |
| `entity_extraction.max_content_chars` | `2000` | config.yaml |
| `entity_extraction.entity_types` | `["Company", "Person", "Technology", "Product", "Sector"]` | config.yaml |
| `entity_extraction.relationship_types` | `["COMPETES_WITH", "BUILDS", "WORKS_AT", "ACQUIRED", "PARTNERS_WITH", "FUNDS"]` | config.yaml |

---

### EntityStore

**File:** `src/intelligence/entity_store.py`
**Status:** Draft

#### Behavior

SQLite persistence layer for entities, relationships, and item links. Lives in `intel.db` alongside `intel_items`. Initialized by schema migration (SCHEMA_VERSION bump from 3 → 4).

Constructor:
```python
EntityStore(db_path: str | Path)
    # Calls wal_connect, runs migration if needed
```

#### Inputs / Outputs

```python
def save_entity(self, name: str, entity_type: str, aliases: list[str] | None = None) -> int
    # Returns entity_id. Upserts: if (normalized_name, type) exists, merges aliases.

def save_relationship(self, source_id: int, target_id: int, rel_type: str, evidence: str = "", item_id: int | None = None) -> int
    # Returns relationship_id. Upserts on (source_id, target_id, type).

def link_item(self, item_id: int, entity_id: int) -> None
    # INSERT OR IGNORE into entity_item_links.

def get_entity(self, entity_id: int) -> dict | None
def get_entity_by_name(self, name: str, entity_type: str | None = None) -> dict | None
    # Searches normalized_name and aliases.

def search_entities(self, query: str, limit: int = 20) -> list[dict]
    # LIKE on normalized_name and aliases. Returns [{id, name, type, aliases, item_count}].

def get_relationships(self, entity_id: int, direction: str = "both") -> list[dict]
    # direction: "outgoing", "incoming", "both"
    # Returns [{id, source, target, type, evidence, source_name, target_name}].

def get_entity_items(self, entity_id: int, limit: int = 20) -> list[dict]
    # JOIN entity_item_links → intel_items. Returns intel item dicts.

def get_item_entities(self, item_id: int) -> list[dict]
    # Returns entities linked to a specific item.

def is_item_processed(self, item_id: int) -> bool
    # True if any row in entity_item_links for this item_id.

def get_unprocessed_items(self, limit: int = 100) -> list[int]
    # item_ids in intel_items with no row in entity_item_links.
```

#### Configuration

**New SQLite tables (intel.db, SCHEMA_VERSION = 4):**

```sql
CREATE TABLE entities (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    type            TEXT NOT NULL,
    aliases         TEXT,            -- JSON array string
    first_seen_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    item_count      INTEGER DEFAULT 0,
    UNIQUE(normalized_name, type)
);
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_normalized ON entities(normalized_name);

CREATE TABLE entity_relationships (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id   INTEGER NOT NULL REFERENCES entities(id),
    target_id   INTEGER NOT NULL REFERENCES entities(id),
    type        TEXT NOT NULL,
    evidence    TEXT,
    item_id     INTEGER REFERENCES intel_items(id),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, type)
);
CREATE INDEX idx_relationships_source ON entity_relationships(source_id);
CREATE INDEX idx_relationships_target ON entity_relationships(target_id);

CREATE TABLE entity_item_links (
    entity_id   INTEGER NOT NULL REFERENCES entities(id),
    item_id     INTEGER NOT NULL REFERENCES intel_items(id),
    PRIMARY KEY (entity_id, item_id)
);
CREATE INDEX idx_item_links_item ON entity_item_links(item_id);
```

#### Invariants

- `normalized_name` is always `name.lower().strip()` with collapsed whitespace.
- `(normalized_name, type)` is unique — no two entities share the same name+type.
- `aliases` is stored as JSON array string, parsed on read.
- `item_count` is maintained via trigger or manual update after link insertion.
- All writes go through `wal_connect`.

#### Error Handling

| Trigger | Action |
|---------|--------|
| UNIQUE constraint on entity insert | Return existing entity_id (upsert behavior) |
| UNIQUE constraint on relationship insert | Update evidence if new evidence is non-empty |
| FK violation (item_id not in intel_items) | Raise ValueError — caller must validate |
| FK violation (entity_id not in entities) | Raise ValueError — caller must validate |

---

### ExtractionScheduler

**File:** `src/intelligence/entity_extractor.py` (bottom of file)
**Status:** Draft

#### Behavior

Hooks into the existing APScheduler in `scheduler.py`. After each scraper run completes, queues unprocessed items for entity extraction.

```python
async def run_extraction(
    entity_extractor: EntityExtractor,
    entity_store: EntityStore,
    batch_size: int = 10,
) -> ExtractionResult:
    item_ids = entity_store.get_unprocessed_items(limit=batch_size)
    items = [storage.get_item_by_id(id) for id in item_ids]
    return await entity_extractor.extract_batch(items)
```

Registered as a job in `scheduler.py` → `_init_scrapers()`, runs after scraper jobs complete. Uses `misfire_grace_time=300` to handle overlapping runs.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `entity_extraction.schedule_minutes` | `30` | config.yaml |
| `entity_extraction.backfill_on_first_run` | `false` | config.yaml |

---

### Web API additions

**File:** `src/web/routes/intel.py` (additions)
**Status:** Draft

#### New endpoints

```
GET /api/intel/entities?q=&type=&limit=20
    → EntityStore.search_entities()

GET /api/intel/entities/{entity_id}
    → EntityStore.get_entity() + get_relationships() + get_entity_items()

GET /api/intel/items/{item_id}/entities
    → EntityStore.get_item_entities()
```

All endpoints use existing JWT auth and user isolation patterns.

---

## Cross-Cutting Concerns

**Schema migration:** Bumping SCHEMA_VERSION from 3 to 4 must be backward-compatible. The new tables are additive — existing `intel_items` queries are unaffected. Migration runs on first `EntityStore.__init__()` via `ensure_schema_version()`.

**Cost control:** All extraction uses the cheap LLM. With default batch_size=10 and ~200 tokens per extraction call, a 50-item scrape costs ~10k tokens on the cheap model. Config allows disabling entirely.

**Multi-user isolation:** In web mode, `intel.db` is shared (global intel), so entities are also shared. Per-user entity customization is out of scope.

## Test Expectations

- Extraction from a known article produces expected entities and relationships (mock LLM response).
- Malformed LLM JSON is handled gracefully — item skipped, batch continues.
- Entity dedup: inserting "OpenAI" and "openai" as Company yields one entity with alias.
- Relationship upsert: same (source, target, type) updates evidence.
- `get_unprocessed_items` correctly excludes items with existing links.
- Schema migration from v3 → v4 runs without data loss on existing `intel_items`.
- Backfill processes historical items correctly.
- Web endpoints return correct entity data with proper auth.
- Mock: LLM calls, SQLite (use temp db).

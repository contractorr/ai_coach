# AI-generated Mind Maps from User Journals

## Overview

The mind-map feature adds a derived, user-scoped artifact for a journal entry. It reuses the existing journal, receipt, thread, and memory signals, then augments them with matched Research artifacts, RSS-fed intelligence, and prior advisor conversations to assemble a small graph of concepts and relationships that the Journal UI can render inline. The feature remains per-entry and user-triggered, but cached artifacts should also be refreshable when relevant external context changes.

## Dependencies

**Depends on:** `journal` (entry read/update/delete), `web` (routes, auth, models), `extraction-receipt` (themes, memory facts, goal candidates, thread match), `research` (stored reports and dossiers), `intelligence` (RSS-derived intel items), `conversation-storage` (advisor chat history), `db` (WAL SQLite)

**Depended on by:** `web/src/app/(dashboard)/journal/page.tsx`

---

## Architecture

### Chosen architecture

Use a dedicated per-user SQLite store for derived mind-map artifacts plus a deterministic generation service that consumes:

- the current journal entry title, tags, content, and timestamps
- any existing extraction receipt for that entry
- lightweight fallback concept extraction from the entry text itself
- matched Research entries from the user's journal store
- matched RSS-fed intelligence items from shared `intel.db`
- matched prior conversations from `users.db`

This keeps the feature:

- user-scoped like other derived journal artifacts
- fast to read after first generation
- independent from live LLM availability
- easy to invalidate when the source entry changes

### Runtime flow

1. Journal entry detail opens in the web app.
2. Frontend requests `GET /api/journal/{filepath}/mind-map`.
3. If a cached map exists, backend revalidates it against the current journal plus matched external context signature before returning it.
4. If no map exists, frontend offers `Generate mind map`.
5. `POST /api/journal/{filepath}/mind-map` reads the entry, optionally reads the extraction receipt, gathers matched research, RSS intel, and conversation context, generates graph nodes and edges, persists the artifact, and returns it.
6. Journal entry update deletes the cached map for that entry.
7. Journal entry delete deletes the cached map during normal derived-state cleanup.

---

## Concept extraction

### Sources, in priority order

1. Extraction receipt themes
2. Extraction receipt memory facts
3. Extraction receipt goal candidates
4. Extraction receipt thread label
5. Related Research reports and dossier updates
6. Relevant RSS-fed intelligence items
7. Relevant prior advisor conversations
8. Journal tags
9. Content-derived phrases from planning and reflection language in the entry body

### Extraction heuristics

The generator should normalize signals into a small node set:

- `entry` node: the journal entry itself
- `theme` nodes: dominant topics or concerns
- `action` nodes: plans, next steps, or follow-through language
- `memory` nodes: durable facts or constraints surfaced by the memory pipeline
- `thread` node: recurring-topic context when present
- `research` nodes: matched Research artifacts or dossier topics
- `intel` nodes: matched RSS-derived external developments
- `conversation` nodes: relevant prior advisor discussion snippets
- `tag` nodes: explicit user tags when they add non-duplicate context

Rules:

- deduplicate labels case-insensitively
- trim labels to a readable display length
- keep the graph compact, targeting `5-10` total nodes
- cap external augmentation aggressively so it enriches interpretation without drowning the journal entry
- reject graphs that produce fewer than `2` useful non-root concepts

### Fallback extraction

If receipt signals are weak or missing, parse the entry body with simple phrase detectors for patterns such as:

- `need to`
- `want to`
- `plan to`
- `focus on`
- `working on`
- `blocked by`
- `struggling with`

This keeps the feature usable even before every journal pipeline signal is available.

### External matching

External augmentation should use bounded local retrieval rather than another large LLM call.

#### Research matching

- Query the user's `research` journal entries and dossier updates from `JournalStorage`.
- Score by token overlap between the current entry and research titles, previews, tags, and stored topic metadata when available.
- Prefer the strongest `1-2` matches.

#### RSS / intelligence matching

- Query recent intel items from shared `intel.db`.
- Restrict to sources whose `source` begins with `rss:`.
- Score by overlap against title, summary, and tags.
- Prefer the strongest `1-2` matches, with a stricter threshold than research because RSS is noisier.

#### Conversation matching

- Inspect a bounded number of the user's recent conversations from `users.db`.
- Score conversation messages by lexical overlap with the current entry.
- Prefer `1-2` concise conversation signals drawn from matched excerpts, not whole transcripts.

---

## Relationship detection

Relationships are intentionally lightweight and explanatory rather than ontological.

### Base edges

Every non-root node connects to the root entry node with a role label:

- `highlights` for themes
- `points to` for actions
- `reinforces` for memory facts
- `recurs as` for thread matches
- `expanded by` for research nodes
- `echoed by` for RSS intel nodes
- `discussed in` for conversation nodes
- `tagged` for tags

### Secondary edges

Add a small number of extra edges when there is clear lexical overlap:

- action -> theme when an action obviously advances a theme
- memory -> theme when a constraint or preference explains a theme
- thread -> theme when the recurring thread overlaps the same topic
- research -> theme when research strengthens a local theme
- intel -> theme when outside developments align with the note
- conversation -> action/theme when the same issue was discussed previously

Secondary edges are optional. The system should avoid dense edge networks that make the graph harder to scan than the original note.

---

## Data model

### Store

**File:** `src/journal/mind_map.py`

Suggested schema:

```sql
CREATE TABLE journal_mind_maps (
    map_id TEXT PRIMARY KEY,
    entry_path TEXT NOT NULL UNIQUE,
    entry_title TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    rationale TEXT NOT NULL DEFAULT '',
    generator TEXT NOT NULL DEFAULT 'derived',
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_journal_mind_maps_entry_path ON journal_mind_maps(entry_path);
CREATE INDEX idx_journal_mind_maps_updated_at ON journal_mind_maps(updated_at DESC);
```

### Payload

```json
{
  "nodes": [
    {
      "id": "root",
      "label": "Weekly review",
      "kind": "entry",
      "weight": 1.0,
      "confidence": 1.0,
      "is_root": true,
      "source_type": null,
      "source_label": "",
      "source_ref": ""
    }
  ],
  "edges": [
    {
      "source": "root",
      "target": "theme-career",
      "label": "highlights",
      "strength": 0.82
    }
  ]
}
```

### API models

Expose:

- `JournalMindMapNode`
- `JournalMindMapEdge`
- `JournalMindMapResponse`
- `JournalMindMapEnvelope`

Envelope status values:

- `ready`
- `not_available`

---

## Mind map generation

### Generator responsibilities

`JournalMindMapGenerator` should:

1. Build a deterministic source hash from the entry content plus relevant metadata.
2. Gather bounded external context candidates from research, RSS intel, and conversations.
3. Return the cached artifact when the source hash still matches and regeneration is not forced.
4. Aggregate concepts from receipt data, external matches, and text heuristics.
5. Build nodes and edges with conservative labels and confidence values.
6. Persist the artifact only if the graph clears the minimum-signal threshold.

### Summary generation

The generator should also produce:

- a one-sentence summary of what the map surfaces
- a short rationale describing the signal sources used, such as tags, memory facts, thread match, research, RSS, or conversation overlap

This keeps the graph inspectable and aligned with the product rule that AI output should explain itself.

### Invalidation

- `PUT /api/journal/{filepath}` deletes any cached map for that entry after the source changes.
- `DELETE /api/journal/{filepath}` deletes the cached map during derived-state cleanup.
- `GET /api/journal/{filepath}/mind-map` may refresh an existing artifact if matched external context changed enough to alter the source hash.

---

## Rendering strategy

### Frontend

Render the map inline in the Journal entry detail sheet using a dedicated React component. Do not add a graph library.

### Layout

Use a simple radial layout:

- root entry node centered
- non-root nodes distributed around the root
- node color driven by semantic kind
- edges drawn as thin SVG lines with short role labels where space allows
- external nodes visually distinct from local nodes but still lower-emphasis than the root

### UI states

- loading skeleton while fetching
- empty state with `Generate mind map`
- generated state with summary, rationale, and graph
- generated state also surfaces which external source families were used
- error state with retry

This approach matches the current stack, avoids new dependencies, and stays consistent with the design-system guidance for calm, legible surfaces.

---

## Performance considerations

- Generation is bounded to a single journal entry plus small external candidate pools, so it remains cheap relative to advisor or research paths.
- Stored artifacts avoid recomputing the graph on every entry open.
- Existing artifacts can be revalidated on read using a deterministic source hash instead of forcing a manual rebuild for every external update.
- The graph stays intentionally small to keep SVG rendering fast on mobile and desktop.
- Invalidation on entry edits prevents stale derived output without requiring a background reindex job.
- No new external service dependency is required because the feature only reuses already-stored research, intelligence, and conversation data.

---

## Architecture options

### Option 1: Dedicated per-user derived store with on-demand external context collection

Store a cached map artifact in a new per-user SQLite file.

Pros:

- clean separation from receipt payloads
- easy invalidation rules
- extensible to future multi-entry maps
- can incorporate dynamic external context without overloading other stores

Cons:

- adds one more derived store to path management

### Option 2: Extend extraction receipts with mind-map payload and external context

Persist the graph inside `receipts.db` as another receipt payload section.

Pros:

- fewer storage files
- tight coupling to receipt lifecycle

Cons:

- receipt payload becomes overloaded
- harder to regenerate independently from receipt creation or external-context changes

### Option 3: Generate on every view with no persistence

Build the map on demand from the entry and receipt without storing it.

Pros:

- minimal persistence surface
- simplest cleanup model

Cons:

- repeated compute on every view
- harder to support future user interactions such as saved layout state or feedback
- makes bounded-but-expensive external context collection run too often

### Recommendation

Choose Option 1. It best matches existing per-user derived-storage patterns like memory, threads, receipts, and outcomes while keeping the feature isolated and easy to evolve.

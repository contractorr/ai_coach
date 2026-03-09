# Entity Extraction

**Status:** Draft
**Author:** —
**Date:** 2026-03-09

## Problem

Intelligence items are stored as flat text blobs (title, summary, content). The advisor can retrieve items by keyword or semantic similarity, but cannot answer relational questions like "which companies are competing in X space" or "what is person Y connected to" because no structured entity or relationship data exists. Users asking strategic questions get keyword-matched articles instead of connected knowledge.

## Users

All users who ask the advisor questions about companies, people, technologies, or trends — particularly power users tracking competitive landscapes and emerging sectors.

## Desired Behavior

### Background extraction (invisible to user)

1. When new intelligence items are scraped and stored, the system extracts entities (companies, people, technologies, products, sectors) and relationships between them.
2. Extraction runs as a post-processing step after scraper ingestion — does not block or slow the scrape itself.
3. Entities accumulate over time, building a knowledge graph alongside the existing flat intel store.
4. Duplicate entities across different articles are merged (e.g., "OpenAI" from two different HN posts resolves to one entity).

### Advisor queries (visible to user)

1. When a user asks a relational question, the advisor retrieves relevant entities and their relationships as additional context alongside the existing journal + intel retrieval.
2. The advisor can answer "what companies are in X space", "how is A related to B", "what has changed about company C recently" using entity graph context.
3. Entity context appears naturally in advisor responses — no separate UI for the graph.

### Radar enrichment (visible to user)

1. Intelligence items in Radar show extracted entity tags (e.g., company names, technologies mentioned).
2. Users can click an entity tag to filter Radar by that entity, surfacing all related items.

## Acceptance Criteria

- [ ] After scraper ingestion, entities and relationships are extracted and stored within a configurable delay (default: process in batch after scrape completes).
- [ ] Entity types include at minimum: Company, Person, Technology, Product, Sector.
- [ ] Relationships include at minimum: COMPETES_WITH, BUILDS, WORKS_AT, ACQUIRED, PARTNERS_WITH, FUNDS.
- [ ] Entities are deduplicated by normalized name — "OpenAI", "openai", "Open AI" resolve to one entity.
- [ ] Each entity links back to the intel items it was extracted from.
- [ ] Advisor retrieval includes entity graph context when the query matches extracted entities.
- [ ] Entity extraction uses the cheap LLM instance (not the expensive one).
- [ ] Extraction failures for individual items do not block the rest of the batch.
- [ ] Radar intel items display extracted entity names as tags.
- [ ] Filtering Radar by an entity tag shows all items linked to that entity.
- [ ] Entity extraction is toggleable via config (`entity_extraction.enabled`, default `true`).
- [ ] Batch size for extraction is configurable (`entity_extraction.batch_size`, default `10`).

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Intel item has no extractable entities | Item stored normally, no entity rows created |
| Two items mention the same entity with different casing/spelling | Merged into one entity via name normalization |
| LLM extraction returns malformed JSON | Log warning, skip item, continue batch |
| Entity name conflicts across types (e.g., "Apple" as Company vs fruit) | Type-qualified dedup — same name can exist as different types |
| Very long article (>10k chars) | Truncate to first 2000 chars for extraction to stay within cheap LLM context |
| Extraction backlog grows during high-volume scrape | Batch queue with configurable concurrency; oldest-first processing |
| User disables entity extraction in config | No extraction runs; advisor falls back to existing keyword/semantic retrieval only |

## Out of Scope

- Interactive graph visualization UI (entities power retrieval and tags only)
- User-editable entity corrections or manual entity creation
- Cross-user entity graphs (entities are per-user in web mode, shared in CLI mode — same isolation as intel)
- Real-time streaming extraction during scrape (batch post-processing only)
- Entity extraction from journal entries (intel items only for now)

## Open Questions

- Should entity extraction run on historical items (backfill) on first enable, or only on new items going forward?
- Should the ontology (entity types + relationship types) be fixed or LLM-generated per user's profile/interests (MiroFish approach)?
- What is the acceptable cost ceiling per intel item for cheap LLM extraction calls?

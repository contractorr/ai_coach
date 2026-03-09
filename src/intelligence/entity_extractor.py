"""Entity extraction pipeline for intelligence items."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta

import structlog

from intelligence.scraper import IntelStorage
from llm.base import LLMProvider

from .entity_store import EntityStore, normalize_entity_name

logger = structlog.get_logger()

DEFAULT_ENTITY_TYPES = ["Company", "Person", "Technology", "Product", "Sector"]
DEFAULT_RELATIONSHIP_TYPES = [
    "COMPETES_WITH",
    "BUILDS",
    "WORKS_AT",
    "ACQUIRED",
    "PARTNERS_WITH",
    "FUNDS",
]


@dataclass
class ItemExtractionResult:
    item_id: int
    entities: list[dict]
    relationships: list[dict]
    error: str | None = None


@dataclass
class ExtractionResult:
    processed: int = 0
    entities_created: int = 0
    entities_merged: int = 0
    relationships_created: int = 0
    errors: int = 0


class EntityExtractor:
    """Extract entities and relationships from intel items using a cheap LLM."""

    def __init__(
        self,
        llm: LLMProvider,
        storage: IntelStorage,
        entity_store: EntityStore,
        batch_size: int = 10,
        max_content_chars: int = 2000,
        entity_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
    ) -> None:
        self.llm = llm
        self.storage = storage
        self.entity_store = entity_store
        self.batch_size = batch_size
        self.max_content_chars = max_content_chars
        self.entity_types = entity_types or DEFAULT_ENTITY_TYPES
        self.relationship_types = relationship_types or DEFAULT_RELATIONSHIP_TYPES

    async def extract_batch(self, items: list[dict]) -> ExtractionResult:
        summary = ExtractionResult()
        for item in items[: self.batch_size]:
            if not item or self.entity_store.is_item_processed(int(item["id"])):
                continue
            result = await self.extract_item(item)
            summary.processed += 1
            if result.error:
                summary.errors += 1
                continue

            summary.entities_created += len(result.entities)
            summary.relationships_created += len(result.relationships)

        return summary

    async def extract_item(self, item: dict) -> ItemExtractionResult:
        prompt = self._build_prompt(item)
        try:
            raw = self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                system=self._system_prompt(),
                max_tokens=1200,
            )
            parsed = json.loads(raw)
        except Exception as exc:
            logger.warning("entity_extraction_failed", item_id=item.get("id"), error=str(exc))
            return ItemExtractionResult(
                item_id=int(item["id"]),
                entities=[],
                relationships=[],
                error=str(exc),
            )

        created_entities = []
        entity_lookup: dict[str, dict] = {}
        for entity in parsed.get("entities", []):
            entity_name = (entity.get("name") or "").strip()
            entity_type = self._normalize_entity_type(entity.get("type"))
            if not entity_name or not entity_type:
                continue
            aliases = [alias for alias in entity.get("aliases", []) if isinstance(alias, str)]
            existing = self.entity_store.get_entity_by_name(entity_name, entity_type)
            entity_id = self.entity_store.save_entity(entity_name, entity_type, aliases=aliases)
            if existing:
                entity_lookup[normalize_entity_name(entity_name)] = {
                    "id": entity_id,
                    "type": entity_type,
                }
            else:
                created_entities.append(
                    {
                        "entity_id": entity_id,
                        "name": entity_name,
                        "type": entity_type,
                        "aliases": aliases,
                    }
                )
                entity_lookup[normalize_entity_name(entity_name)] = {
                    "id": entity_id,
                    "type": entity_type,
                }
            self.entity_store.link_item(int(item["id"]), entity_id)

        created_relationships = []
        for relationship in parsed.get("relationships", []):
            source_name = relationship.get("source")
            target_name = relationship.get("target")
            rel_type = relationship.get("type")
            if not source_name or not target_name or rel_type not in self.relationship_types:
                continue
            source = entity_lookup.get(
                normalize_entity_name(source_name)
            ) or self.entity_store.get_entity_by_name(source_name)
            target = entity_lookup.get(
                normalize_entity_name(target_name)
            ) or self.entity_store.get_entity_by_name(target_name)
            if not source or not target:
                continue
            relationship_id = self.entity_store.save_relationship(
                int(source["id"]),
                int(target["id"]),
                rel_type,
                evidence=(relationship.get("evidence") or "")[:500],
                item_id=int(item["id"]),
            )
            created_relationships.append(
                {
                    "id": relationship_id,
                    "source_id": int(source["id"]),
                    "target_id": int(target["id"]),
                    "type": rel_type,
                }
            )

        return ItemExtractionResult(
            item_id=int(item["id"]),
            entities=created_entities,
            relationships=created_relationships,
        )

    async def backfill(self, since_days: int = 90, limit: int = 500) -> ExtractionResult:
        cutoff = datetime.now() - timedelta(days=since_days)
        items = self.storage.get_items_since(cutoff, limit=limit)
        return await self.extract_batch(items)

    def _system_prompt(self) -> str:
        return (
            "Extract entities and relationships from the following intelligence item.\n\n"
            f"Entity types: {', '.join(self.entity_types)}\n"
            f"Relationship types: {', '.join(self.relationship_types)}\n\n"
            'Return JSON: {"entities": [{"name": "...", "type": "...", "aliases": ["..."]}], '
            '"relationships": [{"source": "...", "target": "...", "type": "...", "evidence": "..."}]}\n\n'
            "Only extract entities explicitly mentioned. Do not infer. Keep evidence to one sentence."
        )

    def _build_prompt(self, item: dict) -> str:
        title = item.get("title", "")
        summary = item.get("summary", "")
        content = (item.get("content") or "")[: self.max_content_chars]
        return f"Title: {title}\nSummary: {summary}\nContent: {content}"

    def _normalize_entity_type(self, raw_type: str | None) -> str | None:
        if not raw_type:
            return None
        normalized = raw_type.strip().title()
        if normalized in self.entity_types:
            return normalized
        return None


class ExtractionScheduler:
    """Fetch and process batches of unprocessed intel items."""

    def __init__(
        self,
        entity_extractor: EntityExtractor,
        entity_store: EntityStore,
        batch_size: int = 10,
    ) -> None:
        self.entity_extractor = entity_extractor
        self.entity_store = entity_store
        self.batch_size = batch_size

    async def run_extraction(self) -> ExtractionResult:
        item_ids = self.entity_store.get_unprocessed_items(limit=self.batch_size)
        items = [self.entity_extractor.storage.get_item_by_id(item_id) for item_id in item_ids]
        return await self.entity_extractor.extract_batch([item for item in items if item])

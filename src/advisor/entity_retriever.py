"""Entity graph retrieval for advisor prompts."""

from __future__ import annotations

from xml.sax.saxutils import quoteattr

from intelligence.entity_store import EntityStore


class EntityRetriever:
    """Render matched entities, relationships, and linked items as XML context."""

    def __init__(
        self,
        entity_store: EntityStore,
        max_entities: int = 5,
        max_relationships_per_entity: int = 10,
        max_items_per_entity: int = 3,
        max_chars: int = 1600,
        fact_store=None,
        max_memory_facts_per_entity: int = 5,
    ) -> None:
        self.entity_store = entity_store
        self.max_entities = max_entities
        self.max_relationships_per_entity = max_relationships_per_entity
        self.max_items_per_entity = max_items_per_entity
        self.max_chars = max_chars
        self.fact_store = fact_store
        self.max_memory_facts_per_entity = max_memory_facts_per_entity
        self._bridge = None
        if fact_store is not None:
            try:
                from services.entity_bridge import EntityBridge

                self._bridge = EntityBridge(entity_store, fact_store)
            except Exception:
                pass

    def retrieve(
        self, matched_entities: list[dict], _query: str = "", max_chars: int | None = None
    ) -> str:
        effective_max = max_chars if max_chars is not None else self.max_chars
        if not matched_entities:
            return ""

        sorted_entities = sorted(
            matched_entities,
            key=lambda entity: entity.get("item_count", 0),
            reverse=True,
        )[: self.max_entities]

        parts = ["<entity_context>"]
        for entity in sorted_entities:
            relationships = self.entity_store.get_relationships(entity["id"])[
                : self.max_relationships_per_entity
            ]
            items = self.entity_store.get_entity_items(
                entity["id"], limit=self.max_items_per_entity
            )
            block = [
                f"<entity name={self._attr(entity.get('name'))} type={self._attr(entity.get('type'))}>",
                "<relationships>",
            ]
            for relationship in relationships:
                target_name = (
                    relationship.get("target_name")
                    if relationship.get("source_id") == entity["id"]
                    else relationship.get("source_name")
                )
                block.append(
                    f"<rel type={self._attr(relationship.get('type'))} "
                    f"target={self._attr(target_name)} "
                    f"evidence={self._attr((relationship.get('evidence') or '')[:160])} />"
                )
            block.append("</relationships>")
            block.append(f"<recent_items count={self._attr(len(items))}>")
            for item in items:
                block.append(
                    f"<item source={self._attr(item.get('source', ''))} "
                    f"title={self._attr(item.get('title', ''))} "
                    f"summary={self._attr((item.get('summary') or '')[:180])} />"
                )
            block.append("</recent_items>")

            # Memory facts enrichment
            if self._bridge is not None:
                facts = self._bridge.get_memory_facts_for_entity(
                    entity, max_facts=self.max_memory_facts_per_entity
                )
                if facts:
                    block.append("<memory_facts>")
                    for fact in facts:
                        cat = (
                            fact.category.value
                            if hasattr(fact.category, "value")
                            else str(fact.category)
                        )
                        block.append(
                            f"<fact confidence={self._attr(fact.confidence)} "
                            f"category={self._attr(cat)}>{fact.text}</fact>"
                        )
                    block.append("</memory_facts>")

            block.append("</entity>")
            candidate = "\n".join(parts + block + ["</entity_context>"])
            if len(candidate) > effective_max:
                break
            parts.extend(block)
        parts.append("</entity_context>")
        return "\n".join(parts) if len(parts) > 2 else ""

    @staticmethod
    def _attr(value) -> str:
        return quoteattr("" if value is None else str(value))

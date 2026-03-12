"""Bridge between intel entities and memory entities via normalized name matching."""

from __future__ import annotations

import structlog

from intelligence.entity_store import EntityStore, normalize_entity_name

logger = structlog.get_logger()


class EntityBridge:
    """Resolve intel entities to personal memory facts by shared normalized name."""

    def __init__(self, entity_store: EntityStore, fact_store) -> None:
        self.entity_store = entity_store
        self.fact_store = fact_store

    def get_memory_facts_for_entity(self, intel_entity: dict, max_facts: int = 5) -> list:
        """Return memory facts matching an intel entity's normalized name.

        Side-effect: persists cross_entity_link on match (best-effort).
        Returns [] on any error.
        """
        try:
            name = intel_entity.get("name", "")
            normalized = normalize_entity_name(name)
            if not normalized:
                return []

            facts = self.fact_store.get_facts_for_entity(normalized, limit=max_facts)
            if facts:
                try:
                    self.entity_store.save_cross_entity_link(intel_entity["id"], normalized)
                except Exception:
                    pass
            return facts
        except Exception as exc:
            logger.debug("entity_bridge_lookup_failed", error=str(exc))
            return []

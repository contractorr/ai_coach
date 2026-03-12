"""Tests for EntityBridge — cross-system entity resolution."""

from unittest.mock import Mock, patch

import pytest

from intelligence.entity_store import EntityStore
from intelligence.scraper import IntelStorage
from memory.models import FactCategory, FactSource, StewardFact
from memory.store import FactStore
from services.entity_bridge import EntityBridge


@pytest.fixture
def intel_db(tmp_path):
    IntelStorage(tmp_path / "intel.db")
    return EntityStore(tmp_path / "intel.db")


@pytest.fixture
def fact_store(tmp_path):
    return FactStore(tmp_path / "memory.db", chroma_dir=None)


@pytest.fixture
def bridge(intel_db, fact_store):
    return EntityBridge(intel_db, fact_store)


def _fact(id, text, confidence=0.85):
    return StewardFact(
        id=id,
        text=text,
        category=FactCategory.SKILL,
        source_type=FactSource.JOURNAL,
        source_id="entry-1",
        confidence=confidence,
    )


class TestEntityBridge:
    def test_returns_facts_when_normalized_names_match(self, bridge, intel_db, fact_store):
        # Intel entity "Rust" and memory fact with "Rust" entity
        entity_id = intel_db.save_entity("Rust", "Technology")
        fact_store.add(_fact("f1", "User is learning Rust programming"))
        intel_entity = {"id": entity_id, "name": "Rust"}

        facts = bridge.get_memory_facts_for_entity(intel_entity)
        assert len(facts) == 1
        assert "Rust" in facts[0].text

    def test_returns_empty_when_no_match(self, bridge, intel_db, fact_store):
        entity_id = intel_db.save_entity("Go", "Technology")
        fact_store.add(_fact("f1", "User prefers Python for backend"))
        intel_entity = {"id": entity_id, "name": "Go"}

        facts = bridge.get_memory_facts_for_entity(intel_entity)
        assert facts == []

    def test_returns_empty_on_fact_store_exception(self, intel_db):
        bad_fact_store = Mock()
        bad_fact_store.get_facts_for_entity.side_effect = RuntimeError("db locked")
        bridge = EntityBridge(intel_db, bad_fact_store)

        entity_id = intel_db.save_entity("Rust", "Technology")
        facts = bridge.get_memory_facts_for_entity({"id": entity_id, "name": "Rust"})
        assert facts == []

    def test_saves_cross_entity_link_on_match(self, bridge, intel_db, fact_store):
        entity_id = intel_db.save_entity("Python", "Technology")
        fact_store.add(_fact("f1", "User builds Django with Python"))
        intel_entity = {"id": entity_id, "name": "Python"}

        bridge.get_memory_facts_for_entity(intel_entity)
        links = intel_db.get_cross_entity_links(entity_id)
        assert "python" in links

    def test_max_facts_caps_returned_list(self, bridge, intel_db, fact_store):
        entity_id = intel_db.save_entity("Python", "Technology")
        for i in range(10):
            fact_store.add(_fact(f"f{i}", f"User uses Python for project {i}"))
        intel_entity = {"id": entity_id, "name": "Python"}

        facts = bridge.get_memory_facts_for_entity(intel_entity, max_facts=3)
        assert len(facts) <= 3

    def test_empty_name_returns_empty(self, bridge):
        facts = bridge.get_memory_facts_for_entity({"id": 1, "name": ""})
        assert facts == []

    def test_cross_link_failure_does_not_affect_return(self, intel_db, fact_store):
        entity_id = intel_db.save_entity("Rust", "Technology")
        fact_store.add(_fact("f1", "User is learning Rust"))

        bridge = EntityBridge(intel_db, fact_store)
        with patch.object(intel_db, "save_cross_entity_link", side_effect=RuntimeError("fail")):
            facts = bridge.get_memory_facts_for_entity({"id": entity_id, "name": "Rust"})
        assert len(facts) == 1

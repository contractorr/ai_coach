"""Tests for entity storage and schema migration."""

from db import get_schema_version, wal_connect
from intelligence.entity_store import EntityStore
from intelligence.scraper import IntelItem, IntelStorage


def test_entity_store_migrates_schema_and_deduplicates_names(tmp_path):
    intel_storage = IntelStorage(tmp_path / "intel.db")
    intel_storage.save(
        IntelItem(
            source="rss",
            title="OpenAI news",
            url="https://example.com/openai",
            summary="OpenAI shipped something.",
        )
    )

    store = EntityStore(tmp_path / "intel.db")
    first_id = store.save_entity("OpenAI", "Company", aliases=["Open AI"])
    second_id = store.save_entity("openai", "Company", aliases=["OpenAI"])

    assert first_id == second_id
    entity = store.get_entity(first_id)
    assert entity["name"] == "OpenAI"
    assert entity["type"] == "Company"

    with wal_connect(tmp_path / "intel.db") as conn:
        assert get_schema_version(conn) == 4


def test_entity_store_links_items_and_relationships(tmp_path):
    intel_storage = IntelStorage(tmp_path / "intel.db")
    item_id = intel_storage.save(
        IntelItem(
            source="rss",
            title="Anthropic partners with OpenAI",
            url="https://example.com/partnership",
            summary="Partnership summary",
        )
    )
    store = EntityStore(tmp_path / "intel.db")
    openai_id = store.save_entity("OpenAI", "Company")
    anthropic_id = store.save_entity("Anthropic", "Company")

    store.link_item(item_id, openai_id)
    relationship_id = store.save_relationship(
        anthropic_id,
        openai_id,
        "PARTNERS_WITH",
        evidence="The companies announced a partnership.",
        item_id=item_id,
    )

    assert relationship_id
    assert store.is_item_processed(item_id) is True
    assert store.get_item_entities(item_id)[0]["name"] == "OpenAI"
    assert store.get_relationships(anthropic_id)[0]["target_name"] == "OpenAI"

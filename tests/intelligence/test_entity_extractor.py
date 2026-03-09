"""Tests for entity extraction and scheduling."""

from intelligence.entity_extractor import EntityExtractor, ExtractionScheduler
from intelligence.entity_store import EntityStore
from intelligence.scraper import IntelItem, IntelStorage


class FakeLLM:
    def __init__(self, response: str):
        self.response = response

    def generate(self, messages, system=None, max_tokens=0, use_thinking=False):
        return self.response


def test_entity_extractor_saves_entities_and_relationships(tmp_path):
    storage = IntelStorage(tmp_path / "intel.db")
    item_id = storage.save(
        IntelItem(
            source="rss",
            title="OpenAI competes with Anthropic",
            url="https://example.com/competes",
            summary="Competitive update",
            content="OpenAI competes with Anthropic in frontier models.",
        )
    )
    store = EntityStore(tmp_path / "intel.db")
    extractor = EntityExtractor(
        llm=FakeLLM(
            """
            {
              "entities": [
                {"name": "OpenAI", "type": "Company", "aliases": ["Open AI"]},
                {"name": "Anthropic", "type": "Company", "aliases": []}
              ],
              "relationships": [
                {
                  "source": "OpenAI",
                  "target": "Anthropic",
                  "type": "COMPETES_WITH",
                  "evidence": "OpenAI competes with Anthropic."
                }
              ]
            }
            """
        ),
        storage=storage,
        entity_store=store,
    )

    result = _run(extractor.extract_item(storage.get_item_by_id(item_id)))

    assert result.error is None
    assert len(result.entities) == 2
    assert len(result.relationships) == 1
    assert store.search_entities("openai")[0]["name"] == "OpenAI"


def test_entity_extractor_handles_bad_json(tmp_path):
    storage = IntelStorage(tmp_path / "intel.db")
    item_id = storage.save(
        IntelItem(
            source="rss",
            title="Malformed",
            url="https://example.com/bad",
            summary="Bad response",
        )
    )
    store = EntityStore(tmp_path / "intel.db")
    extractor = EntityExtractor(
        llm=FakeLLM("not-json"),
        storage=storage,
        entity_store=store,
    )

    result = _run(extractor.extract_item(storage.get_item_by_id(item_id)))

    assert result.error is not None


def test_extraction_scheduler_processes_oldest_unprocessed_items(tmp_path):
    storage = IntelStorage(tmp_path / "intel.db")
    storage.save(
        IntelItem(
            source="rss",
            title="OpenAI builds tools",
            url="https://example.com/tools",
            summary="OpenAI builds tools",
        )
    )
    store = EntityStore(tmp_path / "intel.db")
    extractor = EntityExtractor(
        llm=FakeLLM(
            '{"entities": [{"name": "OpenAI", "type": "Company", "aliases": []}], "relationships": []}'
        ),
        storage=storage,
        entity_store=store,
    )
    scheduler = ExtractionScheduler(extractor, store, batch_size=5)

    result = _run(scheduler.run_extraction())

    assert result.processed == 1
    assert store.get_unprocessed_items(limit=5) == []


def _run(coro):
    import asyncio

    return asyncio.run(coro)

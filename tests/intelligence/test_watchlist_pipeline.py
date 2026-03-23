"""Tests for WatchlistPipeline framework."""

from unittest.mock import MagicMock

from intelligence.scraper import IntelItem, IntelStorage
from intelligence.watchlist import WatchlistStore
from intelligence.watchlist_pipeline import (
    WatchlistPipeline,
    WatchlistPipelineConfig,
    create_company_movement_pipeline,
    create_hiring_pipeline,
    create_regulatory_pipeline,
)
from storage_paths import get_user_paths


def _setup_watchlist_and_storage(tmp_path, monkeypatch):
    """Shared setup: storage + watchlist items."""
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    storage = IntelStorage(tmp_path / "intel.db")
    storage.save(
        IntelItem(
            source="rss",
            title="OpenAI launches enterprise pricing update",
            url="https://example.com/openai-pricing",
            summary="OpenAI launched new pricing plans for enterprise customers.",
        )
    )
    storage.save(
        IntelItem(
            source="rss",
            title="OpenAI is hiring across London and New York",
            url="https://example.com/openai-hiring",
            summary="OpenAI is expanding the team with several new open roles.",
        )
    )
    storage.save(
        IntelItem(
            source="rss",
            title="EU AI Act finalized with updated guidance",
            url="https://example.com/eu-ai-act",
            summary="The EU AI Act was finalized and includes updated compliance guidance.",
        )
    )

    user_paths = get_user_paths("user-1", coach_home=tmp_path)
    watchlist = WatchlistStore(user_paths["watchlist_path"])
    watchlist.save_item(
        {
            "label": "OpenAI",
            "kind": "company",
            "priority": "high",
            "domain": "openai.com",
            "aliases": ["Open AI"],
        }
    )
    watchlist.save_item(
        {
            "label": "AI Act",
            "kind": "regulation",
            "priority": "high",
            "topics": ["AI Act"],
            "geographies": ["EU"],
        }
    )
    return storage


def test_company_movement_pipeline_via_factory(tmp_path, monkeypatch):
    storage = _setup_watchlist_and_storage(tmp_path, monkeypatch)
    pipeline = create_company_movement_pipeline(
        storage,
        {"company_movement": {"enabled": True, "min_significance": 0.4, "lookback_days": 14}},
    )
    result = pipeline.run()
    assert result["saved"] >= 1
    assert "watched_companies" in result


def test_hiring_pipeline_via_factory(tmp_path, monkeypatch):
    storage = _setup_watchlist_and_storage(tmp_path, monkeypatch)
    pipeline = create_hiring_pipeline(
        storage,
        {"hiring": {"enabled": True, "lookback_days": 14}},
    )
    result = pipeline.run()
    assert result["saved"] >= 1
    assert "watched_entities" in result


def test_regulatory_pipeline_via_factory(tmp_path, monkeypatch):
    storage = _setup_watchlist_and_storage(tmp_path, monkeypatch)
    pipeline = create_regulatory_pipeline(
        storage,
        {"regulatory": {"enabled": True, "min_relevance": 0.3, "lookback_days": 30}},
    )
    result = pipeline.run()
    assert result["saved"] >= 1
    assert "targets" in result


def test_pipeline_returns_empty_when_no_entities(tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    storage = IntelStorage(tmp_path / "intel.db")
    # No watchlist items → empty result
    pipeline = create_company_movement_pipeline(storage, {"company_movement": {}})
    result = pipeline.run()
    assert result == {"watched_companies": 0, "events_detected": 0, "saved": 0}


def test_pipeline_deduplicates_by_priority(tmp_path, monkeypatch):
    """Pipeline keeps highest-priority entity per key."""
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    storage = IntelStorage(tmp_path / "intel.db")

    cfg = WatchlistPipelineConfig(
        name="test",
        config_key="test",
        entity_key_field="key",
        default_lookback_days=14,
        default_limit_per_entity=100,
        empty_result={"count": 0},
    )

    resolved = []

    def resolver(_items):
        return [
            {"key": "a", "priority": 1, "label": "low"},
            {"key": "a", "priority": 5, "label": "high"},
        ]

    def processor(entities, _items, _conf):
        resolved.extend(entities)
        return []

    mock_store = MagicMock()
    mock_store.save_many.return_value = 0

    pipeline = WatchlistPipeline(
        storage=storage,
        full_config={"test": {}},
        pipeline_config=cfg,
        resolver=resolver,
        processor=processor,
        store_factory=lambda _db_path: mock_store,
    )
    pipeline.run()
    # Only the high-priority entity should remain
    assert len(resolved) == 1
    assert resolved[0]["label"] == "high"

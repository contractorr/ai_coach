from datetime import datetime, timedelta

from intelligence.company_watch import CompanyMovementStore
from intelligence.hiring_signals import HiringSignalStore
from intelligence.regulatory import RegulatoryAlertStore
from intelligence.scheduler import IntelScheduler
from intelligence.scraper import IntelItem, IntelStorage
from intelligence.watchlist import WatchlistStore
from storage_paths import get_user_paths


def test_pipeline_scheduler_emits_company_hiring_and_regulatory_signals(tmp_path, monkeypatch):
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

    scheduler = IntelScheduler(
        storage=storage,
        config={},
        full_config={
            "company_movement": {"enabled": True, "min_significance": 0.4, "lookback_days": 14},
            "hiring": {"enabled": True, "lookback_days": 14},
            "regulatory": {"enabled": True, "min_relevance": 0.3, "lookback_days": 30},
        },
    )

    company_result = scheduler.run_company_movement_pipeline()
    hiring_result = scheduler.run_hiring_activity_pipeline()
    regulatory_result = scheduler.run_regulatory_pipeline()

    assert company_result["saved"] >= 1
    assert hiring_result["saved"] >= 1
    assert regulatory_result["saved"] >= 1

    assert CompanyMovementStore(storage.db_path).get_recent_for_company("openai", limit=10)
    assert HiringSignalStore(storage.db_path).get_recent(entity_key="openai", limit=10)
    assert RegulatoryAlertStore(storage.db_path).get_recent(
        since=datetime.now() - timedelta(days=30),
        limit=10,
    )


def test_scheduler_registers_pipeline_jobs_when_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    scheduler = IntelScheduler(
        storage=IntelStorage(tmp_path / "intel.db"),
        config={},
        full_config={
            "company_movement": {"enabled": True, "run_cron": "0 */6 * * *"},
            "hiring": {"enabled": True, "run_cron": "0 */12 * * *"},
            "regulatory": {"enabled": True, "run_cron": "0 */12 * * *"},
        },
    )

    scheduler._schedule_extended_jobs()

    assert scheduler.scheduler.get_job("company_movement_pipeline") is not None
    assert scheduler.scheduler.get_job("hiring_activity_pipeline") is not None
    assert scheduler.scheduler.get_job("regulatory_pipeline") is not None


def test_scheduler_registers_entity_extraction_job(tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    scheduler = IntelScheduler(
        storage=IntelStorage(tmp_path / "intel.db"),
        config={},
        full_config={"entity_extraction": {"enabled": True, "schedule_minutes": 15}},
    )

    scheduler._schedule_entity_extraction_job()

    assert scheduler.scheduler.get_job("entity_extraction") is not None

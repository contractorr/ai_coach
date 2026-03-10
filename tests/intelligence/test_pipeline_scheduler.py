from datetime import datetime, timedelta
from unittest.mock import MagicMock

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


def test_start_web_registers_full_job_set(tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    scheduler = IntelScheduler(
        storage=IntelStorage(tmp_path / "intel.db"),
        config={},
        full_config={
            "research": {"enabled": True},
            "recommendations": {"enabled": True, "delivery": {"schedule": "0 8 * * 0"}},
            "agent": {"enabled": True, "signals": {"schedule": "0 9 * * *"}},
            "heartbeat": {"enabled": True, "interval_minutes": 30},
            "trending_radar": {"enabled": True, "interval_hours": 6},
        },
    )
    scheduler.scheduler.start = MagicMock()

    scheduler.start_web()

    assert scheduler.scheduler.get_job("intel_gather") is not None
    assert scheduler.scheduler.get_job("deep_research") is not None
    assert scheduler.scheduler.get_job("weekly_recommendations") is not None
    assert scheduler.scheduler.get_job("signal_detection") is not None
    assert scheduler.scheduler.get_job("autonomous_actions") is not None
    assert scheduler.scheduler.get_job("goal_intel_matching") is not None
    assert scheduler.scheduler.get_job("trending_radar") is not None
    assert scheduler.scheduler.get_job("heartbeat") is not None


def test_web_scheduler_filters_research_jobs_to_users_with_personal_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    scheduler = IntelScheduler(
        storage=IntelStorage(tmp_path / "intel.db"),
        config={},
        full_config={"recommendations": {"enabled": True}},
        web_user_contexts_factory=lambda require_personal_key: (
            [{"user_id": "u1"}] if require_personal_key else [{"user_id": "u1"}, {"user_id": "u2"}]
        ),
    )

    contexts = scheduler._iter_web_user_contexts(require_personal_key=True)

    assert [ctx["user_id"] for ctx in contexts] == ["u1"]


def test_start_keeps_cli_job_set_minimal(tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    scheduler = IntelScheduler(
        storage=IntelStorage(tmp_path / "intel.db"),
        config={},
        full_config={"entity_extraction": {"enabled": True, "schedule_minutes": 15}},
    )
    scheduler.scheduler.start = MagicMock()

    scheduler.start()

    assert scheduler.scheduler.get_job("intel_gather") is not None
    assert scheduler.scheduler.get_job("entity_extraction") is not None
    assert scheduler.scheduler.get_job("deep_research") is None
    assert scheduler.scheduler.get_job("weekly_recommendations") is None
    assert scheduler.scheduler.get_job("signal_detection") is None

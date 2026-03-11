"""Tests for heartbeat on-demand LLM evaluation and supporting stores."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from advisor.insights import Insight, InsightStore, InsightType
from intelligence.heartbeat import ActionBriefStore, HeartbeatPipeline


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "intel.db"


@pytest.fixture
def brief_store(db_path):
    return ActionBriefStore(db_path)


@pytest.fixture
def insight_store(db_path):
    return InsightStore(db_path)


# --- ActionBriefStore.get_last_llm_run_at ---


def test_get_last_llm_run_at_none_when_empty(brief_store):
    assert brief_store.get_last_llm_run_at() is None


def test_get_last_llm_run_at_returns_latest_llm_run(brief_store):
    now = datetime.now()
    # Non-LLM run
    brief_store.log_run(
        {
            "started_at": (now - timedelta(hours=2)).isoformat(),
            "finished_at": (now - timedelta(hours=2)).isoformat(),
            "llm_used": 0,
        }
    )
    # LLM run
    llm_time = now - timedelta(hours=1)
    brief_store.log_run(
        {
            "started_at": llm_time.isoformat(),
            "finished_at": llm_time.isoformat(),
            "llm_used": 1,
        }
    )
    result = brief_store.get_last_llm_run_at()
    assert result is not None
    assert abs((result - llm_time).total_seconds()) < 2


# --- InsightStore.upsert ---


def test_upsert_inserts_new(insight_store):
    insight = Insight(
        type=InsightType.INTEL_MATCH,
        severity=5,
        title="Test Insight",
        detail="some detail",
        suggested_actions=["do something"],
    )
    assert insight_store.upsert(insight) is True
    active = insight_store.get_active()
    assert len(active) == 1
    assert active[0]["title"] == "Test Insight"


def test_upsert_updates_existing(insight_store):
    insight = Insight(
        type=InsightType.INTEL_MATCH,
        severity=3,
        title="Test Insight",
        detail="old detail",
        suggested_actions=["old action"],
    )
    insight_store.upsert(insight)

    updated = Insight(
        type=InsightType.INTEL_MATCH,
        severity=8,
        title="Test Insight",  # same hash
        detail="new detail",
        suggested_actions=["new action"],
    )
    assert insight_store.upsert(updated) is True
    active = insight_store.get_active()
    assert len(active) == 1
    assert active[0]["severity"] == 8
    assert active[0]["detail"] == "new detail"
    assert active[0]["suggested_actions"] == ["new action"]


# --- HeartbeatPipeline.evaluate_pending ---


def _make_pipeline(db_path, goals=None, config=None, items=None):
    storage = MagicMock()
    storage.get_items_since.return_value = items or []
    return HeartbeatPipeline(
        intel_storage=storage,
        goals=goals or [],
        db_path=db_path,
        config=config or {},
    )


def test_evaluate_pending_skips_within_cooldown(db_path):
    pipeline = _make_pipeline(db_path, goals=[{"title": "g", "path": "g.md"}])
    # Seed a recent LLM run
    store = ActionBriefStore(db_path)
    store.log_run(
        {
            "started_at": datetime.now().isoformat(),
            "finished_at": datetime.now().isoformat(),
            "llm_used": 1,
        }
    )
    result = pipeline.evaluate_pending()
    assert result == {"skipped": "cooldown"}


def test_evaluate_pending_skips_no_goals(db_path):
    pipeline = _make_pipeline(db_path, goals=[])
    result = pipeline.evaluate_pending()
    assert result == {"skipped": "no_goals"}


@patch("intelligence.heartbeat.HeartbeatEvaluator")
def test_evaluate_pending_runs_after_cooldown(mock_eval_cls, db_path):
    goals = [{"title": "Launch MVP", "path": "launch.md", "tags": ["mvp"]}]
    items = [
        {
            "id": 1,
            "url": "https://example.com/1",
            "title": "MVP tips",
            "summary": "good stuff",
            "source": "hn",
        }
    ]
    pipeline = _make_pipeline(
        db_path, goals=goals, config={"notification_cooldown_hours": 0}, items=items
    )

    mock_evaluator = MagicMock()
    mock_evaluator.evaluate.return_value = []
    mock_eval_cls.return_value = mock_evaluator

    result = pipeline.evaluate_pending(budget=3)
    assert result["llm_used"] == 1
    assert "skipped" not in result
    mock_eval_cls.assert_called_once_with(budget=3)

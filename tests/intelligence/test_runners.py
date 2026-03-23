"""Tests for extracted runner functions."""

from unittest.mock import MagicMock, patch

from intelligence.runners import (
    RecommendationRunner,
    ResearchRunner,
    RunnerContext,
    run_memory_consolidation,
    run_signal_detection,
    run_weekly_summary,
)
from intelligence.scraper import IntelStorage


def test_runner_context_defaults():
    storage = MagicMock(spec=IntelStorage)
    ctx = RunnerContext(storage=storage)
    assert ctx.journal_storage is None
    assert ctx.embeddings is None
    assert ctx.intel_embedding_mgr is None
    assert ctx.full_config == {}


def test_signal_detection_requires_journal_storage():
    ctx = RunnerContext(storage=MagicMock(), journal_storage=None)
    result = run_signal_detection(ctx)
    assert result == []


def test_memory_consolidation_disabled():
    ctx = RunnerContext(
        storage=MagicMock(),
        full_config={"memory": {"consolidation": {"enabled": False}}},
    )
    result = run_memory_consolidation(ctx)
    assert result == {"status": "disabled"}


def test_memory_consolidation_no_db(tmp_path):
    ctx = RunnerContext(
        storage=MagicMock(),
        full_config={
            "memory": {"consolidation": {"enabled": True}},
            "paths": {"memory_db": str(tmp_path / "nonexistent.db")},
        },
    )
    result = run_memory_consolidation(ctx)
    assert result == {"status": "no_db"}


@patch.dict("sys.modules", {"user_state_store": None})
def test_weekly_summary_handles_missing_module(tmp_path):
    """If user_state_store is not available, weekly summary should not crash."""
    ctx = RunnerContext(storage=MagicMock())
    # Should not raise
    run_weekly_summary(ctx)


def test_research_runner_returns_empty_without_deps():
    runner = ResearchRunner(
        storage=MagicMock(),
        journal_storage=None,
        embeddings=None,
        config={},
    )
    assert runner.run() == []
    assert runner.get_topics() == []
    assert runner.list_dossiers() == []


@patch("journal.fts.JournalFTSIndex")
@patch("journal.JournalSearch")
@patch("journal.EmbeddingManager")
@patch("advisor.rag.RAGRetriever")
@patch("advisor.engine.AdvisorEngine")
def test_recommendation_runner_from_runners_module(
    mock_advisor_cls, mock_rag_cls, mock_search_cls, mock_emb_cls, mock_fts_cls, tmp_path
):
    """RecommendationRunner works identically from runners module."""
    storage = MagicMock()
    storage.db_path = tmp_path / "intel.db"
    runner = RecommendationRunner(
        storage=storage,
        journal_storage=MagicMock(),
        config={"recommendations": {"enabled": True, "delivery": {"methods": ["email"]}}},
    )
    mock_advisor = MagicMock()
    mock_advisor.generate_recommendations.return_value = [object()]
    mock_advisor_cls.return_value = mock_advisor
    mock_rag_cls.return_value = MagicMock()
    mock_search_cls.return_value = MagicMock()
    mock_emb_cls.return_value = MagicMock()
    mock_fts_cls.return_value = MagicMock()

    result = runner.run()
    assert result == {"recommendations": 1, "brief_saved": False}

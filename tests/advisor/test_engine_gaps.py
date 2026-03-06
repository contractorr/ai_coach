"""Tests for AdvisorEngine coverage gaps — lines 157-176, 271-273, 325-338, 378-383, 415-420."""

from unittest.mock import MagicMock, patch

import pytest

from advisor.engine import AdvisorEngine, LLMError
from llm import LLMError as BaseLLMError


@pytest.fixture
def mock_rag():
    rag = MagicMock()
    rag.get_combined_context.return_value = ("journal ctx", "intel ctx")
    rag.get_recent_entries.return_value = "recent entries"
    rag.get_intel_context.return_value = "intel context"
    rag.get_journal_context.return_value = "journal context"
    rag.get_profile_context.return_value = "profile context"
    rag.get_research_context.return_value = ""
    rag.get_recurring_thoughts_context.return_value = ""
    rag.cache = None
    return rag


@pytest.fixture
def mock_client():
    client = MagicMock()
    resp = MagicMock()
    resp.content = [MagicMock(text="Mocked LLM response")]
    client.messages.create.return_value = resp
    return client


@pytest.fixture
def engine(mock_rag, mock_client):
    return AdvisorEngine(rag=mock_rag, provider="claude", client=mock_client)


# ── _call_cheap_llm (lines 157-176) ──


class TestCallCheapLLM:
    def test_successful_call(self, engine, mock_client):
        result = engine._call_cheap_llm("system", "prompt")
        assert result == "Mocked LLM response"

    def test_base_llm_error_raises_llm_error(self, engine, mock_client):
        mock_client.messages.create.side_effect = BaseLLMError("boom")
        with pytest.raises(LLMError, match="boom"):
            engine._call_cheap_llm("system", "prompt")

    def test_conversation_history_prepended(self, engine, mock_client):
        history = [{"role": "user", "content": "prior"}]
        engine._call_cheap_llm("sys", "new_prompt", conversation_history=history)
        call_args = mock_client.messages.create.call_args
        msgs = call_args.kwargs["messages"]
        assert msgs[0] == {"role": "user", "content": "prior"}
        assert msgs[1] == {"role": "user", "content": "new_prompt"}


# ── weekly_review with stale goals (lines 271-273) ──


class TestWeeklyReviewStaleGoals:
    def test_stale_goals_included_in_prompt(self, engine, mock_rag, mock_client):
        mock_storage = MagicMock()
        with patch("advisor.engine.GoalTracker") as MockTracker:
            tracker_inst = MockTracker.return_value
            tracker_inst.get_stale_goals.return_value = [
                {"title": "Learn Rust", "days_since_check": 15},
                {"title": "Write blog", "days_since_check": 30},
            ]
            engine.weekly_review(journal_storage=mock_storage)

        call_args = mock_client.messages.create.call_args
        user_msg = [m for m in call_args.kwargs["messages"] if m["role"] == "user"][0]
        assert "STALE GOALS" in user_msg["content"]
        assert "Learn Rust" in user_msg["content"]

    def test_recurring_thoughts_called(self, engine, mock_rag):
        mock_rag.get_recurring_thoughts_context.return_value = (
            "<recurring_thoughts>stuff</recurring_thoughts>"
        )
        engine.weekly_review()
        mock_rag.get_recurring_thoughts_context.assert_called_once()


# ── skill_gap via ask() ──


class TestSkillGapViaAsk:
    def test_skill_gap_advice_type(self, engine, mock_rag, mock_client):
        result = engine.ask("What skills should I learn?", advice_type="skill_gap")
        assert result == "Mocked LLM response"
        mock_rag.get_profile_context.assert_called()
        mock_rag.get_journal_context.assert_called()


# ── generate_recommendations category="all" (lines 378-383) ──


class TestGenerateRecommendationsAll:
    def test_all_category_flattens_and_sorts(self, engine, tmp_path):
        db_path = tmp_path / "recs.db"
        rec_a = MagicMock(score=8.0)
        rec_b = MagicMock(score=9.5)
        rec_c = MagicMock(score=7.0)

        with patch.object(engine, "_get_rec_engine") as mock_get:
            mock_engine = mock_get.return_value
            mock_engine.generate_all.return_value = {
                "learning": [rec_a],
                "career": [rec_b, rec_c],
            }
            result = engine.generate_recommendations("all", db_path)

        assert result[0].score == 9.5
        assert result[-1].score == 7.0
        assert len(result) == 3


# ── generate_action_brief save flag (lines 415-420) ──


class TestGenerateActionBriefSave:
    def test_save_true_calls_generate_and_save(self, engine, tmp_path):
        db_path = tmp_path / "recs.db"
        mock_js = MagicMock()

        with patch("advisor.engine.ActionBriefGenerator") as MockGen:
            MockGen.return_value.generate.return_value = "brief text"
            MockGen.return_value.generate_and_save.return_value = tmp_path / "brief.md"
            result = engine.generate_action_brief(db_path, journal_storage=mock_js, save=True)

        MockGen.return_value.generate_and_save.assert_called_once()
        assert result == "brief text"

    def test_save_false_only_generates(self, engine, tmp_path):
        db_path = tmp_path / "recs.db"

        with patch("advisor.engine.ActionBriefGenerator") as MockGen:
            MockGen.return_value.generate.return_value = "brief"
            result = engine.generate_action_brief(db_path, save=False)

        MockGen.return_value.generate_and_save.assert_not_called()
        assert result == "brief"

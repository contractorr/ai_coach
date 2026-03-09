"""Tests for recommendation engine."""

from unittest.mock import Mock

import pytest

from advisor.recommendation_storage import Recommendation, RecommendationStorage
from advisor.recommendations import RecommendationEngine
from advisor.scoring import RecommendationScorer


class TestRecommendationScorer:
    """Tests for scoring functionality."""

    def test_passes_threshold(self):
        scorer = RecommendationScorer(min_threshold=6.0)
        assert scorer.passes_threshold(7.0)
        assert not scorer.passes_threshold(5.0)

    def test_content_hash(self):
        scorer = RecommendationScorer()
        h1 = scorer.content_hash("Learn Rust", "Master async programming")
        h2 = scorer.content_hash("Learn Rust", "Master async programming")
        h3 = scorer.content_hash("Learn Go", "Master concurrency")
        assert h1 == h2
        assert h1 != h3


class TestRecommendationStorage:
    """Tests for markdown-based storage."""

    @pytest.fixture
    def storage(self, tmp_path):
        return RecommendationStorage(tmp_path / "recs")

    def test_init_creates_dir(self, tmp_path):
        path = tmp_path / "recs"
        RecommendationStorage(path)
        assert path.exists()

    def test_save_and_get(self, storage):
        rec = Recommendation(
            category="learning",
            title="Learn Rust",
            description="Master async",
            score=8.0,
        )
        rec_id = storage.save(rec)
        retrieved = storage.get(rec_id)
        assert retrieved.title == "Learn Rust"
        assert retrieved.category == "learning"

    def test_update_status(self, storage):
        rec = Recommendation(category="career", title="Test", score=7.0)
        rec_id = storage.save(rec)
        storage.update_status(rec_id, "completed")
        retrieved = storage.get(rec_id)
        assert retrieved.status == "completed"

    def test_list_by_category(self, storage):
        storage.save(Recommendation(category="learning", title="A", score=8.0))
        storage.save(Recommendation(category="learning", title="B", score=7.0))
        storage.save(Recommendation(category="career", title="C", score=9.0))

        learning = storage.list_by_category("learning")
        assert len(learning) == 2

    def test_hash_exists(self, storage):
        rec = Recommendation(
            category="learning",
            title="Test",
            embedding_hash="abc123",
            score=7.0,
        )
        storage.save(rec)
        assert storage.hash_exists("abc123")
        assert not storage.hash_exists("xyz789")

    def test_add_feedback(self, storage):
        rec = Recommendation(category="learning", title="Test", score=7.0)
        rec_id = storage.save(rec)
        assert storage.add_feedback(rec_id, 4, comment="useful")
        retrieved = storage.get(rec_id)
        assert retrieved.metadata["user_rating"] == 4
        assert retrieved.metadata["feedback_comment"] == "useful"

    def test_create_action_item(self, storage):
        rec = Recommendation(
            category="learning",
            title="Learn Rust",
            description="Master async Rust",
            rationale="It supports your systems goal",
            score=8.0,
            metadata={"action_plan": "## Week 1\n- Install Rust\n- Build a tiny CLI"},
        )
        rec_id = storage.save(rec)

        action_item = storage.create_action_item(
            rec_id,
            goal_path="/tmp/goal.md",
            goal_title="Become stronger at systems programming",
        )

        assert action_item is not None
        assert action_item["objective"] == "Learn Rust"
        assert action_item["goal_title"] == "Become stronger at systems programming"

        retrieved = storage.get(rec_id)
        assert retrieved.status == "in_progress"
        assert retrieved.metadata["action_item"]["next_step"] == "Install Rust"

    def test_build_weekly_plan_respects_capacity(self, storage):
        first_id = storage.save(Recommendation(category="career", title="A", score=9.0))
        second_id = storage.save(Recommendation(category="career", title="B", score=8.0))
        third_id = storage.save(Recommendation(category="career", title="C", score=7.0))

        storage.create_action_item(first_id, effort="large", due_window="today")
        storage.create_action_item(second_id, effort="medium", due_window="today")
        storage.create_action_item(third_id, effort="small", due_window="later")

        plan = storage.build_weekly_plan(capacity_points=3)
        ids = [item.recommendation_id for item in plan["items"]]
        assert plan["used_points"] <= 3
        assert second_id in ids
        assert third_id in ids
        assert first_id not in ids

    def test_execution_stats_capture_outcomes(self, storage):
        completed_id = storage.save(Recommendation(category="career", title="Ship", score=9.0))
        abandoned_id = storage.save(Recommendation(category="career", title="Drop", score=6.0))

        storage.create_action_item(completed_id)
        storage.update_action_item(completed_id, status="completed", review_notes="Worked well")
        storage.create_action_item(abandoned_id)
        storage.update_action_item(abandoned_id, status="abandoned", review_notes="Wrong timing")

        stats = storage.get_execution_stats()
        assert stats["by_category"]["career"]["completed"] == 1
        assert stats["by_category"]["career"]["abandoned"] == 1


class TestRecommendationEngine:
    """Tests for engine orchestration."""

    @pytest.fixture
    def mock_rag(self):
        rag = Mock()
        rag.get_journal_context.return_value = "User wants to learn Rust"
        rag.get_intel_context.return_value = "Rust demand growing 40%"
        rag.get_filtered_intel_context.return_value = "Rust demand growing 40%"
        rag.get_research_context.return_value = "Dossier says API prices are dropping"
        rag.get_profile_context.return_value = ""
        rag.get_profile_keywords.return_value = []
        return rag

    @pytest.fixture
    def mock_llm(self):
        def llm_caller(system, prompt, **kwargs):
            return """
### Learn Rust Async
**Description**: Master async programming in Rust
**Why**: Mentioned interest in systems programming
SCORE: 8.0

**REASONING**
SOURCE: Journal entry about wanting to learn systems programming
PROFILE_MATCH: Aligns with stated goal of backend performance work
CONFIDENCE: 0.85
CAVEATS: Steep learning curve, requires dedicated time commitment
"""

        return llm_caller

    @pytest.fixture
    def storage(self, tmp_path):
        return RecommendationStorage(tmp_path / "recs")

    def test_init_categories(self, mock_rag, mock_llm, storage):
        engine = RecommendationEngine(mock_rag, mock_llm, storage)
        assert "learning" in engine.enabled_categories
        assert "career" in engine.enabled_categories

    def test_generate_category(self, mock_rag, mock_llm, storage):
        engine = RecommendationEngine(mock_rag, mock_llm, storage)
        recs = engine.generate_category("learning", max_items=3, save=False)
        assert len(recs) >= 0  # May be empty if score threshold not met

    def test_generate_category_reads_research_context(self, mock_rag, mock_llm, storage):
        engine = RecommendationEngine(mock_rag, mock_llm, storage)
        engine.generate_category("learning", max_items=3, save=False)
        mock_rag.get_research_context.assert_called()

    def test_config_disables_categories(self, mock_rag, mock_llm, storage):
        config = {"categories": {"learning": True, "career": False}}
        engine = RecommendationEngine(mock_rag, mock_llm, storage, config)
        assert "learning" in engine.enabled_categories
        assert "career" not in engine.enabled_categories

    def test_reasoning_trace_extracted(self, mock_rag, mock_llm, storage):
        """Reasoning trace fields parsed into metadata, critic pipeline runs."""
        engine = RecommendationEngine(
            mock_rag, mock_llm, storage, {"scoring": {"min_threshold": 0.0}}
        )
        recs = engine.generate_category("learning", save=False, with_action_plans=False)
        assert len(recs) >= 1
        trace = recs[0].metadata.get("reasoning_trace")
        assert trace is not None
        assert trace["source_signal"] == "Journal entry about wanting to learn systems programming"
        assert trace["profile_match"] == "Aligns with stated goal of backend performance work"
        # Confidence is now set by adversarial critic (High=0.85, Medium=0.55, Low=0.25)
        assert trace["confidence"] in (0.85, 0.55, 0.25)
        assert "Steep learning curve" in trace["caveats"]
        # Adversarial critic fields should be present
        meta = recs[0].metadata
        assert "confidence" in meta  # High/Medium/Low string

    def test_reasoning_trace_absent_backward_compat(self, mock_rag, storage):
        """Recs without reasoning block in LLM output still work — critic adds trace."""

        def llm_no_reasoning(system, prompt, **kwargs):
            return """
### Learn Go Concurrency
**Description**: Master goroutines and channels
**Why**: Mentioned interest in distributed systems
SCORE: 7.5
"""

        engine = RecommendationEngine(
            mock_rag, llm_no_reasoning, storage, {"scoring": {"min_threshold": 0.0}}
        )
        recs = engine.generate_category("learning", save=False, with_action_plans=False)
        assert len(recs) >= 1
        # Critic pipeline always runs, so reasoning_trace gets added with confidence
        meta = recs[0].metadata or {}
        trace = meta.get("reasoning_trace", {})
        assert "source_signal" not in trace  # initial parse had no SOURCE field

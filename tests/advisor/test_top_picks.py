from unittest.mock import Mock

from advisor.recommendation_storage import Recommendation, RecommendationStorage
from advisor.recommendations import RecommendationEngine


def _make_rec(**overrides):
    defaults = dict(
        category="learning",
        title="Learn Rust Async",
        description="Master async programming in Rust",
        rationale="Strong demand in systems programming",
        score=8.0,
        metadata={},
    )
    defaults.update(overrides)
    return Recommendation(**defaults)


def _make_rag():
    rag = Mock()
    rag._profile_path = "~/coach/profile.yaml"
    rag.get_profile_context.return_value = "profile context"
    rag.get_intel_context.return_value = "recent intel"
    return rag


class TestTopPicksContrarianTarget:
    def test_contrarian_follows_displayed_top_pick(self, tmp_path):
        storage = RecommendationStorage(tmp_path / "recs")
        storage.save(_make_rec(title="Highest Score", score=9.5))
        storage.save(_make_rec(title="LLM Selected", score=8.5))

        llm = Mock(
            return_value=(
                "### TOP 1: [LEARNING] LLM Selected\n"
                "**Why this is #1 this week**: It is more urgent.\n"
                "**Key action**: Do it.\n"
                "ORIGINAL_SCORE: 8.5\n"
                "PICK_RANK: 1\n"
            )
        )
        cheap_llm = Mock(return_value="FLIP: NO")
        engine = RecommendationEngine(
            rag=_make_rag(),
            llm_caller=llm,
            storage=storage,
            cheap_llm_caller=cheap_llm,
        )

        engine.generate_top_picks(max_picks=1, pool_size=5)

        contrarian_prompt = cheap_llm.call_args.args[1]
        assert "Title: LLM Selected" in contrarian_prompt
        assert "Title: Highest Score" not in contrarian_prompt

    def test_falls_back_to_highest_score_when_top_pick_cannot_be_parsed(self, tmp_path):
        storage = RecommendationStorage(tmp_path / "recs")
        storage.save(_make_rec(title="Highest Score", score=9.5))
        storage.save(_make_rec(title="Other Pick", score=8.5))

        llm = Mock(return_value="Unstructured top picks output")
        cheap_llm = Mock(return_value="FLIP: NO")
        engine = RecommendationEngine(
            rag=_make_rag(),
            llm_caller=llm,
            storage=storage,
            cheap_llm_caller=cheap_llm,
        )

        engine.generate_top_picks(max_picks=1, pool_size=5)

        contrarian_prompt = cheap_llm.call_args.args[1]
        assert "Title: Highest Score" in contrarian_prompt

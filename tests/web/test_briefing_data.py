"""Tests for shared briefing data assembly."""

from advisor.recommendation_storage import Recommendation
from storage_access import create_recommendation_storage
from web.briefing_data import assemble_briefing_data
from web.deps import get_user_paths


def test_assemble_briefing_data_includes_harvested_outcome_for_recommendations():
    user_id = "user-123"
    paths = get_user_paths(user_id)
    storage = create_recommendation_storage(paths)
    rec_id = storage.save(
        Recommendation(
            category="projects",
            title="Ship MVP",
            description="Scope tightly and deliver the first version.",
            score=9.1,
            metadata={
                "action_item": {
                    "status": "completed",
                }
            },
        )
    )

    data = assemble_briefing_data(user_id)

    recommendation = next(item for item in data["recommendations"] if item["id"] == rec_id)
    assert recommendation["harvested_outcome"] is not None
    assert recommendation["harvested_outcome"]["state"] == "positive"
    assert recommendation["harvested_outcome"]["user_overridden"] is False

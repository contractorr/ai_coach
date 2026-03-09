"""Tests for shared recommendation action-item services."""

from advisor.recommendation_storage import Recommendation, RecommendationStorage
from services.recommendation_actions import (
    build_weekly_plan,
    create_action_item,
    list_action_items,
    update_action_item,
)


def _storage_for(tmp_path):
    return RecommendationStorage(tmp_path / "recommendations")


def test_create_action_item_returns_serialized_record(tmp_path):
    storage = _storage_for(tmp_path)
    rec_id = storage.save(Recommendation(category="projects", title="Ship MVP", score=8.8))

    result = create_action_item(storage, rec_id, due_window="today")

    assert result["success"] is True
    assert result["persisted"] is True
    assert result["record"]["recommendation_id"] == rec_id
    assert result["record"]["action_item"]["due_window"] == "today"


def test_update_action_item_returns_serialized_record(tmp_path):
    storage = _storage_for(tmp_path)
    rec_id = storage.save(Recommendation(category="learning", title="Learn Go", score=8.0))
    storage.create_action_item(rec_id)

    result = update_action_item(storage, rec_id, status="completed", review_notes="Done")

    assert result["success"] is True
    assert result["record"]["action_item"]["status"] == "completed"
    assert result["record"]["action_item"]["review_notes"] == "Done"


def test_list_and_weekly_plan_return_serialized_actions(tmp_path):
    storage = _storage_for(tmp_path)
    first = storage.save(Recommendation(category="career", title="One", score=8.0))
    second = storage.save(Recommendation(category="career", title="Two", score=7.0))
    storage.create_action_item(first)
    storage.create_action_item(second)
    storage.update_action_item(first, effort="small", due_window="today")
    storage.update_action_item(second, effort="large", due_window="later")

    actions = list_action_items(storage, limit=10)
    weekly_plan = build_weekly_plan(storage, capacity_points=2)

    assert actions["count"] == 2
    assert actions["actions"][0]["recommendation_id"] == first
    assert weekly_plan["used_points"] == 1
    assert len(weekly_plan["items"]) == 1
    assert weekly_plan["items"][0]["recommendation_id"] == first

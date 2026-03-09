"""Tests for recommendations execution routes."""

from advisor.recommendation_storage import Recommendation, RecommendationStorage


def _storage_for(tmp_path):
    return RecommendationStorage(tmp_path / "users" / "user-123" / "recommendations")


def test_recommendation_list_includes_action_item(client, auth_headers, tmp_path):
    storage = _storage_for(tmp_path)
    rec_id = storage.save(Recommendation(category="career", title="Apply", score=8.0))
    storage.create_action_item(rec_id)

    res = client.get("/api/recommendations", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["action_item"]["status"] == "accepted"


def test_create_goal_linked_action_item(client, auth_headers, tmp_path):
    goal_res = client.post(
        "/api/goals",
        headers=auth_headers,
        json={"title": "Launch side project", "content": "Ship something small"},
    )
    goal_path = goal_res.json()["path"]

    storage = _storage_for(tmp_path)
    rec_id = storage.save(Recommendation(category="projects", title="Ship MVP", score=9.0))

    res = client.post(
        f"/api/recommendations/{rec_id}/action-item",
        headers=auth_headers,
        json={"goal_path": goal_path},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["action_item"]["goal_path"] == goal_path
    assert data["action_item"]["status"] == "accepted"


def test_update_action_item_and_weekly_plan(client, auth_headers, tmp_path):
    storage = _storage_for(tmp_path)
    rec_id = storage.save(Recommendation(category="learning", title="Learn Go", score=8.0))
    storage.create_action_item(rec_id)

    update_res = client.put(
        f"/api/recommendations/{rec_id}/action-item",
        headers=auth_headers,
        json={"effort": "small", "due_window": "today", "review_notes": "Looks feasible"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["action_item"]["effort"] == "small"

    weekly_res = client.get("/api/recommendations/weekly-plan", headers=auth_headers)
    assert weekly_res.status_code == 200
    plan = weekly_res.json()
    assert plan["items"][0]["recommendation_id"] == rec_id


def test_list_action_items_can_filter_by_status(client, auth_headers, tmp_path):
    storage = _storage_for(tmp_path)
    first = storage.save(Recommendation(category="career", title="One", score=8.0))
    second = storage.save(Recommendation(category="career", title="Two", score=7.0))
    storage.create_action_item(first)
    storage.create_action_item(second)
    storage.update_action_item(second, status="completed")

    res = client.get("/api/recommendations/actions?status=completed", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["recommendation_id"] == second


def test_add_recommendation_feedback(client, auth_headers, tmp_path):
    storage = _storage_for(tmp_path)
    rec_id = storage.save(Recommendation(category="career", title="Reach out", score=8.4))

    res = client.post(
        f"/api/recommendations/{rec_id}/feedback",
        headers=auth_headers,
        json={"rating": 4, "comment": "Strong fit for this week"},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == rec_id
    assert data["user_rating"] == 4
    assert data["feedback_comment"] == "Strong fit for this week"
    assert data["feedback_at"] is not None

    stored = storage.get(rec_id)
    assert stored is not None
    assert stored.metadata["user_rating"] == 4
    assert stored.metadata["feedback_comment"] == "Strong fit for this week"
    assert stored.metadata["feedback_at"] is not None

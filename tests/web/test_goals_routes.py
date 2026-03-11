"""Tests for goals API routes."""

from pathlib import Path


def test_list_empty(client, auth_headers):
    res = client.get("/api/goals", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_create_goal(client, auth_headers):
    res = client.post(
        "/api/goals",
        headers=auth_headers,
        json={"title": "Learn Rust", "content": "Systems programming goal"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Learn Rust"
    assert "path" in data


def test_create_and_list(client, auth_headers):
    client.post(
        "/api/goals",
        headers=auth_headers,
        json={"title": "Goal 1"},
    )
    res = client.get("/api/goals", headers=auth_headers)
    assert res.status_code == 200
    goals = res.json()
    assert len(goals) == 1
    assert goals[0]["title"] == "Goal 1"


def test_check_in_goal(client, auth_headers):
    create_res = client.post(
        "/api/goals",
        headers=auth_headers,
        json={"title": "Learn Rust", "content": "Systems programming goal"},
    )
    path = create_res.json()["path"]

    res = client.post(
        f"/api/goals/{path}/check-in",
        headers=auth_headers,
        json={"notes": "Made progress this week"},
    )

    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_goal_mutations_reject_non_goal_entries(client, auth_headers):
    create_res = client.post(
        "/api/journal",
        headers=auth_headers,
        json={"content": "A daily note", "entry_type": "daily", "title": "Daily note"},
    )
    path = create_res.json()["path"]
    original = Path(path).read_text(encoding="utf-8")

    requests = [
        ("post", f"/api/goals/{path}/check-in", {"notes": "Should fail"}),
        ("put", f"/api/goals/{path}/status", {"status": "completed"}),
        ("post", f"/api/goals/{path}/milestones", {"title": "Should fail"}),
        ("post", f"/api/goals/{path}/milestones/complete", {"milestone_index": 0}),
    ]

    for method, url, payload in requests:
        response = getattr(client, method)(url, headers=auth_headers, json=payload)
        assert response.status_code == 404
        assert response.json()["detail"] == "Goal not found"
        assert Path(path).read_text(encoding="utf-8") == original


def test_goal_progress_rejects_non_goal_entries(client, auth_headers):
    create_res = client.post(
        "/api/journal",
        headers=auth_headers,
        json={"content": "A daily note", "entry_type": "daily", "title": "Daily note"},
    )
    path = create_res.json()["path"]

    res = client.get(f"/api/goals/{path}/progress", headers=auth_headers)

    assert res.status_code == 404
    assert res.json()["detail"] == "Goal not found"

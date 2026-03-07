"""Tests for memory API routes."""

from unittest.mock import patch

import web.deps as web_deps
from memory.models import FactCategory, FactSource, StewardFact
from memory.store import FactStore


def _seed_store(user_id: str):
    paths = web_deps.get_user_paths(user_id)
    return FactStore(paths["memory_db"], chroma_dir=None)


def _route_store(user_id: str):
    return _seed_store(user_id)


def test_memory_facts_crud_and_stats(client, auth_headers):
    store = _seed_store("user-123")
    fact = StewardFact(
        id="fact-1",
        text="User prefers Python for APIs",
        category=FactCategory.PREFERENCE,
        source_type=FactSource.JOURNAL,
        source_id="entry-1",
        confidence=0.92,
    )
    store.add(fact)

    with patch("web.routes.memory._get_store", side_effect=_route_store):
        list_response = client.get("/api/memory/facts", headers=auth_headers)
        assert list_response.status_code == 200
        assert list_response.json()[0]["id"] == "fact-1"
        assert list_response.json()[0]["category"] == "preference"

        get_response = client.get("/api/memory/facts/fact-1", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["text"] == "User prefers Python for APIs"

        stats_response = client.get("/api/memory/stats", headers=auth_headers)
        assert stats_response.status_code == 200
        assert stats_response.json()["total_active"] == 1
        assert stats_response.json()["by_category"] == {"preference": 1}

        delete_response = client.delete("/api/memory/facts/fact-1", headers=auth_headers)
        assert delete_response.status_code == 200
        assert delete_response.json() == {"ok": True}

        list_after_delete = client.get("/api/memory/facts", headers=auth_headers)
        assert list_after_delete.status_code == 200
        assert list_after_delete.json() == []


def test_memory_category_filter_and_validation(client, auth_headers):
    store = _seed_store("user-123")
    store.add(
        StewardFact(
            id="skill-1",
            text="User knows FastAPI",
            category=FactCategory.SKILL,
            source_type=FactSource.JOURNAL,
            source_id="entry-2",
            confidence=0.88,
        )
    )

    with patch("web.routes.memory._get_store", side_effect=_route_store):
        response = client.get("/api/memory/facts?category=skill", headers=auth_headers)
        assert response.status_code == 200
        assert [item["id"] for item in response.json()] == ["skill-1"]

        invalid = client.get("/api/memory/facts?category=unknown", headers=auth_headers)
        assert invalid.status_code == 400
        assert invalid.json() == {"detail": "Invalid category: unknown"}


def test_memory_is_isolated_per_user(client, auth_headers, auth_headers_b):
    store = _seed_store("user-123")
    store.add(
        StewardFact(
            id="private-fact",
            text="User is planning a confidential move",
            category=FactCategory.CONTEXT,
            source_type=FactSource.JOURNAL,
            source_id="entry-3",
            confidence=0.7,
        )
    )

    with patch("web.routes.memory._get_store", side_effect=_route_store):
        response = client.get("/api/memory/facts", headers=auth_headers_b)

        assert response.status_code == 200
        assert response.json() == []

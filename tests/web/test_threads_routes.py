"""Tests for threads API routes."""

import asyncio
from datetime import datetime

import web.deps as web_deps
from journal.thread_store import ThreadStore


def test_list_threads_and_get_detail(client, auth_headers):
    paths = web_deps.get_user_paths("user-123")
    store = ThreadStore(paths["threads_db"])

    thread = asyncio.run(store.create_thread("Weekly planning"))
    asyncio.run(store.add_entry(thread.id, "entry-1", 0.9876, datetime(2026, 3, 1)))
    asyncio.run(store.add_entry(thread.id, "entry-2", 0.8123, datetime(2026, 3, 3)))

    list_response = client.get("/api/threads", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json() == [
        {
            "id": thread.id,
            "label": "Weekly planning",
            "entry_count": 2,
            "first_date": "2026-03-01",
            "last_date": "2026-03-03",
            "status": "active",
        }
    ]

    detail_response = client.get(f"/api/threads/{thread.id}", headers=auth_headers)
    assert detail_response.status_code == 200
    assert detail_response.json() == {
        "id": thread.id,
        "label": "Weekly planning",
        "entry_count": 2,
        "entries": [
            {"entry_id": "entry-1", "entry_date": "2026-03-01", "similarity": 0.988},
            {"entry_id": "entry-2", "entry_date": "2026-03-03", "similarity": 0.812},
        ],
    }


def test_get_thread_not_found(client, auth_headers):
    response = client.get("/api/threads/missing-thread", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Thread not found"}


def test_threads_are_isolated_per_user(client, auth_headers, auth_headers_b):
    paths = web_deps.get_user_paths("user-123")
    store = ThreadStore(paths["threads_db"])

    thread = asyncio.run(store.create_thread("Private thread"))
    asyncio.run(store.add_entry(thread.id, "entry-1", 0.9, datetime(2026, 3, 2)))
    asyncio.run(store.add_entry(thread.id, "entry-2", 0.8, datetime(2026, 3, 4)))

    response = client.get("/api/threads", headers=auth_headers_b)

    assert response.status_code == 200
    assert response.json() == []

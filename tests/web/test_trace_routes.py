"""Tests for trace API endpoints."""

import pytest

from advisor.trace_store import write_trace


@pytest.fixture
def _seed_trace():
    """Write a trace to the test user's data dir."""
    from pathlib import Path

    from web.deps import get_user_paths

    paths = get_user_paths("user-123")
    data_dir = Path(paths["data_dir"])
    entries = [
        {"v": 1, "type": "session_start", "ts": 1000.0, "session_id": "abcdef1234567890"},
        {"v": 1, "type": "answer", "ts": 1001.0, "iteration": 0, "chars": 5},
    ]
    write_trace(data_dir, "abcdef1234567890", entries)
    return data_dir


class TestListTraces:
    def test_empty_list(self, client, auth_headers):
        resp = client.get("/api/advisor/traces", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_seed(self, client, auth_headers, _seed_trace):
        resp = client.get("/api/advisor/traces", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["session_id"] == "abcdef1234567890"
        assert data[0]["size_bytes"] > 0


class TestGetTrace:
    def test_not_found(self, client, auth_headers):
        resp = client.get("/api/advisor/traces/0000000000000000", headers=auth_headers)
        assert resp.status_code == 404

    def test_bad_session_id(self, client, auth_headers):
        resp = client.get("/api/advisor/traces/ZZZZ_bad_session!", headers=auth_headers)
        assert resp.status_code == 400

    def test_read_seeded_trace(self, client, auth_headers, _seed_trace):
        resp = client.get("/api/advisor/traces/abcdef1234567890", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == "abcdef1234567890"
        assert len(data["entries"]) == 2
        assert data["from_line"] == 0

    def test_from_line_offset(self, client, auth_headers, _seed_trace):
        resp = client.get("/api/advisor/traces/abcdef1234567890?from_line=1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["type"] == "answer"
        assert data["from_line"] == 1

"""Tests for greeting API routes."""

from unittest.mock import MagicMock, patch

from advisor.greeting import STATIC_FALLBACK


def test_greeting_returns_fallback_when_no_cache(client, auth_headers, tmp_path):
    """First call returns static fallback with stale=True."""
    with patch("web.routes.greeting._get_cache") as mock_cache:
        cache = MagicMock()
        cache.get.return_value = None  # no cached greeting
        mock_cache.return_value = cache

        res = client.get("/api/greeting", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data["text"] == STATIC_FALLBACK
    assert data["cached"] is False
    assert data["stale"] is True


def test_greeting_returns_cached(client, auth_headers, tmp_path):
    """When cache has a greeting, return it with cached=True."""
    with patch("web.routes.greeting._get_cache") as mock_cache:
        cache = MagicMock()
        cache.get.return_value = None
        mock_cache.return_value = cache

        with patch("web.routes.greeting.get_cached_greeting", return_value="Hello from cache"):
            res = client.get("/api/greeting", headers=auth_headers)

    assert res.status_code == 200
    data = res.json()
    assert data["text"] == "Hello from cache"
    assert data["cached"] is True
    assert data["stale"] is False


def test_greeting_unauthenticated(client):
    """No token = 401."""
    res = client.get("/api/greeting")
    assert res.status_code in (401, 403)

"""Tests for settings routes (per-user)."""

import os
from unittest.mock import patch


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_get_settings_unauthed(client):
    res = client.get("/api/settings")
    # HTTPBearer returns 403 when no Authorization header
    assert res.status_code in (401, 403)


def test_get_settings(client, auth_headers, secret_key):
    with patch.dict(os.environ, {"SECRET_KEY": secret_key}):
        res = client.get("/api/settings", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "llm_api_key_set" in data
        assert data["llm_api_key_set"] is False
        assert data["llm_council_enabled"] is True
        assert data["llm_council_ready"] is False
        assert len(data["llm_provider_keys"]) == 3


def test_put_settings(client, auth_headers, secret_key, users_db):
    with patch.dict(os.environ, {"SECRET_KEY": secret_key}):
        # Need real user_store for write path
        from web.user_store import get_or_create_user, init_db

        init_db(users_db)
        get_or_create_user("user-123", db_path=users_db)

        with (
            patch("web.user_store._DEFAULT_DB_PATH", users_db),
            patch("web.routes.settings.set_user_secret", wraps=_real_set_user_secret(users_db)),
        ):
            res = client.put(
                "/api/settings",
                headers=auth_headers,
                json={
                    "llm_provider": "claude",
                    "llm_api_key_claude": "sk-ant-test1234",
                    "llm_api_key_openai": "sk-openai5678",
                    "llm_council_enabled": True,
                },
            )
            assert res.status_code == 200
            data = res.json()
            assert data["llm_api_key_set"] is True
            assert data["llm_api_key_hint"] == "...1234"
            assert data["llm_provider"] == "claude"
            assert data["llm_council_ready"] is True
            configured = {item["provider"]: item["configured"] for item in data["llm_provider_keys"]}
            assert configured == {"claude": True, "openai": True, "gemini": False}


def test_put_settings_can_remove_provider_key(client, auth_headers, secret_key, users_db):
    with patch.dict(os.environ, {"SECRET_KEY": secret_key}):
        from web.user_store import get_or_create_user, init_db

        init_db(users_db)
        get_or_create_user("user-123", db_path=users_db)

        with (
            patch("web.user_store._DEFAULT_DB_PATH", users_db),
            patch("web.routes.settings.set_user_secret", wraps=_real_set_user_secret(users_db)),
            patch("web.routes.settings.delete_user_secret", wraps=_real_delete_user_secret(users_db)),
        ):
            res = client.put(
                "/api/settings",
                headers=auth_headers,
                json={
                    "llm_provider": "claude",
                    "llm_api_key_claude": "sk-ant-test1234",
                    "llm_api_key_openai": "sk-openai5678",
                },
            )
            assert res.status_code == 200

            res = client.put(
                "/api/settings",
                headers=auth_headers,
                json={"llm_remove_providers": ["openai"]},
            )
            assert res.status_code == 200
            data = res.json()
            configured = {item["provider"]: item["configured"] for item in data["llm_provider_keys"]}
            assert configured == {"claude": True, "openai": False, "gemini": False}
            assert data["llm_council_ready"] is False


def _real_set_user_secret(db_path):
    """Return a wrapper that forces db_path for set_user_secret calls in test."""
    from web.user_store import set_user_secret as _original

    def _wrapper(user_id, key, value, fernet_key):
        return _original(user_id, key, value, fernet_key, db_path)

    return _wrapper


def _real_delete_user_secret(db_path):
    """Return a wrapper that forces db_path for delete_user_secret calls in test."""
    from web.user_store import delete_user_secret as _original

    def _wrapper(user_id, key):
        return _original(user_id, key, db_path)

    return _wrapper

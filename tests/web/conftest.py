"""Shared fixtures for web API tests."""

import os
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from jose import jwt

from web.rate_limit import reset_rate_limits
from web.user_store import init_db


@pytest.fixture
def secret_key():
    return Fernet.generate_key().decode()


@pytest.fixture
def jwt_secret():
    return "test-nextauth-secret"


@pytest.fixture
def auth_token(jwt_secret):
    return jwt.encode(
        {"sub": "user-123", "email": "test@example.com", "name": "Test"},
        jwt_secret,
        algorithm="HS256",
    )


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


def _make_auth_token(jwt_secret, user_id, email="u@test.com", name="U"):
    return jwt.encode(
        {"sub": user_id, "email": email, "name": name},
        jwt_secret,
        algorithm="HS256",
    )


@pytest.fixture
def auth_token_b(jwt_secret):
    """Second user token for isolation tests."""
    return _make_auth_token(jwt_secret, "user-456", "b@test.com", "UserB")


@pytest.fixture
def auth_headers_b(auth_token_b):
    return {"Authorization": f"Bearer {auth_token_b}"}


@pytest.fixture
def mock_paths(tmp_path):
    """Each test gets a fresh temp directory."""
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    return {
        "journal_dir": journal_dir,
        "chroma_dir": tmp_path / "chroma",
        "intel_db": tmp_path / "intel.db",
        "log_file": tmp_path / "coach.log",
    }


@pytest.fixture
def users_db(tmp_path):
    """Fresh users.db for each test."""
    db_path = tmp_path / "users.db"
    init_db(db_path)
    return db_path


@pytest.fixture
def client(jwt_secret, secret_key, tmp_path, users_db):
    """Test client with per-user tmp dirs."""
    env = {
        "NEXTAUTH_SECRET": jwt_secret,
        "SECRET_KEY": secret_key,
        "ANTHROPIC_API_KEY": "test-key",
    }

    def _mock_user_paths(user_id: str) -> dict:
        base = tmp_path / "users" / user_id
        base.mkdir(parents=True, exist_ok=True)
        jdir = base / "journal"
        jdir.mkdir(exist_ok=True)
        return {
            "journal_dir": jdir,
            "chroma_dir": base / "chroma",
            "recommendations_dir": base / "recommendations",
            "profile": base / "profile.yaml",
            "intel_db": tmp_path / "intel.db",
        }

    patches = [
        patch.dict(os.environ, env),
        patch("web.deps.get_user_paths", side_effect=_mock_user_paths),
        patch("web.routes.journal.get_user_paths", side_effect=_mock_user_paths),
        patch("web.routes.goals.get_user_paths", side_effect=_mock_user_paths),
        patch("web.routes.insights.get_user_paths", side_effect=_mock_user_paths),
        patch(
            "web.routes.intel.get_coach_paths",
            return_value={
                "journal_dir": tmp_path / "journal",
                "chroma_dir": tmp_path / "chroma",
                "intel_db": tmp_path / "intel.db",
                "log_file": tmp_path / "coach.log",
            },
        ),
        # user_store uses test DB — real get_or_create_user so FK rows exist
        patch("web.user_store._DEFAULT_DB_PATH", users_db),
        # Disable rate limiting and shared-key blocks in tests (env key = shared)
        patch("web.routes.advisor.check_shared_key_rate_limit", lambda uid, **kw: None),
        patch("web.routes.onboarding.check_shared_key_rate_limit", lambda uid, **kw: None),
        patch("web.routes.research._check_shared_key", lambda uid: None),
    ]

    for p in patches:
        p.start()

    from web.app import app

    reset_rate_limits()
    yield TestClient(app)

    for p in reversed(patches):
        p.stop()
    reset_rate_limits()

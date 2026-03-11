"""Shared fixtures for web API tests."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from jose import jwt

from web.deps import (
    enforce_onboarding_shared_key_usage_limit,
    enforce_shared_key_usage_limit,
    require_personal_research_key,
)
from web.rate_limit import reset_rate_limits
from web.user_store import init_db

TEST_JWT_SECRET = "test-nextauth-secret"
TEST_SECRET_KEY = Fernet.generate_key().decode()


@pytest.fixture
def secret_key():
    return TEST_SECRET_KEY


@pytest.fixture
def jwt_secret():
    return TEST_JWT_SECRET


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
def users_db(tmp_path):
    """Fresh users.db for each test."""
    db_path = tmp_path / "users.db"
    init_db(db_path)
    return db_path


@pytest.fixture(scope="session")
def app():
    from web.app import create_app

    env = {
        "NEXTAUTH_SECRET": TEST_JWT_SECRET,
        "SECRET_KEY": TEST_SECRET_KEY,
        "ANTHROPIC_API_KEY": "test-key",
        "DISABLE_INTEL_SCHEDULER": "1",
    }
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        app = create_app()
        yield app
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@pytest.fixture(autouse=True)
def _web_test_state(app, tmp_path):
    import web.routes.greeting as greeting_routes
    import web.routes.journal as journal_routes

    coach_home = Path(tmp_path)
    previous = {
        "COACH_HOME": os.environ.get("COACH_HOME"),
        "COACH_USERS_DB_PATH": os.environ.get("COACH_USERS_DB_PATH"),
    }
    os.environ["COACH_HOME"] = str(coach_home)
    os.environ["COACH_USERS_DB_PATH"] = str(coach_home / "users.db")

    init_db()
    reset_rate_limits()

    app.dependency_overrides[enforce_shared_key_usage_limit] = lambda: None
    app.dependency_overrides[enforce_onboarding_shared_key_usage_limit] = lambda: None
    app.dependency_overrides[require_personal_research_key] = lambda: None

    original_schedule_greeting = greeting_routes._schedule_greeting_refresh
    original_schedule_heartbeat = greeting_routes._schedule_heartbeat_eval
    original_schedule_hooks = journal_routes._schedule_post_create_hooks
    greeting_routes._schedule_greeting_refresh = MagicMock(name="schedule_greeting_refresh")
    greeting_routes._schedule_heartbeat_eval = MagicMock(name="schedule_heartbeat_eval")
    journal_routes._schedule_post_create_hooks = MagicMock(name="schedule_post_create_hooks")

    try:
        yield
    finally:
        greeting_routes._schedule_greeting_refresh = original_schedule_greeting
        greeting_routes._schedule_heartbeat_eval = original_schedule_heartbeat
        journal_routes._schedule_post_create_hooks = original_schedule_hooks
        app.dependency_overrides.clear()
        reset_rate_limits()
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@pytest.fixture(scope="session")
def client(app):
    """Shared test client with per-test env isolation."""
    with TestClient(app) as test_client:
        yield test_client

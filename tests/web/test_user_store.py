"""Tests for user_store: user CRUD, secrets CRUD, isolation."""

import sqlite3

from cryptography.fernet import Fernet

from web.user_store import (
    delete_user,
    delete_user_secret,
    get_feedback_count,
    get_or_create_user,
    get_user_secret,
    get_user_secrets,
    init_db,
    log_engagement,
    log_event,
    set_user_secret,
)
from web.conversation_store import create_conversation


def test_create_user(tmp_path):
    db = tmp_path / "users.db"
    init_db(db)
    user = get_or_create_user("u1", email="a@b.com", name="Alice", db_path=db)
    assert user["id"] == "u1"
    assert user["email"] == "a@b.com"


def test_idempotent_upsert(tmp_path):
    db = tmp_path / "users.db"
    init_db(db)
    get_or_create_user("u1", email="a@b.com", name="Alice", db_path=db)
    user = get_or_create_user("u1", email="new@b.com", name="Alice2", db_path=db)
    assert user["email"] == "new@b.com"
    # Existing name is preserved (not overwritten by OAuth name)
    assert user["name"] == "Alice"


def test_set_get_secret(tmp_path):
    db = tmp_path / "users.db"
    fernet_key = Fernet.generate_key().decode()
    init_db(db)
    get_or_create_user("u1", db_path=db)

    set_user_secret("u1", "llm_api_key", "sk-abc", fernet_key, db)
    val = get_user_secret("u1", "llm_api_key", fernet_key, db)
    assert val == "sk-abc"


def test_get_all_secrets(tmp_path):
    db = tmp_path / "users.db"
    fernet_key = Fernet.generate_key().decode()
    init_db(db)
    get_or_create_user("u1", db_path=db)

    set_user_secret("u1", "key_a", "val_a", fernet_key, db)
    set_user_secret("u1", "key_b", "val_b", fernet_key, db)

    secrets = get_user_secrets("u1", fernet_key, db)
    assert secrets == {"key_a": "val_a", "key_b": "val_b"}


def test_overwrite_secret(tmp_path):
    db = tmp_path / "users.db"
    fernet_key = Fernet.generate_key().decode()
    init_db(db)
    get_or_create_user("u1", db_path=db)

    set_user_secret("u1", "key", "v1", fernet_key, db)
    set_user_secret("u1", "key", "v2", fernet_key, db)
    assert get_user_secret("u1", "key", fernet_key, db) == "v2"


def test_delete_secret(tmp_path):
    db = tmp_path / "users.db"
    fernet_key = Fernet.generate_key().decode()
    init_db(db)
    get_or_create_user("u1", db_path=db)

    set_user_secret("u1", "key", "val", fernet_key, db)
    delete_user_secret("u1", "key", db)
    assert get_user_secret("u1", "key", fernet_key, db) is None


def test_secrets_isolation(tmp_path):
    """User A's secrets invisible to User B."""
    db = tmp_path / "users.db"
    fernet_key = Fernet.generate_key().decode()
    init_db(db)
    get_or_create_user("alice", db_path=db)
    get_or_create_user("bob", db_path=db)

    set_user_secret("alice", "api_key", "sk-alice", fernet_key, db)
    set_user_secret("bob", "api_key", "sk-bob", fernet_key, db)

    assert get_user_secret("alice", "api_key", fernet_key, db) == "sk-alice"
    assert get_user_secret("bob", "api_key", fernet_key, db) == "sk-bob"
    assert get_user_secrets("alice", fernet_key, db) == {"api_key": "sk-alice"}


def test_missing_secret_returns_none(tmp_path):
    db = tmp_path / "users.db"
    fernet_key = Fernet.generate_key().decode()
    init_db(db)
    get_or_create_user("u1", db_path=db)
    assert get_user_secret("u1", "nonexistent", fernet_key, db) is None


def test_wrong_fernet_key_returns_none(tmp_path):
    """Secret saved with key1, loaded with key2 → None (simulates SECRET_KEY rotation)."""
    db = tmp_path / "users.db"
    key1 = Fernet.generate_key().decode()
    key2 = Fernet.generate_key().decode()
    init_db(db)
    get_or_create_user("u1", db_path=db)

    set_user_secret("u1", "llm_api_key", "sk-abc", key1, db)
    assert get_user_secret("u1", "llm_api_key", key2, db) is None


def test_wrong_fernet_key_skips_in_get_all(tmp_path):
    """get_user_secrets skips entries that fail to decrypt."""
    db = tmp_path / "users.db"
    key1 = Fernet.generate_key().decode()
    key2 = Fernet.generate_key().decode()
    init_db(db)
    get_or_create_user("u1", db_path=db)

    set_user_secret("u1", "api_key", "sk-123", key1, db)
    set_user_secret("u1", "other_key", "val", key1, db)

    secrets = get_user_secrets("u1", key2, db)
    assert secrets == {}


def test_delete_user(tmp_path):
    """Delete user removes user + secrets, cascades conversations."""
    db = tmp_path / "users.db"
    fernet_key = Fernet.generate_key().decode()
    init_db(db)
    get_or_create_user("u1", email="a@b.com", name="Alice", db_path=db)
    set_user_secret("u1", "api_key", "sk-123", fernet_key, db)

    assert delete_user("u1", db) is True

    # User gone
    user = get_or_create_user("u1", db_path=db)
    assert user["email"] is None  # freshly created, no email
    # Secrets gone
    assert get_user_secret("u1", "api_key", fernet_key, db) is None


def test_delete_nonexistent_user(tmp_path):
    db = tmp_path / "users.db"
    init_db(db)
    assert delete_user("ghost", db) is False


def test_last_login_set_on_create_and_updated_on_upsert(tmp_path):
    db = tmp_path / "users.db"
    init_db(db)
    user = get_or_create_user("u1", email="a@b.com", name="Alice", db_path=db)
    assert user["last_login"] is not None
    first_login = user["last_login"]

    user2 = get_or_create_user("u1", email="a@b.com", db_path=db)
    assert user2["last_login"] >= first_login


def test_feedback_count_includes_numeric_and_binary_feedback(tmp_path):
    db = tmp_path / "users.db"
    init_db(db)
    get_or_create_user("u1", db_path=db)

    log_engagement("u1", "feedback_useful", "recommendation", "rec-1", db_path=db)
    log_event("recommendation_feedback", "u1", {"rating": 5, "score": 1}, db_path=db)

    assert get_feedback_count("u1", db_path=db) == 2


def test_duplicate_email_secret_migration_preserves_historical_rows(tmp_path):
    db = tmp_path / "users.db"
    fernet_key = Fernet.generate_key().decode()
    init_db(db)

    get_or_create_user("legacy-id", email="a@b.com", name="Legacy", db_path=db)
    set_user_secret("legacy-id", "api_key", "sk-legacy", fernet_key, db)
    conversation_id = create_conversation("legacy-id", "Legacy conversation", db_path=db)

    conn = sqlite3.connect(db)
    try:
        conn.execute(
            "INSERT INTO onboarding_responses (user_id, turn_number, role, content) VALUES (?, ?, ?, ?)",
            ("legacy-id", 1, "user", "hello"),
        )
        conn.commit()
    finally:
        conn.close()

    migrated_user = get_or_create_user("new-id", email="a@b.com", name="Current", db_path=db)

    assert migrated_user["id"] == "new-id"
    assert get_user_secret("new-id", "api_key", fernet_key, db) == "sk-legacy"

    conn = sqlite3.connect(db)
    try:
        conversation_row = conn.execute(
            "SELECT user_id FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        onboarding_row = conn.execute(
            "SELECT user_id FROM onboarding_responses WHERE user_id = ?",
            ("legacy-id",),
        ).fetchone()
        legacy_user = conn.execute(
            "SELECT id FROM users WHERE id = ?",
            ("legacy-id",),
        ).fetchone()
    finally:
        conn.close()

    assert conversation_row == ("legacy-id",)
    assert onboarding_row == ("legacy-id",)
    assert legacy_user == ("legacy-id",)

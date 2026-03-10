"""Multi-user SQLite store: users table + per-user encrypted secrets."""

import json as _json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from db import wal_connect
from web.crypto import decrypt_value, encrypt_value

logger = structlog.get_logger()

_DEFAULT_DB_PATH = Path(os.environ.get("COACH_HOME", Path.home() / "coach")) / "users.db"


def get_default_db_path() -> Path:
    """Resolve the default users DB path from the current environment."""
    explicit_path = os.environ.get("COACH_USERS_DB_PATH")
    if explicit_path:
        return Path(explicit_path).expanduser()

    coach_home = os.environ.get("COACH_HOME")
    if coach_home:
        return Path(coach_home).expanduser() / "users.db"

    return _DEFAULT_DB_PATH


def _get_conn(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = wal_connect(path, row_factory=True)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Create tables if they don't exist."""
    conn = _get_conn(db_path)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_secrets (
                user_id TEXT NOT NULL REFERENCES users(id),
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (user_id, key)
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, updated_at DESC);
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_msg_conv ON conversation_messages(conversation_id, created_at ASC);
            CREATE TABLE IF NOT EXISTS conversation_message_attachments (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                library_item_id TEXT NOT NULL,
                file_name TEXT,
                mime_type TEXT,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (message_id) REFERENCES conversation_messages(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_msg_attachment_message ON conversation_message_attachments(message_id);

            CREATE TABLE IF NOT EXISTS onboarding_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL REFERENCES users(id),
                turn_number INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_onboard_user ON onboarding_responses(user_id, created_at);

            CREATE TABLE IF NOT EXISTS engagement_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL REFERENCES users(id),
                event_type TEXT NOT NULL CHECK(event_type IN (
                    'opened','saved','dismissed','acted_on','feedback_useful','feedback_irrelevant'
                )),
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                metadata_json TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_engage_user ON engagement_events(user_id, created_at DESC);

            CREATE TABLE IF NOT EXISTS usage_events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                event      TEXT NOT NULL,
                user_id    TEXT,
                metadata   TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_usage_event ON usage_events(event, created_at DESC);

            CREATE TABLE IF NOT EXISTS user_rss_feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL REFERENCES users(id),
                url TEXT NOT NULL,
                name TEXT,
                added_by TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, url)
            );
            CREATE INDEX IF NOT EXISTS idx_rss_user ON user_rss_feeds(user_id);
        """)
        conn.commit()
        # Migration: add last_login to existing DBs
        try:
            conn.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
    finally:
        conn.close()


def _migrate_secrets(conn: sqlite3.Connection, target_id: str, email: str) -> None:
    """Move secrets from old user IDs (same email) to the new stable ID."""
    old_users = conn.execute(
        "SELECT id FROM users WHERE email = ? AND id != ?",
        (email, target_id),
    ).fetchall()
    if not old_users:
        return
    migrated = 0
    for (old_id,) in old_users:
        rows = conn.execute(
            "SELECT key, value FROM user_secrets WHERE user_id = ?", (old_id,)
        ).fetchall()
        for key, value in rows:
            # Only migrate if target doesn't already have this key
            exists = conn.execute(
                "SELECT 1 FROM user_secrets WHERE user_id = ? AND key = ?",
                (target_id, key),
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO user_secrets (user_id, key, value) VALUES (?, ?, ?)",
                    (target_id, key, value),
                )
                migrated += 1
        # Clean up old user's secrets and record
        conn.execute("DELETE FROM user_secrets WHERE user_id = ?", (old_id,))
        conn.execute("DELETE FROM conversations WHERE user_id = ?", (old_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (old_id,))
    if migrated:
        conn.commit()
        logger.info("user_store.secrets_migrated", target=target_id, migrated=migrated)


def get_or_create_user(
    user_id: str,
    email: str | None = None,
    name: str | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Upsert user on OAuth login. Returns user dict."""
    conn = _get_conn(db_path)
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            now = datetime.now(timezone.utc).isoformat()
            # Update email if changed + always bump last_login.
            # Only set name if DB has no name yet (preserve onboarding-set name).
            conn.execute(
                "UPDATE users SET email = COALESCE(?, email), name = COALESCE(name, ?), last_login = ? WHERE id = ?",
                (email, name, now, user_id),
            )
            conn.commit()
            # Migrate secrets from old duplicate user IDs (same email)
            if email:
                _migrate_secrets(conn, user_id, email)
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row)
        else:
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO users (id, email, name, created_at, last_login) VALUES (?, ?, ?, ?, ?)",
                (user_id, email, name, now, now),
            )
            conn.commit()
            # Migrate secrets from old duplicate user IDs (same email)
            if email:
                _migrate_secrets(conn, user_id, email)
            return {
                "id": user_id,
                "email": email,
                "name": name,
                "created_at": now,
                "last_login": now,
            }
    finally:
        conn.close()


def get_user_secret(
    user_id: str,
    secret_key: str,
    fernet_key: str,
    db_path: Path | None = None,
) -> str | None:
    """Get a single decrypted secret for a user."""
    conn = _get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT value FROM user_secrets WHERE user_id = ? AND key = ?",
            (user_id, secret_key),
        ).fetchone()
        if not row:
            return None
        return decrypt_value(fernet_key, row["value"], key_name=secret_key)
    finally:
        conn.close()


def get_user_secrets(
    user_id: str,
    fernet_key: str,
    db_path: Path | None = None,
) -> dict[str, str]:
    """Get all decrypted secrets for a user."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT key, value FROM user_secrets WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        result = {}
        skipped = 0
        for row in rows:
            val = decrypt_value(fernet_key, row["value"], key_name=row["key"])
            if val is not None:
                result[row["key"]] = val
            else:
                skipped += 1
        if skipped:
            logger.warning(
                "user_store.secrets_skipped",
                user_id=user_id,
                total=len(rows),
                skipped=skipped,
            )
        return result
    finally:
        conn.close()


def set_user_secret(
    user_id: str,
    secret_key: str,
    value: str,
    fernet_key: str,
    db_path: Path | None = None,
) -> None:
    """Encrypt and store a secret for a user."""
    conn = _get_conn(db_path)
    try:
        encrypted = encrypt_value(fernet_key, value)
        conn.execute(
            "INSERT INTO user_secrets (user_id, key, value) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value",
            (user_id, secret_key, encrypted),
        )
        conn.commit()
        logger.info("user_store.secret_saved", user_id=user_id, key=secret_key)
    finally:
        conn.close()


def delete_user_secret(
    user_id: str,
    secret_key: str,
    db_path: Path | None = None,
) -> None:
    """Remove a secret for a user."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            "DELETE FROM user_secrets WHERE user_id = ? AND key = ?",
            (user_id, secret_key),
        )
        conn.commit()
    finally:
        conn.close()


# --- Onboarding responses ---


def save_onboarding_turn(
    user_id: str,
    turn_number: int,
    role: str,
    content: str,
    db_path: Path | None = None,
) -> None:
    """Persist a single onboarding conversation turn."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO onboarding_responses (user_id, turn_number, role, content) VALUES (?, ?, ?, ?)",
            (user_id, turn_number, role, content),
        )
        conn.commit()
    finally:
        conn.close()


def get_onboarding_responses(
    user_id: str,
    db_path: Path | None = None,
) -> list[dict]:
    """Get all onboarding responses for a user, ordered by turn."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT turn_number, role, content, created_at FROM onboarding_responses "
            "WHERE user_id = ? ORDER BY turn_number, created_at",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def clear_onboarding_responses(
    user_id: str,
    db_path: Path | None = None,
) -> None:
    """Delete all onboarding responses for a user (for re-onboarding)."""
    conn = _get_conn(db_path)
    try:
        conn.execute("DELETE FROM onboarding_responses WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


# --- Engagement events ---


def log_engagement(
    user_id: str,
    event_type: str,
    target_type: str,
    target_id: str,
    metadata: dict | None = None,
    db_path: Path | None = None,
) -> None:
    """Record an engagement event."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO engagement_events (user_id, event_type, target_type, target_id, metadata_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, event_type, target_type, target_id, _json.dumps(metadata or {})),
        )
        conn.commit()
    finally:
        conn.close()


def get_engagement_stats(
    user_id: str,
    days: int = 30,
    db_path: Path | None = None,
) -> dict:
    """Return engagement counts by target_type and event_type for the last N days."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            """
            SELECT target_type, event_type, COUNT(*) as cnt
            FROM engagement_events
            WHERE user_id = ? AND created_at >= datetime('now', ?)
            GROUP BY target_type, event_type
            """,
            (user_id, f"-{days} days"),
        ).fetchall()
        stats: dict = {"by_target": {}, "by_event": {}, "total": 0}
        for r in rows:
            tt, et, cnt = r["target_type"], r["event_type"], r["cnt"]
            stats["by_target"].setdefault(tt, {})[et] = cnt
            stats["by_event"].setdefault(et, {})[tt] = cnt
            stats["total"] += cnt
        return stats
    finally:
        conn.close()


def update_user_name(
    user_id: str,
    name: str,
    db_path: Path | None = None,
) -> None:
    """Update the display name for a user."""
    conn = _get_conn(db_path)
    try:
        conn.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        conn.commit()
    finally:
        conn.close()


def get_user_name(
    user_id: str,
    db_path: Path | None = None,
) -> str | None:
    """Get the display name for a user."""
    conn = _get_conn(db_path)
    try:
        row = conn.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
        return row["name"] if row else None
    finally:
        conn.close()


def log_event(
    event: str,
    user_id: str | None = None,
    metadata: dict | None = None,
    db_path: Path | None = None,
) -> None:
    """Record a usage analytics event. Fail-silent — never bubbles up."""
    try:
        conn = _get_conn(db_path)
        conn.execute(
            "INSERT INTO usage_events (event, user_id, metadata) VALUES (?, ?, ?)",
            (event, user_id, _json.dumps(metadata) if metadata else None),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_usage_stats(days: int = 30, db_path: Path | None = None) -> dict:
    """Return aggregate usage stats for the last N days."""
    conn = _get_conn(db_path)
    window = f"-{days} days"
    try:
        # Chat queries
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM usage_events WHERE event='chat_query' AND created_at >= datetime('now', ?)",
            (window,),
        ).fetchone()
        chat_queries = row["cnt"] if row else 0

        # Avg latency
        row = conn.execute(
            "SELECT AVG(json_extract(metadata, '$.latency_ms')) as avg_ms FROM usage_events "
            "WHERE event='chat_query' AND created_at >= datetime('now', ?)",
            (window,),
        ).fetchone()
        avg_latency_ms = round(row["avg_ms"]) if row and row["avg_ms"] else None

        # Active users (7d)
        row = conn.execute(
            "SELECT COUNT(DISTINCT user_id) as cnt FROM usage_events "
            "WHERE created_at >= datetime('now', '-7 days') AND user_id IS NOT NULL"
        ).fetchone()
        active_users_7d = row["cnt"] if row else 0

        # Event counts
        event_counts = {}
        for ev in ("onboarding_complete", "journal_entry_created", "goal_created"):
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM usage_events WHERE event=? AND created_at >= datetime('now', ?)",
                (ev, window),
            ).fetchone()
            event_counts[ev] = row["cnt"] if row else 0

        # Recommendation feedback
        feedback_rows = conn.execute(
            "SELECT json_extract(metadata, '$.category') as cat, "
            "json_extract(metadata, '$.score') as score, COUNT(*) as cnt "
            "FROM usage_events WHERE event='recommendation_feedback' AND created_at >= datetime('now', ?) "
            "GROUP BY cat, score",
            (window,),
        ).fetchall()
        feedback: dict = {}
        for r in feedback_rows:
            cat = r["cat"] or "unknown"
            feedback.setdefault(cat, {"positive": 0, "negative": 0})
            if r["score"] and int(r["score"]) >= 1:
                feedback[cat]["positive"] += r["cnt"]
            else:
                feedback[cat]["negative"] += r["cnt"]

        # Scraper health
        scraper_rows = conn.execute(
            "SELECT json_extract(metadata, '$.source') as src, "
            "MAX(created_at) as last_run, "
            "AVG(json_extract(metadata, '$.items_added')) as avg_items, "
            "COUNT(*) as runs "
            "FROM usage_events WHERE event='scraper_run' AND created_at >= datetime('now', ?) "
            "GROUP BY src",
            (window,),
        ).fetchall()
        scraper_health = [
            {
                "source": r["src"],
                "last_run": r["last_run"],
                "avg_items": round(r["avg_items"], 1) if r["avg_items"] else 0,
                "runs": r["runs"],
            }
            for r in scraper_rows
        ]

        # Page views
        pv_rows = conn.execute(
            "SELECT json_extract(metadata, '$.path') as path, COUNT(*) as cnt "
            "FROM usage_events WHERE event='page_view' AND created_at >= datetime('now', ?) "
            "GROUP BY path ORDER BY cnt DESC",
            (window,),
        ).fetchall()
        page_views = [{"path": r["path"], "count": r["cnt"]} for r in pv_rows]

        return {
            "days": days,
            "chat_queries": chat_queries,
            "avg_latency_ms": avg_latency_ms,
            "active_users_7d": active_users_7d,
            "event_counts": event_counts,
            "recommendation_feedback": feedback,
            "scraper_health": scraper_health,
            "page_views": page_views,
        }
    finally:
        conn.close()


def delete_user(
    user_id: str,
    db_path: Path | None = None,
) -> bool:
    """Delete a user and all associated data. Returns True if user existed."""
    conn = _get_conn(db_path)
    try:
        row = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM user_secrets WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM onboarding_responses WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM engagement_events WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM usage_events WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM user_rss_feeds WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        logger.info("user_store.user_deleted", user_id=user_id)
        return True
    finally:
        conn.close()


# --- User RSS feeds ---


def get_user_rss_feeds(
    user_id: str,
    db_path: Path | None = None,
) -> list[dict]:
    """Get all RSS feeds for a user."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT id, user_id, url, name, added_by, created_at FROM user_rss_feeds "
            "WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_user_rss_feed(
    user_id: str,
    url: str,
    name: str | None = None,
    added_by: str = "user",
    db_path: Path | None = None,
) -> dict:
    """Upsert an RSS feed for a user. Returns the row."""
    conn = _get_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO user_rss_feeds (user_id, url, name, added_by) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, url) DO UPDATE SET name = COALESCE(excluded.name, name)",
            (user_id, url, name, added_by),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, user_id, url, name, added_by, created_at FROM user_rss_feeds "
            "WHERE user_id = ? AND url = ?",
            (user_id, url),
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def remove_user_rss_feed(
    user_id: str,
    url: str,
    db_path: Path | None = None,
) -> bool:
    """Remove an RSS feed for a user. Returns True if deleted."""
    conn = _get_conn(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM user_rss_feeds WHERE user_id = ? AND url = ?",
            (user_id, url),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_all_user_rss_feeds(
    db_path: Path | None = None,
) -> list[dict]:
    """Get all user RSS feeds across all users (for scheduler merge)."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT id, user_id, url, name, added_by, created_at FROM user_rss_feeds "
            "ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_user_ids(
    db_path: Path | None = None,
) -> list[str]:
    """Return known user IDs ordered by most recent login."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id
            FROM users
            ORDER BY COALESCE(last_login, created_at) DESC, id ASC
            """
        ).fetchall()
        return [row["id"] for row in rows if row["id"]]
    finally:
        conn.close()


def get_feedback_count(
    user_id: str,
    days: int = 30,
    db_path: Path | None = None,
) -> int:
    """Count binary and numeric feedback events in the last N days."""
    conn = _get_conn(db_path)
    try:
        engagement_row = conn.execute(
            """
            SELECT COUNT(*) as cnt FROM engagement_events
            WHERE user_id = ?
              AND event_type IN ('feedback_useful', 'feedback_irrelevant')
              AND created_at >= datetime('now', ?)
            """,
            (user_id, f"-{days} days"),
        ).fetchone()
        recommendation_row = conn.execute(
            """
            SELECT COUNT(*) as cnt FROM usage_events
            WHERE user_id = ?
              AND event = 'recommendation_feedback'
              AND created_at >= datetime('now', ?)
            """,
            (user_id, f"-{days} days"),
        ).fetchone()
        engagement_count = engagement_row["cnt"] if engagement_row else 0
        recommendation_count = recommendation_row["cnt"] if recommendation_row else 0
        return engagement_count + recommendation_count
    finally:
        conn.close()

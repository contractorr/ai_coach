"""Conversation persistence — per-user chat history in SQLite."""

import uuid
from datetime import datetime, timezone

from web.user_store import _get_conn


def _load_attachments(conn, message_ids: list[str]) -> dict[str, list[dict]]:
    if not message_ids:
        return {}

    placeholders = ", ".join("?" for _ in message_ids)
    rows = conn.execute(
        f"""
        SELECT message_id, library_item_id, file_name, mime_type
        FROM conversation_message_attachments
        WHERE message_id IN ({placeholders})
        ORDER BY created_at ASC
        """,
        message_ids,
    ).fetchall()
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        payload = {
            "library_item_id": row["library_item_id"],
            "file_name": row["file_name"],
            "mime_type": row["mime_type"],
        }
        grouped.setdefault(row["message_id"], []).append(payload)
    return grouped


def create_conversation(user_id: str, title: str, db_path=None) -> str:
    """Create conversation, return its id."""
    conv_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    title = title[:80].strip() or "New conversation"
    conn = _get_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conv_id, user_id, title, now, now),
        )
        conn.commit()
        return conv_id
    finally:
        conn.close()


def list_conversations(user_id: str, limit: int = 50, db_path=None) -> list[dict]:
    """List conversations for a user, newest first, with message count."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            """
            SELECT c.id, c.title, c.updated_at,
                   COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN conversation_messages m ON m.conversation_id = c.id
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_conversation(conv_id: str, user_id: str, db_path=None) -> dict | None:
    """Get conversation with all messages. Returns None if not found or wrong user."""
    conn = _get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ? AND user_id = ?",
            (conv_id, user_id),
        ).fetchone()
        if not row:
            return None
        conv = dict(row)
        msgs = conn.execute(
            "SELECT id, role, content, created_at FROM conversation_messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conv_id,),
        ).fetchall()
        attachments_by_message = _load_attachments(conn, [message["id"] for message in msgs])
        conv["messages"] = [
            {
                "role": message["role"],
                "content": message["content"],
                "created_at": message["created_at"],
                "attachments": attachments_by_message.get(message["id"], []),
            }
            for message in msgs
        ]
        return conv
    finally:
        conn.close()


def add_message(
    conv_id: str,
    role: str,
    content: str,
    attachments: list[dict] | None = None,
    db_path=None,
) -> str:
    """Add message to conversation, return message id."""
    msg_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn(db_path)
    try:
        conn.execute(
            "INSERT INTO conversation_messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (msg_id, conv_id, role, content, now),
        )
        for attachment in attachments or []:
            conn.execute(
                """
                INSERT INTO conversation_message_attachments
                    (id, message_id, library_item_id, file_name, mime_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    msg_id,
                    attachment["library_item_id"],
                    attachment.get("file_name"),
                    attachment.get("mime_type"),
                    now,
                ),
            )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conv_id),
        )
        conn.commit()
        return msg_id
    finally:
        conn.close()


def get_messages(conv_id: str, limit: int = 20, db_path=None) -> list[dict]:
    """Get last N messages for a conversation (oldest first)."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, role, content, created_at FROM (
                SELECT id, role, content, created_at
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ) sub ORDER BY created_at ASC
            """,
            (conv_id, limit),
        ).fetchall()
        attachments_by_message = _load_attachments(conn, [row["id"] for row in rows])
        return [
            {
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"],
                "attachments": attachments_by_message.get(row["id"], []),
            }
            for row in rows
        ]
    finally:
        conn.close()


def delete_conversation(conv_id: str, user_id: str, db_path=None) -> bool:
    """Delete conversation if it belongs to user. Returns True if deleted."""
    conn = _get_conn(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?",
            (conv_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def update_timestamp(conv_id: str, db_path=None) -> None:
    """Bump updated_at on a conversation."""
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn(db_path)
    try:
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
        conn.commit()
    finally:
        conn.close()


def conversation_belongs_to(conv_id: str, user_id: str, db_path=None) -> bool:
    """Check if conversation belongs to user."""
    conn = _get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM conversations WHERE id = ? AND user_id = ?",
            (conv_id, user_id),
        ).fetchone()
        return row is not None
    finally:
        conn.close()

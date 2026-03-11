"""Inbox-state overlay and view-model helpers for recurring threads."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from db import wal_connect
from journal.storage import JournalStorage
from journal.thread_store import ThreadStore

VALID_INBOX_STATES = {
    "active",
    "dismissed",
    "goal_created",
    "research_started",
    "dossier_started",
    "dormant",
}

_UNSET = object()


def _now() -> str:
    return datetime.now().isoformat()


class ThreadInboxStateStore:
    """Workflow overlay persisted alongside thread detection state."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS thread_inbox_state (
                    thread_id TEXT PRIMARY KEY,
                    inbox_state TEXT NOT NULL DEFAULT 'active',
                    linked_goal_path TEXT,
                    linked_dossier_id TEXT,
                    last_action TEXT DEFAULT '',
                    snoozed_until TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def get_state(self, thread_id: str) -> dict | None:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM thread_inbox_state WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_state(
        self,
        thread_id: str,
        *,
        inbox_state: str,
        linked_goal_path: str | None | object = _UNSET,
        linked_dossier_id: str | None | object = _UNSET,
        last_action: str = "",
    ) -> dict:
        if inbox_state not in VALID_INBOX_STATES:
            raise ValueError(f"Invalid inbox state: {inbox_state}")
        goal_path_provided = linked_goal_path is not _UNSET
        dossier_id_provided = linked_dossier_id is not _UNSET
        goal_path_value = None if linked_goal_path is _UNSET else linked_goal_path
        dossier_id_value = None if linked_dossier_id is _UNSET else linked_dossier_id
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO thread_inbox_state (
                    thread_id, inbox_state, linked_goal_path, linked_dossier_id, last_action, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    inbox_state = excluded.inbox_state,
                    linked_goal_path = CASE
                        WHEN ? THEN excluded.linked_goal_path
                        ELSE thread_inbox_state.linked_goal_path
                    END,
                    linked_dossier_id = CASE
                        WHEN ? THEN excluded.linked_dossier_id
                        ELSE thread_inbox_state.linked_dossier_id
                    END,
                    last_action = excluded.last_action,
                    updated_at = excluded.updated_at
                """,
                (
                    thread_id,
                    inbox_state,
                    goal_path_value,
                    dossier_id_value,
                    last_action,
                    _now(),
                    int(goal_path_provided),
                    int(dossier_id_provided),
                ),
            )
        return self.get_state(thread_id) or {
            "thread_id": thread_id,
            "inbox_state": inbox_state,
            "linked_goal_path": goal_path_value,
            "linked_dossier_id": dossier_id_value,
            "last_action": last_action,
            "updated_at": _now(),
        }

    def clear_state(self, thread_id: str) -> bool:
        with wal_connect(self.db_path) as conn:
            result = conn.execute(
                "DELETE FROM thread_inbox_state WHERE thread_id = ?",
                (thread_id,),
            )
        return bool(result.rowcount)

    def clear_all(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute("DELETE FROM thread_inbox_state")


class ThreadInboxService:
    """Merge thread detection rows with inbox-state overlays and previews."""

    def __init__(
        self,
        thread_store: ThreadStore,
        state_store: ThreadInboxStateStore,
        journal_storage: JournalStorage,
    ):
        self.thread_store = thread_store
        self.state_store = state_store
        self.journal_storage = journal_storage

    async def list_inbox(
        self, *, state: str | None = None, query: str = "", limit: int = 50
    ) -> list[dict]:
        threads = await self.thread_store.get_active_threads(min_entries=2)
        rows: list[dict] = []
        query_norm = query.strip().lower()

        for thread in threads:
            detail = await self.get_thread_detail(thread.id)
            if not detail:
                continue
            inbox_state = detail.get("inbox_state") or "active"
            if state and inbox_state != state:
                continue
            if query_norm:
                haystack = " ".join(
                    [
                        str(detail.get("label") or ""),
                        *[str(snippet) for snippet in detail.get("recent_snippets") or []],
                    ]
                ).lower()
                if query_norm not in haystack:
                    continue
            rows.append(detail)

        def _sort_key(item: dict):
            is_active = item.get("inbox_state") == "active"
            return (
                1 if is_active else 0,
                item.get("last_date") or "",
                item.get("updated_at") or "",
            )

        rows.sort(key=_sort_key, reverse=True)
        return rows[:limit]

    async def get_thread_detail(self, thread_id: str) -> dict | None:
        thread = await self.thread_store.get_thread(thread_id)
        if not thread:
            return None
        entries = await self.thread_store.get_thread_entries(thread_id)
        state = self.state_store.get_state(thread_id) or {
            "inbox_state": "active",
            "last_action": "",
        }

        snippets: list[str] = []
        for entry in entries[-3:]:
            try:
                post = self.journal_storage.read(Path(entry.entry_id))
                text = (post.content or "").strip().replace("\n", " ")
                if text:
                    snippets.append(text[:160])
            except Exception:
                continue

        return {
            "id": thread.id,
            "label": thread.label,
            "entry_count": thread.entry_count,
            "status": thread.status,
            "first_date": entries[0].entry_date.strftime("%Y-%m-%d") if entries else "",
            "last_date": entries[-1].entry_date.strftime("%Y-%m-%d") if entries else "",
            "entries": [
                {
                    "entry_id": entry.entry_id,
                    "entry_date": entry.entry_date.strftime("%Y-%m-%d"),
                    "similarity": round(entry.similarity, 3),
                }
                for entry in entries
            ],
            "recent_snippets": snippets,
            "inbox_state": state.get("inbox_state") or "active",
            "linked_goal_path": state.get("linked_goal_path"),
            "linked_dossier_id": state.get("linked_dossier_id"),
            "last_action": state.get("last_action") or "",
            "updated_at": state.get("updated_at") or thread.updated_at.isoformat(),
            "available_actions": {
                "make_goal": state.get("inbox_state") != "goal_created",
                "run_research": state.get("inbox_state") != "research_started",
                "start_dossier": state.get("inbox_state") != "dossier_started",
            },
        }

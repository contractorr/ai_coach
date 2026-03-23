"""User-scoped read wrapper over IntelStorage.

Injects ``AND (user_id IS NULL OR user_id = ?)`` into all read queries
so each user only sees shared items + their own.  Write methods pass
through to the underlying storage unchanged.

When ``user_id=None`` no filter is applied (CLI single-user compat).
"""

import sqlite3
from datetime import datetime

from db import wal_connect

from .scraper import IntelStorage


class UserIntelView:
    """Duck-typed filtered wrapper over :class:`IntelStorage`."""

    def __init__(self, storage: IntelStorage, user_id: str | None = None):
        self.storage = storage
        self.user_id = user_id
        self.db_path = storage.db_path

    # ── helpers ──────────────────────────────────────────────────────

    def _user_clause(self) -> str:
        if not self.user_id:
            return ""
        return "AND (user_id IS NULL OR user_id = ?)"

    def _user_params(self) -> tuple:
        if not self.user_id:
            return ()
        return (self.user_id,)

    # ── filtered reads ──────────────────────────────────────────────

    def get_recent(
        self, days: int = 7, limit: int = 50, include_duplicates: bool = False
    ) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            dedup_clause = "" if include_duplicates else "AND duplicate_of IS NULL"
            user_clause = self._user_clause()
            params: list = [f"-{days} days", *self._user_params(), limit]
            cursor = conn.execute(
                f"""
                SELECT * FROM intel_items
                WHERE scraped_at >= datetime('now', ?)
                  {dedup_clause}
                  {user_clause}
                ORDER BY scraped_at DESC
                LIMIT ?
                """,
                params,
            )
            return [IntelStorage._row_to_dict(row) for row in cursor.fetchall()]

    def search(self, query: str, limit: int = 20, source_filter: str | None = None) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            params: list = [f"%{query}%", f"%{query}%", *self._user_params()]
            source_clause = ""
            if source_filter:
                source_clause = "AND source = ?"
                params.append(source_filter)
            params.append(limit)
            user_clause = self._user_clause()
            cursor = conn.execute(
                f"""
                SELECT * FROM intel_items
                WHERE (title LIKE ? OR summary LIKE ?)
                  {user_clause}
                  {source_clause}
                ORDER BY scraped_at DESC
                LIMIT ?
                """,
                tuple(params),
            )
            return [IntelStorage._row_to_dict(row) for row in cursor.fetchall()]

    def fts_search(
        self, query: str, limit: int = 20, source_filter: str | None = None
    ) -> list[dict]:
        fts_query = IntelStorage._to_fts5_query(query)
        if not fts_query:
            return []
        try:
            with wal_connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                user_clause = (
                    self._user_clause().replace("user_id", "i.user_id") if self.user_id else ""
                )
                source_clause = "AND i.source = ?" if source_filter else ""
                params: list = [fts_query, *self._user_params()]
                if source_filter:
                    params.append(source_filter)
                params.append(limit)
                cursor = conn.execute(
                    f"""
                    SELECT i.*
                    FROM intel_fts f
                    JOIN intel_items i ON f.rowid = i.id
                    WHERE intel_fts MATCH ?
                      {user_clause}
                      {source_clause}
                    ORDER BY bm25(intel_fts)
                    LIMIT ?
                    """,
                    tuple(params),
                )
                return [IntelStorage._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            return self.search(query, limit=limit, source_filter=source_filter)

    def get_items_since(self, since: datetime, limit: int = 200) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            user_clause = self._user_clause()
            params: list = [since.isoformat(), *self._user_params(), limit]
            cursor = conn.execute(
                f"""SELECT * FROM intel_items
                    WHERE scraped_at >= ? AND duplicate_of IS NULL
                    {user_clause}
                    ORDER BY scraped_at DESC LIMIT ?""",
                params,
            )
            return [IntelStorage._row_to_dict(row) for row in cursor.fetchall()]

    def get_by_date_range(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 50,
    ) -> list[dict]:
        clauses = ["duplicate_of IS NULL"]
        params: list = []
        if start:
            clauses.append("COALESCE(published, scraped_at) >= ?")
            params.append(start.isoformat())
        if end:
            clauses.append("COALESCE(published, scraped_at) <= ?")
            params.append(end.isoformat())
        if self.user_id:
            clauses.append("(user_id IS NULL OR user_id = ?)")
            params.append(self.user_id)
        where = " AND ".join(clauses)
        params.append(limit)
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                f"""SELECT * FROM intel_items
                    WHERE {where}
                    ORDER BY COALESCE(published, scraped_at) DESC
                    LIMIT ?""",
                tuple(params),
            )
            return [IntelStorage._row_to_dict(row) for row in cursor.fetchall()]

    # ── write-through (no filtering needed) ─────────────────────────

    def save(self, item):
        return self.storage.save(item)

    def hash_exists(self, h, days=7):
        return self.storage.hash_exists(h, days)

    def get_item_by_id(self, item_id):
        return self.storage.get_item_by_id(item_id)

    def mark_duplicate(self, row_id, canonical_id):
        return self.storage.mark_duplicate(row_id, canonical_id)

    # ── pass-through for _row_to_dict / _to_fts5_query ──────────────

    @staticmethod
    def _row_to_dict(row):
        return IntelStorage._row_to_dict(row)

    @staticmethod
    def _to_fts5_query(query):
        return IntelStorage._to_fts5_query(query)

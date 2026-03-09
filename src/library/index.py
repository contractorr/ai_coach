"""Search index for Library items."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import structlog

from db import wal_connect

logger = structlog.get_logger()


def _to_fts5_query(query: str) -> str:
    tokens = re.findall(r"[\w]+", query.lower())
    if not tokens:
        return ""
    return " ".join(f"{token}*" for token in tokens)


def _make_snippet(text: str, query: str, max_chars: int = 240) -> str:
    normalized_text = " ".join((text or "").split())
    if not normalized_text:
        return ""

    lowered = normalized_text.lower()
    query_tokens = [token for token in re.findall(r"[\w]+", query.lower()) if token]
    match_at = min(
        (lowered.find(token) for token in query_tokens if lowered.find(token) >= 0),
        default=-1,
    )
    if match_at < 0:
        return normalized_text[:max_chars]

    start = max(0, match_at - max_chars // 3)
    end = min(len(normalized_text), start + max_chars)
    snippet = normalized_text[start:end]
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(normalized_text):
        snippet = f"{snippet}..."
    return snippet


class LibraryIndex:
    """SQLite FTS5 index for Library items."""

    def __init__(self, library_dir: str | Path):
        self.library_dir = Path(library_dir).expanduser().resolve()
        self.db_path = self.library_dir / "library_index.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS library_fts USING fts5(
                    report_id UNINDEXED,
                    title,
                    source_kind UNINDEXED,
                    report_type UNINDEXED,
                    status UNINDEXED,
                    collection UNINDEXED,
                    file_name,
                    body_text,
                    extracted_text,
                    updated_at UNINDEXED,
                    tokenize='porter unicode61'
                )
                """
            )

    def upsert_item(
        self,
        *,
        report_id: str,
        title: str,
        source_kind: str,
        report_type: str,
        status: str,
        collection: str | None,
        file_name: str | None,
        body_text: str,
        extracted_text: str,
        updated_at: str,
    ) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute("DELETE FROM library_fts WHERE report_id = ?", (report_id,))
            conn.execute(
                """
                INSERT INTO library_fts(
                    report_id, title, source_kind, report_type, status, collection,
                    file_name, body_text, extracted_text, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    title,
                    source_kind,
                    report_type,
                    status,
                    collection or "",
                    file_name or "",
                    body_text or "",
                    extracted_text or "",
                    updated_at or "",
                ),
            )

    def delete_item(self, report_id: str) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute("DELETE FROM library_fts WHERE report_id = ?", (report_id,))

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        source_kind: str | None = None,
        status: str | None = None,
        collection: str | None = None,
    ) -> list[dict]:
        fts_query = _to_fts5_query(query)
        if not fts_query:
            return []

        sql = (
            "SELECT report_id, title, source_kind, report_type, status, collection, file_name, "
            "body_text, extracted_text, bm25(library_fts) AS rank "
            "FROM library_fts WHERE library_fts MATCH ?"
        )
        params: list[object] = [fts_query]

        if source_kind:
            sql += " AND source_kind = ?"
            params.append(source_kind)
        if status:
            sql += " AND status = ?"
            params.append(status)
        if collection:
            sql += " AND collection = ?"
            params.append(collection)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        try:
            with wal_connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError as exc:
            logger.warning("library_index_search_failed", error=str(exc))
            return []

        results = []
        for row in rows:
            if row["source_kind"] == "uploaded_pdf":
                text = row["extracted_text"] or ""
            else:
                text = (row["body_text"] or "") + "\n" + (row["extracted_text"] or "")
            results.append(
                {
                    "id": row["report_id"],
                    "title": row["title"],
                    "source_kind": row["source_kind"],
                    "file_name": row["file_name"],
                    "snippet": _make_snippet(text, query),
                    "score": row["rank"],
                }
            )
        return results

    def get_item_text(self, report_id: str) -> dict | None:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT report_id, title, source_kind, report_type, status, collection,
                       file_name, body_text, extracted_text, updated_at
                FROM library_fts
                WHERE report_id = ?
                """,
                (report_id,),
            ).fetchone()
        if not row:
            return None
        return dict(row)

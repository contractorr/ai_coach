"""Search index for Library items."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from db import wal_connect

if TYPE_CHECKING:
    from library.embeddings import LibraryEmbeddingManager

logger = structlog.get_logger()


def _to_fts5_query(query: str) -> str:
    tokens = re.findall(r"[\w][\w\-]*[\w]|[\w]", query.lower())
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
    """SQLite FTS5 index for Library items with optional semantic search."""

    def __init__(
        self,
        library_dir: str | Path,
        embedding_manager: LibraryEmbeddingManager | None = None,
    ):
        self.library_dir = Path(library_dir).expanduser().resolve()
        self.db_path = self.library_dir / "library_index.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.embedding_manager = embedding_manager
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

    # Gemini/OpenAI models accept 8k+ tokens; MiniLM accepts ~256.
    # 4000 chars is safe for all providers while capturing more content.
    MAX_EMBED_CHARS = 4000

    @staticmethod
    def _build_embed_content(title: str, body_text: str, extracted_text: str) -> str:
        """Concatenate text fields into a single string for embedding, truncated to fit model window."""
        parts = [p for p in (title, body_text, extracted_text) if p and p.strip()]
        content = "\n\n".join(parts)
        if len(content) > LibraryIndex.MAX_EMBED_CHARS:
            content = content[: LibraryIndex.MAX_EMBED_CHARS]
        return content

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

        if self.embedding_manager:
            embed_content = self._build_embed_content(title, body_text, extracted_text)
            if embed_content:
                self.embedding_manager.add_item(
                    report_id,
                    embed_content,
                    {
                        "source_kind": source_kind,
                        "status": status,
                        "collection": collection or "",
                    },
                )

    def delete_item(self, report_id: str) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute("DELETE FROM library_fts WHERE report_id = ?", (report_id,))
        if self.embedding_manager:
            self.embedding_manager.remove_item(report_id)

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
            sql += " AND collection = ? COLLATE NOCASE"
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

    def semantic_search(
        self,
        query: str,
        *,
        n_results: int = 10,
        source_kind: str | None = None,
        status: str | None = None,
        collection: str | None = None,
    ) -> list[dict]:
        """Search using semantic similarity via embedding manager."""
        if not self.embedding_manager:
            return []

        where: dict | None = None
        filters = {}
        if source_kind:
            filters["source_kind"] = source_kind
        if status:
            filters["status"] = status
        if collection:
            filters["collection"] = collection
        if filters:
            where = filters

        results = self.embedding_manager.query(query, n_results=n_results, where=where)

        enriched = []
        for r in results:
            item = self.get_item_text(r["id"])
            if not item:
                continue

            if item.get("source_kind") == "uploaded_pdf":
                text = item.get("extracted_text") or ""
            else:
                text = (item.get("body_text") or "") + "\n" + (item.get("extracted_text") or "")

            enriched.append(
                {
                    "id": item["report_id"],
                    "title": item["title"],
                    "source_kind": item.get("source_kind"),
                    "file_name": item.get("file_name"),
                    "snippet": _make_snippet(text, query),
                    "score": 1 - r["distance"],
                }
            )

        return enriched

    def hybrid_search(
        self,
        query: str,
        *,
        limit: int = 20,
        semantic_weight: float = 0.7,
        source_kind: str | None = None,
        status: str | None = None,
        collection: str | None = None,
    ) -> list[dict]:
        """Combine semantic + FTS5 search via reciprocal rank fusion.

        Falls back to FTS5-only when no embedding manager is present.
        """
        fts_results = self.search(
            query,
            limit=limit * 2,
            source_kind=source_kind,
            status=status,
            collection=collection,
        )

        if not self.embedding_manager:
            return fts_results[:limit]

        sem_results = self.semantic_search(
            query,
            n_results=limit * 2,
            source_kind=source_kind,
            status=status,
            collection=collection,
        )

        if not sem_results:
            return fts_results[:limit]

        k = 60  # standard RRF smoothing constant
        scores: dict[str, float] = {}
        items: dict[str, dict] = {}

        for i, item in enumerate(sem_results):
            key = item["id"]
            scores[key] = scores.get(key, 0) + (1.0 / (k + i + 1)) * semantic_weight
            items[key] = item

        for i, item in enumerate(fts_results):
            key = item["id"]
            scores[key] = scores.get(key, 0) + (1.0 / (k + i + 1)) * (1 - semantic_weight)
            if key not in items:
                items[key] = item

        sorted_keys = sorted(scores, key=lambda rid: scores[rid], reverse=True)
        return [items[rid] for rid in sorted_keys[:limit]]

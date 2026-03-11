"""Base scraper and intelligence storage."""

import hashlib
import re
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

from db import ensure_schema_version, wal_connect

logger = structlog.get_logger().bind(source="intel_storage")

SCHEMA_VERSION = 3

_ALLOWED_SCHEMES = {"http", "https"}
_INTERNAL_SCHEMES = {"research"}


def validate_url(url: str) -> bool:
    """Validate URL has allowed scheme and reasonable structure."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        # Internal schemes (research://) are always valid
        if parsed.scheme in _INTERNAL_SCHEMES:
            return True
        if parsed.scheme not in _ALLOWED_SCHEMES:
            return False
        if not parsed.netloc or "." not in parsed.netloc:
            return False
        return True
    except Exception:
        return False


@dataclass
class IntelItem:
    """Single intelligence item."""

    source: str
    title: str
    url: str
    summary: str
    content: Optional[str] = None
    published: Optional[datetime] = None
    tags: Optional[list[str]] = None
    content_hash: Optional[str] = None

    def compute_hash(self) -> str:
        """Compute content hash for deduplication."""
        text = f"{self.title.lower().strip()}|{self.summary.lower().strip()}"
        return hashlib.sha256(text.encode()).hexdigest()[:16]


class IntelStorage:
    """SQLite storage for intelligence items."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with wal_connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS intel_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    summary TEXT,
                    content TEXT,
                    published TIMESTAMP,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT,
                    content_hash TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_intel_source ON intel_items(source)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_intel_scraped ON intel_items(scraped_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_intel_hash ON intel_items(content_hash)
            """)
            # Add columns if not exists (for existing DBs)
            for col, typedef in [
                ("content_hash", "TEXT"),
                ("duplicate_of", "INTEGER"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE intel_items ADD COLUMN {col} {typedef}")
                except sqlite3.OperationalError:
                    pass  # Column already exists

            conn.execute("""
                CREATE TABLE IF NOT EXISTS scraper_health (
                    source TEXT PRIMARY KEY,
                    last_run_at TIMESTAMP,
                    last_success_at TIMESTAMP,
                    consecutive_errors INTEGER DEFAULT 0,
                    total_runs INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0,
                    last_error TEXT,
                    backoff_until TIMESTAMP
                )
            """)
            # Scraper health metrics columns (for existing DBs)
            for col, typedef in [
                ("last_items_scraped", "INTEGER DEFAULT 0"),
                ("last_items_new", "INTEGER DEFAULT 0"),
                ("last_duration_seconds", "REAL"),
                ("last_items_deduped", "INTEGER DEFAULT 0"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE scraper_health ADD COLUMN {col} {typedef}")
                except sqlite3.OperationalError:
                    pass

            # --- FTS5 full-text index ---
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS intel_fts USING fts5(
                    title, summary, content, tags,
                    tokenize='porter unicode61'
                )
            """)
            # Triggers keep FTS in sync with intel_items
            conn.executescript("""
                CREATE TRIGGER IF NOT EXISTS intel_fts_ai AFTER INSERT ON intel_items BEGIN
                    INSERT INTO intel_fts(rowid, title, summary, content, tags)
                    VALUES (NEW.id, NEW.title, COALESCE(NEW.summary,''), COALESCE(NEW.content,''), COALESCE(NEW.tags,''));
                END;

                CREATE TRIGGER IF NOT EXISTS intel_fts_ad AFTER DELETE ON intel_items BEGIN
                    DELETE FROM intel_fts WHERE rowid = OLD.id;
                END;

                CREATE TRIGGER IF NOT EXISTS intel_fts_au AFTER UPDATE ON intel_items BEGIN
                    DELETE FROM intel_fts WHERE rowid = OLD.id;
                    INSERT INTO intel_fts(rowid, title, summary, content, tags)
                    VALUES (NEW.id, NEW.title, COALESCE(NEW.summary,''), COALESCE(NEW.content,''), COALESCE(NEW.tags,''));
                END;
            """)
            # Backfill any rows not yet in FTS (e.g. existing DB upgraded)
            conn.execute("""
                INSERT OR IGNORE INTO intel_fts(rowid, title, summary, content, tags)
                SELECT id, title, COALESCE(summary,''), COALESCE(content,''), COALESCE(tags,'')
                FROM intel_items
                WHERE id NOT IN (SELECT rowid FROM intel_fts)
            """)
            ensure_schema_version(conn, SCHEMA_VERSION)

    def save(self, item: IntelItem) -> int | None:
        """Save intel item, skip if URL invalid/exists or content hash exists.

        Returns:
            Row ID of the newly inserted row, or None on skip.
            Truthiness preserved: ``if storage.save(item):`` still works.
        """
        if not validate_url(item.url):
            logger.warning("Invalid URL rejected: %s", item.url[:100])
            return None

        content_hash = item.content_hash or item.compute_hash()

        # Check for hash-based duplicate
        if self.hash_exists(content_hash):
            logger.info("Duplicate content skipped (hash): %s", item.title[:50])
            return None

        try:
            with wal_connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO intel_items
                    (source, title, url, summary, content, published, tags, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        item.source,
                        item.title,
                        item.url,
                        item.summary,
                        item.content,
                        item.published.isoformat() if item.published else None,
                        ",".join(item.tags) if item.tags else None,
                        content_hash,
                    ),
                )
                if conn.total_changes > 0:
                    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    return row_id
                return None
        except sqlite3.IntegrityError:
            logger.debug("Duplicate URL skipped: %s", item.url)
            return None
        except sqlite3.Error as e:
            logger.error("DB error saving item %s: %s", item.url, e)
            return None

    def mark_duplicate(self, row_id: int, canonical_id: int) -> None:
        """Mark *row_id* as a semantic duplicate of *canonical_id*."""
        with wal_connect(self.db_path) as conn:
            conn.execute(
                "UPDATE intel_items SET duplicate_of = ? WHERE id = ?",
                (canonical_id, row_id),
            )

    def hash_exists(self, content_hash: str, days: int = 7) -> bool:
        """Check if content hash exists in recent items."""
        with wal_connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT 1 FROM intel_items
                WHERE content_hash = ?
                AND scraped_at >= datetime('now', ?)
                LIMIT 1
            """,
                (content_hash, f"-{days} days"),
            ).fetchone()
            return row is not None

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        item = dict(row)
        if item.get("tags"):
            item["tags"] = [t.strip() for t in item["tags"].split(",")]
        else:
            item["tags"] = []
        return item

    def get_recent(
        self, days: int = 7, limit: int = 50, include_duplicates: bool = False
    ) -> list[dict]:
        """Get recent intel items, optionally including semantic duplicates."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            dedup_clause = "" if include_duplicates else "AND duplicate_of IS NULL"
            cursor = conn.execute(
                f"""
                SELECT * FROM intel_items
                WHERE scraped_at >= datetime('now', ?)
                  {dedup_clause}
                ORDER BY scraped_at DESC
                LIMIT ?
            """,
                (f"-{days} days", limit),
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_items_since(self, since: datetime, limit: int = 200) -> list[dict]:
        """Get intel items scraped since a given timestamp (excludes semantic duplicates)."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT * FROM intel_items
                   WHERE scraped_at >= ? AND duplicate_of IS NULL
                   ORDER BY scraped_at DESC LIMIT ?""",
                (since.isoformat(), limit),
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_item_by_id(self, item_id: int) -> dict | None:
        """Fetch a single intel item by ID."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM intel_items WHERE id = ?", (item_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def search(self, query: str, limit: int = 20, source_filter: str | None = None) -> list[dict]:
        """Simple text search in titles and summaries."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            params: list[object] = [f"%{query}%", f"%{query}%"]
            source_clause = ""
            if source_filter:
                source_clause = "AND source = ?"
                params.append(source_filter)
            params.append(limit)
            cursor = conn.execute(
                f"""
                SELECT * FROM intel_items
                WHERE (title LIKE ? OR summary LIKE ?)
                  {source_clause}
                ORDER BY scraped_at DESC
                LIMIT ?
            """,
                tuple(params),
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def fts_search(
        self, query: str, limit: int = 20, source_filter: str | None = None
    ) -> list[dict]:
        """FTS5 full-text search with BM25 ranking.

        Falls back to LIKE-based ``search()`` on OperationalError.
        """
        fts_query = self._to_fts5_query(query)
        if not fts_query:
            return []
        try:
            with wal_connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                source_clause = "AND i.source = ?" if source_filter else ""
                params: list[object] = [fts_query]
                if source_filter:
                    params.append(source_filter)
                params.append(limit)
                cursor = conn.execute(
                    f"""
                    SELECT i.*
                    FROM intel_fts f
                    JOIN intel_items i ON f.rowid = i.id
                    WHERE intel_fts MATCH ?
                      {source_clause}
                    ORDER BY bm25(intel_fts)
                    LIMIT ?
                    """,
                    tuple(params),
                )
                return [self._row_to_dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            logger.warning("intel_fts_search_fallback", error=str(e))
            return self.search(query, limit=limit, source_filter=source_filter)

    @staticmethod
    def _to_fts5_query(query: str) -> str:
        """Convert user query to FTS5 MATCH expression (prefix + AND)."""
        tokens = re.findall(r"[\w]+", query.lower())
        if not tokens:
            return ""
        return " ".join(f"{t}*" for t in tokens)


class BaseScraper(ABC):
    """Async base class for intelligence scrapers."""

    def __init__(self, storage: IntelStorage, embedding_manager=None):
        self.storage = storage
        self.embedding_manager = embedding_manager
        self._client: httpx.AsyncClient | None = None
        self._client_headers = {"User-Agent": "AI-Coach/1.0 (Personal Use)"}

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers=dict(self._client_headers),
            )
        return self._client

    @client.setter
    def client(self, value: httpx.AsyncClient) -> None:
        self._client = value

    def set_client_headers(self, **headers: str) -> None:
        """Apply headers to a future or existing async client."""
        self._client_headers.update(headers)
        if self._client is not None:
            self._client.headers.update(headers)

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique source identifier."""
        pass

    @abstractmethod
    async def scrape(self) -> list[IntelItem]:
        """Scrape and return intel items."""
        pass

    async def fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse HTML asynchronously."""
        try:
            logger.debug("Fetching %s", url)
            response = await self.client.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP %d fetching %s", e.response.status_code, url)
            return None
        except httpx.RequestError as e:
            logger.warning("Request error fetching %s: %s", url, e)
            return None

    async def save_items(
        self, items: list[IntelItem], semantic_dedup: bool = True, dedup_threshold: float = 0.92
    ) -> tuple[int, int]:
        """Save items with optional semantic dedup + canonical linking.

        Args:
            items: List of items to save
            semantic_dedup: Check for semantic duplicates via embeddings
            dedup_threshold: Similarity threshold for semantic dedup (0-1)

        Returns:
            ``(new_count, deduped_count)`` tuple.
        """
        new_count = 0
        deduped_count = 0
        for item in items:
            canonical_id: str | None = None

            # Semantic dedup check if embedding manager available
            if semantic_dedup and self.embedding_manager:
                content = f"{item.title} {item.summary}"
                canonical_id = self.embedding_manager.find_similar(
                    content, threshold=dedup_threshold
                )

            row_id = self.storage.save(item)

            if row_id and canonical_id:
                # Saved but is a near-duplicate — link to canonical
                self.storage.mark_duplicate(row_id, int(canonical_id))
                deduped_count += 1
            elif row_id and not canonical_id:
                # Genuinely new — index for intra-batch dedup
                new_count += 1
                if self.embedding_manager:
                    content = f"{item.title} {item.summary}"
                    meta = {"source": item.source}
                    self.embedding_manager.add_item(str(row_id), content, meta)
            # else: URL/hash dupe, skip

        return new_count, deduped_count

    async def close(self):
        """Close the async client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

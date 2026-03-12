"""Persistent storage for Steward Facts — SQLite metadata + ChromaDB embeddings."""

import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import structlog

from db import ensure_schema_version, wal_connect

from .models import FactCategory, FactSource, StewardFact

logger = structlog.get_logger()

SCHEMA_VERSION = 1
DEFAULT_REINFORCEMENT = 0.05
DEFAULT_CONTRADICTION_DECAY = 0.15
_SEARCH_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "from",
    "has",
    "have",
    "into",
    "is",
    "its",
    "now",
    "that",
    "the",
    "their",
    "then",
    "they",
    "this",
    "user",
    "with",
}


class FactStore:
    """SQLite + ChromaDB persistence for distilled memory facts."""

    def __init__(self, db_path: str | Path, chroma_dir: str | Path | None = None):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._chroma_dir = Path(chroma_dir).expanduser() if chroma_dir else None
        self._collection = None
        self._init_db()

    def _init_db(self):
        with wal_connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS steward_facts (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.8,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    superseded_by TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_facts_active
                ON steward_facts(superseded_by)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_facts_source
                ON steward_facts(source_type, source_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_facts_category
                ON steward_facts(category)
            """)
            ensure_schema_version(conn, SCHEMA_VERSION)

    @property
    def _chroma(self):
        """Lazy-init ChromaDB collection with shared embedding function."""
        if self._collection is None and self._chroma_dir:
            try:
                import chromadb
                from chromadb.config import Settings

                self._chroma_dir.mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(
                    path=str(self._chroma_dir),
                    settings=Settings(anonymized_telemetry=False),
                )

                # Use shared embedding provider for consistency
                embedding_fn = None
                try:
                    from embeddings import create_embedding_function

                    embedding_fn = create_embedding_function()
                except Exception:
                    pass  # ChromaDB will use its built-in default

                kwargs = {
                    "name": "steward_facts",
                    "metadata": {"hnsw:space": "cosine"},
                }
                if embedding_fn is not None:
                    kwargs["embedding_function"] = embedding_fn
                self._collection = client.get_or_create_collection(**kwargs)
            except Exception as e:
                logger.warning("chroma_init_failed", error=str(e))
        return self._collection

    def add(self, fact: StewardFact) -> StewardFact:
        """Insert fact into SQLite + embed into ChromaDB."""
        if not fact.id:
            fact.id = uuid.uuid4().hex[:16]

        with wal_connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO steward_facts
                   (id, text, category, source_type, source_id, confidence, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fact.id,
                    fact.text,
                    fact.category.value
                    if isinstance(fact.category, FactCategory)
                    else fact.category,
                    fact.source_type.value
                    if isinstance(fact.source_type, FactSource)
                    else fact.source_type,
                    fact.source_id,
                    fact.confidence,
                    fact.created_at.isoformat(),
                    fact.updated_at.isoformat(),
                ),
            )

        self._upsert_embedding(fact)

        return fact

    def reinforce(
        self,
        fact_id: str,
        amount: float = DEFAULT_REINFORCEMENT,
        max_confidence: float = 1.0,
    ) -> StewardFact | None:
        """Increase fact confidence when the same signal reappears."""
        fact = self.get(fact_id)
        if not fact or fact.superseded_by is not None:
            return fact

        new_confidence = min(max_confidence, fact.confidence + amount)
        return self._update_confidence(fact, new_confidence)

    def decay_confidence(
        self,
        fact_id: str,
        amount: float = DEFAULT_CONTRADICTION_DECAY,
        min_confidence: float = 0.0,
    ) -> StewardFact | None:
        """Reduce fact confidence when contradictory evidence appears."""
        fact = self.get(fact_id)
        if not fact:
            return None

        new_confidence = max(min_confidence, fact.confidence - amount)
        return self._update_confidence(fact, new_confidence)

    def apply_time_decay(
        self,
        stale_days: int = 30,
        amount: float = 0.02,
        floor: float = 0.4,
    ) -> int:
        """Decay facts that have not been reinforced recently.

        The method is opt-in so callers can decide whether to schedule time decay.
        """
        cutoff = datetime.now() - timedelta(days=stale_days)
        updated = 0

        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM steward_facts
                WHERE superseded_by IS NULL
                  AND updated_at < ?
                """,
                (cutoff.isoformat(),),
            ).fetchall()

        for row in rows:
            fact = self._row_to_fact(row)
            new_confidence = max(floor, fact.confidence - amount)
            if new_confidence < fact.confidence:
                self._update_confidence(fact, new_confidence)
                updated += 1

        return updated

    def update(
        self,
        fact_id: str,
        new_text: str,
        new_source_id: str,
        new_source_type: FactSource | str | None = None,
        new_category: FactCategory | str | None = None,
        new_confidence: float | None = None,
        decay_amount: float = DEFAULT_CONTRADICTION_DECAY,
    ) -> StewardFact:
        """Update existing fact: supersede old, create new with updated text."""
        old = self.get(fact_id)
        if not old:
            raise ValueError(f"Fact not found: {fact_id}")

        new_id = uuid.uuid4().hex[:16]
        now = datetime.now()
        decayed_confidence = max(0.0, old.confidence - decay_amount)

        # Supersede old fact
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE steward_facts
                SET confidence = ?, updated_at = ?, superseded_by = ?
                WHERE id = ?
                """,
                (decayed_confidence, now.isoformat(), new_id, fact_id),
            )

        # Remove old from ChromaDB
        coll = self._chroma
        if coll:
            try:
                coll.delete(ids=[fact_id])
            except Exception:
                pass

        # Create new fact
        new_fact = StewardFact(
            id=new_id,
            text=new_text,
            category=new_category if new_category is not None else old.category,
            source_type=new_source_type if new_source_type is not None else old.source_type,
            source_id=new_source_id,
            confidence=new_confidence if new_confidence is not None else old.confidence,
            created_at=old.created_at,
            updated_at=now,
        )
        return self.add(new_fact)

    def delete(
        self,
        fact_id: str,
        reason: str = "manual",
        decay_amount: float = DEFAULT_CONTRADICTION_DECAY,
    ) -> None:
        """Soft-delete: set superseded_by. Remove from ChromaDB."""
        fact = self.get(fact_id)
        next_confidence = max(0.0, (fact.confidence if fact else 0.0) - decay_amount)
        now = datetime.now()

        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE steward_facts
                SET confidence = ?, updated_at = ?, superseded_by = ?
                WHERE id = ?
                """,
                (next_confidence, now.isoformat(), f"DELETED:{reason}", fact_id),
            )

        coll = self._chroma
        if coll:
            try:
                coll.delete(ids=[fact_id])
            except Exception:
                pass

    def get(self, fact_id: str) -> StewardFact | None:
        """Get a single fact by ID."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM steward_facts WHERE id = ?", (fact_id,)).fetchone()
            if row:
                return self._row_to_fact(row)
        return None

    def search(
        self,
        query: str,
        limit: int = 10,
        categories: list[FactCategory] | None = None,
    ) -> list[StewardFact]:
        """Semantic search over active facts via ChromaDB."""
        coll = self._chroma
        if not coll:
            # Fallback to keyword search
            return self._keyword_search(query, limit, categories)

        where = None
        if categories:
            cat_values = [c.value if isinstance(c, FactCategory) else c for c in categories]
            if len(cat_values) == 1:
                where = {"category": cat_values[0]}
            else:
                where = {"category": {"$in": cat_values}}

        try:
            # Get active fact IDs first
            active_ids = self._get_active_ids()
            if not active_ids:
                return []

            results = coll.query(
                query_texts=[query],
                n_results=min(limit * 2, len(active_ids)),
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            facts = []
            if results["ids"] and results["ids"][0]:
                for fid in results["ids"][0]:
                    if fid in active_ids:
                        fact = self.get(fid)
                        if fact:
                            facts.append(fact)
                    if len(facts) >= limit:
                        break
            return facts
        except Exception as e:
            logger.warning("chroma_search_failed", error=str(e))
            return self._keyword_search(query, limit, categories)

    def _keyword_search(
        self,
        query: str,
        limit: int = 10,
        categories: list[FactCategory] | None = None,
    ) -> list[StewardFact]:
        """Fallback keyword search in SQLite."""
        query = query.strip()
        if not query:
            return []

        sql = "SELECT * FROM steward_facts WHERE superseded_by IS NULL"
        params: list[str] = []

        if categories:
            cat_values = [c.value if isinstance(c, FactCategory) else c for c in categories]
            placeholders = ",".join("?" for _ in cat_values)
            sql += f" AND category IN ({placeholders})"
            params.extend(cat_values)

        patterns = [query.lower()]
        patterns.extend(token for token in self._search_tokens(query) if token not in patterns)
        placeholders = " OR ".join("LOWER(text) LIKE ?" for _ in patterns)
        sql += f" AND ({placeholders})"
        params.extend(f"%{pattern}%" for pattern in patterns)

        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            facts = [self._row_to_fact(r) for r in rows]

        facts.sort(
            key=lambda fact: (self._fallback_keyword_score(query, fact.text), fact.confidence),
            reverse=True,
        )
        return facts[:limit]

    def get_all_active(self) -> list[StewardFact]:
        """Return all non-superseded facts ordered by confidence desc."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM steward_facts WHERE superseded_by IS NULL ORDER BY confidence DESC"
            ).fetchall()
            return [self._row_to_fact(r) for r in rows]

    def get_by_source(self, source_type: FactSource, source_id: str) -> list[StewardFact]:
        """Find facts derived from a specific source."""
        st = source_type.value if isinstance(source_type, FactSource) else source_type
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM steward_facts WHERE source_type = ? AND source_id = ?",
                (st, source_id),
            ).fetchall()
            return [self._row_to_fact(r) for r in rows]

    def get_by_category(
        self, category: FactCategory, active_only: bool = True
    ) -> list[StewardFact]:
        """Get facts by category."""
        cat = category.value if isinstance(category, FactCategory) else category
        sql = "SELECT * FROM steward_facts WHERE category = ?"
        if active_only:
            sql += " AND superseded_by IS NULL"
        sql += " ORDER BY confidence DESC"
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, (cat,)).fetchall()
            return [self._row_to_fact(r) for r in rows]

    def get_history(self, fact_id: str) -> list[StewardFact]:
        """Return the full supersession chain for a fact."""
        chain = []
        current_id = fact_id

        # Walk backwards through supersession chain
        seen = set()
        while current_id and current_id not in seen:
            seen.add(current_id)
            fact = self.get(current_id)
            if fact:
                chain.append(fact)
            # Check if any fact was superseded_by this one
            with wal_connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT id FROM steward_facts WHERE superseded_by = ?",
                    (current_id,),
                ).fetchone()
                current_id = row[0] if row else None

        chain.reverse()
        return chain

    def get_stats(self) -> dict:
        """Get fact counts by category and total."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM steward_facts WHERE superseded_by IS NULL GROUP BY category"
            ).fetchall()
            by_category = {r["category"]: r["cnt"] for r in rows}

            total = conn.execute(
                "SELECT COUNT(*) FROM steward_facts WHERE superseded_by IS NULL"
            ).fetchone()[0]

            superseded = conn.execute(
                "SELECT COUNT(*) FROM steward_facts WHERE superseded_by IS NOT NULL"
            ).fetchone()[0]

        return {
            "total_active": total,
            "total_superseded": superseded,
            "by_category": by_category,
        }

    def delete_by_source(self, source_type: FactSource, source_id: str) -> int:
        """Delete all facts from a specific source. Returns count deleted."""
        facts = self.get_by_source(source_type, source_id)
        for f in facts:
            if f.superseded_by is None:
                self.delete(f.id, reason=f"source_reextract:{source_id}")
        return len(facts)

    def reset(self) -> int:
        """Delete ALL facts. Returns count deleted."""
        with wal_connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM steward_facts").fetchone()[0]
            conn.execute("DELETE FROM steward_facts")

        coll = self._chroma
        if coll:
            try:
                # Get all IDs and delete
                existing = coll.get()
                if existing["ids"]:
                    coll.delete(ids=existing["ids"])
            except Exception:
                pass

        return count

    def _get_active_ids(self) -> set[str]:
        """Get set of active (non-superseded) fact IDs."""
        with wal_connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id FROM steward_facts WHERE superseded_by IS NULL"
            ).fetchall()
            return {r[0] for r in rows}

    def _update_confidence(self, fact: StewardFact, new_confidence: float) -> StewardFact:
        now = datetime.now()
        with wal_connect(self.db_path) as conn:
            conn.execute(
                "UPDATE steward_facts SET confidence = ?, updated_at = ? WHERE id = ?",
                (new_confidence, now.isoformat(), fact.id),
            )

        updated = StewardFact(
            id=fact.id,
            text=fact.text,
            category=fact.category,
            source_type=fact.source_type,
            source_id=fact.source_id,
            confidence=new_confidence,
            created_at=fact.created_at,
            updated_at=now,
            superseded_by=fact.superseded_by,
        )
        self._upsert_embedding(updated)
        return updated

    def _upsert_embedding(self, fact: StewardFact) -> None:
        """Sync fact confidence metadata into ChromaDB when available."""
        coll = self._chroma
        if not coll:
            return

        try:
            cat = fact.category.value if isinstance(fact.category, FactCategory) else fact.category
            coll.upsert(
                ids=[fact.id],
                documents=[fact.text],
                metadatas=[{"category": cat, "confidence": fact.confidence}],
            )
        except Exception as e:
            logger.warning("chroma_upsert_failed", fact_id=fact.id, error=str(e))

    @staticmethod
    def _search_tokens(text: str) -> list[str]:
        return [
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) >= 3 and token not in _SEARCH_STOPWORDS
        ]

    @classmethod
    def _fallback_keyword_score(cls, query: str, text: str) -> float:
        query_lower = query.lower()
        text_lower = text.lower()
        exact_match = 1.0 if query_lower in text_lower else 0.0
        query_tokens = set(cls._search_tokens(query))
        if not query_tokens:
            return exact_match

        text_tokens = set(cls._search_tokens(text))
        if not text_tokens:
            return exact_match

        overlap = len(query_tokens & text_tokens) / len(query_tokens)
        return max(exact_match, overlap)

    @staticmethod
    def _row_to_fact(row: sqlite3.Row) -> StewardFact:
        d = dict(row)
        created = d.get("created_at", "")
        updated = d.get("updated_at", "")
        return StewardFact(
            id=d["id"],
            text=d["text"],
            category=FactCategory(d["category"]),
            source_type=FactSource(d["source_type"]),
            source_id=d["source_id"],
            confidence=d["confidence"],
            created_at=datetime.fromisoformat(created) if created else datetime.now(),
            updated_at=datetime.fromisoformat(updated) if updated else datetime.now(),
            superseded_by=d.get("superseded_by"),
        )

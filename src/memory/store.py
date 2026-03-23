"""Persistent storage for Steward Facts — SQLite metadata + ChromaDB embeddings."""

import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import structlog

from db import ensure_schema_version, wal_connect

from .entity_extractor import extract_entities
from .models import FactCategory, FactSource, StewardFact

logger = structlog.get_logger()

SCHEMA_VERSION = 4
DEFAULT_REINFORCEMENT = 0.05
DEFAULT_CONTRADICTION_DECAY = 0.15
_MIN_ABSTRACT_WORDS = 3
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

    def __init__(
        self,
        db_path: str | Path,
        chroma_dir: str | Path | None = None,
        config: dict | None = None,
    ):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._chroma_dir = Path(chroma_dir).expanduser() if chroma_dir else None
        self._config = config
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
            # Entity graph tables (v2)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fact_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    normalized TEXT NOT NULL UNIQUE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fact_entities_normalized
                ON fact_entities(normalized)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fact_entity_links (
                    entity_id INTEGER NOT NULL REFERENCES fact_entities(id),
                    fact_id TEXT NOT NULL REFERENCES steward_facts(id),
                    PRIMARY KEY (entity_id, fact_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fact_entity_links_fact
                ON fact_entity_links(fact_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fact_entity_links_entity
                ON fact_entity_links(entity_id)
            """)
            # Observation consolidation junction table (v3)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS observation_sources (
                    observation_id TEXT NOT NULL REFERENCES steward_facts(id),
                    fact_id TEXT NOT NULL REFERENCES steward_facts(id),
                    PRIMARY KEY (observation_id, fact_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_obs_sources_obs
                ON observation_sources(observation_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_obs_sources_fact
                ON observation_sources(fact_id)
            """)
            # L0 abstract column (v4)
            try:
                conn.execute("ALTER TABLE steward_facts ADD COLUMN abstract TEXT")
            except sqlite3.OperationalError:
                pass  # column already exists
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

                    embedding_fn = create_embedding_function(config=self._config)
                except Exception as e:
                    logger.warning("embedding_factory_failed", error=str(e))

                if embedding_fn is None:
                    logger.info("memory_chroma_skipped_no_embeddings")
                    return None

                # Derive versioned collection name
                coll_name = "steward_facts"
                try:
                    from embeddings.versioning import versioned_name

                    if embedding_fn is not None:
                        coll_name = versioned_name("steward_facts", embedding_fn)
                except Exception:
                    pass

                kwargs = {
                    "name": coll_name,
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
                   (id, text, category, source_type, source_id, confidence, created_at, updated_at, abstract)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                    fact.abstract,
                ),
            )

        self._upsert_embedding(fact)
        self._index_entities(fact)

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
        new_abstract: str | None = None,
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
            conn.execute("DELETE FROM fact_entity_links WHERE fact_id = ?", (fact_id,))

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
            abstract=new_abstract,
        )
        return self.add(new_fact)

    def delete(
        self,
        fact_id: str,
        reason: str = "manual",
        decay_amount: float = DEFAULT_CONTRADICTION_DECAY,
    ) -> None:
        """Soft-delete: set superseded_by. Remove from ChromaDB. Orphan-clean observations."""
        fact = self.get(fact_id)
        if not fact:
            return  # nothing to delete
        next_confidence = max(0.0, fact.confidence - decay_amount)
        now = datetime.now()

        # Single transaction: read affected obs, soft-delete, clean links
        affected_obs_ids: list[str] = []
        with wal_connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT observation_id FROM observation_sources WHERE fact_id = ?",
                (fact_id,),
            ).fetchall()
            affected_obs_ids = [r[0] for r in rows]
            conn.execute(
                """
                UPDATE steward_facts
                SET confidence = ?, updated_at = ?, superseded_by = ?
                WHERE id = ?
                """,
                (next_confidence, now.isoformat(), f"DELETED:{reason}", fact_id),
            )
            conn.execute("DELETE FROM fact_entity_links WHERE fact_id = ?", (fact_id,))
            conn.execute("DELETE FROM observation_sources WHERE fact_id = ?", (fact_id,))

        coll = self._chroma
        if coll:
            try:
                coll.delete(ids=[fact_id])
            except Exception:
                pass

        # Orphan cleanup: soft-delete observations with zero remaining active sources
        self._cleanup_orphaned_observations(affected_obs_ids)

    def _cleanup_orphaned_observations(self, obs_ids: list[str]) -> None:
        """Soft-delete observations that have zero remaining active source facts.

        Uses direct SQL to avoid recursive delete() → _cleanup_orphaned_observations cycles.
        """
        now = datetime.now()
        for obs_id in obs_ids:
            obs = self.get(obs_id)
            if not obs or obs.superseded_by is not None:
                continue
            with wal_connect(self.db_path) as conn:
                remaining = conn.execute(
                    """
                    SELECT COUNT(*) FROM observation_sources os
                    JOIN steward_facts f ON os.fact_id = f.id
                    WHERE os.observation_id = ? AND f.superseded_by IS NULL
                    """,
                    (obs_id,),
                ).fetchone()[0]
            if remaining == 0:
                with wal_connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE steward_facts SET superseded_by = ?, updated_at = ? WHERE id = ? AND superseded_by IS NULL",
                        ("DELETED:orphaned_observation", now.isoformat(), obs_id),
                    )
                    conn.execute("DELETE FROM fact_entity_links WHERE fact_id = ?", (obs_id,))
                    conn.execute(
                        "DELETE FROM observation_sources WHERE observation_id = ?", (obs_id,)
                    )
                coll = self._chroma
                if coll:
                    try:
                        coll.delete(ids=[obs_id])
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
        use_graph: bool = True,
        graph_limit: int = 5,
        alpha: float = 0.5,
    ) -> list[StewardFact]:
        """Semantic search over active facts via ChromaDB, with optional graph expansion.

        When ChromaDB is available, uses parent-score propagation: embedding scores
        flow through entity groups to boost topically related neighbors.
        ``alpha`` controls the blend: 1.0 = pure embedding, 0.0 = pure group score.
        """
        coll = self._chroma
        if not coll:
            seeds = self._keyword_search(query, limit, categories)
            if not use_graph or not seeds:
                return seeds[:limit]
            return self._graph_expand_and_merge(seeds, limit, graph_limit, categories)

        scored_seeds = self._chroma_search_scored(query, limit, categories)
        if not use_graph or not scored_seeds:
            return [f for f, _ in scored_seeds][:limit]

        return self._propagate_and_merge(scored_seeds, limit, graph_limit, categories, alpha)

    def _chroma_search_scored(
        self,
        query: str,
        limit: int,
        categories: list[FactCategory] | None = None,
    ) -> list[tuple[StewardFact, float]]:
        """ChromaDB semantic search returning (fact, similarity_score) tuples."""
        coll = self._chroma
        if not coll:
            return [(f, 0.0) for f in self._keyword_search(query, limit, categories)]

        where = None
        if categories:
            cat_values = [c.value if isinstance(c, FactCategory) else c for c in categories]
            if len(cat_values) == 1:
                where = {"category": cat_values[0]}
            else:
                where = {"category": {"$in": cat_values}}

        try:
            active_ids = self._get_active_ids()
            if not active_ids:
                return []

            results = coll.query(
                query_texts=[query],
                n_results=min(limit * 2, len(active_ids)),
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            facts: list[tuple[StewardFact, float]] = []
            if results["ids"] and results["ids"][0]:
                distances = results["distances"][0] if results.get("distances") else []
                for idx, fid in enumerate(results["ids"][0]):
                    if fid in active_ids:
                        fact = self.get(fid)
                        if fact:
                            # Cosine distance ∈ [0,2]; normalize to similarity ∈ [0,1]
                            score = max(0.0, 1.0 - distances[idx]) if idx < len(distances) else 0.0
                            facts.append((fact, score))
                    if len(facts) >= limit:
                        break
            return facts
        except Exception as e:
            logger.warning("chroma_search_failed", error=str(e))
            return [(f, 0.0) for f in self._keyword_search(query, limit, categories)]

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

    def get_facts_for_entity(self, normalized_name: str, limit: int = 5) -> list[StewardFact]:
        """Return active facts linked to a memory entity by normalized name.

        Uses whitespace-collapsed matching to bridge different normalization schemes.
        """
        collapsed = " ".join(normalized_name.lower().split())
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT f.* FROM steward_facts f
                JOIN fact_entity_links l ON f.id = l.fact_id
                JOIN fact_entities e ON l.entity_id = e.id
                WHERE REPLACE(e.normalized, '  ', ' ') = ?
                  AND f.superseded_by IS NULL
                ORDER BY f.confidence DESC
                LIMIT ?
                """,
                (collapsed, limit),
            ).fetchall()
            return [self._row_to_fact(r) for r in rows]

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

    def link_observation_sources(self, observation_id: str, fact_ids: list[str]) -> None:
        """Bulk insert links between an observation and its source facts."""
        if not fact_ids:
            return
        with wal_connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO observation_sources (observation_id, fact_id) VALUES (?, ?)",
                [(observation_id, fid) for fid in fact_ids],
            )

    def get_observation_source_ids(self, observation_id: str) -> list[str]:
        """Return active fact IDs backing an observation."""
        with wal_connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT os.fact_id FROM observation_sources os
                   JOIN steward_facts f ON os.fact_id = f.id
                   WHERE os.observation_id = ? AND f.superseded_by IS NULL""",
                (observation_id,),
            ).fetchall()
            return [r[0] for r in rows]

    def get_observations_for_fact(self, fact_id: str) -> list[StewardFact]:
        """Return active observations that cite a given fact."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT f.* FROM steward_facts f
                JOIN observation_sources os ON f.id = os.observation_id
                WHERE os.fact_id = ? AND f.superseded_by IS NULL
                """,
                (fact_id,),
            ).fetchall()
            return [self._row_to_fact(r) for r in rows]

    def get_all_active_observations(self) -> list[StewardFact]:
        """Return all active observations (category=observation, not superseded)."""
        return self.get_by_category(FactCategory.OBSERVATION, active_only=True)

    def get_history(self, fact_id: str) -> list[StewardFact]:
        """Return the full supersession chain for a fact (oldest first).

        Works from any point in the chain — walks forward to find the newest,
        then walks backward to collect the full chain.
        """
        # Step 1: walk forward via superseded_by to find the chain tail (newest)
        tail_id = fact_id
        seen_forward: set[str] = {tail_id}
        with wal_connect(self.db_path) as conn:
            while True:
                row = conn.execute(
                    "SELECT superseded_by FROM steward_facts WHERE id = ?",
                    (tail_id,),
                ).fetchone()
                if not row or not row[0] or row[0].startswith("DELETED:"):
                    break
                next_id = row[0]
                if next_id in seen_forward:
                    break
                seen_forward.add(next_id)
                tail_id = next_id

        # Step 2: walk backward from tail — find who was superseded by each ID
        chain: list[StewardFact] = []
        current_id: str | None = tail_id
        seen: set[str] = set()
        while current_id and current_id not in seen:
            seen.add(current_id)
            fact = self.get(current_id)
            if fact:
                chain.append(fact)
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
            conn.execute("DELETE FROM observation_sources")
            conn.execute("DELETE FROM fact_entity_links")
            conn.execute("DELETE FROM fact_entities")
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

    def backfill_entity_links(self) -> int:
        """Index entities for all active facts missing entity links. One-time migration."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT f.* FROM steward_facts f
                LEFT JOIN fact_entity_links l ON f.id = l.fact_id
                WHERE f.superseded_by IS NULL AND l.fact_id IS NULL
            """).fetchall()

        count = 0
        for row in rows:
            fact = self._row_to_fact(row)
            self._index_entities(fact)
            count += 1
        return count

    def _index_entities(self, fact: StewardFact) -> None:
        """Extract entities from fact text and store links."""
        entities = extract_entities(fact.text)
        if not entities:
            return

        with wal_connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO fact_entities (name, normalized) VALUES (?, ?)",
                entities,
            )
            normalized_names = [n for _, n in entities]
            placeholders = ",".join("?" for _ in normalized_names)
            rows = conn.execute(
                f"SELECT id, normalized FROM fact_entities WHERE normalized IN ({placeholders})",
                normalized_names,
            ).fetchall()
            conn.executemany(
                "INSERT OR IGNORE INTO fact_entity_links (entity_id, fact_id) VALUES (?, ?)",
                [(row[0], fact.id) for row in rows],
            )

    def _get_entity_neighbors(
        self, seed_ids: set[str], exclude_ids: set[str]
    ) -> list[tuple[str, int]]:
        """Find active facts sharing entities with seed facts.

        Returns list of (fact_id, shared_entity_count) ordered by shared_count DESC.
        """
        if not seed_ids:
            return []

        placeholders = ",".join("?" for _ in seed_ids)
        exclude_all = seed_ids | exclude_ids
        exclude_ph = ",".join("?" for _ in exclude_all)

        with wal_connect(self.db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT l2.fact_id, COUNT(DISTINCT l2.entity_id) as shared_count
                FROM fact_entity_links l1
                JOIN fact_entity_links l2 ON l1.entity_id = l2.entity_id
                JOIN steward_facts f ON l2.fact_id = f.id
                WHERE l1.fact_id IN ({placeholders})
                  AND l2.fact_id NOT IN ({exclude_ph})
                  AND f.superseded_by IS NULL
                GROUP BY l2.fact_id
                ORDER BY shared_count DESC
                """,
                list(seed_ids) + list(exclude_all),
            ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def _graph_expand_and_merge(
        self,
        seeds: list[StewardFact],
        limit: int,
        graph_limit: int,
        categories: list[FactCategory] | None = None,
    ) -> list[StewardFact]:
        """Expand seed results via entity graph and merge with RRF.

        Used only for keyword fallback path (no embedding scores available).
        When ChromaDB is available, _propagate_and_merge is used instead.
        """
        seed_ids = {f.id for f in seeds}
        neighbors = self._get_entity_neighbors(seed_ids, set())

        if not neighbors:
            return seeds[:limit]

        cat_values = None
        if categories:
            cat_values = {c.value if isinstance(c, FactCategory) else c for c in categories}

        # RRF merge
        k = 60
        seed_weight, graph_weight = 0.8, 0.2
        scores: dict[str, float] = {}
        fact_map: dict[str, StewardFact] = {}

        for i, fact in enumerate(seeds):
            scores[fact.id] = scores.get(fact.id, 0.0) + seed_weight / (k + i + 1)
            fact_map[fact.id] = fact

        added = 0
        for rank, (fact_id, shared_count) in enumerate(neighbors):
            if added >= graph_limit:
                break
            # Filter by category if specified
            if cat_values and fact_id not in fact_map:
                fact = self.get(fact_id)
                if not fact:
                    continue
                fact_cat = (
                    fact.category.value
                    if isinstance(fact.category, FactCategory)
                    else fact.category
                )
                if fact_cat not in cat_values:
                    continue
                fact_map[fact_id] = fact
                added += 1
            elif fact_id not in fact_map:
                fact = self.get(fact_id)
                if not fact:
                    continue
                fact_map[fact_id] = fact
                added += 1

            boost = min(1.0, shared_count * 0.5)
            scores[fact_id] = scores.get(fact_id, 0.0) + graph_weight * (1 + boost) / (k + rank + 1)

        ranked = sorted(scores.keys(), key=lambda fid: scores[fid], reverse=True)
        return [fact_map[fid] for fid in ranked if fid in fact_map][:limit]

    def _get_fact_entities(self, fact_ids: set[str]) -> dict[str, list[int]]:
        """Map fact_id → list of entity_ids it's linked to."""
        if not fact_ids:
            return {}
        placeholders = ",".join("?" for _ in fact_ids)
        with wal_connect(self.db_path) as conn:
            rows = conn.execute(
                f"SELECT fact_id, entity_id FROM fact_entity_links WHERE fact_id IN ({placeholders})",
                list(fact_ids),
            ).fetchall()
        result: dict[str, list[int]] = {}
        for fact_id, entity_id in rows:
            result.setdefault(fact_id, []).append(entity_id)
        return result

    def _propagate_and_merge(
        self,
        scored_seeds: list[tuple[StewardFact, float]],
        limit: int,
        graph_limit: int,
        categories: list[FactCategory] | None = None,
        alpha: float = 0.5,
    ) -> list[StewardFact]:
        """Parent-score propagation: embedding scores flow through entity groups to neighbors."""
        seed_scores: dict[str, float] = {f.id: s for f, s in scored_seeds}
        fact_map: dict[str, StewardFact] = {f.id: f for f, _ in scored_seeds}
        seed_ids = set(seed_scores.keys())

        # Step 1: map seed facts → their entities
        seed_entity_map = self._get_fact_entities(seed_ids)

        # Step 2: entity-group scores = max embedding score of seeds linked to each entity
        entity_group_scores: dict[int, float] = {}
        for fid, entity_ids in seed_entity_map.items():
            emb = seed_scores.get(fid, 0.0)
            for eid in entity_ids:
                if emb > entity_group_scores.get(eid, 0.0):
                    entity_group_scores[eid] = emb

        # Step 3: get graph neighbors
        neighbors = self._get_entity_neighbors(seed_ids, set())
        if not neighbors and not entity_group_scores:
            # No entities, no neighbors — fall back to embedding score order
            return [f for f, _ in sorted(scored_seeds, key=lambda x: x[1], reverse=True)][:limit]

        # Load neighbor facts (respecting category filter + graph_limit)
        cat_values = None
        if categories:
            cat_values = {c.value if isinstance(c, FactCategory) else c for c in categories}

        added = 0
        neighbor_ids: list[str] = []
        for fact_id, _shared_count in neighbors:
            if added >= graph_limit:
                break
            if fact_id in fact_map:
                continue
            fact = self.get(fact_id)
            if not fact:
                continue
            if cat_values:
                fact_cat = (
                    fact.category.value
                    if isinstance(fact.category, FactCategory)
                    else fact.category
                )
                if fact_cat not in cat_values:
                    continue
            fact_map[fact_id] = fact
            neighbor_ids.append(fact_id)
            added += 1

        # Step 4: map neighbor facts → their entities
        neighbor_entity_map = self._get_fact_entities(set(neighbor_ids))

        # Step 5: score all facts
        final_scores: dict[str, float] = {}

        for fid, emb_score in seed_scores.items():
            eids = seed_entity_map.get(fid, [])
            group_score = max((entity_group_scores.get(eid, 0.0) for eid in eids), default=0.0)
            final_scores[fid] = alpha * emb_score + (1 - alpha) * group_score

        for fid in neighbor_ids:
            eids = neighbor_entity_map.get(fid, [])
            group_score = max((entity_group_scores.get(eid, 0.0) for eid in eids), default=0.0)
            # Neighbors have no direct embedding score
            final_scores[fid] = (1 - alpha) * group_score

        # Step 6: observation → fact propagation
        obs_boost = 0.1
        for fid in list(final_scores.keys()):
            fact = fact_map.get(fid)
            if not fact:
                continue
            cat = fact.category.value if isinstance(fact.category, FactCategory) else fact.category
            if cat != FactCategory.OBSERVATION.value:
                continue
            source_ids = self.get_observation_source_ids(fid)
            for sid in source_ids[:graph_limit]:
                boost = obs_boost * final_scores[fid]
                if sid in final_scores:
                    final_scores[sid] += boost
                else:
                    source_fact = self.get(sid)
                    if source_fact:
                        fact_map[sid] = source_fact
                        final_scores[sid] = boost

        ranked = sorted(final_scores.keys(), key=lambda fid: final_scores[fid], reverse=True)
        return [fact_map[fid] for fid in ranked if fid in fact_map][:limit]

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
            abstract=fact.abstract,
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
            doc_text = (
                fact.abstract
                if fact.abstract and len(fact.abstract.split()) >= _MIN_ABSTRACT_WORDS
                else fact.text
            )
            coll.upsert(
                ids=[fact.id],
                documents=[doc_text],
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
            abstract=d.get("abstract"),
        )

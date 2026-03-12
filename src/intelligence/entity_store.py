"""SQLite-backed entity and relationship storage for intel items."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from db import ensure_schema_version, wal_connect

SCHEMA_VERSION = 6


def normalize_entity_name(name: str) -> str:
    """Normalize an entity name for de-duplication."""
    return " ".join((name or "").lower().strip().split())


class EntityStore:
    """Persistence layer for extracted entities and relationships."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    aliases TEXT,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    item_count INTEGER DEFAULT 0,
                    UNIQUE(normalized_name, type)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_entities_normalized ON entities(normalized_name)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entity_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL REFERENCES entities(id),
                    target_id INTEGER NOT NULL REFERENCES entities(id),
                    type TEXT NOT NULL,
                    evidence TEXT,
                    item_id INTEGER REFERENCES intel_items(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_id, target_id, type)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_relationships_source ON entity_relationships(source_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_relationships_target ON entity_relationships(target_id)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entity_item_links (
                    entity_id INTEGER NOT NULL REFERENCES entities(id),
                    item_id INTEGER NOT NULL REFERENCES intel_items(id),
                    PRIMARY KEY (entity_id, item_id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_item_links_item ON entity_item_links(item_id)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entity_item_processing (
                    item_id INTEGER PRIMARY KEY REFERENCES intel_items(id),
                    status TEXT NOT NULL,
                    last_error TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cross_entity_links (
                    intel_entity_id INTEGER NOT NULL REFERENCES entities(id),
                    memory_normalized TEXT NOT NULL,
                    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (intel_entity_id, memory_normalized)
                )
                """
            )
            ensure_schema_version(conn, SCHEMA_VERSION)

    @staticmethod
    def _decode_aliases(aliases: str | None) -> list[str]:
        if not aliases:
            return []
        try:
            data = json.loads(aliases)
            return [str(alias) for alias in data if str(alias).strip()]
        except json.JSONDecodeError:
            return []

    def save_entity(self, name: str, entity_type: str, aliases: list[str] | None = None) -> int:
        normalized_name = normalize_entity_name(name)
        alias_values = {
            alias.strip()
            for alias in (aliases or [])
            if alias and normalize_entity_name(alias) != normalized_name
        }

        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO entities (name, normalized_name, type, aliases)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        name.strip(),
                        normalized_name,
                        entity_type,
                        json.dumps(sorted(alias_values)) if alias_values else None,
                    ),
                )
                return int(cursor.lastrowid)
            except sqlite3.IntegrityError:
                row = conn.execute(
                    "SELECT id, name, aliases FROM entities WHERE normalized_name = ? AND type = ?",
                    (normalized_name, entity_type),
                ).fetchone()
                if not row:
                    raise
                merged_aliases = set(self._decode_aliases(row["aliases"]))
                merged_aliases.update(alias_values)
                # Add incoming name as alias when it differs from the stored display name
                if name.strip() and name.strip() != row["name"]:
                    merged_aliases.add(name.strip())
                conn.execute(
                    "UPDATE entities SET aliases = ? WHERE id = ?",
                    (json.dumps(sorted(merged_aliases)) if merged_aliases else None, row["id"]),
                )
                return int(row["id"])

    def save_relationship(
        self,
        source_id: int,
        target_id: int,
        rel_type: str,
        evidence: str = "",
        item_id: int | None = None,
    ) -> int:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO entity_relationships (source_id, target_id, type, evidence, item_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (source_id, target_id, rel_type, evidence, item_id),
                )
                return int(cursor.lastrowid)
            except sqlite3.IntegrityError:
                row = conn.execute(
                    """
                    SELECT id, evidence, item_id
                    FROM entity_relationships
                    WHERE source_id = ? AND target_id = ? AND type = ?
                    """,
                    (source_id, target_id, rel_type),
                ).fetchone()
                if not row:
                    raise
                next_evidence = evidence or row["evidence"] or ""
                next_item_id = item_id if item_id is not None else row["item_id"]
                conn.execute(
                    "UPDATE entity_relationships SET evidence = ?, item_id = ? WHERE id = ?",
                    (next_evidence, next_item_id, row["id"]),
                )
                return int(row["id"])

    def link_item(self, item_id: int, entity_id: int) -> None:
        with wal_connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO entity_item_links (entity_id, item_id) VALUES (?, ?)",
                (entity_id, item_id),
            )
            if cursor.rowcount:
                conn.execute(
                    "UPDATE entities SET item_count = item_count + 1 WHERE id = ?",
                    (entity_id,),
                )

    def get_entity(self, entity_id: int) -> dict | None:
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
        if not row:
            return None
        entity = dict(row)
        entity["aliases"] = self._decode_aliases(entity.get("aliases"))
        return entity

    def get_entity_by_name(self, name: str, entity_type: str | None = None) -> dict | None:
        normalized_name = normalize_entity_name(name)
        with wal_connect(self.db_path, row_factory=True) as conn:
            if entity_type:
                row = conn.execute(
                    """
                    SELECT * FROM entities
                    WHERE normalized_name = ? AND type = ?
                    """,
                    (normalized_name, entity_type),
                ).fetchone()
                if row:
                    entity = dict(row)
                    entity["aliases"] = self._decode_aliases(entity.get("aliases"))
                    return entity

            rows = conn.execute(
                "SELECT * FROM entities WHERE normalized_name = ?", (normalized_name,)
            ).fetchall()
            if rows:
                entity = dict(rows[0])
                entity["aliases"] = self._decode_aliases(entity.get("aliases"))
                return entity

            rows = conn.execute(
                "SELECT * FROM entities WHERE COALESCE(aliases, '') LIKE ?",
                (f"%{normalized_name}%",),
            ).fetchall()

        for row in rows:
            aliases = self._decode_aliases(row["aliases"])
            if normalized_name in {normalize_entity_name(alias) for alias in aliases}:
                entity = dict(row)
                entity["aliases"] = aliases
                return entity
        return None

    def search_entities(
        self,
        query: str,
        limit: int = 20,
        entity_type: str | None = None,
    ) -> list[dict]:
        normalized_query = normalize_entity_name(query)
        like_query = f"%{normalized_query}%"
        with wal_connect(self.db_path, row_factory=True) as conn:
            params: list[object] = [like_query, like_query]
            sql = """
                SELECT * FROM entities
                WHERE (normalized_name LIKE ? OR COALESCE(aliases, '') LIKE ?)
            """
            if entity_type:
                sql += " AND type = ?"
                params.append(entity_type)
            sql += " ORDER BY item_count DESC, name ASC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, tuple(params)).fetchall()

        entities = []
        for row in rows:
            entity = dict(row)
            entity["aliases"] = self._decode_aliases(entity.get("aliases"))
            entities.append(entity)
        return entities

    def get_relationships(self, entity_id: int, direction: str = "both") -> list[dict]:
        with wal_connect(self.db_path, row_factory=True) as conn:
            params: tuple[object, ...]
            if direction == "outgoing":
                sql = """
                    SELECT r.*, s.name AS source_name, t.name AS target_name
                    FROM entity_relationships r
                    JOIN entities s ON s.id = r.source_id
                    JOIN entities t ON t.id = r.target_id
                    WHERE r.source_id = ?
                    ORDER BY r.created_at DESC
                """
                params = (entity_id,)
            elif direction == "incoming":
                sql = """
                    SELECT r.*, s.name AS source_name, t.name AS target_name
                    FROM entity_relationships r
                    JOIN entities s ON s.id = r.source_id
                    JOIN entities t ON t.id = r.target_id
                    WHERE r.target_id = ?
                    ORDER BY r.created_at DESC
                """
                params = (entity_id,)
            else:
                sql = """
                    SELECT r.*, s.name AS source_name, t.name AS target_name
                    FROM entity_relationships r
                    JOIN entities s ON s.id = r.source_id
                    JOIN entities t ON t.id = r.target_id
                    WHERE r.source_id = ? OR r.target_id = ?
                    ORDER BY r.created_at DESC
                """
                params = (entity_id, entity_id)
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def get_entity_items(self, entity_id: int, limit: int = 20) -> list[dict]:
        with wal_connect(self.db_path, row_factory=True) as conn:
            rows = conn.execute(
                """
                SELECT i.*
                FROM entity_item_links l
                JOIN intel_items i ON i.id = l.item_id
                WHERE l.entity_id = ?
                ORDER BY i.scraped_at DESC
                LIMIT ?
                """,
                (entity_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_item_entities(self, item_id: int) -> list[dict]:
        with wal_connect(self.db_path, row_factory=True) as conn:
            rows = conn.execute(
                """
                SELECT e.*
                FROM entity_item_links l
                JOIN entities e ON e.id = l.entity_id
                WHERE l.item_id = ?
                ORDER BY e.item_count DESC, e.name ASC
                """,
                (item_id,),
            ).fetchall()
        entities = []
        for row in rows:
            entity = dict(row)
            entity["aliases"] = self._decode_aliases(entity.get("aliases"))
            entities.append(entity)
        return entities

    def is_item_processed(self, item_id: int) -> bool:
        with wal_connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT status FROM entity_item_processing WHERE item_id = ? LIMIT 1",
                (item_id,),
            ).fetchone()
            if row is not None:
                return True
            row = conn.execute(
                "SELECT 1 FROM entity_item_links WHERE item_id = ? LIMIT 1",
                (item_id,),
            ).fetchone()
        return row is not None

    def mark_item_processed(self, item_id: int, status: str, last_error: str | None = None) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO entity_item_processing (item_id, status, last_error, processed_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(item_id) DO UPDATE SET
                    status = excluded.status,
                    last_error = excluded.last_error,
                    processed_at = CURRENT_TIMESTAMP
                """,
                (item_id, status, last_error),
            )

    def get_unprocessed_items(self, limit: int = 100) -> list[int]:
        with wal_connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT i.id
                FROM intel_items i
                LEFT JOIN entity_item_links l ON l.item_id = i.id
                LEFT JOIN entity_item_processing p ON p.item_id = i.id
                WHERE l.item_id IS NULL AND p.item_id IS NULL
                ORDER BY i.scraped_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [int(row[0]) for row in rows]

    def save_cross_entity_link(self, intel_entity_id: int, memory_normalized: str) -> None:
        """Persist a link between an intel entity and a memory entity normalized name."""
        with wal_connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO cross_entity_links (intel_entity_id, memory_normalized) VALUES (?, ?)",
                (intel_entity_id, memory_normalized),
            )

    def get_cross_entity_links(self, intel_entity_id: int) -> list[str]:
        """Return memory normalized names linked to an intel entity."""
        with wal_connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT memory_normalized FROM cross_entity_links WHERE intel_entity_id = ?",
                (intel_entity_id,),
            ).fetchall()
        return [row[0] for row in rows]

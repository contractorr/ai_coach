"""SQLite persistence for curriculum catalog and user progress."""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import structlog

from db import ensure_schema_version, wal_connect

from .models import (
    Chapter,
    Guide,
    LearningStats,
    ReviewItem,
)
from .spaced_repetition import sm2_update

logger = structlog.get_logger()

SCHEMA_VERSION = 6


class CurriculumStore:
    """SQLite store for curriculum catalog + user progress."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS guides (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT 'humanities',
                    difficulty TEXT NOT NULL DEFAULT 'intermediate',
                    source_dir TEXT NOT NULL DEFAULT '',
                    origin TEXT NOT NULL DEFAULT 'builtin',
                    kind TEXT NOT NULL DEFAULT 'core',
                    owner_user_id TEXT NOT NULL DEFAULT '',
                    base_guide_id TEXT,
                    chapter_count INTEGER NOT NULL DEFAULT 0,
                    total_word_count INTEGER NOT NULL DEFAULT 0,
                    total_reading_time_minutes INTEGER NOT NULL DEFAULT 0,
                    has_glossary INTEGER NOT NULL DEFAULT 0,
                    prerequisites TEXT NOT NULL DEFAULT '[]',
                    track TEXT NOT NULL DEFAULT '',
                    archived_at TEXT,
                    archive_path TEXT NOT NULL DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id TEXT PRIMARY KEY,
                    guide_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    "order" INTEGER NOT NULL DEFAULT 0,
                    summary TEXT NOT NULL DEFAULT '',
                    objectives TEXT NOT NULL DEFAULT '[]',
                    checkpoints TEXT NOT NULL DEFAULT '[]',
                    content_references TEXT NOT NULL DEFAULT '[]',
                    content_format TEXT NOT NULL DEFAULT 'markdown',
                    schema_version INTEGER NOT NULL DEFAULT 0,
                    word_count INTEGER NOT NULL DEFAULT 0,
                    reading_time_minutes INTEGER NOT NULL DEFAULT 0,
                    has_diagrams INTEGER NOT NULL DEFAULT 0,
                    has_tables INTEGER NOT NULL DEFAULT 0,
                    has_formulas INTEGER NOT NULL DEFAULT 0,
                    is_glossary INTEGER NOT NULL DEFAULT 0,
                    content_hash TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (guide_id) REFERENCES guides(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chapters_guide
                ON chapters(guide_id, "order")
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_guide_enrollment (
                    user_id TEXT NOT NULL,
                    guide_id TEXT NOT NULL,
                    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    linked_goal_id TEXT,
                    PRIMARY KEY (user_id, guide_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_chapter_progress (
                    user_id TEXT NOT NULL,
                    chapter_id TEXT NOT NULL,
                    guide_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'not_started',
                    reading_time_seconds INTEGER NOT NULL DEFAULT 0,
                    scroll_position REAL NOT NULL DEFAULT 0.0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, chapter_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_progress_guide
                ON user_chapter_progress(user_id, guide_id)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS review_items (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    chapter_id TEXT NOT NULL,
                    guide_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    expected_answer TEXT NOT NULL DEFAULT '',
                    bloom_level TEXT NOT NULL DEFAULT 'remember',
                    easiness_factor REAL NOT NULL DEFAULT 2.5,
                    interval_days INTEGER NOT NULL DEFAULT 1,
                    repetitions INTEGER NOT NULL DEFAULT 0,
                    next_review TIMESTAMP,
                    last_reviewed TIMESTAMP,
                    content_hash TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_review_due
                ON review_items(user_id, next_review)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_review_chapter
                ON review_items(user_id, chapter_id)
            """)
            # --- v1 → v2 migration: add item_type column ---
            current_ver = conn.execute("PRAGMA user_version").fetchone()[0]
            if current_ver < 2:
                try:
                    conn.execute(
                        "ALTER TABLE review_items ADD COLUMN item_type TEXT NOT NULL DEFAULT 'quiz'"
                    )
                except sqlite3.OperationalError:
                    pass  # column already exists
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_review_type ON review_items(item_type)"
                )

            # --- v2 → v3 migration: add track column to guides ---
            if current_ver < 3:
                try:
                    conn.execute("ALTER TABLE guides ADD COLUMN track TEXT NOT NULL DEFAULT ''")
                except sqlite3.OperationalError:
                    pass  # column already exists

            # --- v3 -> v4 migration: add schema-aware chapter metadata ---
            if current_ver < 4:
                for statement in (
                    "ALTER TABLE chapters ADD COLUMN summary TEXT NOT NULL DEFAULT ''",
                    "ALTER TABLE chapters ADD COLUMN objectives TEXT NOT NULL DEFAULT '[]'",
                    "ALTER TABLE chapters ADD COLUMN checkpoints TEXT NOT NULL DEFAULT '[]'",
                    "ALTER TABLE chapters ADD COLUMN content_references TEXT NOT NULL DEFAULT '[]'",
                    "ALTER TABLE chapters ADD COLUMN content_format TEXT NOT NULL DEFAULT 'markdown'",
                    "ALTER TABLE chapters ADD COLUMN schema_version INTEGER NOT NULL DEFAULT 0",
                ):
                    try:
                        conn.execute(statement)
                    except sqlite3.OperationalError:
                        pass

            if current_ver < 5:
                for statement in (
                    "ALTER TABLE guides ADD COLUMN origin TEXT NOT NULL DEFAULT 'builtin'",
                    "ALTER TABLE guides ADD COLUMN kind TEXT NOT NULL DEFAULT 'core'",
                    "ALTER TABLE guides ADD COLUMN owner_user_id TEXT NOT NULL DEFAULT ''",
                    "ALTER TABLE guides ADD COLUMN base_guide_id TEXT",
                    "ALTER TABLE guides ADD COLUMN archived_at TEXT",
                    "ALTER TABLE guides ADD COLUMN archive_path TEXT NOT NULL DEFAULT ''",
                ):
                    try:
                        conn.execute(statement)
                    except sqlite3.OperationalError:
                        pass

            if current_ver < 6:
                try:
                    conn.execute("ALTER TABLE guides ADD COLUMN summary TEXT NOT NULL DEFAULT ''")
                except sqlite3.OperationalError:
                    pass

            ensure_schema_version(conn, SCHEMA_VERSION)
            conn.commit()

    # --- Catalog operations ---

    def upsert_guide(self, guide: Guide) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO guides (id, title, summary, category, difficulty, source_dir, origin, kind,
                   owner_user_id, base_guide_id, chapter_count, total_word_count,
                   total_reading_time_minutes, has_glossary, prerequisites, track)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   title=excluded.title, summary=excluded.summary, category=excluded.category,
                   difficulty=excluded.difficulty, source_dir=excluded.source_dir,
                   origin=excluded.origin, kind=excluded.kind,
                   owner_user_id=excluded.owner_user_id,
                   base_guide_id=excluded.base_guide_id,
                   chapter_count=excluded.chapter_count,
                   total_word_count=excluded.total_word_count,
                   total_reading_time_minutes=excluded.total_reading_time_minutes,
                   has_glossary=excluded.has_glossary,
                   prerequisites=excluded.prerequisites,
                   track=excluded.track""",
                (
                    guide.id,
                    guide.title,
                    guide.summary,
                    guide.category.value,
                    guide.difficulty.value,
                    guide.source_dir,
                    guide.origin.value,
                    guide.kind.value,
                    guide.owner_user_id,
                    guide.base_guide_id,
                    guide.chapter_count,
                    guide.total_word_count,
                    guide.total_reading_time_minutes,
                    int(guide.has_glossary),
                    json.dumps(guide.prerequisites),
                    guide.track,
                ),
            )
            conn.commit()

    def upsert_chapter(self, chapter: Chapter) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO chapters (id, guide_id, title, filename, "order",
                   summary, objectives, checkpoints, content_references, content_format,
                   schema_version, word_count, reading_time_minutes, has_diagrams, has_tables,
                   has_formulas, is_glossary, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   title=excluded.title, filename=excluded.filename,
                   "order"=excluded."order", summary=excluded.summary,
                   objectives=excluded.objectives, checkpoints=excluded.checkpoints,
                   content_references=excluded.content_references,
                   content_format=excluded.content_format,
                   schema_version=excluded.schema_version, word_count=excluded.word_count,
                   reading_time_minutes=excluded.reading_time_minutes,
                   has_diagrams=excluded.has_diagrams, has_tables=excluded.has_tables,
                   has_formulas=excluded.has_formulas, is_glossary=excluded.is_glossary,
                   content_hash=excluded.content_hash""",
                (
                    chapter.id,
                    chapter.guide_id,
                    chapter.title,
                    chapter.filename,
                    chapter.order,
                    chapter.summary,
                    json.dumps(chapter.objectives),
                    json.dumps(chapter.checkpoints),
                    json.dumps(chapter.content_references),
                    chapter.content_format,
                    chapter.schema_version,
                    chapter.word_count,
                    chapter.reading_time_minutes,
                    int(chapter.has_diagrams),
                    int(chapter.has_tables),
                    int(chapter.has_formulas),
                    int(chapter.is_glossary),
                    chapter.content_hash,
                ),
            )
            conn.commit()

    def sync_catalog(self, guides: list[Guide], chapters: list[Chapter]) -> None:
        """Bulk upsert guides and chapters from a scan."""
        with wal_connect(self.db_path) as conn:
            for g in guides:
                conn.execute(
                    """INSERT INTO guides (id, title, summary, category, difficulty, source_dir, origin,
                       kind, owner_user_id, base_guide_id, chapter_count, total_word_count,
                       total_reading_time_minutes, has_glossary, prerequisites, track)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                       title=excluded.title, summary=excluded.summary, category=excluded.category,
                       difficulty=excluded.difficulty, source_dir=excluded.source_dir,
                       origin=excluded.origin, kind=excluded.kind,
                       owner_user_id=excluded.owner_user_id,
                       base_guide_id=excluded.base_guide_id,
                       chapter_count=excluded.chapter_count,
                       total_word_count=excluded.total_word_count,
                       total_reading_time_minutes=excluded.total_reading_time_minutes,
                       has_glossary=excluded.has_glossary,
                       prerequisites=excluded.prerequisites,
                       track=excluded.track""",
                    (
                        g.id,
                        g.title,
                        g.summary,
                        g.category.value,
                        g.difficulty.value,
                        g.source_dir,
                        g.origin.value,
                        g.kind.value,
                        g.owner_user_id,
                        g.base_guide_id,
                        g.chapter_count,
                        g.total_word_count,
                        g.total_reading_time_minutes,
                        int(g.has_glossary),
                        json.dumps(g.prerequisites),
                        g.track,
                    ),
                )
            for c in chapters:
                conn.execute(
                    """INSERT INTO chapters (id, guide_id, title, filename, "order",
                       summary, objectives, checkpoints, content_references, content_format,
                       schema_version, word_count, reading_time_minutes, has_diagrams, has_tables,
                       has_formulas, is_glossary, content_hash)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                       title=excluded.title, filename=excluded.filename,
                       "order"=excluded."order", summary=excluded.summary,
                       objectives=excluded.objectives, checkpoints=excluded.checkpoints,
                       content_references=excluded.content_references,
                       content_format=excluded.content_format,
                       schema_version=excluded.schema_version, word_count=excluded.word_count,
                       reading_time_minutes=excluded.reading_time_minutes,
                       has_diagrams=excluded.has_diagrams, has_tables=excluded.has_tables,
                       has_formulas=excluded.has_formulas, is_glossary=excluded.is_glossary,
                       content_hash=excluded.content_hash""",
                    (
                        c.id,
                        c.guide_id,
                        c.title,
                        c.filename,
                        c.order,
                        c.summary,
                        json.dumps(c.objectives),
                        json.dumps(c.checkpoints),
                        json.dumps(c.content_references),
                        c.content_format,
                        c.schema_version,
                        c.word_count,
                        c.reading_time_minutes,
                        int(c.has_diagrams),
                        int(c.has_tables),
                        int(c.has_formulas),
                        int(c.is_glossary),
                        c.content_hash,
                    ),
                )
            conn.commit()

    def reconcile_guide_aliases(self, guide_aliases: dict[str, str]) -> dict[str, int]:
        """Merge stale alias-based catalog and user data into canonical guide IDs."""
        stats = {
            "aliases_processed": 0,
            "enrollments_merged": 0,
            "progress_rows_migrated": 0,
            "review_items_migrated": 0,
            "chapters_deleted": 0,
            "guides_deleted": 0,
        }
        if not guide_aliases:
            return stats

        with wal_connect(self.db_path, row_factory=True) as conn:
            for alias_id, canonical_id in guide_aliases.items():
                if alias_id == canonical_id:
                    continue
                stats["aliases_processed"] += 1
                stats["enrollments_merged"] += self._merge_alias_enrollments(
                    conn, alias_id, canonical_id
                )
                stats["progress_rows_migrated"] += self._merge_alias_progress(
                    conn, alias_id, canonical_id
                )
                stats["review_items_migrated"] += self._migrate_alias_review_items(
                    conn, alias_id, canonical_id
                )
                stats["chapters_deleted"] += conn.execute(
                    "DELETE FROM chapters WHERE guide_id=?",
                    (alias_id,),
                ).rowcount
                stats["guides_deleted"] += conn.execute(
                    "DELETE FROM guides WHERE id=?",
                    (alias_id,),
                ).rowcount
            conn.commit()
        return stats

    @staticmethod
    def _replace_guide_prefix(value: str, alias_id: str, canonical_id: str) -> str:
        prefix = f"{alias_id}/"
        if value.startswith(prefix):
            return f"{canonical_id}/{value[len(prefix) :]}"
        return value

    @staticmethod
    def _pick_earliest_timestamp(*values: str | None) -> str | None:
        present = [value for value in values if value]
        return min(present) if present else None

    @staticmethod
    def _pick_latest_timestamp(*values: str | None) -> str | None:
        present = [value for value in values if value]
        return max(present) if present else None

    @staticmethod
    def _merge_progress_status(current: str | None, incoming: str | None) -> str:
        priority = {"not_started": 0, "enrolled": 1, "in_progress": 2, "completed": 3}
        current_status = current or "not_started"
        incoming_status = incoming or "not_started"
        return (
            incoming_status
            if priority.get(incoming_status, 0) >= priority.get(current_status, 0)
            else current_status
        )

    def _merge_alias_enrollments(
        self,
        conn: sqlite3.Connection,
        alias_id: str,
        canonical_id: str,
    ) -> int:
        rows = conn.execute(
            "SELECT * FROM user_guide_enrollment WHERE guide_id=?",
            (alias_id,),
        ).fetchall()
        merged = 0
        for row in rows:
            alias_row = dict(row)
            existing = conn.execute(
                "SELECT * FROM user_guide_enrollment WHERE user_id=? AND guide_id=?",
                (alias_row["user_id"], canonical_id),
            ).fetchone()
            if existing:
                canonical_row = dict(existing)
                conn.execute(
                    """UPDATE user_guide_enrollment
                       SET enrolled_at=?, completed_at=?, linked_goal_id=?
                       WHERE user_id=? AND guide_id=?""",
                    (
                        self._pick_earliest_timestamp(
                            canonical_row.get("enrolled_at"),
                            alias_row.get("enrolled_at"),
                        ),
                        self._pick_latest_timestamp(
                            canonical_row.get("completed_at"),
                            alias_row.get("completed_at"),
                        ),
                        canonical_row.get("linked_goal_id") or alias_row.get("linked_goal_id"),
                        alias_row["user_id"],
                        canonical_id,
                    ),
                )
                conn.execute(
                    "DELETE FROM user_guide_enrollment WHERE user_id=? AND guide_id=?",
                    (alias_row["user_id"], alias_id),
                )
            else:
                conn.execute(
                    """UPDATE user_guide_enrollment
                       SET guide_id=?
                       WHERE user_id=? AND guide_id=?""",
                    (canonical_id, alias_row["user_id"], alias_id),
                )
            merged += 1
        return merged

    def _merge_alias_progress(
        self,
        conn: sqlite3.Connection,
        alias_id: str,
        canonical_id: str,
    ) -> int:
        rows = conn.execute(
            "SELECT * FROM user_chapter_progress WHERE guide_id=? OR chapter_id LIKE ?",
            (alias_id, f"{alias_id}/%"),
        ).fetchall()
        migrated = 0
        for row in rows:
            alias_row = dict(row)
            target_chapter_id = self._replace_guide_prefix(
                alias_row["chapter_id"], alias_id, canonical_id
            )
            existing = conn.execute(
                "SELECT * FROM user_chapter_progress WHERE user_id=? AND chapter_id=?",
                (alias_row["user_id"], target_chapter_id),
            ).fetchone()
            if existing and target_chapter_id != alias_row["chapter_id"]:
                canonical_row = dict(existing)
                conn.execute(
                    """UPDATE user_chapter_progress
                       SET guide_id=?, status=?, reading_time_seconds=?, scroll_position=?,
                           started_at=?, completed_at=?, updated_at=?
                       WHERE user_id=? AND chapter_id=?""",
                    (
                        canonical_id,
                        self._merge_progress_status(
                            canonical_row.get("status"), alias_row.get("status")
                        ),
                        int(canonical_row.get("reading_time_seconds") or 0)
                        + int(alias_row.get("reading_time_seconds") or 0),
                        max(
                            float(canonical_row.get("scroll_position") or 0.0),
                            float(alias_row.get("scroll_position") or 0.0),
                        ),
                        self._pick_earliest_timestamp(
                            canonical_row.get("started_at"),
                            alias_row.get("started_at"),
                        ),
                        self._pick_latest_timestamp(
                            canonical_row.get("completed_at"),
                            alias_row.get("completed_at"),
                        ),
                        self._pick_latest_timestamp(
                            canonical_row.get("updated_at"),
                            alias_row.get("updated_at"),
                        ),
                        alias_row["user_id"],
                        target_chapter_id,
                    ),
                )
                conn.execute(
                    "DELETE FROM user_chapter_progress WHERE user_id=? AND chapter_id=?",
                    (alias_row["user_id"], alias_row["chapter_id"]),
                )
            else:
                conn.execute(
                    """UPDATE user_chapter_progress
                       SET guide_id=?, chapter_id=?
                       WHERE user_id=? AND chapter_id=?""",
                    (
                        canonical_id,
                        target_chapter_id,
                        alias_row["user_id"],
                        alias_row["chapter_id"],
                    ),
                )
            migrated += 1
        return migrated

    def _migrate_alias_review_items(
        self,
        conn: sqlite3.Connection,
        alias_id: str,
        canonical_id: str,
    ) -> int:
        rows = conn.execute(
            "SELECT id, chapter_id FROM review_items WHERE guide_id=? OR chapter_id LIKE ?",
            (alias_id, f"{alias_id}/%"),
        ).fetchall()
        migrated = 0
        for row in rows:
            current = dict(row)
            conn.execute(
                """UPDATE review_items
                   SET guide_id=?, chapter_id=?
                   WHERE id=?""",
                (
                    canonical_id,
                    self._replace_guide_prefix(current["chapter_id"], alias_id, canonical_id),
                    current["id"],
                ),
            )
            migrated += 1
        return migrated

    @staticmethod
    def _deserialize_guide_row(row: sqlite3.Row | dict) -> dict:
        guide = dict(row)
        guide["summary"] = guide.get("summary") or ""
        guide["has_glossary"] = bool(guide["has_glossary"])
        guide["prerequisites"] = json.loads(guide.get("prerequisites", "[]"))
        guide["base_guide_id"] = guide.get("base_guide_id")
        guide["archived_at"] = guide.get("archived_at")
        guide["archive_path"] = guide.get("archive_path") or ""
        guide["deletable"] = guide.get("origin") == "user"
        return guide

    def is_guide_archived(self, guide_id: str) -> bool:
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute(
                "SELECT archived_at FROM guides WHERE id=?",
                (guide_id,),
            ).fetchone()
            return bool(row and dict(row).get("archived_at"))

    def list_guides(
        self,
        category: str | None = None,
        user_id: str | None = None,
        *,
        origin: str | None = None,
        include_archived: bool = False,
    ) -> list[dict]:
        """List guides with optional user progress summary."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            where_clauses: list[str] = []
            params: list[object] = []
            if category:
                where_clauses.append("category = ?")
                params.append(category)
            if origin:
                where_clauses.append("origin = ?")
                params.append(origin)
            if not include_archived:
                where_clauses.append("archived_at IS NULL")

            query = "SELECT * FROM guides"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            query += " ORDER BY id"
            rows = conn.execute(query, tuple(params)).fetchall()

            results = []
            for row in rows:
                d = self._deserialize_guide_row(row)

                if user_id:
                    enrollment = conn.execute(
                        "SELECT * FROM user_guide_enrollment WHERE user_id=? AND guide_id=?",
                        (user_id, d["id"]),
                    ).fetchone()
                    d["enrolled"] = enrollment is not None
                    d["enrollment_completed_at"] = (
                        dict(enrollment).get("completed_at") if enrollment else None
                    )

                    # Progress counts
                    total = conn.execute(
                        "SELECT COUNT(*) FROM chapters WHERE guide_id=? AND is_glossary=0",
                        (d["id"],),
                    ).fetchone()[0]
                    completed = conn.execute(
                        """SELECT COUNT(*) FROM user_chapter_progress ucp
                           JOIN chapters c ON c.id = ucp.chapter_id
                           WHERE ucp.user_id=? AND ucp.guide_id=? AND ucp.status='completed'
                           AND c.is_glossary=0""",
                        (user_id, d["id"]),
                    ).fetchone()[0]
                    d["chapters_total"] = total
                    d["chapters_completed"] = completed
                    d["progress_pct"] = round(completed / total * 100, 1) if total > 0 else 0.0

                    d["mastery_score"] = self._compute_mastery(
                        conn, user_id, d["id"], completed, total
                    )
                else:
                    d["enrolled"] = False
                    d["chapters_completed"] = 0
                    d["chapters_total"] = d["chapter_count"]
                    d["progress_pct"] = 0.0
                    d["mastery_score"] = 0.0

                results.append(d)
            return results

    def list_linked_extensions(
        self,
        base_guide_id: str,
        *,
        user_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict]:
        with wal_connect(self.db_path, row_factory=True) as conn:
            query = "SELECT * FROM guides WHERE origin='user' AND base_guide_id=?"
            if not include_archived:
                query += " AND archived_at IS NULL"
            query += " ORDER BY title"
            rows = conn.execute(query, (base_guide_id,)).fetchall()

            results = []
            for row in rows:
                guide = self._deserialize_guide_row(row)
                if user_id:
                    detailed = self.get_guide(
                        guide["id"], user_id=user_id, include_archived=include_archived
                    )
                    if detailed:
                        results.append(detailed)
                else:
                    results.append(guide)
            return results

    def list_archived_guides(self, user_id: str | None = None) -> list[dict]:
        guides = self.list_guides(user_id=user_id, origin="user", include_archived=True)
        return [guide for guide in guides if guide.get("archived_at")]

    def get_guide(
        self,
        guide_id: str,
        user_id: str | None = None,
        *,
        include_archived: bool = False,
    ) -> dict | None:
        """Get guide with chapters and progress."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            query = "SELECT * FROM guides WHERE id=?"
            if not include_archived:
                query += " AND archived_at IS NULL"
            row = conn.execute(query, (guide_id,)).fetchone()
            if not row:
                return None
            d = self._deserialize_guide_row(row)

            chapters = conn.execute(
                'SELECT * FROM chapters WHERE guide_id=? ORDER BY "order"', (guide_id,)
            ).fetchall()
            d["chapters"] = []
            for ch in chapters:
                cd = self._deserialize_chapter_row(ch)

                if user_id:
                    prog = conn.execute(
                        "SELECT * FROM user_chapter_progress WHERE user_id=? AND chapter_id=?",
                        (user_id, cd["id"]),
                    ).fetchone()
                    cd["status"] = dict(prog)["status"] if prog else "not_started"
                    cd["reading_time_seconds"] = (
                        dict(prog).get("reading_time_seconds", 0) if prog else 0
                    )
                else:
                    cd["status"] = "not_started"
                    cd["reading_time_seconds"] = 0

                d["chapters"].append(cd)

            if user_id:
                enrollment = conn.execute(
                    "SELECT * FROM user_guide_enrollment WHERE user_id=? AND guide_id=?",
                    (user_id, guide_id),
                ).fetchone()
                d["enrolled"] = enrollment is not None
                d["enrollment_completed_at"] = (
                    dict(enrollment).get("completed_at") if enrollment else None
                )
                assessable_chapters = [c for c in d["chapters"] if not c.get("is_glossary")]
                completed = sum(1 for c in assessable_chapters if c["status"] == "completed")
                d["chapters_completed"] = completed
                d["chapters_total"] = len(assessable_chapters)
                d["progress_pct"] = (
                    round(completed / len(assessable_chapters) * 100, 1)
                    if assessable_chapters
                    else 0.0
                )
                d["mastery_score"] = self._compute_mastery(
                    conn, user_id, guide_id, completed, len(assessable_chapters)
                )
            else:
                d["enrolled"] = False
                d["chapters_completed"] = 0
                d["chapters_total"] = sum(
                    1 for chapter in d["chapters"] if not chapter.get("is_glossary")
                )
                d["progress_pct"] = 0.0
                d["mastery_score"] = 0.0

            return d

    def get_chapter(self, chapter_id: str, *, include_archived: bool = False) -> dict | None:
        """Get chapter metadata."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            query = "SELECT c.* FROM chapters c JOIN guides g ON g.id = c.guide_id WHERE c.id=?"
            if not include_archived:
                query += " AND g.archived_at IS NULL"
            row = conn.execute(query, (chapter_id,)).fetchone()
            if not row:
                return None
            return self._deserialize_chapter_row(row)

    # --- Enrollment ---

    def enroll(self, user_id: str, guide_id: str, linked_goal_id: str | None = None) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO user_guide_enrollment (user_id, guide_id, linked_goal_id)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id, guide_id) DO UPDATE SET linked_goal_id=excluded.linked_goal_id""",
                (user_id, guide_id, linked_goal_id),
            )
            conn.commit()

    def is_enrolled(self, user_id: str, guide_id: str) -> bool:
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute(
                "SELECT 1 FROM user_guide_enrollment WHERE user_id=? AND guide_id=?",
                (user_id, guide_id),
            ).fetchone()
            return row is not None

    def get_enrollments(self, user_id: str, *, include_archived: bool = False) -> list[dict]:
        with wal_connect(self.db_path, row_factory=True) as conn:
            query = (
                "SELECT uge.* FROM user_guide_enrollment uge JOIN guides g ON g.id = uge.guide_id "
                "WHERE uge.user_id=?"
            )
            if not include_archived:
                query += " AND g.archived_at IS NULL"
            query += " ORDER BY uge.enrolled_at DESC"
            rows = conn.execute(query, (user_id,)).fetchall()
            return [dict(r) for r in rows]

    def archive_guide(self, guide_id: str, archive_path: str) -> dict | None:
        now = datetime.utcnow().isoformat()
        with wal_connect(self.db_path, row_factory=True) as conn:
            conn.execute(
                "UPDATE guides SET archived_at=?, archive_path=? WHERE id=? AND origin='user'",
                (now, archive_path, guide_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM guides WHERE id=?", (guide_id,)).fetchone()
            return self._deserialize_guide_row(row) if row else None

    def restore_guide(self, guide_id: str) -> dict | None:
        with wal_connect(self.db_path, row_factory=True) as conn:
            conn.execute(
                "UPDATE guides SET archived_at=NULL, archive_path='' WHERE id=? AND origin='user'",
                (guide_id,),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM guides WHERE id=?", (guide_id,)).fetchone()
            return self._deserialize_guide_row(row) if row else None

    # --- Progress ---

    def update_progress(
        self,
        user_id: str,
        chapter_id: str,
        guide_id: str,
        status: str | None = None,
        reading_time_seconds: int | None = None,
        scroll_position: float | None = None,
    ) -> dict:
        now = datetime.utcnow().isoformat()
        with wal_connect(self.db_path, row_factory=True) as conn:
            existing = conn.execute(
                "SELECT * FROM user_chapter_progress WHERE user_id=? AND chapter_id=?",
                (user_id, chapter_id),
            ).fetchone()

            if existing:
                updates = []
                params = []
                if status:
                    updates.append("status=?")
                    params.append(status)
                    if status == "completed":
                        updates.append("completed_at=?")
                        params.append(now)
                    elif status == "in_progress" and not dict(existing).get("started_at"):
                        updates.append("started_at=?")
                        params.append(now)
                if reading_time_seconds is not None:
                    # Accumulate reading time
                    updates.append("reading_time_seconds=reading_time_seconds+?")
                    params.append(reading_time_seconds)
                if scroll_position is not None:
                    updates.append("scroll_position=?")
                    params.append(scroll_position)
                updates.append("updated_at=?")
                params.append(now)
                params.extend([user_id, chapter_id])
                conn.execute(
                    f"UPDATE user_chapter_progress SET {', '.join(updates)} WHERE user_id=? AND chapter_id=?",
                    params,
                )
            else:
                started = now if (status and status != "not_started") else None
                completed = now if status == "completed" else None
                conn.execute(
                    """INSERT INTO user_chapter_progress
                       (user_id, chapter_id, guide_id, status, reading_time_seconds,
                        scroll_position, started_at, completed_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        chapter_id,
                        guide_id,
                        status or "not_started",
                        reading_time_seconds or 0,
                        scroll_position or 0.0,
                        started,
                        completed,
                        now,
                    ),
                )
            conn.commit()

            # Check if guide completed
            if status == "completed":
                self._check_guide_completion(conn, user_id, guide_id)

            row = conn.execute(
                "SELECT * FROM user_chapter_progress WHERE user_id=? AND chapter_id=?",
                (user_id, chapter_id),
            ).fetchone()
            return dict(row) if row else {}

    def _check_guide_completion(
        self, conn: sqlite3.Connection, user_id: str, guide_id: str
    ) -> None:
        """Mark guide completed if all non-glossary chapters are done."""
        total = conn.execute(
            "SELECT COUNT(*) FROM chapters WHERE guide_id=? AND is_glossary=0",
            (guide_id,),
        ).fetchone()[0]
        completed = conn.execute(
            """SELECT COUNT(*) FROM user_chapter_progress ucp
               JOIN chapters c ON c.id = ucp.chapter_id
               WHERE ucp.user_id=? AND ucp.guide_id=? AND ucp.status='completed'
               AND c.is_glossary=0""",
            (user_id, guide_id),
        ).fetchone()[0]
        if total > 0 and completed >= total:
            conn.execute(
                "UPDATE user_guide_enrollment SET completed_at=? WHERE user_id=? AND guide_id=?",
                (datetime.utcnow().isoformat(), user_id, guide_id),
            )
            conn.commit()

    def get_chapter_progress(self, user_id: str, chapter_id: str) -> dict | None:
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute(
                "SELECT * FROM user_chapter_progress WHERE user_id=? AND chapter_id=?",
                (user_id, chapter_id),
            ).fetchone()
            return dict(row) if row else None

    def get_last_read_chapter(self, user_id: str) -> dict | None:
        """Get most recently updated in-progress or completed chapter."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute(
                """SELECT ucp.*, c.title as chapter_title, c.guide_id,
                   g.title as guide_title
                   FROM user_chapter_progress ucp
                   JOIN chapters c ON c.id = ucp.chapter_id
                   JOIN guides g ON g.id = c.guide_id
                   WHERE ucp.user_id=? AND g.archived_at IS NULL
                   ORDER BY ucp.updated_at DESC LIMIT 1""",
                (user_id,),
            ).fetchone()
            return dict(row) if row else None

    # --- Review items ---

    def add_review_items(self, items: list[ReviewItem]) -> None:
        with wal_connect(self.db_path) as conn:
            for item in items:
                item_id = item.id or uuid.uuid4().hex[:16]
                conn.execute(
                    """INSERT INTO review_items
                       (id, user_id, chapter_id, guide_id, question, expected_answer,
                        bloom_level, item_type, easiness_factor, interval_days, repetitions,
                        next_review, last_reviewed, content_hash, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO NOTHING""",
                    (
                        item_id,
                        item.user_id,
                        item.chapter_id,
                        item.guide_id,
                        item.question,
                        item.expected_answer,
                        item.bloom_level.value,
                        item.item_type.value,
                        item.easiness_factor,
                        item.interval_days,
                        item.repetitions,
                        item.next_review.isoformat()
                        if item.next_review
                        else datetime.utcnow().isoformat(),
                        item.last_reviewed.isoformat() if item.last_reviewed else None,
                        item.content_hash,
                        item.created_at.isoformat()
                        if item.created_at
                        else datetime.utcnow().isoformat(),
                    ),
                )
            conn.commit()

    def get_due_reviews(
        self, user_id: str, limit: int = 20, guide_id: str | None = None
    ) -> list[dict]:
        now = datetime.utcnow().isoformat()
        with wal_connect(self.db_path, row_factory=True) as conn:
            if guide_id:
                rows = conn.execute(
                    """SELECT ri.* FROM review_items ri
                       JOIN guides g ON g.id = ri.guide_id
                       WHERE ri.user_id=? AND ri.guide_id=? AND ri.next_review <= ?
                       AND item_type != 'pre_reading'
                       AND g.archived_at IS NULL
                       ORDER BY ri.next_review ASC LIMIT ?""",
                    (user_id, guide_id, now, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT ri.* FROM review_items ri
                       JOIN guides g ON g.id = ri.guide_id
                       WHERE ri.user_id=? AND ri.next_review <= ?
                       AND ri.item_type != 'pre_reading' AND g.archived_at IS NULL
                       ORDER BY ri.next_review ASC LIMIT ?""",
                    (user_id, now, limit),
                ).fetchall()
            return [dict(r) for r in rows]

    def list_review_items(
        self,
        user_id: str,
        *,
        guide_id: str | None = None,
        include_pre_reading: bool = True,
    ) -> list[dict]:
        with wal_connect(self.db_path, row_factory=True) as conn:
            query = (
                "SELECT ri.* FROM review_items ri JOIN guides g ON g.id = ri.guide_id "
                "WHERE ri.user_id=? AND g.archived_at IS NULL"
            )
            params: list[object] = [user_id]
            if guide_id:
                query += " AND ri.guide_id=?"
                params.append(guide_id)
            if not include_pre_reading:
                query += " AND ri.item_type != 'pre_reading'"
            query += " ORDER BY ri.created_at DESC"
            rows = conn.execute(query, tuple(params)).fetchall()
            return [dict(r) for r in rows]

    def get_retry_review_items(
        self,
        user_id: str,
        limit: int = 20,
        guide_id: str | None = None,
    ) -> list[dict]:
        """Return recently graded items that still look weak and worth retrying."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            if guide_id:
                rows = conn.execute(
                    """SELECT ri.* FROM review_items ri
                       JOIN guides g ON g.id = ri.guide_id
                       WHERE ri.user_id=?
                       AND ri.guide_id=?
                       AND ri.item_type != 'pre_reading'
                       AND ri.last_reviewed IS NOT NULL
                       AND g.archived_at IS NULL
                       AND (ri.repetitions = 0 OR ri.easiness_factor < 2.4)
                       ORDER BY ri.last_reviewed DESC
                       LIMIT ?""",
                    (user_id, guide_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT ri.* FROM review_items ri
                       JOIN guides g ON g.id = ri.guide_id
                       WHERE ri.user_id=?
                       AND ri.item_type != 'pre_reading'
                       AND ri.last_reviewed IS NOT NULL
                       AND g.archived_at IS NULL
                       AND (ri.repetitions = 0 OR ri.easiness_factor < 2.4)
                       ORDER BY ri.last_reviewed DESC
                       LIMIT ?""",
                    (user_id, limit),
                ).fetchall()
            return [dict(r) for r in rows]

    def get_review_queue(
        self,
        user_id: str,
        limit: int = 20,
        guide_id: str | None = None,
    ) -> list[dict]:
        """Return a merged review queue across due and recently weak items."""
        now = datetime.utcnow().isoformat()
        weak_clause = (
            "ri.last_reviewed IS NOT NULL AND (ri.repetitions = 0 OR ri.easiness_factor < 2.4)"
        )
        with wal_connect(self.db_path, row_factory=True) as conn:
            params: list[object] = [user_id]
            query = """SELECT ri.* FROM review_items ri
                   JOIN guides g ON g.id = ri.guide_id
                   WHERE ri.user_id=?
                   AND ri.item_type != 'pre_reading'
                   AND g.archived_at IS NULL """
            if guide_id:
                query += "AND ri.guide_id=? "
                params.append(guide_id)
            query += f"""AND (ri.next_review <= ? OR ({weak_clause}))
                    ORDER BY
                      CASE WHEN ({weak_clause}) THEN 0 ELSE 1 END,
                      CASE WHEN ri.next_review IS NULL THEN 1 ELSE 0 END,
                      ri.next_review ASC,
                      ri.last_reviewed DESC,
                      ri.created_at DESC
                    LIMIT ?"""
            params.extend([now, limit])
            rows = conn.execute(query, tuple(params)).fetchall()
            return [dict(r) for r in rows]

    def count_review_queue(self, user_id: str, guide_id: str | None = None) -> int:
        """Count a merged review queue across due and recently weak items."""
        now = datetime.utcnow().isoformat()
        weak_clause = (
            "ri.last_reviewed IS NOT NULL AND (ri.repetitions = 0 OR ri.easiness_factor < 2.4)"
        )
        with wal_connect(self.db_path) as conn:
            params: list[object] = [user_id]
            query = """SELECT COUNT(*) FROM review_items ri
                   JOIN guides g ON g.id = ri.guide_id
                   WHERE ri.user_id=?
                   AND ri.item_type != 'pre_reading'
                   AND g.archived_at IS NULL """
            if guide_id:
                query += "AND ri.guide_id=? "
                params.append(guide_id)
            query += f"AND (ri.next_review <= ? OR ({weak_clause}))"
            params.append(now)
            row = conn.execute(query, tuple(params)).fetchone()
            return row[0] if row else 0

    def get_review_item(self, review_id: str) -> dict | None:
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute(
                """SELECT ri.* FROM review_items ri
                   JOIN guides g ON g.id = ri.guide_id
                   WHERE ri.id=? AND g.archived_at IS NULL""",
                (review_id,),
            ).fetchone()
            return dict(row) if row else None

    def grade_review(self, review_id: str, grade: int) -> dict | None:
        """Apply SM-2 algorithm and update review schedule."""
        grade = max(0, min(5, grade))
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute("SELECT * FROM review_items WHERE id=?", (review_id,)).fetchone()
            if not row:
                return None
            item = dict(row)

            result = sm2_update(
                easiness_factor=item["easiness_factor"],
                interval_days=item["interval_days"],
                repetitions=item["repetitions"],
                grade=grade,
            )

            next_review = datetime.utcnow() + timedelta(days=result.interval_days)
            conn.execute(
                """UPDATE review_items SET
                   easiness_factor=?, interval_days=?, repetitions=?,
                   next_review=?, last_reviewed=?
                   WHERE id=?""",
                (
                    result.easiness_factor,
                    result.interval_days,
                    result.repetitions,
                    next_review.isoformat(),
                    datetime.utcnow().isoformat(),
                    review_id,
                ),
            )
            conn.commit()

            updated = conn.execute("SELECT * FROM review_items WHERE id=?", (review_id,)).fetchone()
            return dict(updated) if updated else None

    def get_review_items_for_chapter(self, user_id: str, chapter_id: str) -> list[dict]:
        with wal_connect(self.db_path, row_factory=True) as conn:
            rows = conn.execute(
                """SELECT ri.* FROM review_items ri
                   JOIN guides g ON g.id = ri.guide_id
                   WHERE ri.user_id=? AND ri.chapter_id=? AND g.archived_at IS NULL""",
                (user_id, chapter_id),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_review_items_for_chapter(
        self,
        user_id: str,
        chapter_id: str,
        item_types: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> int:
        """Delete cached review items for a chapter, optionally filtered by item type."""
        with wal_connect(self.db_path) as conn:
            if item_types:
                normalized = tuple(item_types)
                placeholders = ",".join("?" for _ in normalized)
                result = conn.execute(
                    f"""DELETE FROM review_items
                        WHERE user_id=? AND chapter_id=? AND item_type IN ({placeholders})""",
                    (user_id, chapter_id, *normalized),
                )
            else:
                result = conn.execute(
                    "DELETE FROM review_items WHERE user_id=? AND chapter_id=?",
                    (user_id, chapter_id),
                )
            conn.commit()
            return result.rowcount

    def get_teachback_for_chapter(self, user_id: str, chapter_id: str) -> dict | None:
        """Get the teach-back review item for a chapter, if any."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute(
                """SELECT ri.* FROM review_items ri
                   JOIN guides g ON g.id = ri.guide_id
                   WHERE ri.user_id=? AND ri.chapter_id=? AND ri.item_type='teachback'
                   AND g.archived_at IS NULL""",
                (user_id, chapter_id),
            ).fetchone()
            return dict(row) if row else None

    def get_pre_reading_questions(self, user_id: str, chapter_id: str) -> list[dict]:
        """Get pre-reading question items for a chapter."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            rows = conn.execute(
                """SELECT ri.* FROM review_items ri
                   JOIN guides g ON g.id = ri.guide_id
                   WHERE ri.user_id=? AND ri.chapter_id=? AND ri.item_type='pre_reading'
                   AND g.archived_at IS NULL""",
                (user_id, chapter_id),
            ).fetchall()
            return [dict(r) for r in rows]

    def count_due_reviews(self, user_id: str) -> int:
        now = datetime.utcnow().isoformat()
        with wal_connect(self.db_path) as conn:
            row = conn.execute(
                """SELECT COUNT(*) FROM review_items ri
                   JOIN guides g ON g.id = ri.guide_id
                   WHERE ri.user_id=? AND ri.next_review <= ?
                   AND ri.item_type != 'pre_reading' AND g.archived_at IS NULL""",
                (user_id, now),
            ).fetchone()
            return row[0] if row else 0

    # --- Stats ---

    def get_stats(self, user_id: str) -> LearningStats:
        with wal_connect(self.db_path, row_factory=True) as conn:
            # Batch 1: enrollment counts (1 query instead of 2)
            enroll_row = conn.execute(
                "SELECT COUNT(*) as enrolled, "
                "SUM(CASE WHEN uge.completed_at IS NOT NULL THEN 1 ELSE 0 END) as completed "
                "FROM user_guide_enrollment uge "
                "JOIN guides g ON g.id = uge.guide_id "
                "WHERE uge.user_id=? AND g.archived_at IS NULL",
                (user_id,),
            ).fetchone()
            enrolled = enroll_row["enrolled"]
            guide_completed = enroll_row["completed"] or 0

            # Batch 2: chapter progress (1 query instead of 2)
            progress_row = conn.execute(
                """SELECT
                   SUM(CASE WHEN ucp.status='completed' THEN 1 ELSE 0 END) as completed,
                   COALESCE(SUM(ucp.reading_time_seconds), 0) as reading_time
                   FROM user_chapter_progress ucp
                   JOIN chapters c ON c.id = ucp.chapter_id
                   JOIN guides g ON g.id = c.guide_id
                   WHERE ucp.user_id=? AND c.is_glossary=0 AND g.archived_at IS NULL""",
                (user_id,),
            ).fetchone()
            chapters_completed = progress_row["completed"] or 0
            reading_time = progress_row["reading_time"]

            # Count only chapters from enrolled guides (0 if not enrolled in anything)
            total_chapters = conn.execute(
                """SELECT COUNT(DISTINCT c.id) FROM chapters c
                   JOIN user_guide_enrollment uge ON uge.guide_id = c.guide_id
                   JOIN guides g ON g.id = c.guide_id
                   WHERE uge.user_id = ? AND c.is_glossary=0 AND g.archived_at IS NULL""",
                (user_id,),
            ).fetchone()[0]

            # Batch 3: review stats (1 query instead of 2)
            review_row = conn.execute(
                "SELECT COUNT(*) as done, AVG(ri.easiness_factor) as avg_ef "
                "FROM review_items ri JOIN guides g ON g.id = ri.guide_id "
                "WHERE ri.user_id=? AND ri.last_reviewed IS NOT NULL AND g.archived_at IS NULL",
                (user_id,),
            ).fetchone()
            reviews_done = review_row["done"]
            avg_grade = round(review_row["avg_ef"], 2) if review_row["avg_ef"] else 0.0

            # Due reviews (inline instead of separate connection)
            now = datetime.utcnow().isoformat()
            due = conn.execute(
                """SELECT COUNT(*) FROM review_items ri
                   JOIN guides g ON g.id = ri.guide_id
                   WHERE ri.user_id=? AND ri.next_review <= ?
                   AND ri.item_type != 'pre_reading' AND g.archived_at IS NULL""",
                (user_id, now),
            ).fetchone()[0]

            # Mastery by category (already batched)
            mastery: dict[str, float] = {}
            cats = conn.execute(
                """SELECT g.category, COUNT(DISTINCT ucp.chapter_id) as done,
                   COUNT(DISTINCT c.id) as total
                   FROM guides g
                   JOIN chapters c ON c.guide_id = g.id
                   LEFT JOIN user_chapter_progress ucp
                   ON ucp.chapter_id = c.id AND ucp.user_id=? AND ucp.status='completed'
                   WHERE c.is_glossary=0 AND g.archived_at IS NULL
                   GROUP BY g.category""",
                (user_id,),
            ).fetchall()
            for cat_row in cats:
                cd = dict(cat_row)
                total = cd["total"]
                done = cd["done"]
                mastery[cd["category"]] = round(done / total * 100, 1) if total > 0 else 0.0

            # Daily activity (last 30 days)
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            daily_rows = conn.execute(
                """SELECT DATE(ucp.updated_at) as day, COUNT(*) as cnt
                   FROM user_chapter_progress ucp
                   JOIN guides g ON g.id = ucp.guide_id
                   WHERE ucp.user_id=? AND ucp.updated_at >= ? AND g.archived_at IS NULL
                   GROUP BY DATE(ucp.updated_at)""",
                (user_id, thirty_days_ago),
            ).fetchall()
            daily = {dict(r)["day"]: dict(r)["cnt"] for r in daily_rows}

            # Streak calc
            streak = 0
            today = datetime.utcnow().date()
            for i in range(365):
                day = (today - timedelta(days=i)).isoformat()
                if day in daily or (i == 0 and daily):
                    if day in daily:
                        streak += 1
                    elif i == 0:
                        break
                    else:
                        break
                elif i > 0:
                    break

            # Mastery by track — batch via pre-fetched data (no N+1)
            chapter_counts, completed_counts, _, avg_ef_map = self._batch_guide_data(conn, user_id)
            mastery_track: dict[str, float] = {}
            guide_rows = conn.execute(
                "SELECT id, track FROM guides WHERE track != '' AND archived_at IS NULL"
            ).fetchall()
            track_guide_map: dict[str, list[str]] = {}
            for gr in guide_rows:
                gd = dict(gr)
                track_guide_map.setdefault(gd["track"], []).append(gd["id"])

            for tid, guide_ids in track_guide_map.items():
                track_scores = []
                for gid in guide_ids:
                    t_total = chapter_counts.get(gid, 0)
                    t_done = completed_counts.get(gid, 0)
                    track_scores.append(
                        self._mastery_from_precomputed(t_done, t_total, avg_ef_map.get(gid))
                    )
                mastery_track[tid] = (
                    round(sum(track_scores) / len(track_scores), 1) if track_scores else 0.0
                )

            return LearningStats(
                guides_enrolled=enrolled,
                guides_completed=guide_completed,
                chapters_completed=chapters_completed,
                total_chapters=total_chapters,
                total_reading_time_seconds=reading_time,
                reviews_completed=reviews_done,
                average_grade=avg_grade,
                current_streak_days=streak,
                reviews_due=due,
                mastery_by_category=mastery,
                mastery_by_track=mastery_track,
                daily_activity=daily,
            )

    @staticmethod
    def _compute_mastery(
        conn: sqlite3.Connection,
        user_id: str,
        guide_id: str,
        chapters_completed: int,
        chapters_total: int,
    ) -> float:
        """Compute mastery score for a guide.

        mastery = completion_pct * 0.4 + review_score * 0.6
        """
        if chapters_total == 0:
            return 0.0
        completion_pct = chapters_completed / chapters_total * 100

        avg_ef_row = conn.execute(
            """SELECT AVG(easiness_factor) FROM review_items
               WHERE user_id=? AND guide_id=? AND last_reviewed IS NOT NULL
               AND item_type != 'pre_reading'""",
            (user_id, guide_id),
        ).fetchone()
        avg_ef = avg_ef_row[0] if avg_ef_row and avg_ef_row[0] is not None else None

        if avg_ef is None:
            return round(completion_pct * 0.4, 1)

        review_score = max(0.0, min(100.0, (avg_ef - 1.3) / 1.2 * 100))
        return round(completion_pct * 0.4 + review_score * 0.6, 1)

    @staticmethod
    def _batch_guide_data(
        conn: sqlite3.Connection, user_id: str | None
    ) -> tuple[dict[str, int], dict[str, int], dict[str, str | None], dict[str, float | None]]:
        """Pre-fetch chapter counts, completion counts, enrollments, and avg EFs in bulk."""
        # chapter_count per guide
        chapter_counts: dict[str, int] = {}
        for r in conn.execute(
            """SELECT c.guide_id, COUNT(*) as cnt
               FROM chapters c JOIN guides g ON g.id = c.guide_id
               WHERE c.is_glossary=0 AND g.archived_at IS NULL
               GROUP BY c.guide_id"""
        ):
            chapter_counts[r[0]] = r[1]

        completed_counts: dict[str, int] = {}
        enrollment_map: dict[str, str | None] = {}
        avg_ef_map: dict[str, float | None] = {}

        if user_id:
            for r in conn.execute(
                "SELECT ucp.guide_id, COUNT(*) as cnt FROM user_chapter_progress ucp "
                "JOIN guides g ON g.id = ucp.guide_id "
                "WHERE ucp.user_id=? AND ucp.status='completed' AND g.archived_at IS NULL "
                "GROUP BY ucp.guide_id",
                (user_id,),
            ):
                completed_counts[r[0]] = r[1]

            for r in conn.execute(
                "SELECT uge.guide_id, uge.completed_at FROM user_guide_enrollment uge "
                "JOIN guides g ON g.id = uge.guide_id "
                "WHERE uge.user_id=? AND g.archived_at IS NULL",
                (user_id,),
            ):
                enrollment_map[r[0]] = r[1]

            for r in conn.execute(
                "SELECT ri.guide_id, AVG(ri.easiness_factor) FROM review_items ri "
                "JOIN guides g ON g.id = ri.guide_id "
                "WHERE ri.user_id=? AND ri.last_reviewed IS NOT NULL "
                "AND ri.item_type != 'pre_reading' AND g.archived_at IS NULL "
                "GROUP BY ri.guide_id",
                (user_id,),
            ):
                avg_ef_map[r[0]] = r[1]

        return chapter_counts, completed_counts, enrollment_map, avg_ef_map

    @staticmethod
    def _mastery_from_precomputed(
        chapters_completed: int, chapters_total: int, avg_ef: float | None
    ) -> float:
        """Compute mastery from pre-fetched data (no extra queries)."""
        if chapters_total == 0:
            return 0.0
        completion_pct = chapters_completed / chapters_total * 100
        if avg_ef is None:
            return round(completion_pct * 0.4, 1)
        review_score = max(0.0, min(100.0, (avg_ef - 1.3) / 1.2 * 100))
        return round(completion_pct * 0.4 + review_score * 0.6, 1)

    def list_tracks(
        self,
        user_id: str,
        track_metadata: dict[str, dict],
        excluded_guide_ids: set[str] | None = None,
    ) -> list[dict]:
        """List tracks with aggregate stats."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            rows = conn.execute(
                "SELECT * FROM guides WHERE archived_at IS NULL AND origin='builtin' ORDER BY id"
            ).fetchall()
            chapter_counts, completed_counts, enrollment_map, avg_ef_map = self._batch_guide_data(
                conn, user_id
            )
            excluded_guide_ids = excluded_guide_ids or set()

            tracks: dict[str, dict] = {}
            # Init from metadata
            for tid, meta in track_metadata.items():
                tracks[tid] = {
                    "id": tid,
                    "title": meta.get("title", tid),
                    "description": meta.get("description", ""),
                    "color": meta.get("color", "#6b7280"),
                    "guide_count": 0,
                    "guides_completed": 0,
                    "mastery_scores": [],
                    "guide_ids": [],
                }

            for row in rows:
                d = dict(row)
                if d["id"] in excluded_guide_ids:
                    continue
                track_id = d.get("track", "") or ""
                if not track_id:
                    track_id = "_uncategorized"
                if track_id not in tracks:
                    tracks[track_id] = {
                        "id": track_id,
                        "title": track_id.replace("_", " ").title(),
                        "description": "",
                        "color": "#6b7280",
                        "guide_count": 0,
                        "guides_completed": 0,
                        "mastery_scores": [],
                        "guide_ids": [],
                    }

                t = tracks[track_id]
                t["guide_count"] += 1
                t["guide_ids"].append(d["id"])

                if user_id:
                    total = chapter_counts.get(d["id"], 0)
                    completed = completed_counts.get(d["id"], 0)
                    mastery = self._mastery_from_precomputed(
                        completed, total, avg_ef_map.get(d["id"])
                    )
                    t["mastery_scores"].append(mastery)

                    if enrollment_map.get(d["id"]):
                        t["guides_completed"] += 1

            result = []
            for t in tracks.values():
                scores = t.pop("mastery_scores")
                t["average_mastery"] = round(sum(scores) / len(scores), 1) if scores else 0.0
                t["completion_pct"] = (
                    round(t["guides_completed"] / t["guide_count"] * 100, 1)
                    if t["guide_count"] > 0
                    else 0.0
                )
                result.append(t)
            return result

    def get_tree_data(self, user_id: str, excluded_guide_ids: set[str] | None = None) -> list[dict]:
        """Return per-guide data for skill tree: progress, mastery, status."""
        import json as _json

        with wal_connect(self.db_path, row_factory=True) as conn:
            rows = conn.execute(
                "SELECT * FROM guides WHERE archived_at IS NULL AND origin='builtin' ORDER BY id"
            ).fetchall()
            chapter_counts, completed_counts, enrollment_map, avg_ef_map = self._batch_guide_data(
                conn, user_id
            )
            excluded_guide_ids = excluded_guide_ids or set()

            results = []
            for row in rows:
                d = dict(row)
                gid = d["id"]
                if gid in excluded_guide_ids:
                    continue
                prereqs = _json.loads(d.get("prerequisites", "[]"))

                total = chapter_counts.get(gid, 0)
                completed = completed_counts.get(gid, 0)
                enrolled = gid in enrollment_map
                guide_completed = enrollment_map.get(gid) is not None if enrolled else False

                progress_pct = round(completed / total * 100, 1) if total > 0 else 0.0
                mastery = self._mastery_from_precomputed(completed, total, avg_ef_map.get(gid))

                # Determine status
                if not enrolled:
                    status = "not_started"
                elif guide_completed:
                    status = "completed"
                elif completed > 0:
                    status = "in_progress"
                else:
                    status = "enrolled"

                results.append(
                    {
                        "id": gid,
                        "title": d["title"],
                        "track": d.get("track", ""),
                        "category": d["category"],
                        "difficulty": d["difficulty"],
                        "chapter_count": d["chapter_count"],
                        "prerequisites": prereqs,
                        "enrolled": enrolled,
                        "chapters_completed": completed,
                        "chapters_total": total,
                        "progress_pct": progress_pct,
                        "mastery_score": mastery,
                        "status": status,
                    }
                )
            return results

    def get_ready_guides(
        self, user_id: str, excluded_guide_ids: set[str] | None = None
    ) -> list[dict]:
        """Return guides where ALL prereqs are completed and guide is NOT enrolled.

        Entry-point guides (no prereqs) are excluded.
        """
        import json

        with wal_connect(self.db_path, row_factory=True) as conn:
            rows = conn.execute(
                "SELECT * FROM guides WHERE archived_at IS NULL AND origin='builtin' ORDER BY id"
            ).fetchall()
            excluded_guide_ids = excluded_guide_ids or set()
            results = []
            for row in rows:
                d = dict(row)
                if d["id"] in excluded_guide_ids:
                    continue
                prereqs = json.loads(d.get("prerequisites", "[]"))
                if not prereqs:
                    continue  # skip entry points

                # Check not enrolled
                enrollment = conn.execute(
                    "SELECT 1 FROM user_guide_enrollment WHERE user_id=? AND guide_id=?",
                    (user_id, d["id"]),
                ).fetchone()
                if enrollment:
                    continue

                # Check ALL prereqs have completed enrollment
                all_met = True
                for prereq_id in prereqs:
                    prereq_enrollment = conn.execute(
                        "SELECT completed_at FROM user_guide_enrollment WHERE user_id=? AND guide_id=?",
                        (user_id, prereq_id),
                    ).fetchone()
                    if not prereq_enrollment or dict(prereq_enrollment).get("completed_at") is None:
                        all_met = False
                        break

                if all_met:
                    results.append(
                        {
                            "id": d["id"],
                            "title": d["title"],
                            "track": d.get("track", ""),
                            "category": d["category"],
                            "difficulty": d["difficulty"],
                            "chapter_count": d["chapter_count"],
                            "prerequisites": prereqs,
                        }
                    )
            return results

    def complete_guide_placement(self, user_id: str, guide_id: str) -> dict:
        """Auto-enroll + mark all chapters completed + complete guide in one transaction."""
        now = datetime.utcnow().isoformat()
        with wal_connect(self.db_path) as conn:
            # Auto-enroll
            conn.execute(
                """INSERT INTO user_guide_enrollment (user_id, guide_id, enrolled_at, completed_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id, guide_id) DO UPDATE SET completed_at=excluded.completed_at""",
                (user_id, guide_id, now, now),
            )

            # Mark all non-glossary chapters completed
            chapters = conn.execute(
                'SELECT id FROM chapters WHERE guide_id=? AND is_glossary=0 ORDER BY "order"',
                (guide_id,),
            ).fetchall()
            for ch in chapters:
                ch_id = ch[0]
                conn.execute(
                    """INSERT INTO user_chapter_progress
                       (user_id, chapter_id, guide_id, status, reading_time_seconds,
                        scroll_position, started_at, completed_at, updated_at)
                       VALUES (?, ?, ?, 'completed', 0, 1.0, ?, ?, ?)
                       ON CONFLICT(user_id, chapter_id) DO UPDATE SET
                       status='completed', completed_at=excluded.completed_at,
                       updated_at=excluded.updated_at""",
                    (user_id, ch_id, guide_id, now, now, now),
                )

            conn.commit()
            return {
                "guide_id": guide_id,
                "chapters_marked": len(chapters),
                "completed_at": now,
            }

    def get_next_chapter(self, user_id: str, guide_id: str) -> dict | None:
        """Get next unread chapter in a guide."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute(
                """SELECT c.* FROM chapters c
                   LEFT JOIN user_chapter_progress ucp
                   ON ucp.chapter_id = c.id AND ucp.user_id=?
                   WHERE c.guide_id=? AND c.is_glossary=0
                   AND (ucp.status IS NULL OR ucp.status != 'completed')
                   ORDER BY c."order" ASC LIMIT 1""",
                (user_id, guide_id),
            ).fetchone()
            if not row:
                return None
            return self._deserialize_chapter_row(row)

    @staticmethod
    def _deserialize_chapter_row(row: sqlite3.Row | dict) -> dict:
        chapter = dict(row)
        chapter["has_diagrams"] = bool(chapter["has_diagrams"])
        chapter["has_tables"] = bool(chapter["has_tables"])
        chapter["has_formulas"] = bool(chapter["has_formulas"])
        chapter["is_glossary"] = bool(chapter["is_glossary"])
        chapter["objectives"] = json.loads(chapter.get("objectives", "[]"))
        chapter["checkpoints"] = json.loads(chapter.get("checkpoints", "[]"))
        chapter["content_references"] = json.loads(chapter.get("content_references", "[]"))
        return chapter

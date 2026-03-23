"""SQLite persistence for curriculum catalog and user progress."""

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

SCHEMA_VERSION = 2


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
                    category TEXT NOT NULL DEFAULT 'humanities',
                    difficulty TEXT NOT NULL DEFAULT 'intermediate',
                    source_dir TEXT NOT NULL DEFAULT '',
                    chapter_count INTEGER NOT NULL DEFAULT 0,
                    total_word_count INTEGER NOT NULL DEFAULT 0,
                    total_reading_time_minutes INTEGER NOT NULL DEFAULT 0,
                    has_glossary INTEGER NOT NULL DEFAULT 0,
                    prerequisites TEXT NOT NULL DEFAULT '[]'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    id TEXT PRIMARY KEY,
                    guide_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    "order" INTEGER NOT NULL DEFAULT 0,
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

            ensure_schema_version(conn, SCHEMA_VERSION)
            conn.commit()

    # --- Catalog operations ---

    def upsert_guide(self, guide: Guide) -> None:
        import json

        with wal_connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO guides (id, title, category, difficulty, source_dir,
                   chapter_count, total_word_count, total_reading_time_minutes,
                   has_glossary, prerequisites)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   title=excluded.title, category=excluded.category,
                   difficulty=excluded.difficulty, source_dir=excluded.source_dir,
                   chapter_count=excluded.chapter_count,
                   total_word_count=excluded.total_word_count,
                   total_reading_time_minutes=excluded.total_reading_time_minutes,
                   has_glossary=excluded.has_glossary,
                   prerequisites=excluded.prerequisites""",
                (
                    guide.id,
                    guide.title,
                    guide.category.value,
                    guide.difficulty.value,
                    guide.source_dir,
                    guide.chapter_count,
                    guide.total_word_count,
                    guide.total_reading_time_minutes,
                    int(guide.has_glossary),
                    json.dumps(guide.prerequisites),
                ),
            )
            conn.commit()

    def upsert_chapter(self, chapter: Chapter) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO chapters (id, guide_id, title, filename, "order",
                   word_count, reading_time_minutes, has_diagrams, has_tables,
                   has_formulas, is_glossary, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   title=excluded.title, filename=excluded.filename,
                   "order"=excluded."order", word_count=excluded.word_count,
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
        import json

        with wal_connect(self.db_path) as conn:
            for g in guides:
                conn.execute(
                    """INSERT INTO guides (id, title, category, difficulty, source_dir,
                       chapter_count, total_word_count, total_reading_time_minutes,
                       has_glossary, prerequisites)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                       title=excluded.title, category=excluded.category,
                       difficulty=excluded.difficulty, source_dir=excluded.source_dir,
                       chapter_count=excluded.chapter_count,
                       total_word_count=excluded.total_word_count,
                       total_reading_time_minutes=excluded.total_reading_time_minutes,
                       has_glossary=excluded.has_glossary,
                       prerequisites=excluded.prerequisites""",
                    (
                        g.id,
                        g.title,
                        g.category.value,
                        g.difficulty.value,
                        g.source_dir,
                        g.chapter_count,
                        g.total_word_count,
                        g.total_reading_time_minutes,
                        int(g.has_glossary),
                        json.dumps(g.prerequisites),
                    ),
                )
            for c in chapters:
                conn.execute(
                    """INSERT INTO chapters (id, guide_id, title, filename, "order",
                       word_count, reading_time_minutes, has_diagrams, has_tables,
                       has_formulas, is_glossary, content_hash)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                       title=excluded.title, filename=excluded.filename,
                       "order"=excluded."order", word_count=excluded.word_count,
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

    def list_guides(self, category: str | None = None, user_id: str | None = None) -> list[dict]:
        """List guides with optional user progress summary."""
        import json

        with wal_connect(self.db_path, row_factory=True) as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM guides WHERE category = ? ORDER BY id", (category,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM guides ORDER BY id").fetchall()

            results = []
            for row in rows:
                d = dict(row)
                d["has_glossary"] = bool(d["has_glossary"])
                d["prerequisites"] = json.loads(d.get("prerequisites", "[]"))

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
                        "SELECT COUNT(*) FROM chapters WHERE guide_id=?", (d["id"],)
                    ).fetchone()[0]
                    completed = conn.execute(
                        "SELECT COUNT(*) FROM user_chapter_progress WHERE user_id=? AND guide_id=? AND status='completed'",
                        (user_id, d["id"]),
                    ).fetchone()[0]
                    d["chapters_total"] = total
                    d["chapters_completed"] = completed
                    d["progress_pct"] = round(completed / total * 100, 1) if total > 0 else 0.0
                else:
                    d["enrolled"] = False
                    d["chapters_completed"] = 0
                    d["chapters_total"] = d["chapter_count"]
                    d["progress_pct"] = 0.0

                results.append(d)
            return results

    def get_guide(self, guide_id: str, user_id: str | None = None) -> dict | None:
        """Get guide with chapters and progress."""
        import json

        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute("SELECT * FROM guides WHERE id=?", (guide_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["has_glossary"] = bool(d["has_glossary"])
            d["prerequisites"] = json.loads(d.get("prerequisites", "[]"))

            chapters = conn.execute(
                'SELECT * FROM chapters WHERE guide_id=? ORDER BY "order"', (guide_id,)
            ).fetchall()
            d["chapters"] = []
            for ch in chapters:
                cd = dict(ch)
                cd["has_diagrams"] = bool(cd["has_diagrams"])
                cd["has_tables"] = bool(cd["has_tables"])
                cd["has_formulas"] = bool(cd["has_formulas"])
                cd["is_glossary"] = bool(cd["is_glossary"])

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
                completed = sum(1 for c in d["chapters"] if c["status"] == "completed")
                d["chapters_completed"] = completed
                d["chapters_total"] = len(d["chapters"])
                d["progress_pct"] = (
                    round(completed / len(d["chapters"]) * 100, 1) if d["chapters"] else 0.0
                )
            else:
                d["enrolled"] = False
                d["chapters_completed"] = 0
                d["chapters_total"] = len(d["chapters"])
                d["progress_pct"] = 0.0

            return d

    def get_chapter(self, chapter_id: str) -> dict | None:
        """Get chapter metadata."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute("SELECT * FROM chapters WHERE id=?", (chapter_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["has_diagrams"] = bool(d["has_diagrams"])
            d["has_tables"] = bool(d["has_tables"])
            d["has_formulas"] = bool(d["has_formulas"])
            d["is_glossary"] = bool(d["is_glossary"])
            return d

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

    def get_enrollments(self, user_id: str) -> list[dict]:
        with wal_connect(self.db_path, row_factory=True) as conn:
            rows = conn.execute(
                "SELECT * FROM user_guide_enrollment WHERE user_id=? ORDER BY enrolled_at DESC",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]

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
                   WHERE ucp.user_id=?
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
                    """SELECT * FROM review_items
                       WHERE user_id=? AND guide_id=? AND next_review <= ?
                       AND item_type != 'pre_reading'
                       ORDER BY next_review ASC LIMIT ?""",
                    (user_id, guide_id, now, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM review_items
                       WHERE user_id=? AND next_review <= ?
                       AND item_type != 'pre_reading'
                       ORDER BY next_review ASC LIMIT ?""",
                    (user_id, now, limit),
                ).fetchall()
            return [dict(r) for r in rows]

    def get_review_item(self, review_id: str) -> dict | None:
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute("SELECT * FROM review_items WHERE id=?", (review_id,)).fetchone()
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
                "SELECT * FROM review_items WHERE user_id=? AND chapter_id=?",
                (user_id, chapter_id),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_teachback_for_chapter(self, user_id: str, chapter_id: str) -> dict | None:
        """Get the teach-back review item for a chapter, if any."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute(
                "SELECT * FROM review_items WHERE user_id=? AND chapter_id=? AND item_type='teachback'",
                (user_id, chapter_id),
            ).fetchone()
            return dict(row) if row else None

    def get_pre_reading_questions(self, user_id: str, chapter_id: str) -> list[dict]:
        """Get pre-reading question items for a chapter."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            rows = conn.execute(
                "SELECT * FROM review_items WHERE user_id=? AND chapter_id=? AND item_type='pre_reading'",
                (user_id, chapter_id),
            ).fetchall()
            return [dict(r) for r in rows]

    def count_due_reviews(self, user_id: str) -> int:
        now = datetime.utcnow().isoformat()
        with wal_connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM review_items WHERE user_id=? AND next_review <= ?",
                (user_id, now),
            ).fetchone()
            return row[0] if row else 0

    # --- Stats ---

    def get_stats(self, user_id: str) -> LearningStats:
        with wal_connect(self.db_path, row_factory=True) as conn:
            enrolled = conn.execute(
                "SELECT COUNT(*) FROM user_guide_enrollment WHERE user_id=?", (user_id,)
            ).fetchone()[0]
            guide_completed = conn.execute(
                "SELECT COUNT(*) FROM user_guide_enrollment WHERE user_id=? AND completed_at IS NOT NULL",
                (user_id,),
            ).fetchone()[0]
            chapters_completed = conn.execute(
                "SELECT COUNT(*) FROM user_chapter_progress WHERE user_id=? AND status='completed'",
                (user_id,),
            ).fetchone()[0]
            total_chapters = conn.execute("SELECT COUNT(*) FROM chapters").fetchone()[0]
            reading_time = conn.execute(
                "SELECT COALESCE(SUM(reading_time_seconds), 0) FROM user_chapter_progress WHERE user_id=?",
                (user_id,),
            ).fetchone()[0]
            reviews_done = conn.execute(
                "SELECT COUNT(*) FROM review_items WHERE user_id=? AND last_reviewed IS NOT NULL",
                (user_id,),
            ).fetchone()[0]
            avg_grade_row = conn.execute(
                """SELECT AVG(ri.easiness_factor) FROM review_items ri
                   WHERE ri.user_id=? AND ri.last_reviewed IS NOT NULL""",
                (user_id,),
            ).fetchone()
            avg_grade = round(avg_grade_row[0], 2) if avg_grade_row[0] else 0.0

            due = self.count_due_reviews(user_id)

            # Mastery by category
            mastery: dict[str, float] = {}
            cats = conn.execute(
                """SELECT g.category, COUNT(DISTINCT ucp.chapter_id) as done,
                   COUNT(DISTINCT c.id) as total
                   FROM guides g
                   JOIN chapters c ON c.guide_id = g.id
                   LEFT JOIN user_chapter_progress ucp
                   ON ucp.chapter_id = c.id AND ucp.user_id=? AND ucp.status='completed'
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
                """SELECT DATE(updated_at) as day, COUNT(*) as cnt
                   FROM user_chapter_progress
                   WHERE user_id=? AND updated_at >= ?
                   GROUP BY DATE(updated_at)""",
                (user_id, thirty_days_ago),
            ).fetchall()
            daily = {dict(r)["day"]: dict(r)["cnt"] for r in daily_rows}

            # Streak calc
            streak = 0
            today = datetime.utcnow().date()
            for i in range(365):
                day = (today - timedelta(days=i)).isoformat()
                if day in daily or (i == 0 and daily):
                    # Check if there's activity for this exact day
                    if day in daily:
                        streak += 1
                    elif i == 0:
                        break
                    else:
                        break
                elif i > 0:
                    break

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
                daily_activity=daily,
            )

    def get_next_chapter(self, user_id: str, guide_id: str) -> dict | None:
        """Get next unread chapter in a guide."""
        with wal_connect(self.db_path, row_factory=True) as conn:
            row = conn.execute(
                """SELECT c.* FROM chapters c
                   LEFT JOIN user_chapter_progress ucp
                   ON ucp.chapter_id = c.id AND ucp.user_id=?
                   WHERE c.guide_id=? AND (ucp.status IS NULL OR ucp.status != 'completed')
                   ORDER BY c."order" ASC LIMIT 1""",
                (user_id, guide_id),
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            d["has_diagrams"] = bool(d["has_diagrams"])
            d["has_tables"] = bool(d["has_tables"])
            d["has_formulas"] = bool(d["has_formulas"])
            d["is_glossary"] = bool(d["is_glossary"])
            return d

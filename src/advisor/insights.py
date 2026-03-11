"""Unified insight store — merges signals, patterns, and heartbeat output."""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

import structlog

from db import wal_connect

logger = structlog.get_logger()

DEFAULT_TTL_DAYS = 14


class InsightType(str, Enum):
    # from signals
    TOPIC_EMERGENCE = "topic_emergence"
    GOAL_STALE = "goal_stale"
    GOAL_COMPLETE = "goal_complete"
    DEADLINE_URGENT = "deadline_urgent"
    JOURNAL_GAP = "journal_gap"
    LEARNING_STALLED = "learning_stalled"
    RESEARCH_TRIGGER = "research_trigger"
    RECURRING_BLOCKER = "recurring_blocker"
    # from patterns
    PATTERN_BLIND_SPOT = "pattern_blind_spot"
    PATTERN_BLOCKER_CYCLE = "pattern_blocker_cycle"
    # from heartbeat
    INTEL_MATCH = "intel_match"


@dataclass
class Insight:
    type: InsightType
    severity: int  # 1-10
    title: str
    detail: str
    suggested_actions: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    source_url: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    insight_hash: str = ""

    def compute_hash(self) -> str:
        text = f"{self.type.value}|{self.title}"
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def __post_init__(self):
        if not self.insight_hash:
            self.insight_hash = self.compute_hash()
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(days=DEFAULT_TTL_DAYS)


class InsightStore:
    """SQLite persistence for insights in intel.db."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path).expanduser()
        self._init_tables()

    def _init_tables(self):
        with wal_connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    detail TEXT,
                    evidence_json TEXT,
                    actions_json TEXT,
                    source_url TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    insight_hash TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_insights_type ON insights(type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_insights_hash ON insights(insight_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_insights_expires ON insights(expires_at)")

    def save(self, insight: Insight) -> bool:
        """Save insight, skip if duplicate hash exists within TTL window."""
        h = insight.insight_hash or insight.compute_hash()
        try:
            with wal_connect(self.db_path) as conn:
                # Check for existing unexpired insight with same hash
                existing = conn.execute(
                    "SELECT id FROM insights WHERE insight_hash = ? AND (expires_at IS NULL OR expires_at > ?)",
                    (h, datetime.now().isoformat()),
                ).fetchone()
                if existing:
                    return False

                conn.execute(
                    """INSERT INTO insights
                    (type, severity, title, detail, evidence_json, actions_json,
                     source_url, created_at, expires_at, insight_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        insight.type.value,
                        insight.severity,
                        insight.title,
                        insight.detail,
                        json.dumps(insight.evidence),
                        json.dumps(insight.suggested_actions),
                        insight.source_url,
                        insight.created_at.isoformat(),
                        insight.expires_at.isoformat() if insight.expires_at else None,
                        h,
                    ),
                )
                return True
        except sqlite3.Error as e:
            logger.error("insight_save_error", error=str(e))
            return False

    def upsert(self, insight: Insight) -> bool:
        """Insert or update insight by hash. Updates detail/actions/severity/expires if match exists."""
        h = insight.insight_hash or insight.compute_hash()
        try:
            with wal_connect(self.db_path) as conn:
                existing = conn.execute(
                    "SELECT id FROM insights WHERE insight_hash = ? AND (expires_at IS NULL OR expires_at > ?)",
                    (h, datetime.now().isoformat()),
                ).fetchone()
                if existing:
                    conn.execute(
                        """UPDATE insights
                        SET detail = ?, actions_json = ?, severity = ?, expires_at = ?
                        WHERE id = ?""",
                        (
                            insight.detail,
                            json.dumps(insight.suggested_actions),
                            insight.severity,
                            insight.expires_at.isoformat() if insight.expires_at else None,
                            existing[0],
                        ),
                    )
                    return True
                conn.execute(
                    """INSERT INTO insights
                    (type, severity, title, detail, evidence_json, actions_json,
                     source_url, created_at, expires_at, insight_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        insight.type.value,
                        insight.severity,
                        insight.title,
                        insight.detail,
                        json.dumps(insight.evidence),
                        json.dumps(insight.suggested_actions),
                        insight.source_url,
                        insight.created_at.isoformat(),
                        insight.expires_at.isoformat() if insight.expires_at else None,
                        h,
                    ),
                )
                return True
        except sqlite3.Error as e:
            logger.error("insight_upsert_error", error=str(e))
            return False

    def get_active(
        self,
        insight_type: Optional[str] = None,
        min_severity: int = 1,
        limit: int = 20,
    ) -> list[dict]:
        """Get active (unexpired) insights."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = """
                SELECT * FROM insights
                WHERE (expires_at IS NULL OR expires_at > ?)
                AND severity >= ?
            """
            params: list = [datetime.now().isoformat(), min_severity]
            if insight_type:
                query += " AND type = ?"
                params.append(insight_type)
            query += " ORDER BY severity DESC, created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row) -> dict:
        d = dict(row)
        d["evidence"] = json.loads(d.pop("evidence_json", "[]") or "[]")
        d["suggested_actions"] = json.loads(d.pop("actions_json", "[]") or "[]")
        return d

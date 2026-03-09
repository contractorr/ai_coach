"""Dossier escalation suggestions derived from private user context."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from db import wal_connect


def _now() -> str:
    return datetime.now().isoformat()


def _topic_key(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-")
    return normalized[:80] or "topic"


class DossierEscalationStore:
    """Per-user store for active, snoozed, dismissed, and accepted escalations."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dossier_escalations (
                    escalation_id TEXT PRIMARY KEY,
                    topic_key TEXT NOT NULL,
                    topic_label TEXT NOT NULL,
                    score REAL NOT NULL,
                    state TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    snoozed_until TEXT,
                    dismissed_at TEXT,
                    accepted_dossier_id TEXT
                )
                """
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_dossier_escalations_topic_active ON dossier_escalations(topic_key, state)"
            )

    def upsert_candidate(self, suggestion: dict) -> str:
        escalation_id = suggestion.get("escalation_id") or uuid.uuid4().hex[:16]
        created_at = suggestion.get("created_at") or _now()
        updated_at = _now()
        topic_key = suggestion.get("topic_key") or _topic_key(suggestion.get("topic_label") or "")

        with wal_connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT escalation_id, created_at, state, accepted_dossier_id, snoozed_until FROM dossier_escalations WHERE topic_key = ? ORDER BY updated_at DESC LIMIT 1",
                (topic_key,),
            ).fetchone()
            if existing and existing[2] == "accepted":
                return existing[0]
            if existing:
                escalation_id = existing[0]
                created_at = existing[1]
            conn.execute(
                """
                INSERT INTO dossier_escalations (
                    escalation_id, topic_key, topic_label, score, state, evidence_json,
                    payload_json, created_at, updated_at, snoozed_until, dismissed_at, accepted_dossier_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(escalation_id) DO UPDATE SET
                    topic_label = excluded.topic_label,
                    score = excluded.score,
                    state = excluded.state,
                    evidence_json = excluded.evidence_json,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at,
                    snoozed_until = excluded.snoozed_until,
                    dismissed_at = excluded.dismissed_at,
                    accepted_dossier_id = excluded.accepted_dossier_id
                """,
                (
                    escalation_id,
                    topic_key,
                    suggestion.get("topic_label") or topic_key,
                    float(suggestion.get("score") or 0.0),
                    suggestion.get("state") or "active",
                    json.dumps(suggestion.get("evidence") or {}),
                    json.dumps(suggestion.get("payload") or {}),
                    created_at,
                    updated_at,
                    suggestion.get("snoozed_until"),
                    suggestion.get("dismissed_at"),
                    suggestion.get("accepted_dossier_id"),
                ),
            )
        return escalation_id

    def _row_to_dict(self, row: sqlite3.Row | None) -> dict | None:
        if not row:
            return None
        return {
            "escalation_id": row["escalation_id"],
            "topic_key": row["topic_key"],
            "topic_label": row["topic_label"],
            "score": row["score"],
            "state": row["state"],
            "evidence": json.loads(row["evidence_json"] or "{}"),
            "payload": json.loads(row["payload_json"] or "{}"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "snoozed_until": row["snoozed_until"],
            "dismissed_at": row["dismissed_at"],
            "accepted_dossier_id": row["accepted_dossier_id"],
        }

    def get(self, escalation_id: str) -> dict | None:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM dossier_escalations WHERE escalation_id = ?",
                (escalation_id,),
            ).fetchone()
        return self._row_to_dict(row)

    def list_active(self, limit: int = 10) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM dossier_escalations WHERE state IN ('active', 'snoozed') ORDER BY score DESC, updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows if row]

    def snooze(self, escalation_id: str, until: str) -> bool:
        with wal_connect(self.db_path) as conn:
            result = conn.execute(
                "UPDATE dossier_escalations SET state = 'snoozed', snoozed_until = ?, updated_at = ? WHERE escalation_id = ?",
                (until, _now(), escalation_id),
            )
        return bool(result.rowcount)

    def dismiss(self, escalation_id: str) -> bool:
        with wal_connect(self.db_path) as conn:
            result = conn.execute(
                "UPDATE dossier_escalations SET state = 'dismissed', dismissed_at = ?, updated_at = ? WHERE escalation_id = ?",
                (_now(), _now(), escalation_id),
            )
        return bool(result.rowcount)

    def accept(self, escalation_id: str, dossier_id: str) -> bool:
        with wal_connect(self.db_path) as conn:
            result = conn.execute(
                "UPDATE dossier_escalations SET state = 'accepted', accepted_dossier_id = ?, updated_at = ? WHERE escalation_id = ?",
                (dossier_id, _now(), escalation_id),
            )
        return bool(result.rowcount)


class DossierEscalationEngine:
    """Heuristic-first engine for suggesting which threads deserve dossiers."""

    def __init__(
        self,
        store: DossierEscalationStore,
        *,
        min_escalation_score: float = 0.62,
        max_active_escalations: int = 3,
    ):
        self.store = store
        self.min_escalation_score = min_escalation_score
        self.max_active_escalations = max_active_escalations

    def refresh(self, user_context: dict) -> list[dict]:
        threads = user_context.get("threads") or []
        recent_intel = user_context.get("recent_intel") or []
        watchlist_items = user_context.get("watchlist") or []
        goals = user_context.get("goals") or []
        existing_dossiers = {
            _topic_key(d.get("topic") or d.get("title") or "")
            for d in (user_context.get("dossiers") or [])
        }

        candidates: list[dict] = []
        for thread in threads:
            label = str(thread.get("label") or "").strip()
            if not label:
                continue
            topic_key = _topic_key(label)
            if topic_key in existing_dossiers:
                continue

            entry_count = int(thread.get("entry_count") or 0)
            thread_recency_score = min(1.0, max(0.2, entry_count / 5.0))
            journal_frequency_score = min(1.0, entry_count / 6.0)
            intel_hits = sum(
                1
                for item in recent_intel
                if label.lower() in f"{item.get('title', '')} {item.get('summary', '')}".lower()
            )
            intel_support_score = min(1.0, intel_hits / 3.0)
            goal_bonus = (
                1.0
                if any(label.lower() in str(goal.get("title") or "").lower() for goal in goals)
                else 0.0
            )
            watchlist_bonus = (
                1.0
                if any(
                    label.lower() in str(item.get("label") or "").lower()
                    for item in watchlist_items
                )
                else 0.0
            )
            bonus = max(goal_bonus, watchlist_bonus)

            score = (
                0.35 * thread_recency_score
                + 0.25 * journal_frequency_score
                + 0.25 * intel_support_score
                + 0.10 * bonus
            )
            if score < self.min_escalation_score:
                continue

            suggestion = {
                "topic_key": topic_key,
                "topic_label": label,
                "score": round(score, 3),
                "state": "active",
                "evidence": {
                    "thread_id": thread.get("id"),
                    "recent_mentions": entry_count,
                    "intel_hits": intel_hits,
                    "goal_titles": [
                        goal.get("title")
                        for goal in goals
                        if label.lower() in str(goal.get("title") or "").lower()
                    ],
                    "watchlist_labels": [
                        item.get("label")
                        for item in watchlist_items
                        if label.lower() in str(item.get("label") or "").lower()
                    ],
                },
                "payload": {
                    "topic": label,
                    "scope": f"Track the recurring topic '{label}' and recent related signals.",
                    "core_questions": [f"What changed recently around {label}?"],
                    "tracked_subtopics": [label],
                },
            }
            saved_id = self.store.upsert_candidate(suggestion)
            saved = self.store.get(saved_id)
            if saved:
                candidates.append(saved)

        candidates.sort(
            key=lambda item: (item.get("score") or 0.0, item.get("updated_at") or ""), reverse=True
        )
        return candidates[: self.max_active_escalations]

    def build_prefill(self, escalation_id: str) -> dict | None:
        escalation = self.store.get(escalation_id)
        if not escalation:
            return None
        payload = dict(escalation.get("payload") or {})
        payload.setdefault("topic", escalation.get("topic_label") or "")
        payload.setdefault("assumptions", [])
        return payload

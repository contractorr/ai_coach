"""Harvested outcomes inferred from later recommendation follow-through."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from db import wal_connect

VALID_OUTCOME_STATES = {"positive", "negative", "unresolved", "conflicted"}


def _now() -> str:
    return datetime.now().isoformat()


class HarvestedOutcomeStore:
    """Per-user store for inferred or overridden recommendation outcomes."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS harvested_outcomes (
                    id TEXT PRIMARY KEY,
                    recommendation_id TEXT NOT NULL,
                    action_item_id TEXT,
                    state TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence_json TEXT NOT NULL,
                    source_summary TEXT NOT NULL DEFAULT '',
                    user_overridden INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_harvested_outcomes_rec ON harvested_outcomes(recommendation_id)"
            )

    def _row_to_dict(self, row: sqlite3.Row | None) -> dict | None:
        if not row:
            return None
        return {
            "id": row["id"],
            "recommendation_id": row["recommendation_id"],
            "action_item_id": row["action_item_id"],
            "state": row["state"],
            "confidence": row["confidence"],
            "evidence": json.loads(row["evidence_json"] or "[]"),
            "source_summary": row["source_summary"],
            "user_overridden": bool(row["user_overridden"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def upsert(self, outcome: dict) -> str:
        state = outcome.get("state") or "unresolved"
        if state not in VALID_OUTCOME_STATES:
            raise ValueError(f"Invalid outcome state: {state}")
        recommendation_id = outcome["recommendation_id"]
        created_at = outcome.get("created_at") or _now()
        outcome_id = outcome.get("id") or uuid.uuid4().hex[:16]
        with wal_connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id, created_at FROM harvested_outcomes WHERE recommendation_id = ?",
                (recommendation_id,),
            ).fetchone()
            if existing:
                outcome_id = existing[0]
                created_at = existing[1]
            conn.execute(
                """
                INSERT INTO harvested_outcomes (
                    id, recommendation_id, action_item_id, state, confidence, evidence_json,
                    source_summary, user_overridden, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(recommendation_id) DO UPDATE SET
                    action_item_id = excluded.action_item_id,
                    state = excluded.state,
                    confidence = excluded.confidence,
                    evidence_json = excluded.evidence_json,
                    source_summary = excluded.source_summary,
                    user_overridden = excluded.user_overridden,
                    updated_at = excluded.updated_at
                """,
                (
                    outcome_id,
                    recommendation_id,
                    outcome.get("action_item_id"),
                    state,
                    float(outcome.get("confidence") or 0.0),
                    json.dumps(outcome.get("evidence") or []),
                    outcome.get("source_summary") or "",
                    1 if outcome.get("user_overridden") else 0,
                    created_at,
                    _now(),
                ),
            )
        return outcome_id

    def get(self, recommendation_id: str) -> dict | None:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM harvested_outcomes WHERE recommendation_id = ?",
                (recommendation_id,),
            ).fetchone()
        return self._row_to_dict(row)

    def list_recent(self, limit: int = 50) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM harvested_outcomes ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows if row]

    def override(self, recommendation_id: str, state: str, note: str = "") -> dict | None:
        existing = self.get(recommendation_id)
        if not existing:
            return None
        payload = dict(existing)
        payload.update(
            {
                "state": state,
                "confidence": 1.0,
                "source_summary": note or f"User marked this outcome as {state}.",
                "user_overridden": True,
                "evidence": list(existing.get("evidence") or [])
                + [
                    {
                        "kind": "override",
                        "value": state,
                        "source_id": recommendation_id,
                        "excerpt": note,
                    }
                ],
            }
        )
        self.upsert(payload)
        return self.get(recommendation_id)


class OutcomeHarvester:
    """Rules-first evaluator for later recommendation outcomes."""

    def __init__(self, store: HarvestedOutcomeStore, recommendation_storage):
        self.store = store
        self.recommendation_storage = recommendation_storage

    def evaluate_recommendation(self, recommendation: dict) -> dict | None:
        existing = self.store.get(recommendation["id"])
        if existing and existing.get("user_overridden"):
            return existing

        meta = recommendation.get("metadata") or {}
        action_item = meta.get("action_item") or {}
        evidence: list[dict] = []
        positive_score = 0.0
        negative_score = 0.0

        action_status = action_item.get("status")
        if action_status == "completed":
            positive_score += 1.0
            evidence.append(
                {
                    "kind": "action_status",
                    "value": "completed",
                    "source_id": recommendation["id"],
                    "excerpt": "",
                }
            )
        elif action_status in {"blocked", "abandoned"}:
            negative_score += 1.0
            evidence.append(
                {
                    "kind": "action_status",
                    "value": action_status,
                    "source_id": recommendation["id"],
                    "excerpt": "",
                }
            )

        rating = meta.get("user_rating")
        if isinstance(rating, int):
            if rating >= 4:
                positive_score += 0.7
                evidence.append(
                    {
                        "kind": "feedback",
                        "value": "positive",
                        "source_id": recommendation["id"],
                        "excerpt": meta.get("feedback_comment") or "",
                    }
                )
            elif rating <= 2:
                negative_score += 0.7
                evidence.append(
                    {
                        "kind": "feedback",
                        "value": "negative",
                        "source_id": recommendation["id"],
                        "excerpt": meta.get("feedback_comment") or "",
                    }
                )

        state = "unresolved"
        confidence = 0.4
        if positive_score >= 1.0 and negative_score < 0.8:
            state = "positive"
            confidence = min(1.0, positive_score)
        elif negative_score >= 1.0 and positive_score < 0.8:
            state = "negative"
            confidence = min(1.0, negative_score)
        elif positive_score >= 0.8 and negative_score >= 0.8:
            state = "conflicted"
            confidence = max(positive_score, negative_score) / 2

        payload = {
            "recommendation_id": recommendation["id"],
            "state": state,
            "confidence": round(confidence, 3),
            "evidence": evidence,
            "source_summary": self._summarize(state, action_status, rating),
            "user_overridden": False,
        }
        self.store.upsert(payload)
        return self.store.get(recommendation["id"])

    def run_recent(self, limit: int = 50) -> list[dict]:
        outcomes = []
        for rec in self.recommendation_storage.list_recent(days=90, limit=limit):
            item = self.evaluate_recommendation(
                {
                    "id": rec.id,
                    "metadata": rec.metadata or {},
                }
            )
            if item:
                outcomes.append(item)
        return outcomes

    @staticmethod
    def _summarize(state: str, action_status: str | None, rating: int | None) -> str:
        if state == "positive":
            if action_status == "completed":
                return "Completed action item and positive follow-through signals."
            return "Positive follow-through signals detected."
        if state == "negative":
            return "Negative follow-through signals detected."
        if state == "conflicted":
            return "Mixed evidence suggests this recommendation had a mixed outcome."
        if rating:
            return "Explicit feedback captured, but more evidence is needed."
        return "No clear outcome signal yet."

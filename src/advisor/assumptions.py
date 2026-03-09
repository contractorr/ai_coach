"""Assumption capture, evidence matching, and lightweight memory adaptation."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from db import wal_connect
from memory.models import FactCategory, FactSource, StewardFact

VALID_ASSUMPTION_STATUS = {
    "suggested",
    "active",
    "confirmed",
    "invalidated",
    "resolved",
    "archived",
}


def _now() -> str:
    return datetime.now().isoformat()


class AssumptionStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assumptions (
                    id TEXT PRIMARY KEY,
                    statement TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    extraction_confidence REAL,
                    linked_goal_path TEXT,
                    linked_dossier_id TEXT,
                    linked_entity_json TEXT NOT NULL DEFAULT '[]',
                    latest_evidence_summary TEXT NOT NULL DEFAULT '',
                    last_evaluated_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assumption_evidence (
                    id TEXT PRIMARY KEY,
                    assumption_id TEXT NOT NULL,
                    evidence_kind TEXT NOT NULL,
                    evidence_state TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    excerpt TEXT NOT NULL DEFAULT '',
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (assumption_id) REFERENCES assumptions(id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_assumptions_status ON assumptions(status, updated_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_assumption_evidence_assumption ON assumption_evidence(assumption_id, created_at DESC)"
            )

    def create(self, assumption: dict) -> str:
        assumption_id = assumption.get("id") or uuid.uuid4().hex[:16]
        status = assumption.get("status") or "active"
        if status not in VALID_ASSUMPTION_STATUS:
            raise ValueError(f"Invalid assumption status: {status}")
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO assumptions (
                    id, statement, status, source_type, source_id, extraction_confidence,
                    linked_goal_path, linked_dossier_id, linked_entity_json, latest_evidence_summary,
                    last_evaluated_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assumption_id,
                    assumption.get("statement") or "",
                    status,
                    assumption.get("source_type") or "manual",
                    assumption.get("source_id") or assumption_id,
                    assumption.get("extraction_confidence"),
                    assumption.get("linked_goal_path"),
                    assumption.get("linked_dossier_id"),
                    json.dumps(assumption.get("linked_entities") or []),
                    assumption.get("latest_evidence_summary") or "",
                    assumption.get("last_evaluated_at"),
                    _now(),
                    _now(),
                ),
            )
        return assumption_id

    def _get_evidence(self, assumption_id: str) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM assumption_evidence WHERE assumption_id = ? ORDER BY created_at DESC",
                (assumption_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_active(self, limit: int = 50) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM assumptions WHERE status IN ('active', 'confirmed', 'invalidated', 'suggested') ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self.get(row["id"]) for row in rows if row]

    def get(self, assumption_id: str) -> dict | None:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM assumptions WHERE id = ?", (assumption_id,)
            ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "statement": row["statement"],
            "status": row["status"],
            "source_type": row["source_type"],
            "source_id": row["source_id"],
            "extraction_confidence": row["extraction_confidence"],
            "linked_goal_path": row["linked_goal_path"],
            "linked_dossier_id": row["linked_dossier_id"],
            "linked_entities": json.loads(row["linked_entity_json"] or "[]"),
            "latest_evidence_summary": row["latest_evidence_summary"],
            "last_evaluated_at": row["last_evaluated_at"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "evidence": self._get_evidence(assumption_id),
        }

    def update_status(self, assumption_id: str, status: str) -> dict | None:
        if status not in VALID_ASSUMPTION_STATUS:
            raise ValueError(f"Invalid assumption status: {status}")
        with wal_connect(self.db_path) as conn:
            result = conn.execute(
                "UPDATE assumptions SET status = ?, updated_at = ? WHERE id = ?",
                (status, _now(), assumption_id),
            )
        if not result.rowcount:
            return None
        return self.get(assumption_id)

    def append_evidence(self, assumption_id: str, evidence: dict) -> str:
        evidence_id = uuid.uuid4().hex[:16]
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO assumption_evidence (
                    id, assumption_id, evidence_kind, evidence_state, source_ref, excerpt, confidence, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    assumption_id,
                    evidence.get("evidence_kind") or "intel",
                    evidence.get("evidence_state") or "informational",
                    evidence.get("source_ref") or "",
                    evidence.get("excerpt") or "",
                    float(evidence.get("confidence") or 0.0),
                    _now(),
                ),
            )
            summary = evidence.get("excerpt") or evidence.get("source_ref") or ""
            conn.execute(
                "UPDATE assumptions SET latest_evidence_summary = ?, last_evaluated_at = ?, updated_at = ? WHERE id = ?",
                (summary[:300], _now(), _now(), assumption_id),
            )
        return evidence_id


class AssumptionExtractor:
    def __init__(self, *, min_confidence: float = 0.75, max_candidates_per_source: int = 3):
        self.min_confidence = min_confidence
        self.max_candidates_per_source = max_candidates_per_source

    def extract_from_journal(self, entry: dict) -> list[dict]:
        content = str(entry.get("content") or "")
        if len(content) < 40:
            return []
        candidates = []
        for line in content.splitlines():
            text = line.strip(" -\t")
            lower = text.lower()
            if not text:
                continue
            if any(
                trigger in lower
                for trigger in ("assuming ", "assume ", "if ", "as long as ", "provided that ")
            ):
                confidence = 0.78 if "assuming" in lower or "assume" in lower else 0.75
                if confidence < self.min_confidence:
                    continue
                entities = re.findall(r"\b[A-Z][a-zA-Z0-9&.-]+\b", text)
                candidates.append(
                    {
                        "statement": text[:300],
                        "confidence": confidence,
                        "source_type": "journal",
                        "source_id": entry.get("path") or "",
                        "linked_entities": entities[:5],
                        "linked_dossier_id": None,
                    }
                )
            if len(candidates) >= self.max_candidates_per_source:
                break
        return candidates

    def extract_from_action_item(self, recommendation: dict) -> list[dict]:
        action_item = (recommendation.get("metadata") or {}).get("action_item") or {}
        text = " ".join(
            filter(
                None,
                [
                    action_item.get("objective"),
                    action_item.get("next_step"),
                    action_item.get("review_notes"),
                ],
            )
        )
        if not text:
            return []
        return self.extract_from_journal(
            {"content": text, "path": recommendation.get("id") or "", "type": "recommendation"}
        )

    def extract_from_dossier(self, dossier: dict) -> list[dict]:
        explicit = dossier.get("assumptions") or []
        result = []
        for item in explicit[: self.max_candidates_per_source]:
            text = str(item).strip()
            if not text:
                continue
            result.append(
                {
                    "statement": text,
                    "confidence": 0.95,
                    "source_type": "dossier",
                    "source_id": dossier.get("dossier_id") or "",
                    "linked_entities": [],
                    "linked_dossier_id": dossier.get("dossier_id"),
                }
            )
        return result


class AssumptionSignalMatcher:
    def __init__(self, store: AssumptionStore):
        self.store = store

    def evaluate(self, assumption: dict, candidate_signals: list[dict]) -> list[dict]:
        assumption_text = str(assumption.get("statement") or "").lower()
        statement_terms = {
            term for term in re.findall(r"[a-z0-9]+", assumption_text) if len(term) > 3
        }
        linked_entities = {
            str(value).lower() for value in (assumption.get("linked_entities") or [])
        }

        evidence_rows: list[dict] = []
        for signal in candidate_signals:
            text = f"{signal.get('title', '')} {signal.get('summary', '')}".lower()
            overlap = sum(1 for term in statement_terms if term in text)
            entity_match = sum(1 for entity in linked_entities if entity and entity in text)
            score = 0.40 * min(1.0, overlap / max(1, len(statement_terms) or 1)) + 0.25 * min(
                1.0, entity_match
            )
            if score <= 0:
                continue
            if any(word in text for word in ("cancel", "decline", "cut", "freeze", "risk", "ban")):
                state = "invalidating" if score >= 0.45 else "informational"
            elif any(
                word in text
                for word in ("launch", "increase", "grow", "approve", "expand", "hiring")
            ):
                state = "confirming" if score >= 0.45 else "informational"
            else:
                state = "informational"
            evidence_rows.append(
                {
                    "evidence_kind": signal.get("kind") or signal.get("source_family") or "intel",
                    "evidence_state": state,
                    "source_ref": signal.get("url")
                    or signal.get("source_url")
                    or signal.get("id")
                    or "",
                    "excerpt": (signal.get("summary") or signal.get("title") or "")[:300],
                    "confidence": round(min(0.95, score + 0.25), 3),
                }
            )
        return evidence_rows

    def run_active(self, limit: int = 100) -> list[dict]:
        return self.store.list_active(limit=limit)


class MemoryAdapter:
    def __init__(self, fact_store):
        self.fact_store = fact_store

    def write_for_assumption(self, assumption: dict) -> StewardFact | None:
        status = assumption.get("status")
        if status not in {"confirmed", "invalidated", "resolved"}:
            return None
        text = assumption.get("latest_evidence_summary") or assumption.get("statement") or ""
        if not text:
            return None
        fact = StewardFact(
            id="",
            text=text[:300],
            category=FactCategory.PATTERN,
            source_type=FactSource.ASSUMPTION,
            source_id=assumption.get("id") or "",
            confidence=0.75,
        )
        return self.fact_store.add(fact)

"""User-scoped extraction receipts for journal post-create transparency."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import structlog

from db import wal_connect

logger = structlog.get_logger()

VALID_RECEIPT_STATUS = {"pending", "complete", "partial", "failed"}


def _now() -> str:
    return datetime.now().isoformat()


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


class ExtractionReceiptStore:
    """SQLite-backed receipt store keyed by journal entry path."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS extraction_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    entry_path TEXT NOT NULL UNIQUE,
                    entry_title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    thread_id TEXT,
                    thread_label TEXT,
                    thread_match_type TEXT,
                    payload_json TEXT NOT NULL,
                    warnings_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_extraction_receipts_entry_path ON extraction_receipts(entry_path)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_extraction_receipts_updated_at ON extraction_receipts(updated_at DESC)"
            )

    def upsert(self, receipt: dict) -> str:
        status = receipt.get("status") or "pending"
        if status not in VALID_RECEIPT_STATUS:
            raise ValueError(f"Invalid receipt status: {status}")

        entry_path = str(receipt["entry_path"])
        created_at = receipt.get("created_at") or _now()
        updated_at = _now()
        receipt_id = receipt.get("receipt_id") or uuid.uuid4().hex[:16]
        payload = receipt.get("payload") or {
            "themes": [],
            "memory_facts": [],
            "goal_candidates": [],
            "next_steps": [],
        }
        warnings = _as_list(receipt.get("warnings") or [])

        with wal_connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT receipt_id, created_at FROM extraction_receipts WHERE entry_path = ?",
                (entry_path,),
            ).fetchone()
            if existing:
                receipt_id = existing[0]
                created_at = existing[1]

            conn.execute(
                """
                INSERT INTO extraction_receipts (
                    receipt_id, entry_path, entry_title, status, thread_id, thread_label,
                    thread_match_type, payload_json, warnings_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(entry_path) DO UPDATE SET
                    entry_title = excluded.entry_title,
                    status = excluded.status,
                    thread_id = excluded.thread_id,
                    thread_label = excluded.thread_label,
                    thread_match_type = excluded.thread_match_type,
                    payload_json = excluded.payload_json,
                    warnings_json = excluded.warnings_json,
                    updated_at = excluded.updated_at
                """,
                (
                    receipt_id,
                    entry_path,
                    str(receipt.get("entry_title") or Path(entry_path).stem),
                    status,
                    receipt.get("thread_id"),
                    receipt.get("thread_label"),
                    receipt.get("thread_match_type"),
                    json.dumps(payload),
                    json.dumps(warnings),
                    created_at,
                    updated_at,
                ),
            )
        return receipt_id

    def get_by_entry(self, entry_path: str) -> dict | None:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM extraction_receipts WHERE entry_path = ?",
                (str(entry_path),),
            ).fetchone()
        if not row:
            return None
        try:
            payload = json.loads(row["payload_json"] or "{}")
            warnings = json.loads(row["warnings_json"] or "[]")
        except json.JSONDecodeError:
            logger.warning("receipt.malformed", entry_path=entry_path)
            return None
        return {
            "receipt_id": row["receipt_id"],
            "entry_path": row["entry_path"],
            "entry_title": row["entry_title"],
            "status": row["status"],
            "thread_id": row["thread_id"],
            "thread_label": row["thread_label"],
            "thread_match_type": row["thread_match_type"],
            "payload": {
                "themes": _as_list(payload.get("themes")),
                "memory_facts": _as_list(payload.get("memory_facts")),
                "goal_candidates": _as_list(payload.get("goal_candidates")),
                "next_steps": _as_list(payload.get("next_steps")),
            },
            "warnings": _as_list(warnings),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def delete_by_entry(self, entry_path: str) -> bool:
        with wal_connect(self.db_path) as conn:
            result = conn.execute(
                "DELETE FROM extraction_receipts WHERE entry_path = ?",
                (str(entry_path),),
            )
        return bool(result.rowcount)

    def list_recent(self, limit: int = 20) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT entry_path FROM extraction_receipts ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [receipt for row in rows if (receipt := self.get_by_entry(row["entry_path"]))]


class ReceiptBuilder:
    """Assemble pending and materialized extraction receipts."""

    def __init__(
        self,
        store: ExtractionReceiptStore,
        *,
        theme_goal_min_confidence: float = 0.7,
        max_themes: int = 3,
        max_goal_candidates: int = 2,
    ):
        self.store = store
        self.theme_goal_min_confidence = theme_goal_min_confidence
        self.max_themes = max_themes
        self.max_goal_candidates = max_goal_candidates

    def seed_pending(self, entry_path: str, entry_title: str) -> str:
        return self.store.upsert(
            {
                "entry_path": entry_path,
                "entry_title": entry_title,
                "status": "pending",
                "payload": {
                    "themes": [],
                    "memory_facts": [],
                    "goal_candidates": [],
                    "next_steps": [],
                },
                "warnings": [],
            }
        )

    def derive_theme_goal_candidates(
        self, entry: dict, memory_facts: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        content = str(entry.get("content") or "")
        title = str(entry.get("title") or "")
        tags = [str(tag).strip() for tag in (entry.get("tags") or []) if str(tag).strip()]
        text = f"{title}\n{content}".strip()
        lowered = text.lower()

        themes: list[dict] = []
        goal_candidates: list[dict] = []

        seed_phrases = [
            "career",
            "health",
            "finances",
            "leadership",
            "research",
            "product",
            "hiring",
            "regulatory",
        ]
        for phrase in seed_phrases:
            if phrase in lowered:
                snippet = next(
                    (line.strip() for line in text.splitlines() if phrase in line.lower()),
                    title or content[:120],
                )
                themes.append({"label": phrase, "confidence": 0.72, "snippet": snippet[:160]})

        for fact in memory_facts:
            text_value = str(fact.get("text") or "").strip()
            if not text_value:
                continue
            themes.append(
                {
                    "label": text_value[:48],
                    "confidence": min(0.9, float(fact.get("confidence") or 0.75)),
                    "snippet": text_value[:160],
                }
            )

        goal_triggers = ["plan to", "want to", "need to", "should ", "goal", "next step"]
        if any(trigger in lowered for trigger in goal_triggers):
            candidate_title = title or content.splitlines()[0] if content else "New goal"
            goal_candidates.append(
                {
                    "title": candidate_title[:80],
                    "confidence": 0.74,
                    "reason": "Planning language detected in the entry.",
                }
            )
        if tags:
            for tag in tags[: self.max_goal_candidates]:
                goal_candidates.append(
                    {
                        "title": f"Follow through on {tag}",
                        "confidence": 0.7,
                        "reason": "Journal tags suggest a concrete follow-up topic.",
                    }
                )

        seen_theme_labels: set[str] = set()
        filtered_themes = []
        for theme in sorted(
            themes, key=lambda item: float(item.get("confidence") or 0.0), reverse=True
        ):
            label = str(theme.get("label") or "").strip().lower()
            if not label or label in seen_theme_labels:
                continue
            if float(theme.get("confidence") or 0.0) < self.theme_goal_min_confidence:
                continue
            seen_theme_labels.add(label)
            filtered_themes.append(theme)
            if len(filtered_themes) >= self.max_themes:
                break

        seen_goal_titles: set[str] = set()
        filtered_goals = []
        for goal in sorted(
            goal_candidates, key=lambda item: float(item.get("confidence") or 0.0), reverse=True
        ):
            goal_title = str(goal.get("title") or "").strip().lower()
            if not goal_title or goal_title in seen_goal_titles:
                continue
            if float(goal.get("confidence") or 0.0) < self.theme_goal_min_confidence:
                continue
            seen_goal_titles.add(goal_title)
            filtered_goals.append(goal)
            if len(filtered_goals) >= self.max_goal_candidates:
                break

        return filtered_themes, filtered_goals

    def finalize(
        self,
        *,
        entry: dict,
        thread_match: dict | None,
        memory_facts: list[dict],
        theme_candidates: list[dict],
        goal_candidates: list[dict],
        warnings: list[str] | None = None,
    ) -> dict:
        warnings = _as_list(warnings or [])
        next_steps: list[dict] = []
        if thread_match and thread_match.get("thread_id"):
            next_steps.append(
                {
                    "kind": "view_thread",
                    "label": "View thread",
                    "enabled": True,
                    "target": thread_match["thread_id"],
                }
            )
        if goal_candidates:
            next_steps.append(
                {
                    "kind": "make_goal",
                    "label": "Turn into a goal",
                    "enabled": True,
                    "target": goal_candidates[0].get("title", ""),
                }
            )
        if theme_candidates:
            next_steps.append(
                {
                    "kind": "run_research",
                    "label": "Research this topic",
                    "enabled": True,
                    "target": theme_candidates[0].get("label", ""),
                }
            )
            next_steps.append(
                {
                    "kind": "start_dossier",
                    "label": "Start dossier",
                    "enabled": True,
                    "target": theme_candidates[0].get("label", ""),
                }
            )

        has_signal = bool(thread_match or memory_facts or theme_candidates or goal_candidates)
        status = (
            "complete" if has_signal and not warnings else "partial" if has_signal else "failed"
        )
        if not has_signal and not warnings:
            status = "partial"

        receipt = {
            "entry_path": entry["path"],
            "entry_title": entry.get("title") or Path(entry["path"]).stem,
            "status": status,
            "thread_id": (thread_match or {}).get("thread_id"),
            "thread_label": (thread_match or {}).get("thread_label"),
            "thread_match_type": (thread_match or {}).get("match_type"),
            "payload": {
                "themes": _as_list(theme_candidates),
                "memory_facts": _as_list(memory_facts),
                "goal_candidates": _as_list(goal_candidates),
                "next_steps": next_steps,
            },
            "warnings": warnings,
        }
        self.store.upsert(receipt)
        return self.store.get_by_entry(entry["path"]) or receipt

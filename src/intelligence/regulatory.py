"""Regulatory watch resolvers, store, and rules-based classifier."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from db import wal_connect


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:80] or "target"


class RegulatoryWatchResolver:
    def from_watchlist_items(self, items: list[dict]) -> list[dict]:
        targets = []
        for item in items:
            label = str(item.get("label") or "").strip()
            tags = [str(tag).strip() for tag in (item.get("tags") or []) if str(tag).strip()]
            if not label or not (tags or item.get("kind") in {"regulation", "sector", "theme"}):
                continue
            explicit_topics = [
                str(value).strip() for value in (item.get("topics") or []) if str(value).strip()
            ]
            explicit_geographies = [
                str(value).strip()
                for value in (item.get("geographies") or [])
                if str(value).strip()
            ]
            targets.append(
                {
                    "target_key": _slug(label),
                    "label": label,
                    "topics": explicit_topics or [label, *tags],
                    "geographies": explicit_geographies
                    or [
                        str(value).strip()
                        for value in (item.get("source_preferences") or [])
                        if str(value).strip()
                    ],
                    "priority": {"low": 1, "medium": 2, "high": 3}.get(item.get("priority"), 2),
                    "watchlist_id": item.get("id"),
                }
            )
        return targets


class RegulatoryAlertStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS regulatory_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_key TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    source_family TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    relevance REAL NOT NULL,
                    effective_date TEXT,
                    source_url TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    dedup_hash TEXT NOT NULL UNIQUE,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )

    def save_many(self, alerts: list[dict]) -> int:
        saved = 0
        with wal_connect(self.db_path) as conn:
            for alert in alerts:
                if alert.get("urgency") not in {"high", "medium", "low"}:
                    continue
                dedup_hash = (
                    alert.get("dedup_hash")
                    or hashlib.sha256(
                        f"{alert.get('target_key')}|{alert.get('change_type')}|{alert.get('title')}|{alert.get('source_url')}".encode()
                    ).hexdigest()[:32]
                )
                conn.execute(
                    """
                    INSERT OR IGNORE INTO regulatory_alerts (
                        target_key, title, summary, source_family, change_type, urgency,
                        relevance, effective_date, source_url, observed_at, dedup_hash, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert.get("target_key") or "",
                        alert.get("title") or "",
                        alert.get("summary") or "",
                        alert.get("source_family") or "generic",
                        alert.get("change_type") or "guidance",
                        alert.get("urgency") or "low",
                        float(alert.get("relevance") or 0.0),
                        alert.get("effective_date"),
                        alert.get("source_url") or "",
                        alert.get("observed_at") or datetime.now().isoformat(),
                        dedup_hash,
                        json.dumps(alert.get("metadata") or {}),
                    ),
                )
                saved += 1
        return saved

    def get_recent(self, since: datetime, limit: int = 100) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM regulatory_alerts WHERE observed_at >= ? ORDER BY relevance DESC, observed_at DESC LIMIT ?",
                (since.isoformat(), limit),
            ).fetchall()
        return [{**dict(row), "metadata": json.loads(row["metadata_json"] or "{}")} for row in rows]


class RegulatoryClassifier:
    def classify(self, raw_item: dict, target: dict) -> dict | None:
        text = f"{raw_item.get('title', '')} {raw_item.get('summary', '')}".lower()
        topics = [
            str(topic).lower() for topic in (target.get("topics") or []) if str(topic).strip()
        ]
        keyword_hits = sum(1 for topic in topics if topic and topic in text)
        if not keyword_hits:
            return None
        geography_hits = sum(
            1
            for geography in (target.get("geographies") or [])
            if str(geography).strip().lower() in text
        )
        priority = float(target.get("priority") or 1)
        relevance = min(
            1.0,
            0.45 * min(1.0, keyword_hits / max(1, len(topics) or 1))
            + 0.30 * min(1.0, geography_hits)
            + 0.25 * min(1.0, priority / 3.0),
        )
        if relevance < 0.35:
            return None

        if any(
            keyword in text
            for keyword in ("enforcement", "effective immediately", "final rule", "finalized")
        ):
            change_type = "finalized"
            urgency = "high"
        elif any(keyword in text for keyword in ("proposed", "consultation", "draft")):
            change_type = "proposed"
            urgency = "medium"
        elif any(keyword in text for keyword in ("standard", "specification")):
            change_type = "standard"
            urgency = "medium"
        else:
            change_type = "guidance"
            urgency = "low" if relevance < 0.6 else "medium"

        return {
            "target_key": target.get("target_key") or _slug(target.get("label") or ""),
            "title": raw_item.get("title") or target.get("label") or "Regulatory update",
            "summary": raw_item.get("summary") or raw_item.get("title") or "",
            "source_family": raw_item.get("source") or "generic",
            "change_type": change_type,
            "urgency": urgency,
            "relevance": round(relevance, 3),
            "effective_date": raw_item.get("effective_date"),
            "source_url": raw_item.get("url") or "",
            "observed_at": raw_item.get("published")
            or raw_item.get("observed_at")
            or datetime.now().isoformat(),
            "metadata": {"target_label": target.get("label")},
        }

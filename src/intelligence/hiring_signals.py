"""Hiring-signal stores and detector helpers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from db import wal_connect


class HiringSignalStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hiring_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_key TEXT NOT NULL,
                    entity_label TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    strength REAL NOT NULL,
                    source_url TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    dedup_hash TEXT NOT NULL UNIQUE,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hiring_baselines (
                    entity_key TEXT PRIMARY KEY,
                    snapshot_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def save_many(self, signals: list[dict]) -> int:
        saved = 0
        with wal_connect(self.db_path) as conn:
            for signal in signals:
                dedup_hash = (
                    signal.get("dedup_hash")
                    or hashlib.sha256(
                        f"{signal.get('entity_key')}|{signal.get('signal_type')}|{signal.get('title')}|{signal.get('source_url')}".encode()
                    ).hexdigest()[:32]
                )
                conn.execute(
                    """
                    INSERT OR IGNORE INTO hiring_signals (
                        entity_key, entity_label, signal_type, title, summary, strength,
                        source_url, observed_at, dedup_hash, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        signal.get("entity_key") or "",
                        signal.get("entity_label") or signal.get("entity_key") or "",
                        signal.get("signal_type") or "jobs",
                        signal.get("title") or "",
                        signal.get("summary") or "",
                        float(signal.get("strength") or 0.0),
                        signal.get("source_url") or "",
                        signal.get("observed_at") or datetime.now().isoformat(),
                        dedup_hash,
                        json.dumps(signal.get("metadata") or {}),
                    ),
                )
                if conn.execute("SELECT changes()").fetchone()[0]:
                    saved += 1
        return saved

    def get_recent(self, entity_key: str | None = None, limit: int = 50) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if entity_key:
                rows = conn.execute(
                    "SELECT * FROM hiring_signals WHERE entity_key = ? ORDER BY observed_at DESC LIMIT ?",
                    (entity_key, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM hiring_signals ORDER BY observed_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [{**dict(row), "metadata": json.loads(row["metadata_json"] or "{}")} for row in rows]


class HiringBaselineTracker:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        HiringSignalStore(self.db_path)

    def update(self, entity_key: str, snapshot: dict) -> dict:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO hiring_baselines (entity_key, snapshot_json, updated_at) VALUES (?, ?, ?) ON CONFLICT(entity_key) DO UPDATE SET snapshot_json = excluded.snapshot_json, updated_at = excluded.updated_at",
                (entity_key, json.dumps(snapshot or {}), datetime.now().isoformat()),
            )
        return self.get(entity_key) or {"entity_key": entity_key, "snapshot": snapshot}

    def get(self, entity_key: str) -> dict | None:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT entity_key, snapshot_json, updated_at FROM hiring_baselines WHERE entity_key = ?",
                (entity_key,),
            ).fetchone()
        if not row:
            return None
        return {
            "entity_key": row["entity_key"],
            "snapshot": json.loads(row["snapshot_json"] or "{}"),
            "updated_at": row["updated_at"],
        }


class HiringSignalDetector:
    def detect(self, entity: dict, snapshot: dict, baseline: dict | None) -> list[dict]:
        baseline_snapshot = (baseline or {}).get("snapshot") or {}
        jobs_now = int(snapshot.get("open_roles") or 0)
        jobs_before = int(baseline_snapshot.get("open_roles") or 0)
        delta = jobs_now - jobs_before
        if delta == 0 and jobs_now == 0:
            return []
        summary = f"{entity.get('label') or entity.get('entity_label') or entity.get('entity_key')} now lists {jobs_now} open roles"
        if delta > 0:
            summary += f", up by {delta}."
        elif delta < 0:
            summary += f", down by {abs(delta)}."
        else:
            summary += "."
        return [
            {
                "entity_key": entity.get("company_key") or entity.get("entity_key") or "",
                "entity_label": entity.get("label")
                or entity.get("entity_label")
                or entity.get("company_key")
                or "",
                "signal_type": "hiring_delta" if delta else "hiring_snapshot",
                "title": f"Hiring activity at {entity.get('label') or entity.get('entity_label') or entity.get('entity_key')}",
                "summary": summary,
                "strength": min(1.0, abs(delta) / 10.0 if delta else jobs_now / 10.0),
                "source_url": snapshot.get("source_url") or "",
                "observed_at": snapshot.get("observed_at") or datetime.now().isoformat(),
                "metadata": {"open_roles": jobs_now, "delta": delta},
            }
        ]


class HiringSignalAnalyzer:
    _KEYWORDS = {
        "hiring_spike": ("hiring spree", "rapid hiring", "doubling headcount", "expanding team"),
        "hiring_signal": ("hiring", "open roles", "job openings", "recruiting", "careers"),
        "geo_expansion": ("remote in", "new office", "expanding in", "hiring in"),
    }

    def _match_terms(self, entity: dict) -> list[str]:
        terms = [
            entity.get("label") or entity.get("entity_label") or entity.get("entity_key") or ""
        ]
        terms.extend(entity.get("aliases") or [])
        seen: set[str] = set()
        result: list[str] = []
        for term in terms:
            cleaned = str(term).strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                result.append(cleaned)
        return result

    def analyze_mentions(
        self, entities: list[dict], intel_items: list[dict] | None = None
    ) -> list[dict]:
        if not intel_items:
            return []

        signals: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for entity in entities:
            terms = self._match_terms(entity)
            for intel_item in intel_items:
                text = f"{intel_item.get('title', '')} {intel_item.get('summary', '')}".lower()
                if not any(term.lower() in text for term in terms):
                    continue

                signal_type = None
                for candidate, keywords in self._KEYWORDS.items():
                    if any(keyword in text for keyword in keywords):
                        signal_type = candidate
                        break
                if signal_type is None:
                    continue

                dedupe_key = (
                    entity.get("company_key") or entity.get("entity_key") or "",
                    intel_item.get("url") or "",
                )
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                strength = (
                    0.8
                    if signal_type == "hiring_spike"
                    else 0.65
                    if signal_type == "geo_expansion"
                    else 0.55
                )
                priority = float(entity.get("priority") or 2) / 3.0
                signals.append(
                    {
                        "entity_key": entity.get("company_key") or entity.get("entity_key") or "",
                        "entity_label": entity.get("label")
                        or entity.get("entity_label")
                        or entity.get("entity_key")
                        or "",
                        "signal_type": signal_type,
                        "title": f"Hiring signal at {entity.get('label') or entity.get('entity_label') or entity.get('entity_key')}",
                        "summary": intel_item.get("summary") or intel_item.get("title") or "",
                        "strength": round(min(1.0, strength + 0.2 * priority), 3),
                        "source_url": intel_item.get("url") or "",
                        "observed_at": intel_item.get("published")
                        or intel_item.get("scraped_at")
                        or datetime.now().isoformat(),
                        "metadata": {
                            "matched_terms": terms,
                            "source": intel_item.get("source") or "generic",
                        },
                    }
                )
        return signals

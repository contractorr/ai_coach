"""Company watch resolvers and stores for entity-centric monitoring."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from db import wal_connect


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:80] or "company"


class WatchedCompanyResolver:
    def from_watchlist_items(self, items: list[dict]) -> list[dict]:
        companies = []
        for item in items:
            if item.get("kind") != "company":
                continue
            label = str(item.get("label") or "").strip()
            if not label:
                continue
            aliases = [value.strip() for value in (item.get("aliases") or []) if str(value).strip()]
            companies.append(
                {
                    "company_id": f"cmp_{_slug(label)}",
                    "company_key": _slug(label),
                    "label": label,
                    "aliases": aliases,
                    "domain": item.get("domain"),
                    "github_org": item.get("github_org") or (aliases[0] if aliases else None),
                    "ticker": item.get("ticker"),
                    "watchlist_id": item.get("id"),
                    "priority": {"low": 1, "medium": 2, "high": 3}.get(item.get("priority"), 2),
                }
            )
        return companies


class CompanyMovementStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS company_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_key TEXT NOT NULL,
                    company_label TEXT NOT NULL,
                    movement_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    significance REAL NOT NULL,
                    source_url TEXT NOT NULL,
                    source_family TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    dedup_hash TEXT NOT NULL UNIQUE,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_company_movements_company ON company_movements(company_key, observed_at DESC)"
            )

    def save_many(self, movements: list[dict]) -> int:
        saved = 0
        with wal_connect(self.db_path) as conn:
            for movement in movements:
                try:
                    company_key = movement["company_key"]
                    title = movement["title"]
                    summary = movement["summary"]
                    movement_type = movement.get("movement_type") or "product"
                    dedup_hash = (
                        movement.get("dedup_hash")
                        or hashlib.sha256(
                            f"{company_key}|{movement_type}|{title}|{movement.get('source_url', '')}".encode()
                        ).hexdigest()[:32]
                    )
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO company_movements (
                            company_key, company_label, movement_type, title, summary, significance,
                            source_url, source_family, observed_at, dedup_hash, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            company_key,
                            movement.get("company_label") or company_key,
                            movement_type,
                            title,
                            summary,
                            float(movement.get("significance") or 0.0),
                            movement.get("source_url") or "",
                            movement.get("source_family") or "generic",
                            movement.get("observed_at") or datetime.now().isoformat(),
                            dedup_hash,
                            json.dumps(movement.get("metadata") or {}),
                        ),
                    )
                    saved += 1
                except KeyError:
                    continue
        return saved

    def _fetch(self, query: str, params: tuple) -> list[dict]:
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        return [
            {
                **dict(row),
                "metadata": json.loads(row["metadata_json"] or "{}"),
            }
            for row in rows
        ]

    def get_recent_for_company(self, company_key: str, limit: int = 20) -> list[dict]:
        return self._fetch(
            "SELECT * FROM company_movements WHERE company_key = ? ORDER BY observed_at DESC LIMIT ?",
            (company_key, limit),
        )

    def get_since(self, since: datetime, limit: int = 200) -> list[dict]:
        return self._fetch(
            "SELECT * FROM company_movements WHERE observed_at >= ? ORDER BY significance DESC, observed_at DESC LIMIT ?",
            (since.isoformat(), limit),
        )


class CompanyMovementCollector:
    async def collect(self, companies: list[dict]) -> list[dict]:
        return []

    def rank(self, events: list[dict]) -> list[dict]:
        return sorted(
            events,
            key=lambda item: (
                float(item.get("significance") or 0.0),
                item.get("observed_at") or "",
            ),
            reverse=True,
        )

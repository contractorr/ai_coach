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
                    if conn.execute("SELECT changes()").fetchone()[0]:
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
    _MOVEMENT_KEYWORDS = {
        "pricing": ("pricing", "price", "plan", "subscription"),
        "partnership": ("partnership", "partnered", "collaboration", "integrat"),
        "leadership": ("ceo", "cto", "chief", "leadership", "appointed", "resigned"),
        "roadmap": ("roadmap", "coming soon", "planned", "preview", "beta"),
        "github": ("github", "release", "repo", "repository", "open source"),
        "filing": ("filing", "10-k", "10-q", "sec", "annual report"),
        "product": ("launch", "launched", "release", "released", "product", "feature"),
    }

    def _match_terms(self, company: dict) -> list[str]:
        terms = [company.get("label") or ""]
        terms.extend(company.get("aliases") or [])
        for field in ("domain", "github_org", "ticker"):
            value = str(company.get(field) or "").strip()
            if value:
                terms.append(value)
        seen: set[str] = set()
        matched: list[str] = []
        for term in terms:
            cleaned = term.strip()
            key = cleaned.lower()
            if cleaned and key not in seen:
                seen.add(key)
                matched.append(cleaned)
        return matched

    def _matches_item(self, company: dict, intel_item: dict) -> list[str]:
        text = f"{intel_item.get('title', '')} {intel_item.get('summary', '')}".lower()
        matches = []
        for term in self._match_terms(company):
            lowered = term.lower()
            if lowered and lowered in text:
                matches.append(term)
        return matches

    def _movement_type(self, intel_item: dict) -> str:
        text = f"{intel_item.get('title', '')} {intel_item.get('summary', '')}".lower()
        for movement_type, keywords in self._MOVEMENT_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return movement_type
        return "product"

    def _significance(self, company: dict, intel_item: dict, movement_type: str) -> float:
        priority_score = float(company.get("priority") or 2) / 3.0
        source = str(intel_item.get("source") or "").lower()
        source_score = (
            0.85
            if source in {"crunchbase", "google_patents"}
            else 0.7
            if source.startswith("rss")
            else 0.6
        )
        type_score = {
            "leadership": 0.9,
            "pricing": 0.85,
            "partnership": 0.8,
            "filing": 0.8,
            "roadmap": 0.7,
            "github": 0.65,
            "product": 0.75,
        }.get(movement_type, 0.7)
        return round(min(1.0, 0.45 * priority_score + 0.3 * source_score + 0.25 * type_score), 3)

    def collect(self, companies: list[dict], intel_items: list[dict] | None = None) -> list[dict]:
        if not intel_items:
            return []

        seen: set[tuple[str, str]] = set()
        events: list[dict] = []
        for company in companies:
            for intel_item in intel_items:
                matched_terms = self._matches_item(company, intel_item)
                if not matched_terms:
                    continue
                movement_type = self._movement_type(intel_item)
                dedupe_key = (company.get("company_key") or "", intel_item.get("url") or "")
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                events.append(
                    {
                        "company_key": company.get("company_key")
                        or _slug(company.get("label") or ""),
                        "company_label": company.get("label") or company.get("company_key") or "",
                        "movement_type": movement_type,
                        "title": intel_item.get("title") or "Company movement detected",
                        "summary": intel_item.get("summary") or intel_item.get("title") or "",
                        "significance": self._significance(company, intel_item, movement_type),
                        "source_url": intel_item.get("url") or "",
                        "source_family": intel_item.get("source") or "generic",
                        "observed_at": intel_item.get("published")
                        or intel_item.get("scraped_at")
                        or datetime.now().isoformat(),
                        "metadata": {
                            "matched_terms": matched_terms,
                            "watchlist_id": company.get("watchlist_id"),
                        },
                    }
                )
        return self.rank(events)

    def rank(self, events: list[dict]) -> list[dict]:
        return sorted(
            events,
            key=lambda item: (
                float(item.get("significance") or 0.0),
                item.get("observed_at") or "",
            ),
            reverse=True,
        )

"""Return-brief builder for users returning after a gap in activity."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from user_state_store import get_default_db_path


class ReturnBriefBuilder:
    """Build a structured briefing when user inactivity crosses a threshold."""

    def __init__(
        self,
        *,
        absence_hours: int = 72,
        max_section_items: int = 3,
        users_db_path=None,
        data_provider=None,
    ):
        self.absence_hours = absence_hours
        self.max_section_items = max_section_items
        self.users_db_path = users_db_path or get_default_db_path()
        self.data_provider = data_provider

    def get_last_active_at(self, user_id: str) -> datetime | None:
        conn = sqlite3.connect(self.users_db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = []
            for query in (
                "SELECT MAX(created_at) AS ts FROM engagement_events WHERE user_id = ?",
                "SELECT MAX(created_at) AS ts FROM usage_events WHERE user_id = ?",
                "SELECT MAX(updated_at) AS ts FROM conversations WHERE user_id = ?",
            ):
                row = conn.execute(query, (user_id,)).fetchone()
                if row and row["ts"]:
                    rows.append(str(row["ts"]))
        finally:
            conn.close()
        if not rows:
            return None
        parsed: list[datetime] = []
        for value in rows:
            try:
                parsed.append(
                    datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
                )
            except ValueError:
                continue
        return max(parsed) if parsed else None

    def build(self, user_id: str) -> dict | None:
        last_active = self.get_last_active_at(user_id)
        if not last_active:
            return None
        now = datetime.now()
        absent_hours = int((now - last_active).total_seconds() / 3600)
        if absent_hours < self.absence_hours:
            return None

        provider = self.data_provider(user_id) if callable(self.data_provider) else {}
        sections: list[dict] = []
        next_steps: list[dict] = []

        for kind, label in (
            ("intel", "intel_matches"),
            ("threads", "threads"),
            ("dossiers", "dossiers"),
            ("goals", "stale_goals"),
        ):
            items = list(provider.get(label) or [])[: self.max_section_items]
            if items:
                sections.append({"kind": kind, "items": items})
                first = items[0]
                next_steps.append(
                    {
                        "kind": kind,
                        "label": f"Review {kind}",
                        "target": first.get("id") or first.get("title") or first.get("path") or "",
                    }
                )

        if not sections:
            sections.append(
                {
                    "kind": "summary",
                    "items": [
                        {
                            "title": "No major changes",
                            "detail": "You were away, but nothing major changed in tracked areas.",
                        }
                    ],
                }
            )

        part_summaries = []
        for section in sections:
            if section["kind"] == "summary":
                continue
            part_summaries.append(f"{len(section['items'])} {section['kind']}")
        summary = (
            f"While you were away, {', '.join(part_summaries)} changed."
            if part_summaries
            else "While you were away, nothing major changed."
        )
        return {
            "active": True,
            "absent_hours": absent_hours,
            "summary": summary,
            "sections": sections,
            "next_steps": next_steps[: self.max_section_items],
            "generated_at": now.isoformat(),
        }


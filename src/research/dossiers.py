"""Persistent research dossiers backed by journal entries."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import structlog

import frontmatter
from journal.storage import JournalStorage

logger = structlog.get_logger()

DOSSIER_KIND = "dossier"
UPDATE_KIND = "dossier_update"


def _normalize_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _parse_dt(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.min


class ResearchDossierStore:
    """Manages long-lived research dossiers inside the journal."""

    def __init__(self, journal_storage: JournalStorage):
        self.journal = journal_storage

    def create_dossier(
        self,
        topic: str,
        scope: str = "",
        core_questions: list[str] | None = None,
        assumptions: list[str] | None = None,
        related_goals: list[str] | None = None,
        tracked_subtopics: list[str] | None = None,
        open_questions: list[str] | None = None,
        status: str = "active",
    ) -> dict:
        dossier_id = uuid4().hex[:12]
        metadata = {
            "research_kind": DOSSIER_KIND,
            "dossier_id": dossier_id,
            "topic": topic,
            "scope": scope.strip(),
            "status": status,
            "core_questions": _normalize_list(core_questions),
            "assumptions": _normalize_list(assumptions),
            "related_goals": _normalize_list(related_goals),
            "tracked_subtopics": _normalize_list(tracked_subtopics),
            "open_questions": _normalize_list(open_questions),
            "update_count": 0,
            "latest_change_summary": "",
            "last_updated": None,
        }
        content = self._render_dossier_content(metadata)
        path = self.journal.create(
            content=content,
            entry_type="research",
            title=f"Research Dossier: {topic}",
            tags=["research", "dossier", status],
            metadata=metadata,
        )
        return self.get_dossier(dossier_id) or {"dossier_id": dossier_id, "path": path}

    def list_dossiers(self, include_archived: bool = False, limit: int = 50) -> list[dict]:
        dossiers = []
        for path, post in self._iter_research_posts(kind=DOSSIER_KIND):
            dossier = self._build_dossier_record(path, post)
            if not include_archived and dossier["status"] == "archived":
                continue
            dossiers.append(dossier)
            if len(dossiers) >= limit:
                break
        return dossiers

    def get_active_dossiers(self, limit: int = 50) -> list[dict]:
        return self.list_dossiers(include_archived=False, limit=limit)

    def get_dossier(self, dossier_id: str) -> dict | None:
        for path, post in self._iter_research_posts(kind=DOSSIER_KIND):
            if post.get("dossier_id") == dossier_id:
                dossier = self._build_dossier_record(path, post)
                dossier["updates"] = self.list_updates(dossier_id)
                if dossier["updates"]:
                    latest = dossier["updates"][0]
                    dossier["last_updated"] = latest.get("created") or dossier.get("last_updated")
                    dossier["latest_change_summary"] = latest.get("change_summary") or dossier.get(
                        "latest_change_summary"
                    )
                    dossier["update_count"] = max(
                        int(dossier.get("update_count", 0) or 0),
                        len(dossier["updates"]),
                    )
                return dossier
        return None

    def list_updates(self, dossier_id: str, limit: int = 20) -> list[dict]:
        updates = []
        for path, post in self._iter_research_posts(kind=UPDATE_KIND):
            if post.get("dossier_id") != dossier_id:
                continue
            updates.append(self._build_update_record(path, post))
            if len(updates) >= limit:
                break
        return updates

    def append_update(self, dossier_id: str, content: str, metadata: dict) -> dict:
        dossier = self.get_dossier(dossier_id)
        if not dossier:
            raise ValueError(f"Unknown dossier: {dossier_id}")

        update_meta = {
            "research_kind": UPDATE_KIND,
            "dossier_id": dossier_id,
            "topic": dossier["topic"],
            "change_summary": metadata.get("change_summary", ""),
            "confidence": metadata.get("confidence", "Medium"),
            "recommended_actions": _normalize_list(metadata.get("recommended_actions")),
            "open_questions": _normalize_list(metadata.get("open_questions")),
            "citations": _normalize_list(metadata.get("citations")),
            "source_urls": _normalize_list(metadata.get("source_urls")),
            "source_titles": _normalize_list(metadata.get("source_titles")),
            "sources_count": int(metadata.get("sources_count", 0) or 0),
            "run_source": metadata.get("run_source", "manual"),
        }
        path = self.journal.create(
            content=content,
            entry_type="research",
            title=f"Research Update: {dossier['topic']}",
            tags=["research", "dossier-update", update_meta["run_source"]],
            metadata=update_meta,
        )

        updates = self.list_updates(dossier_id, limit=500)
        latest = updates[0] if updates else None
        self.update_dossier_metadata(
            dossier_id,
            latest_change_summary=(latest or {}).get("change_summary", ""),
            last_updated=(latest or {}).get("created"),
            update_count=len(updates),
            open_questions=(latest or {}).get("open_questions")
            or dossier.get("open_questions", []),
        )
        return self._build_update_record(path, frontmatter.load(path))

    def update_dossier_metadata(self, dossier_id: str, **fields) -> dict | None:
        dossier = self.get_dossier(dossier_id)
        if not dossier:
            return None
        metadata = {
            "research_kind": DOSSIER_KIND,
            "dossier_id": dossier["dossier_id"],
            "topic": fields.get("topic", dossier["topic"]),
            "scope": fields.get("scope", dossier.get("scope", "")),
            "status": fields.get("status", dossier.get("status", "active")),
            "core_questions": _normalize_list(
                fields.get("core_questions", dossier.get("core_questions", []))
            ),
            "assumptions": _normalize_list(
                fields.get("assumptions", dossier.get("assumptions", []))
            ),
            "related_goals": _normalize_list(
                fields.get("related_goals", dossier.get("related_goals", []))
            ),
            "tracked_subtopics": _normalize_list(
                fields.get("tracked_subtopics", dossier.get("tracked_subtopics", []))
            ),
            "open_questions": _normalize_list(
                fields.get("open_questions", dossier.get("open_questions", []))
            ),
            "update_count": int(fields.get("update_count", dossier.get("update_count", 0)) or 0),
            "latest_change_summary": fields.get(
                "latest_change_summary", dossier.get("latest_change_summary", "")
            ),
            "last_updated": fields.get("last_updated", dossier.get("last_updated")),
        }
        tags = ["research", "dossier", metadata["status"]]
        content = self._render_dossier_content(metadata)
        self.journal.update(dossier["path"], content=content, metadata={**metadata, "tags": tags})
        return self.get_dossier(dossier_id)

    def _iter_research_posts(self, kind: str | None = None):
        posts = []
        for path in self.journal.journal_dir.glob("*.md"):
            try:
                post = frontmatter.load(path)
            except (OSError, ValueError) as exc:
                logger.warning("research_dossier_load_failed", path=str(path), error=str(exc))
                continue
            if post.get("type") != "research":
                continue
            if kind and post.get("research_kind") != kind:
                continue
            posts.append((path, post))
        posts.sort(
            key=lambda item: _parse_dt(item[1].get("last_updated") or item[1].get("created")),
            reverse=True,
        )
        return posts

    def _build_dossier_record(self, path: Path, post) -> dict:
        return {
            "path": path,
            "title": post.get("title", path.stem),
            "dossier_id": post.get("dossier_id"),
            "topic": post.get("topic", ""),
            "scope": post.get("scope", ""),
            "status": post.get("status", "active"),
            "core_questions": _normalize_list(post.get("core_questions")),
            "assumptions": _normalize_list(post.get("assumptions")),
            "related_goals": _normalize_list(post.get("related_goals")),
            "tracked_subtopics": _normalize_list(post.get("tracked_subtopics")),
            "open_questions": _normalize_list(post.get("open_questions")),
            "created": post.get("created"),
            "updated": post.get("updated"),
            "last_updated": post.get("last_updated") or post.get("updated") or post.get("created"),
            "update_count": int(post.get("update_count", 0) or 0),
            "latest_change_summary": post.get("latest_change_summary", ""),
            "content": post.content,
        }

    def _build_update_record(self, path: Path, post) -> dict:
        return {
            "path": path,
            "title": post.get("title", path.stem),
            "dossier_id": post.get("dossier_id"),
            "topic": post.get("topic", ""),
            "created": post.get("created"),
            "updated": post.get("updated"),
            "change_summary": post.get("change_summary", ""),
            "confidence": post.get("confidence", "Medium"),
            "recommended_actions": _normalize_list(post.get("recommended_actions")),
            "open_questions": _normalize_list(post.get("open_questions")),
            "citations": _normalize_list(post.get("citations")),
            "source_urls": _normalize_list(post.get("source_urls")),
            "source_titles": _normalize_list(post.get("source_titles")),
            "sources_count": int(post.get("sources_count", 0) or 0),
            "run_source": post.get("run_source", "manual"),
            "content": post.content,
        }

    def _render_dossier_content(self, metadata: dict) -> str:
        lines = [f"# {metadata.get('topic', 'Research Dossier')}", ""]

        if metadata.get("scope"):
            lines.extend(["## Scope", metadata["scope"], ""])

        lines.extend(
            [
                "## Latest Change",
                metadata.get("latest_change_summary") or "No updates yet.",
                "",
                "## Status",
                metadata.get("status", "active"),
                "",
            ]
        )

        sections = [
            ("Core Questions", metadata.get("core_questions", [])),
            ("Assumptions", metadata.get("assumptions", [])),
            ("Related Goals", metadata.get("related_goals", [])),
            ("Tracked Subtopics", metadata.get("tracked_subtopics", [])),
            ("Open Questions", metadata.get("open_questions", [])),
        ]
        for heading, items in sections:
            lines.append(f"## {heading}")
            if items:
                lines.extend(f"- {item}" for item in items)
            else:
                lines.append("- None recorded")
            lines.append("")

        last_updated = metadata.get("last_updated") or "Not updated yet"
        lines.extend(
            [
                "## Timeline",
                f"- Last updated: {last_updated}",
                f"- Updates recorded: {metadata.get('update_count', 0)}",
            ]
        )
        return "\n".join(lines).strip() + "\n"

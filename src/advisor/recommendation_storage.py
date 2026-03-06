"""Markdown-based persistence for recommendations."""

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import frontmatter

from shared_types import ActionItemStatus, RecommendationStatus


@dataclass
class Recommendation:
    """A single recommendation."""

    id: Optional[str] = None
    category: str = ""
    title: str = ""
    description: str = ""
    rationale: str = ""
    score: float = 0.0
    created_at: Optional[str] = None
    status: str = RecommendationStatus.SUGGESTED
    metadata: Optional[dict] = None
    embedding_hash: Optional[str] = None


@dataclass
class RecommendationAction:
    """Tracked execution artifact attached to a recommendation."""

    recommendation_id: str
    recommendation_title: str
    category: str
    score: float
    recommendation_status: str
    created_at: Optional[str] = None
    action_item: dict[str, Any] = field(default_factory=dict)


ACTION_ITEM_EFFORTS = {"small", "medium", "large"}
ACTION_ITEM_DUE_WINDOWS = {"today", "this_week", "later"}
ACTION_ITEM_STATUSES = {status.value for status in ActionItemStatus}
EFFORT_POINTS = {"small": 1, "medium": 2, "large": 3}
ACTION_ITEM_OUTCOME_WEIGHTS = {
    ActionItemStatus.ACCEPTED.value: 0.25,
    ActionItemStatus.DEFERRED.value: -0.25,
    ActionItemStatus.BLOCKED.value: -0.5,
    ActionItemStatus.COMPLETED.value: 1.0,
    ActionItemStatus.ABANDONED.value: -1.0,
}
_BULLET_PREFIX_RE = re.compile(r"^(?:[-*+]\s+|\d+[.)]\s+)")


def _slug(text: str) -> str:
    """Generate filename-safe slug."""
    s = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"[\s_]+", "-", s)[:40]


def _normalize_effort(value: Optional[str]) -> str:
    if value in ACTION_ITEM_EFFORTS:
        return str(value)
    return "medium"


def _normalize_due_window(value: Optional[str]) -> str:
    if value in ACTION_ITEM_DUE_WINDOWS:
        return str(value)
    return "this_week"


def _normalize_action_status(value: Optional[str]) -> str:
    if value in ACTION_ITEM_STATUSES:
        return str(value)
    return ActionItemStatus.ACCEPTED.value


def _clean_markdown_line(line: str) -> str:
    cleaned = line.strip()
    if not cleaned or cleaned.startswith("#"):
        return ""
    cleaned = _BULLET_PREFIX_RE.sub("", cleaned).strip()
    return cleaned


def _first_meaningful_line(*chunks: Optional[str]) -> str:
    for chunk in chunks:
        if not chunk:
            continue
        for raw_line in chunk.splitlines():
            line = _clean_markdown_line(raw_line)
            if line:
                return line
    return ""


def _extract_success_criteria(action_plan: Optional[str], rationale: str, description: str) -> str:
    if action_plan:
        lines = [_clean_markdown_line(line) for line in action_plan.splitlines()]
        meaningful = [line for line in lines if line]
        if meaningful:
            return meaningful[-1]
    fallback = _first_meaningful_line(rationale, description)
    return fallback or "Make measurable progress against this recommendation."


def _derive_action_item(
    rec: Recommendation,
    goal_path: Optional[str] = None,
    goal_title: Optional[str] = None,
    objective: Optional[str] = None,
    next_step: Optional[str] = None,
    effort: Optional[str] = None,
    due_window: Optional[str] = None,
    blockers: Optional[list[str]] = None,
    success_criteria: Optional[str] = None,
) -> dict[str, Any]:
    action_plan = (rec.metadata or {}).get("action_plan") if rec.metadata else None
    derived_next_step = next_step or _first_meaningful_line(action_plan, rec.description, rec.rationale)
    if not derived_next_step:
        derived_next_step = "Choose the first concrete step and schedule time for it."

    cleaned_blockers = [item.strip() for item in (blockers or []) if item and item.strip()]
    now = datetime.now().isoformat()
    return {
        "objective": (objective or rec.title or "Untitled action").strip(),
        "next_step": derived_next_step.strip(),
        "effort": _normalize_effort(effort),
        "due_window": _normalize_due_window(due_window),
        "blockers": cleaned_blockers,
        "success_criteria": (
            success_criteria or _extract_success_criteria(action_plan, rec.rationale, rec.description)
        ).strip(),
        "status": ActionItemStatus.ACCEPTED.value,
        "review_notes": None,
        "goal_path": goal_path,
        "goal_title": goal_title,
        "created_at": now,
        "updated_at": now,
    }


class RecommendationStorage:
    """Markdown file storage for recommendations."""

    def __init__(self, path: Path, dedup_window_days: int = 30):
        self.dir = Path(path)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.dedup_window_days = dedup_window_days

    def save(self, rec: Recommendation) -> str:
        """Save recommendation as markdown file. Returns id."""
        rec_id = rec.id or uuid.uuid4().hex[:8]
        now = rec.created_at or datetime.now().isoformat()
        date_prefix = now[:10]

        filename = f"{date_prefix}_{rec.category}_{_slug(rec.title)}_{rec_id}.md"
        filepath = self.dir / filename

        post = frontmatter.Post("")
        post.metadata = {
            "id": rec_id,
            "category": str(rec.category),
            "title": str(rec.title),
            "score": float(rec.score),
            "status": str(rec.status),
            "created_at": str(now),
            "embedding_hash": str(rec.embedding_hash) if rec.embedding_hash else None,
        }
        if rec.metadata:
            post.metadata["metadata"] = rec.metadata

        body_parts = []
        if rec.description:
            body_parts.append(rec.description)
        if rec.rationale:
            body_parts.append(f"\n## Rationale\n\n{rec.rationale}")
        if rec.metadata and rec.metadata.get("action_plan"):
            body_parts.append(f"\n## Action Plan\n\n{rec.metadata['action_plan']}")
        post.content = "\n".join(body_parts)

        filepath.write_text(frontmatter.dumps(post))
        return rec_id

    def get(self, rec_id) -> Optional[Recommendation]:
        """Get recommendation by id."""
        rec_id = str(rec_id)
        for f in self.dir.glob("*.md"):
            rec = self._read_file(f)
            if rec and str(rec.id) == rec_id:
                return rec
        return None

    def update_status(self, rec_id, status: str) -> bool:
        """Update recommendation status."""
        rec_id = str(rec_id)
        for f in self.dir.glob("*.md"):
            post = frontmatter.load(f)
            if str(post.metadata.get("id")) == rec_id:
                post.metadata["status"] = status
                f.write_text(frontmatter.dumps(post))
                return True
        return False

    def create_action_item(
        self,
        rec_id,
        *,
        goal_path: Optional[str] = None,
        goal_title: Optional[str] = None,
        objective: Optional[str] = None,
        next_step: Optional[str] = None,
        effort: Optional[str] = None,
        due_window: Optional[str] = None,
        blockers: Optional[list[str]] = None,
        success_criteria: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Create a structured action item for a recommendation if one doesn't exist."""
        rec = self.get(rec_id)
        if not rec:
            return None
        if rec.metadata and rec.metadata.get("action_item"):
            return rec.metadata["action_item"]

        action_item = _derive_action_item(
            rec,
            goal_path=goal_path,
            goal_title=goal_title,
            objective=objective,
            next_step=next_step,
            effort=effort,
            due_window=due_window,
            blockers=blockers,
            success_criteria=success_criteria,
        )

        def _updater(post):
            meta = post.metadata.get("metadata") or {}
            meta["action_item"] = action_item
            post.metadata["metadata"] = meta
            post.metadata["status"] = RecommendationStatus.IN_PROGRESS.value

        if not self._update_post(rec_id, _updater):
            return None
        return action_item

    def update_action_item(
        self,
        rec_id,
        *,
        status: Optional[str] = None,
        effort: Optional[str] = None,
        due_window: Optional[str] = None,
        blockers: Optional[list[str]] = None,
        review_notes: Optional[str] = None,
        next_step: Optional[str] = None,
        success_criteria: Optional[str] = None,
        goal_path: Optional[str] = None,
        goal_title: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Update an existing action item for a recommendation."""
        rec = self.get(rec_id)
        if not rec or not rec.metadata or not rec.metadata.get("action_item"):
            return None

        action_item = dict(rec.metadata["action_item"])
        if status is not None:
            action_item["status"] = _normalize_action_status(status)
        if effort is not None:
            action_item["effort"] = _normalize_effort(effort)
        if due_window is not None:
            action_item["due_window"] = _normalize_due_window(due_window)
        if blockers is not None:
            action_item["blockers"] = [item.strip() for item in blockers if item and item.strip()]
        if review_notes is not None:
            action_item["review_notes"] = review_notes.strip() or None
        if next_step is not None:
            action_item["next_step"] = next_step.strip()
        if success_criteria is not None:
            action_item["success_criteria"] = success_criteria.strip()
        if goal_path is not None:
            action_item["goal_path"] = goal_path
        if goal_title is not None:
            action_item["goal_title"] = goal_title
        action_item["updated_at"] = datetime.now().isoformat()

        rec_status = RecommendationStatus.IN_PROGRESS.value
        if action_item["status"] == ActionItemStatus.COMPLETED.value:
            rec_status = RecommendationStatus.COMPLETED.value
        elif action_item["status"] == ActionItemStatus.ABANDONED.value:
            rec_status = RecommendationStatus.DISMISSED.value
        elif action_item["status"] == ActionItemStatus.DEFERRED.value:
            rec_status = RecommendationStatus.SUGGESTED.value

        def _updater(post):
            meta = post.metadata.get("metadata") or {}
            meta["action_item"] = action_item
            post.metadata["metadata"] = meta
            post.metadata["status"] = rec_status

        if not self._update_post(rec_id, _updater):
            return None
        return action_item

    def list_by_category(
        self, category: str, status: Optional[str] = None, limit: int = 10
    ) -> list[Recommendation]:
        """List recommendations by category."""
        recs = [r for r in self._all() if r.category == category]
        if status:
            recs = [r for r in recs if r.status == status]
        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def list_recent(
        self, days: int = 7, status: Optional[str] = None, limit: int = 20
    ) -> list[Recommendation]:
        """List recent recommendations."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recs = [r for r in self._all() if (r.created_at or "") >= cutoff]
        if status:
            recs = [r for r in recs if r.status == status]
        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def hash_exists(self, embedding_hash: str, days: int | None = None) -> bool:
        """Check if similar recommendation exists recently."""
        days = days if days is not None else self.dedup_window_days
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        for r in self._all():
            if r.embedding_hash == embedding_hash and (r.created_at or "") >= cutoff:
                return True
        return False

    def get_top_by_score(
        self,
        min_score: float = 6.0,
        limit: int = 5,
        exclude_status: Optional[list[str]] = None,
    ) -> list[Recommendation]:
        """Get top recommendations by score."""
        exclude = set(exclude_status or [])
        recs = [r for r in self._all() if r.score >= min_score and r.status not in exclude]
        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def add_feedback(self, rec_id, rating: int, comment: Optional[str] = None) -> bool:
        """Add user feedback to recommendation."""
        rec_id = str(rec_id)
        for f in self.dir.glob("*.md"):
            post = frontmatter.load(f)
            if str(post.metadata.get("id")) == rec_id:
                meta = post.metadata.get("metadata") or {}
                meta["user_rating"] = rating
                meta["feedback_at"] = datetime.now().isoformat()
                if comment:
                    meta["feedback_comment"] = comment
                post.metadata["metadata"] = meta
                f.write_text(frontmatter.dumps(post))
                return True
        return False

    def get_feedback_stats(self, category: Optional[str] = None, days: int = 90) -> dict:
        """Get feedback statistics."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        ratings_by_cat: dict[str, list] = {}

        for r in self._all():
            if (r.created_at or "") < cutoff:
                continue
            if category and r.category != category:
                continue
            if r.metadata and "user_rating" in r.metadata:
                ratings_by_cat.setdefault(r.category, []).append(r.metadata["user_rating"])

        all_ratings = []
        by_category = {}
        for cat, ratings in ratings_by_cat.items():
            avg = sum(ratings) / len(ratings)
            by_category[cat] = {"avg_rating": avg, "count": len(ratings)}
            all_ratings.extend(ratings)

        return {
            "avg_rating": sum(all_ratings) / len(all_ratings) if all_ratings else 3.0,
            "count": len(all_ratings),
            "by_category": by_category,
        }

    def get_action_item(self, rec_id) -> Optional[RecommendationAction]:
        """Return a tracked action item with source recommendation context."""
        rec = self.get(rec_id)
        if not rec or not rec.metadata or not rec.metadata.get("action_item"):
            return None
        return RecommendationAction(
            recommendation_id=str(rec.id or ""),
            recommendation_title=rec.title,
            category=rec.category,
            score=rec.score,
            recommendation_status=rec.status,
            created_at=rec.created_at,
            action_item=dict(rec.metadata["action_item"]),
        )

    def list_action_items(
        self,
        status: Optional[str] = None,
        goal_path: Optional[str] = None,
        limit: int = 20,
    ) -> list[RecommendationAction]:
        """List tracked action items across recommendations."""
        items = []
        for rec in self._all():
            meta = rec.metadata or {}
            action_item = meta.get("action_item")
            if not action_item:
                continue
            if status and action_item.get("status") != status:
                continue
            if goal_path is not None and action_item.get("goal_path") != goal_path:
                continue
            items.append(
                RecommendationAction(
                    recommendation_id=str(rec.id or ""),
                    recommendation_title=rec.title,
                    category=rec.category,
                    score=rec.score,
                    recommendation_status=rec.status,
                    created_at=rec.created_at,
                    action_item=dict(action_item),
                )
            )

        due_priority = {"today": 0, "this_week": 1, "later": 2}
        effort_priority = {"small": 0, "medium": 1, "large": 2}
        items.sort(
            key=lambda item: (
                due_priority.get(item.action_item.get("due_window"), 3),
                effort_priority.get(item.action_item.get("effort"), 3),
                -item.score,
                item.action_item.get("updated_at") or "",
            )
        )
        return items[:limit]

    def build_weekly_plan(
        self,
        capacity_points: int = 6,
        goal_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Select a small set of accepted actions that fit within a weekly budget."""
        selected: list[RecommendationAction] = []
        used_points = 0
        candidates = self.list_action_items(
            status=ActionItemStatus.ACCEPTED.value,
            goal_path=goal_path,
            limit=100,
        )
        for item in candidates:
            effort = item.action_item.get("effort") or "medium"
            effort_points = EFFORT_POINTS.get(effort, 2)
            if used_points + effort_points > capacity_points:
                continue
            selected.append(item)
            used_points += effort_points

        return {
            "items": selected,
            "capacity_points": capacity_points,
            "used_points": used_points,
            "remaining_points": max(0, capacity_points - used_points),
            "generated_at": datetime.now().isoformat(),
        }

    def get_execution_stats(self, category: Optional[str] = None, days: int = 90) -> dict:
        """Aggregate action-item outcome stats for ranking feedback."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        by_category: dict[str, dict[str, Any]] = {}

        for rec in self._all():
            if (rec.created_at or "") < cutoff:
                continue
            if category and rec.category != category:
                continue
            action_item = (rec.metadata or {}).get("action_item")
            if not action_item:
                continue

            cat = rec.category
            stats = by_category.setdefault(
                cat,
                {
                    "count": 0,
                    "avg_outcome": 0.0,
                    "accepted": 0,
                    "deferred": 0,
                    "blocked": 0,
                    "completed": 0,
                    "abandoned": 0,
                    "outcome_total": 0.0,
                },
            )
            item_status = _normalize_action_status(action_item.get("status"))
            stats[item_status] += 1
            stats["count"] += 1
            stats["outcome_total"] += ACTION_ITEM_OUTCOME_WEIGHTS[item_status]

        all_count = 0
        all_total = 0.0
        for stats in by_category.values():
            if stats["count"]:
                stats["avg_outcome"] = stats["outcome_total"] / stats["count"]
                all_count += stats["count"]
                all_total += stats["outcome_total"]
            stats.pop("outcome_total", None)

        return {
            "count": all_count,
            "avg_outcome": (all_total / all_count) if all_count else 0.0,
            "by_category": by_category,
        }

    def _all(self) -> list[Recommendation]:
        """Read all recommendations from disk."""
        recs = []
        for f in sorted(self.dir.glob("*.md"), reverse=True):
            rec = self._read_file(f)
            if rec:
                recs.append(rec)
        return recs

    def _update_post(self, rec_id, updater) -> bool:
        """Apply a mutation callback to a recommendation post by id."""
        rec_id = str(rec_id)
        for f in self.dir.glob("*.md"):
            post = frontmatter.load(f)
            if str(post.metadata.get("id")) == rec_id:
                updater(post)
                f.write_text(frontmatter.dumps(post))
                return True
        return False

    def _read_file(self, path: Path) -> Optional[Recommendation]:
        """Parse a recommendation markdown file."""
        try:
            post = frontmatter.load(path)
            m = post.metadata

            # Extract description and rationale from body
            body = post.content
            description = body.split("\n## Rationale")[0].strip() if body else ""
            rationale = ""
            if "## Rationale" in body:
                rationale = body.split("## Rationale")[-1].split("## Action Plan")[0].strip()

            meta = m.get("metadata")
            if isinstance(meta, str):
                meta = json.loads(meta)

            # Reconstruct action_plan into metadata
            if "## Action Plan" in body:
                action_plan = body.split("## Action Plan")[-1].strip()
                meta = meta or {}
                meta["action_plan"] = action_plan

            return Recommendation(
                id=str(m.get("id", "")),
                category=m.get("category", ""),
                title=m.get("title", ""),
                description=description,
                rationale=rationale,
                score=float(m.get("score", 0)),
                created_at=m.get("created_at"),
                status=m.get("status", "suggested"),
                metadata=meta,
                embedding_hash=m.get("embedding_hash"),
            )
        except Exception:
            return None

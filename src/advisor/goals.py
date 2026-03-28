"""Goal tracking and check-in management."""

from datetime import datetime, timedelta
from pathlib import Path

import structlog

import frontmatter
from shared_types import GoalStatus

logger = structlog.get_logger()


class GoalTracker:
    """Track goals and detect stale ones needing attention."""

    DEFAULT_CHECK_IN_DAYS = 14
    INACTIVE_STATUSES = (GoalStatus.PAUSED, GoalStatus.COMPLETED, GoalStatus.ABANDONED)

    def __init__(self, journal_storage):
        self.storage = journal_storage

    def get_goals(self, include_inactive: bool = False, goal_type: str | None = None) -> list[dict]:
        """Get all goals with their metadata.

        Args:
            include_inactive: Include completed/paused/abandoned goals
            goal_type: Filter by type (career, learning, project, general)

        Returns:
            List of goal entries with staleness info
        """
        entries = self.storage.list_entries(entry_type="goal", limit=100)
        goals = []

        for entry in entries:
            try:
                post = frontmatter.load(entry["path"])
                meta = dict(post.metadata)

                status = meta.get("status", "active")
                if not include_inactive and status in self.INACTIVE_STATUSES:
                    continue

                g_type = meta.get("goal_type", "general")
                if goal_type and g_type != goal_type:
                    continue

                last_checked = meta.get("last_checked", meta.get("created"))
                check_in_days = meta.get("check_in_days", self.DEFAULT_CHECK_IN_DAYS)

                # Calculate staleness
                days_since = self._days_since(last_checked)
                is_stale = days_since >= check_in_days if days_since else False

                goals.append(
                    {
                        "path": entry["path"],
                        "title": meta.get("title", "Untitled Goal"),
                        "status": status,
                        "goal_type": g_type,
                        "created": meta.get("created"),
                        "last_checked": last_checked,
                        "check_in_days": check_in_days,
                        "days_since_check": days_since,
                        "is_stale": is_stale,
                        "tags": meta.get("tags", []),
                        "content": post.content[:200] if post.content else "",
                    }
                )
            except (OSError, ValueError) as e:
                logger.debug("Failed to load goal entry", error=str(e))
                continue

        return sorted(
            goals,
            key=lambda g: (g["is_stale"], g.get("days_since_check") or -1),
            reverse=True,
        )

    def get_stale_goals(self, days_threshold: int | None = None) -> list[dict]:
        """Get goals that haven't been checked in recently.

        Args:
            days_threshold: Override default threshold

        Returns:
            List of stale goals
        """
        threshold = days_threshold or self.DEFAULT_CHECK_IN_DAYS
        all_goals = self.get_goals(include_inactive=False)

        return [g for g in all_goals if g.get("days_since_check", 0) >= threshold]

    def check_in_goal(
        self,
        goal_path: Path,
        notes: str | None = None,
    ) -> bool:
        """Record a check-in for a goal.

        Args:
            goal_path: Path to goal file
            notes: Optional check-in notes

        Returns:
            True if successful
        """
        try:
            post = frontmatter.load(goal_path)
            now = datetime.now().isoformat()

            # Update last_checked
            post["last_checked"] = now

            # Append notes to content if provided
            if notes:
                check_in_entry = f"\n\n---\n**Check-in {now[:10]}**: {notes}"
                post.content = (post.content or "") + check_in_entry

            with open(goal_path, "w") as f:
                f.write(frontmatter.dumps(post))

            return True
        except (OSError, ValueError) as e:
            logger.debug("Failed to check in goal", error=str(e))
            return False

    def update_goal_status(
        self,
        goal_path: Path,
        status: str,
    ) -> bool:
        """Update goal status.

        Args:
            goal_path: Path to goal file
            status: New status (active, paused, completed, abandoned)

        Returns:
            True if successful
        """
        valid = tuple(GoalStatus)
        if status not in valid:
            return False

        try:
            post = frontmatter.load(goal_path)
            post["status"] = status
            post["status_updated"] = datetime.now().isoformat()

            with open(goal_path, "w") as f:
                f.write(frontmatter.dumps(post))

            return True
        except (OSError, ValueError) as e:
            logger.debug("Failed to update goal status", error=str(e))
            return False

    def add_milestone(self, goal_path: Path, title: str) -> bool:
        """Append a milestone to goal's frontmatter.

        Args:
            goal_path: Path to goal file
            title: Milestone title

        Returns:
            True if successful
        """
        try:
            post = frontmatter.load(goal_path)
            milestones = post.metadata.get("milestones", [])
            milestones.append(
                {
                    "title": title,
                    "completed": False,
                    "completed_at": None,
                }
            )
            post["milestones"] = milestones
            post["progress"] = self._calc_progress(milestones)

            with open(goal_path, "w") as f:
                f.write(frontmatter.dumps(post))
            return True
        except (OSError, ValueError) as e:
            logger.debug("Failed to add milestone", error=str(e))
            return False

    def complete_milestone(self, goal_path: Path, milestone_index: int) -> bool:
        """Mark a milestone as completed.

        Args:
            goal_path: Path to goal file
            milestone_index: 0-based index of milestone

        Returns:
            True if successful
        """
        try:
            post = frontmatter.load(goal_path)
            milestones = post.metadata.get("milestones", [])

            if milestone_index < 0 or milestone_index >= len(milestones):
                return False

            milestones[milestone_index]["completed"] = True
            milestones[milestone_index]["completed_at"] = datetime.now().isoformat()
            post["milestones"] = milestones
            post["progress"] = self._calc_progress(milestones)

            with open(goal_path, "w") as f:
                f.write(frontmatter.dumps(post))
            return True
        except (OSError, ValueError) as e:
            logger.debug("Failed to complete milestone", error=str(e))
            return False

    def get_progress(self, goal_path: Path) -> dict:
        """Get progress info for a goal.

        Returns:
            Dict with percent, completed, total, milestones list
        """
        try:
            post = frontmatter.load(goal_path)
            milestones = post.metadata.get("milestones", [])
            completed = sum(1 for m in milestones if m.get("completed"))
            total = len(milestones)
            percent = int((completed / total * 100) if total > 0 else 0)

            return {
                "percent": percent,
                "completed": completed,
                "total": total,
                "milestones": milestones,
            }
        except (OSError, ValueError):
            return {"percent": 0, "completed": 0, "total": 0, "milestones": []}

    @staticmethod
    def _calc_progress(milestones: list) -> int:
        """Calculate progress percentage from milestones."""
        if not milestones:
            return 0
        completed = sum(1 for m in milestones if m.get("completed"))
        return int(completed / len(milestones) * 100)

    def _days_since(self, iso_date: str | None) -> int | None:
        """Calculate days since ISO date string."""
        if not iso_date:
            return None
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            return (datetime.now() - dt).days
        except (OSError, ValueError) as e:
            logger.debug("Failed to parse date", error=str(e))
            return None


class GoalJournalLinker:
    """Auto-detect journal entries relevant to goals via embedding similarity."""

    SIMILARITY_THRESHOLD = 0.4

    def __init__(self, journal_storage, embeddings):
        self.storage = journal_storage
        self.embeddings = embeddings

    def link_recent_entries(self, days: int = 1) -> list[dict]:
        """Check new entries against active goals, return suggested links.

        Returns:
            List of {goal_title, goal_path, entry_title, entry_path, similarity}
        """
        tracker = GoalTracker(self.storage)
        goals = tracker.get_goals(include_inactive=False)
        active_goals = [g for g in goals if g["status"] == "active"]
        if not active_goals:
            return []

        # Get recent entries
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        entries = self.storage.list_entries(limit=20)
        recent = [e for e in entries if e.get("created", "") >= cutoff and e.get("type") != "goal"]
        if not recent:
            return []

        links = []
        for entry in recent:
            for goal in active_goals:
                goal_text = f"{goal['title']} {goal.get('content', '')}"
                try:
                    # Query embeddings with goal text and check if entry appears in results
                    results = self.embeddings.query(goal_text, n_results=10)
                    for r in results:
                        if str(r.get("id", "")) == str(entry.get("path", "")):
                            similarity = 1.0 - r.get("distance", 1.0)
                            if similarity >= self.SIMILARITY_THRESHOLD:
                                links.append(
                                    {
                                        "goal_title": goal["title"],
                                        "goal_path": str(goal.get("path", "")),
                                        "entry_title": entry.get("title", ""),
                                        "entry_path": str(entry.get("path", "")),
                                        "similarity": round(similarity, 3),
                                    }
                                )
                            break
                except Exception as e:
                    logger.debug("link_check_failed", error=str(e))
                    continue

        return sorted(links, key=lambda x: x["similarity"], reverse=True)


def get_goal_defaults(goal_type: str = "general") -> dict:
    """Get default metadata for new goal entries."""
    return {
        "status": str(GoalStatus.ACTIVE),
        "goal_type": goal_type,  # career, learning, project, general
        "last_checked": datetime.now().isoformat(),
        "check_in_days": 14,
    }

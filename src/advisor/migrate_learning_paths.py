"""One-time migration: convert learning paths to goals with type=learning."""

import re
from pathlib import Path

import structlog

import frontmatter

from .goals import GoalTracker, get_goal_defaults

logger = structlog.get_logger()

MARKER_FILE = ".learning_paths_migrated"


def migrate_learning_paths(
    user_base_dir: Path,
    journal_storage,
    tracker: GoalTracker,
) -> dict:
    """Migrate learning path files to goals with type=learning.

    Args:
        user_base_dir: User's base directory (e.g. ~/coach or ~/coach/users/{id})
        journal_storage: JournalStorage instance for creating goal entries
        tracker: GoalTracker instance for adding milestones

    Returns:
        {"migrated": count, "skipped": count, "errors": list[str]}
    """
    lp_dir = user_base_dir / "learning_paths"
    if not lp_dir.exists():
        return {"migrated": 0, "skipped": 0, "errors": []}

    migrated = 0
    skipped = 0
    errors = []

    for lp_file in sorted(lp_dir.glob("*.md")):
        try:
            post = frontmatter.load(lp_file)
            meta = post.metadata
            skill = meta.get("skill", lp_file.stem)
            status = meta.get("status", "active")
            completed_modules = meta.get("completed_modules", 0)

            # Create goal entry
            defaults = get_goal_defaults(goal_type="learning")
            goal_path = journal_storage.create(
                content=post.content[:3000] if post.content else "",
                entry_type="goal",
                title=skill,
                metadata=defaults,
            )

            # Parse modules from content
            modules = _parse_modules(post.content or "")
            for mod_title in modules:
                tracker.add_milestone(Path(goal_path), mod_title)

            # Mark completed milestones
            for i in range(min(completed_modules, len(modules))):
                tracker.complete_milestone(Path(goal_path), i)

            # If source was completed, update goal status
            if status == "completed":
                tracker.update_goal_status(Path(goal_path), "completed")

            migrated += 1
            logger.info("migration.converted", skill=skill, path=str(lp_file))

        except Exception as e:
            errors.append(f"{lp_file.name}: {e}")
            logger.warning("migration.error", file=str(lp_file), error=str(e))
            continue

    return {"migrated": migrated, "skipped": skipped, "errors": errors}


def _parse_modules(content: str) -> list[str]:
    """Extract module titles from learning path content."""
    titles = []
    for match in re.finditer(r"^###\s+Module\s+\d+\s*:\s*(.+)$", content, re.MULTILINE):
        titles.append(match.group(1).strip())
    if not titles:
        # Fallback: try numbered list at top level
        for match in re.finditer(r"^\d+\.\s+(.+)$", content, re.MULTILINE):
            titles.append(match.group(1).strip())
    return titles


def run_migration_if_needed(
    user_base_dir: Path,
    journal_storage=None,
    tracker: GoalTracker | None = None,
) -> dict | None:
    """Run migration if not already done (marker file check).

    Returns migration result dict, or None if already migrated.
    """
    marker = user_base_dir / MARKER_FILE
    if marker.exists():
        return None

    if not journal_storage or not tracker:
        return None

    result = migrate_learning_paths(user_base_dir, journal_storage, tracker)

    try:
        marker.write_text(f"migrated={result['migrated']}\n")
    except OSError as e:
        logger.warning("migration.marker_write_failed", error=str(e))

    return result

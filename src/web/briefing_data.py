"""Shared briefing data assembly used by both /api/briefing and /api/greeting."""

from pathlib import Path

import structlog

from web.deps import get_user_paths

logger = structlog.get_logger()


def assemble_briefing_data(user_id: str) -> dict:
    """Assemble core briefing data: profile, stale goals, all goals, recs, intel matches.

    Returns dict with keys: name, stale_goals, all_goals, recommendations, goal_intel_matches.
    Each key is always present (empty list / empty string as default).
    """
    paths = get_user_paths(user_id)
    data: dict = {
        "name": "",
        "stale_goals": [],
        "all_goals": [],
        "recommendations": [],
        "goal_intel_matches": [],
    }

    # Profile name
    try:
        from profile.storage import ProfileStorage

        profile_path = paths.get("profile")
        if profile_path and Path(profile_path).exists():
            prof = ProfileStorage(profile_path).load()
            if prof:
                data["name"] = getattr(prof, "name", None) or getattr(prof, "current_role", "")
    except Exception:
        pass

    # Goals
    try:
        from advisor.goals import GoalTracker
        from journal.storage import JournalStorage

        storage = JournalStorage(paths["journal_dir"])
        tracker = GoalTracker(storage)
        raw_stale = tracker.get_stale_goals()
        data["stale_goals"] = [
            {
                "path": str(g["path"]),
                "title": g["title"],
                "status": g["status"],
                "days_since_check": g.get("days_since_check") or 0,
            }
            for g in raw_stale
        ]
        raw_all = tracker.get_goals(include_inactive=False)
        data["all_goals"] = [
            {
                "path": str(g["path"]),
                "title": g["title"],
                "status": g["status"],
                "days_since_check": g.get("days_since_check") or 0,
            }
            for g in raw_all
        ]
    except Exception as e:
        logger.warning("briefing_data.goals_error", error=str(e))

    # Recommendations
    try:
        from advisor.recommendation_storage import RecommendationStorage

        rec_dir = paths.get("recommendations_dir")
        if rec_dir:
            rec_storage = RecommendationStorage(rec_dir)
            recs = rec_storage.get_top_by_score(limit=5)
            for r in recs:
                meta = r.metadata or {}
                critic = None
                if any(meta.get(k) for k in ("confidence", "critic_challenge", "missing_context")):
                    critic = {
                        "confidence": meta.get("confidence", "Medium"),
                        "confidence_rationale": meta.get("confidence_rationale", ""),
                        "critic_challenge": meta.get("critic_challenge", ""),
                        "missing_context": meta.get("missing_context", ""),
                        "alternative": meta.get("alternative"),
                        "intel_contradictions": meta.get("intel_contradictions"),
                    }
                data["recommendations"].append(
                    {
                        "id": r.id or "",
                        "category": r.category,
                        "title": r.title,
                        "description": r.description[:200] if r.description else "",
                        "score": r.score,
                        "status": r.status,
                        "reasoning_trace": meta.get("reasoning_trace"),
                        "critic": critic,
                    }
                )
    except Exception as e:
        logger.warning("briefing_data.recommendations_error", error=str(e))

    # Goal-intel matches
    try:
        from intelligence.goal_intel_match import GoalIntelMatchStore

        db_path = paths["intel_db"]
        match_store = GoalIntelMatchStore(db_path)
        goal_paths = [g["path"] for g in data["all_goals"]]
        if goal_paths:
            data["goal_intel_matches"] = match_store.get_matches(goal_paths=goal_paths, limit=20)
    except Exception as e:
        logger.warning("briefing_data.goal_intel_matches_error", error=str(e))

    return data

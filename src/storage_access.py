"""Shared storage constructors built on canonical path dictionaries."""

from pathlib import Path
from typing import Mapping

from storage_paths import StoragePaths  # noqa: F401 — re-exported for consumers

PathMap = Mapping[str, Path]


def _require_path(paths: PathMap, key: str) -> Path:
    """Get a required path key or raise a clear KeyError."""
    try:
        return Path(paths[key])
    except KeyError as exc:
        raise KeyError(f"Missing required path key: {key}") from exc


def get_profile_path(paths: PathMap) -> Path:
    """Return the profile path from a canonical or legacy path map."""
    if "profile_path" in paths:
        return Path(paths["profile_path"])
    return _require_path(paths, "profile")


def get_recommendations_dir(paths: PathMap) -> Path:
    """Return the recommendations directory from a canonical path map."""
    return _require_path(paths, "recommendations_dir")


def create_recommendation_storage(paths: PathMap):
    """Construct recommendation storage from canonical paths."""
    from advisor.recommendation_storage import RecommendationStorage

    return RecommendationStorage(get_recommendations_dir(paths))


def create_insight_store(paths: PathMap):
    """Construct insight storage from canonical paths."""
    from advisor.insights import InsightStore

    return InsightStore(_require_path(paths, "intel_db"))


def create_goal_intel_match_store(paths: PathMap):
    """Construct goal-intel match storage from canonical paths."""
    from intelligence.goal_intel_match import GoalIntelMatchStore

    return GoalIntelMatchStore(_require_path(paths, "intel_db"))


def create_profile_storage(paths: PathMap):
    """Construct a profile store from canonical paths."""
    from profile.storage import ProfileStorage

    return ProfileStorage(get_profile_path(paths))


def create_profile_embedding_manager(paths: PathMap):
    """Construct the profile embedding manager from canonical paths."""
    from journal.embeddings import EmbeddingManager

    return EmbeddingManager(_require_path(paths, "chroma_dir"), collection_name="profile")


def create_memory_store(paths: PathMap):
    """Construct a memory store from canonical paths."""
    from memory.store import FactStore

    chroma_dir = Path(paths["chroma_dir"]) if "chroma_dir" in paths else None
    return FactStore(_require_path(paths, "memory_db"), chroma_dir)


def create_thread_store(paths: PathMap):
    """Construct a thread store from canonical paths."""
    from journal.thread_store import ThreadStore

    return ThreadStore(_require_path(paths, "threads_db"))


def create_mind_map_store(paths: PathMap):
    """Construct a journal mind-map store from canonical paths."""
    from journal.mind_map import JournalMindMapStore

    return JournalMindMapStore(_require_path(paths, "mind_maps_db"))


def create_intel_storage(paths: PathMap):
    """Construct shared intel storage from canonical paths."""
    from intelligence.scraper import IntelStorage

    return IntelStorage(_require_path(paths, "intel_db"))


def create_watchlist_store(paths: PathMap):
    """Construct a watchlist store from canonical paths."""
    from intelligence.watchlist import WatchlistStore

    return WatchlistStore(_require_path(paths, "watchlist_path"))


def create_follow_up_store(paths: PathMap):
    """Construct a follow-up store from canonical paths."""
    from intelligence.watchlist import IntelFollowUpStore

    return IntelFollowUpStore(_require_path(paths, "follow_up_path"))

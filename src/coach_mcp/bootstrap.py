"""Lazy component initialization for MCP server."""

from pathlib import Path

import structlog

from storage_access import (
    create_insight_store,
    create_intel_storage,
    create_memory_store,
    create_profile_storage,
    create_recommendation_storage,
    create_thread_store,
    create_watchlist_store,
)
from storage_paths import get_coach_home, get_single_user_paths

logger = structlog.get_logger()

_components = None


def get_components() -> dict:
    """Lazy singleton wrapping cli.utils.get_components(skip_advisor=True).

    Returns the same dict as cli/utils.py but skips LLM/advisor init.
    """
    global _components
    if _components is None:
        logger.info("mcp_bootstrap_init")
        from cli.utils import get_components as _get

        _components = _get(skip_advisor=True)
    return _components


def _resolve_profile_path(components: dict) -> Path | None:
    """Resolve any explicit profile path configured for the single-user MCP surface."""
    config = components.get("config", {})
    raw_path = config.get("profile", {}).get("path")
    if not raw_path:
        return None
    return Path(raw_path).expanduser()


def _resolve_coach_home(components: dict) -> Path:
    """Infer the base coach directory from initialized component paths."""
    paths = components.get("paths", {})
    intel_db = paths.get("intel_db")
    if intel_db:
        return Path(intel_db).expanduser().parent

    journal_dir = paths.get("journal_dir")
    if journal_dir:
        return Path(journal_dir).expanduser().parent

    return get_coach_home()


def get_storage_paths() -> dict:
    """Return canonical single-user storage paths for MCP tools."""
    components = get_components()
    cached = components.get("storage_paths")
    if cached is not None:
        return cached

    storage_paths = get_single_user_paths(
        coach_home=_resolve_coach_home(components),
        profile_path=_resolve_profile_path(components),
    )
    components["storage_paths"] = storage_paths
    return storage_paths


def get_profile_storage():
    """Construct the profile store for MCP tools."""
    return create_profile_storage(get_storage_paths())


def get_memory_store():
    """Construct the single-user memory store for MCP tools."""
    return create_memory_store(get_storage_paths())


def get_thread_store():
    """Construct the single-user thread store for MCP tools."""
    return create_thread_store(get_storage_paths())


def get_watchlist_store():
    """Construct the single-user watchlist store for MCP tools."""
    return create_watchlist_store(get_storage_paths())


def get_intel_storage():
    """Construct the shared intel store for MCP tools."""
    return create_intel_storage(get_storage_paths())


def get_recommendation_storage():
    """Construct the recommendation store for MCP tools."""
    return create_recommendation_storage(get_storage_paths())


def get_insight_store():
    """Construct the insight store for MCP tools."""
    return create_insight_store(get_storage_paths())

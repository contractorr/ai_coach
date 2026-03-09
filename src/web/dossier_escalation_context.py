"""Shared dossier-escalation context assembly for user-scoped surfaces."""

from __future__ import annotations

from journal.storage import JournalStorage
from research.dossiers import ResearchDossierStore
from web.deps import (
    get_intel_storage,
    get_thread_inbox_service,
    get_user_paths,
    get_watchlist_store,
)


def list_user_dossiers(user_id: str, *, limit: int = 50) -> list[dict]:
    """Load active dossiers for suppression and cross-surface context."""

    paths = get_user_paths(user_id)
    dossier_store = ResearchDossierStore(JournalStorage(paths["journal_dir"]))
    return dossier_store.list_dossiers(include_archived=False, limit=limit)


async def load_dossier_escalation_context(
    user_id: str,
    *,
    goals: list[dict] | None = None,
    thread_limit: int = 20,
    intel_days: int = 7,
    intel_limit: int = 50,
    dossier_limit: int = 50,
) -> dict:
    """Assemble the shared user context for dossier escalation refreshes."""

    threads = await get_thread_inbox_service(user_id).list_inbox(limit=thread_limit)
    return {
        "threads": threads,
        "recent_intel": get_intel_storage().get_recent(
            days=intel_days,
            limit=intel_limit,
            include_duplicates=True,
        ),
        "watchlist": get_watchlist_store(user_id).list_items(),
        "goals": goals or [],
        "dossiers": list_user_dossiers(user_id, limit=dossier_limit),
    }

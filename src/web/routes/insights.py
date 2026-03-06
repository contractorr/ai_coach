"""Insights routes — unified view of signals, patterns, and heartbeat output."""

from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, Query

from advisor.insights import InsightStore
from intelligence.scraper import IntelStorage
from intelligence.watchlist import (
    WatchlistStore,
    annotate_items,
    find_evidence_for_text,
    sort_ranked_items,
)
from web.auth import get_current_user
from web.deps import get_coach_paths, get_user_paths
from web.models import InsightResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/insights", tags=["insights"])


def _recent_watchlist_intel(user_id: str) -> list[dict]:
    paths = get_user_paths(user_id)
    watchlist_path = Path(paths["profile"]).parent / "watchlist.json"
    watchlist_items = WatchlistStore(watchlist_path).list_items()
    if not watchlist_items:
        return []

    intel_storage = IntelStorage(get_coach_paths()["intel_db"])
    items = intel_storage.get_recent(days=21, limit=80, include_duplicates=True)
    annotate_items(items, watchlist_items)
    return sort_ranked_items(items)


@router.get("", response_model=list[InsightResponse])
async def get_insights(
    type: str | None = Query(default=None, description="Filter by insight type"),
    min_severity: int = Query(default=1, ge=1, le=10),
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    paths = get_user_paths(user["id"])
    store = InsightStore(paths["intel_db"])
    rows = store.get_active(insight_type=type, min_severity=min_severity, limit=limit)
    ranked_watchlist_intel = _recent_watchlist_intel(user["id"])
    return [
        InsightResponse(
            **r,
            watchlist_evidence=find_evidence_for_text(
                f"{r.get('title', '')}\n{r.get('detail', '')}", ranked_watchlist_intel, limit=2
            ),
        )
        for r in rows
    ]

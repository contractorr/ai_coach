"""Insights routes — unified view of signals, patterns, and heartbeat output."""

import structlog
from fastapi import APIRouter, Depends, Query

from intelligence.watchlist import (
    annotate_items,
    find_evidence_for_text,
    sort_ranked_items,
)
from web.auth import get_current_user
from web.deps import get_insight_store, get_intel_storage, get_watchlist_store
from web.models import InsightResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/insights", tags=["insights"])


def _recent_watchlist_intel(user_id: str) -> list[dict]:
    watchlist_items = get_watchlist_store(user_id).list_items()
    if not watchlist_items:
        return []

    intel_storage = get_intel_storage()
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
    store = get_insight_store()
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

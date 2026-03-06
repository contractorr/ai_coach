"""Insights routes — unified view of signals, patterns, and heartbeat output."""

import structlog
from fastapi import APIRouter, Depends, Query

from advisor.insights import InsightStore
from web.auth import get_current_user
from web.deps import get_user_paths
from web.models import InsightResponse

logger = structlog.get_logger()

router = APIRouter(prefix="/api/insights", tags=["insights"])


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
    return [InsightResponse(**r) for r in rows]

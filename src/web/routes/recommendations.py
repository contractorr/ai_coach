"""Recommendations query endpoint — text search + category filtering."""

from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, Query

from advisor.recommendation_storage import RecommendationStorage
from intelligence.scraper import IntelStorage
from intelligence.watchlist import (
    WatchlistStore,
    annotate_items,
    find_evidence_for_text,
    sort_ranked_items,
)
from web.auth import get_current_user
from web.deps import get_coach_paths, get_user_paths
from web.models import BriefingRecommendation

logger = structlog.get_logger()

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


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


@router.get("", response_model=list[BriefingRecommendation])
async def list_recommendations(
    search: str | None = None,
    category: str | None = None,
    limit: int = Query(default=5, ge=1, le=20),
    user: dict = Depends(get_current_user),
):
    paths = get_user_paths(user["id"])
    rec_dir = paths.get("recommendations_dir")
    if not rec_dir:
        return []

    rec_storage = RecommendationStorage(rec_dir)
    ranked_watchlist_intel = _recent_watchlist_intel(user["id"])

    # Over-fetch for filtering headroom
    fetch_limit = limit * 3
    if category:
        recs = rec_storage.list_by_category(category, limit=fetch_limit)
    else:
        recs = rec_storage.list_recent(days=90, limit=fetch_limit)

    # Keyword search filter
    if search:
        keywords = search.lower().split()
        filtered = []
        for r in recs:
            text = f"{r.title} {r.description}".lower()
            if any(kw in text for kw in keywords):
                filtered.append(r)
        recs = filtered

    # Shape output like briefing.py
    results = []
    for r in recs[:limit]:
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
        results.append(
            BriefingRecommendation(
                id=r.id or "",
                category=r.category,
                title=r.title,
                description=r.description[:200] if r.description else "",
                score=r.score,
                status=r.status,
                reasoning_trace=meta.get("reasoning_trace"),
                critic=critic,
                watchlist_evidence=find_evidence_for_text(
                    f"{r.title}\n{r.description}", ranked_watchlist_intel, limit=2
                ),
            )
        )

    return results

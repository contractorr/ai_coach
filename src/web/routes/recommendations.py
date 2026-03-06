"""Recommendations query endpoint — text search + category filtering."""

from pathlib import Path

import frontmatter
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

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
from web.models import (
    BriefingRecommendation,
    RecommendationActionCreate,
    RecommendationActionItem,
    RecommendationActionUpdate,
    TrackedRecommendationAction,
    WeeklyPlanResponse,
)

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


def _get_storage(user_id: str) -> RecommendationStorage:
    paths = get_user_paths(user_id)
    rec_dir = paths.get("recommendations_dir")
    if not rec_dir:
        raise HTTPException(status_code=404, detail="Recommendations storage not configured")
    return RecommendationStorage(rec_dir)


def _resolve_goal_link(goal_path: str | None, user_id: str) -> tuple[str | None, str | None]:
    if not goal_path:
        return None, None

    paths = get_user_paths(user_id)
    journal_dir = paths["journal_dir"]
    resolved = Path(goal_path).resolve()
    if not resolved.is_relative_to(journal_dir):
        raise HTTPException(status_code=400, detail="Invalid goal path")
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Goal not found")

    try:
        post = frontmatter.load(resolved)
        title = str(post.metadata.get("title") or resolved.stem)
    except Exception:
        title = resolved.stem
    return str(resolved), title


def _shape_action_item(payload: dict | None) -> RecommendationActionItem | None:
    if not payload:
        return None
    return RecommendationActionItem(**payload)


def _shape_action_record(record) -> TrackedRecommendationAction:
    return TrackedRecommendationAction(
        recommendation_id=record.recommendation_id,
        recommendation_title=record.recommendation_title,
        category=record.category,
        score=record.score,
        recommendation_status=record.recommendation_status,
        created_at=record.created_at or "",
        action_item=RecommendationActionItem(**record.action_item),
    )


def _shape_recommendation(r, ranked_watchlist_intel: list[dict]) -> BriefingRecommendation:
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
    return BriefingRecommendation(
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
        action_item=_shape_action_item(meta.get("action_item")),
    )


@router.get("/actions", response_model=list[TrackedRecommendationAction])
async def list_action_items(
    status_filter: str | None = Query(default=None, alias="status"),
    goal_path: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    resolved_goal_path, _goal_title = _resolve_goal_link(goal_path, user["id"]) if goal_path else (None, None)
    records = storage.list_action_items(status=status_filter, goal_path=resolved_goal_path, limit=limit)
    return [_shape_action_record(record) for record in records]


@router.get("/weekly-plan", response_model=WeeklyPlanResponse)
async def weekly_plan(
    capacity_points: int = Query(default=6, ge=1, le=12),
    goal_path: str | None = None,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    resolved_goal_path, _goal_title = _resolve_goal_link(goal_path, user["id"]) if goal_path else (None, None)
    plan = storage.build_weekly_plan(capacity_points=capacity_points, goal_path=resolved_goal_path)
    return WeeklyPlanResponse(
        items=[_shape_action_record(record) for record in plan["items"]],
        capacity_points=plan["capacity_points"],
        used_points=plan["used_points"],
        remaining_points=plan["remaining_points"],
        generated_at=plan["generated_at"],
    )


@router.get("", response_model=list[BriefingRecommendation])
async def list_recommendations(
    search: str | None = None,
    category: str | None = None,
    limit: int = Query(default=5, ge=1, le=20),
    user: dict = Depends(get_current_user),
):
    rec_storage = _get_storage(user["id"])
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
    return [_shape_recommendation(r, ranked_watchlist_intel) for r in recs[:limit]]


@router.post(
    "/{rec_id}/action-item",
    response_model=TrackedRecommendationAction,
    status_code=status.HTTP_201_CREATED,
)
async def create_action_item(
    rec_id: str,
    body: RecommendationActionCreate,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    goal_path, goal_title = _resolve_goal_link(body.goal_path, user["id"]) if body.goal_path else (None, None)
    action_item = storage.create_action_item(
        rec_id,
        goal_path=goal_path,
        goal_title=goal_title,
        objective=body.objective,
        next_step=body.next_step,
        effort=body.effort,
        due_window=body.due_window,
        blockers=body.blockers,
        success_criteria=body.success_criteria,
    )
    if not action_item:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    record = storage.get_action_item(rec_id)
    if not record:
        raise HTTPException(status_code=500, detail="Action item was not persisted")
    return _shape_action_record(record)


@router.put("/{rec_id}/action-item", response_model=TrackedRecommendationAction)
async def update_action_item(
    rec_id: str,
    body: RecommendationActionUpdate,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    goal_path, goal_title = (None, None)
    if body.goal_path is not None:
        goal_path, goal_title = _resolve_goal_link(body.goal_path, user["id"])

    action_item = storage.update_action_item(
        rec_id,
        status=body.status,
        effort=body.effort,
        due_window=body.due_window,
        blockers=body.blockers,
        review_notes=body.review_notes,
        next_step=body.next_step,
        success_criteria=body.success_criteria,
        goal_path=goal_path,
        goal_title=goal_title,
    )
    if not action_item:
        raise HTTPException(status_code=404, detail="Tracked action not found")
    record = storage.get_action_item(rec_id)
    if not record:
        raise HTTPException(status_code=500, detail="Tracked action was not persisted")
    return _shape_action_record(record)

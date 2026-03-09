"""Recommendations query endpoint — text search + category filtering."""

from pathlib import Path

import frontmatter
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from advisor.outcomes import OutcomeHarvester
from advisor.why_now import WhyNowReasoner
from intelligence.watchlist import (
    annotate_items,
    find_evidence_for_text,
    sort_ranked_items,
)
from services.recommendation_actions import (
    build_weekly_plan as build_weekly_action_plan,
)
from services.recommendation_actions import (
    create_action_item as create_tracked_action,
)
from services.recommendation_actions import (
    list_action_items as list_tracked_actions,
)
from services.recommendation_actions import (
    update_action_item as update_tracked_action,
)
from web.auth import get_current_user
from web.deps import (
    get_intel_storage,
    get_outcome_store,
    get_recommendation_storage,
    get_user_paths,
    get_watchlist_store,
)
from web.models import (
    BriefingRecommendation,
    RecommendationActionCreate,
    RecommendationActionItem,
    RecommendationActionUpdate,
    RecommendationFeedbackRequest,
    RecommendationOutcomeOverrideRequest,
    RecommendationOutcomeResponse,
    TrackedRecommendationAction,
    WeeklyPlanResponse,
)
from web.user_store import log_event

logger = structlog.get_logger()

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def _recent_watchlist_intel(user_id: str) -> list[dict]:
    watchlist_items = get_watchlist_store(user_id).list_items()
    if not watchlist_items:
        return []

    intel_storage = get_intel_storage()
    items = intel_storage.get_recent(days=21, limit=80, include_duplicates=True)
    annotate_items(items, watchlist_items)
    return sort_ranked_items(items)


def _get_storage(user_id: str):
    paths = get_user_paths(user_id)
    rec_dir = paths.get("recommendations_dir")
    if not rec_dir:
        raise HTTPException(status_code=404, detail="Recommendations storage not configured")
    return get_recommendation_storage(user_id)


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
    payload = (
        record
        if isinstance(record, dict)
        else {
            "recommendation_id": record.recommendation_id,
            "recommendation_title": record.recommendation_title,
            "category": record.category,
            "score": record.score,
            "recommendation_status": record.recommendation_status,
            "created_at": record.created_at or "",
            "action_item": record.action_item,
        }
    )
    return TrackedRecommendationAction(
        recommendation_id=payload["recommendation_id"],
        recommendation_title=payload["recommendation_title"],
        category=payload["category"],
        score=payload["score"],
        recommendation_status=payload["recommendation_status"],
        created_at=payload.get("created_at") or "",
        action_item=RecommendationActionItem(**payload["action_item"]),
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
        user_rating=meta.get("user_rating"),
        feedback_comment=meta.get("feedback_comment"),
        feedback_at=meta.get("feedback_at"),
    )


@router.get("/actions", response_model=list[TrackedRecommendationAction])
async def list_action_items(
    status_filter: str | None = Query(default=None, alias="status"),
    goal_path: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    resolved_goal_path, _goal_title = (
        _resolve_goal_link(goal_path, user["id"]) if goal_path else (None, None)
    )
    result = list_tracked_actions(
        storage,
        status=status_filter,
        goal_path=resolved_goal_path,
        limit=limit,
    )
    return [_shape_action_record(record) for record in result["actions"]]


@router.get("/weekly-plan", response_model=WeeklyPlanResponse)
async def weekly_plan(
    capacity_points: int = Query(default=6, ge=1, le=12),
    goal_path: str | None = None,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    resolved_goal_path, _goal_title = (
        _resolve_goal_link(goal_path, user["id"]) if goal_path else (None, None)
    )
    plan = build_weekly_action_plan(
        storage,
        capacity_points=capacity_points,
        goal_path=resolved_goal_path,
    )
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
    harvester = OutcomeHarvester(get_outcome_store(user["id"]), rec_storage)
    reasoner = WhyNowReasoner()

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

    results = []
    for recommendation in recs[:limit]:
        shaped = _shape_recommendation(recommendation, ranked_watchlist_intel)
        harvested = harvester.evaluate_recommendation(
            {"id": recommendation.id, "metadata": recommendation.metadata or {}}
        )
        payload = shaped.model_dump()
        payload["harvested_outcome"] = harvested
        payload["why_now"] = reasoner.explain_recommendation(
            payload, {"recent_intel": ranked_watchlist_intel}
        )
        results.append(BriefingRecommendation(**payload))
    return results


@router.get("/{rec_id}/outcome", response_model=RecommendationOutcomeResponse | None)
async def get_recommendation_outcome(
    rec_id: str,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    outcome_store = get_outcome_store(user["id"])
    recommendation = storage.get(rec_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    harvester = OutcomeHarvester(outcome_store, storage)
    outcome = outcome_store.get(rec_id) or harvester.evaluate_recommendation(
        {"id": recommendation.id, "metadata": recommendation.metadata or {}}
    )
    return RecommendationOutcomeResponse(**outcome) if outcome else None


@router.post("/{rec_id}/outcome/override", response_model=RecommendationOutcomeResponse)
async def override_recommendation_outcome(
    rec_id: str,
    payload: RecommendationOutcomeOverrideRequest,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    outcome_store = get_outcome_store(user["id"])
    recommendation = storage.get(rec_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if not outcome_store.get(rec_id):
        OutcomeHarvester(outcome_store, storage).evaluate_recommendation(
            {"id": recommendation.id, "metadata": recommendation.metadata or {}}
        )
    outcome = outcome_store.override(rec_id, payload.state, payload.note)
    if not outcome:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return RecommendationOutcomeResponse(**outcome)


@router.post(
    "/{rec_id}/feedback",
    response_model=BriefingRecommendation,
    status_code=status.HTTP_200_OK,
)
async def add_recommendation_feedback(
    rec_id: str,
    payload: RecommendationFeedbackRequest,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    added = storage.add_feedback(rec_id, payload.rating, payload.comment)
    if not added:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    recommendation = storage.get(rec_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    log_event(
        "recommendation_feedback",
        user["id"],
        {
            "recommendation_id": rec_id,
            "category": recommendation.category,
            "rating": payload.rating,
            "score": 1 if payload.rating >= 4 else (-1 if payload.rating <= 2 else 0),
        },
    )

    ranked_watchlist_intel = _recent_watchlist_intel(user["id"])
    shaped = _shape_recommendation(recommendation, ranked_watchlist_intel)
    outcome = get_outcome_store(user["id"]).get(rec_id)
    payload = shaped.model_dump()
    payload["harvested_outcome"] = outcome
    payload["why_now"] = WhyNowReasoner().explain_recommendation(
        payload, {"recent_intel": ranked_watchlist_intel}
    )
    return BriefingRecommendation(**payload)


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
    payload = body.model_dump()
    goal_path_value = payload.get("goal_path")
    goal_path, goal_title = (
        _resolve_goal_link(goal_path_value, user["id"]) if goal_path_value else (None, None)
    )
    result = create_tracked_action(
        storage,
        rec_id,
        goal_path=goal_path,
        goal_title=goal_title,
        objective=payload.get("objective"),
        next_step=payload.get("next_step"),
        effort=payload.get("effort"),
        due_window=payload.get("due_window"),
        blockers=payload.get("blockers"),
        success_criteria=payload.get("success_criteria"),
    )
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if not result["persisted"] or not result["record"]:
        raise HTTPException(status_code=500, detail="Action item was not persisted")
    return _shape_action_record(result["record"])


@router.put("/{rec_id}/action-item", response_model=TrackedRecommendationAction)
async def update_action_item(
    rec_id: str,
    body: RecommendationActionUpdate,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    payload = body.model_dump()
    goal_path, goal_title = (None, None)
    goal_path_value = payload.get("goal_path")
    if goal_path_value is not None:
        goal_path, goal_title = _resolve_goal_link(goal_path_value, user["id"])

    result = update_tracked_action(
        storage,
        rec_id,
        status=payload.get("status"),
        effort=payload.get("effort"),
        due_window=payload.get("due_window"),
        blockers=payload.get("blockers"),
        review_notes=payload.get("review_notes"),
        next_step=payload.get("next_step"),
        success_criteria=payload.get("success_criteria"),
        goal_path=goal_path,
        goal_title=goal_title,
    )
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Tracked action not found")
    if not result["persisted"] or not result["record"]:
        raise HTTPException(status_code=500, detail="Tracked action was not persisted")
    return _shape_action_record(result["record"])

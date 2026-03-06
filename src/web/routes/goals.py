"""Goals CRUD routes wrapping advisor/goals.py (per-user)."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from advisor.goals import GoalTracker
from journal.storage import JournalStorage
from web.auth import get_current_user
from web.deps import get_user_paths
from web.models import GoalCheckIn, GoalCreate, GoalStatusUpdate, MilestoneAdd, MilestoneComplete
from web.user_store import log_event

router = APIRouter(prefix="/api/goals", tags=["goals"])


def _get_storage(user_id: str) -> JournalStorage:
    paths = get_user_paths(user_id)
    return JournalStorage(paths["journal_dir"])


def _get_tracker(user_id: str) -> GoalTracker:
    storage = _get_storage(user_id)
    return GoalTracker(storage)


def _validate_goal_path(filepath: str, user_id: str) -> Path:
    """Validate path is inside the user's journal dir (prevent traversal)."""
    paths = get_user_paths(user_id)
    journal_dir = paths["journal_dir"]
    resolved = Path(filepath).resolve()
    if not resolved.is_relative_to(journal_dir):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Goal not found")
    return resolved


@router.get("")
async def list_goals(
    include_inactive: bool = False,
    user: dict = Depends(get_current_user),
):
    tracker = _get_tracker(user["id"])
    goals = tracker.get_goals(include_inactive=include_inactive)
    for g in goals:
        g["path"] = str(g["path"])
    return goals


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_goal(
    body: GoalCreate,
    user: dict = Depends(get_current_user),
):
    from advisor.goals import get_goal_defaults

    storage = _get_storage(user["id"])
    try:
        filepath = storage.create(
            content=body.content,
            entry_type="goal",
            title=body.title,
            tags=body.tags,
            metadata=get_goal_defaults(),
        )
        log_event("goal_created", user["id"])
        return {"path": str(filepath), "title": body.title}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{filepath:path}/check-in")
async def check_in(
    filepath: str,
    body: GoalCheckIn,
    user: dict = Depends(get_current_user),
):
    resolved = _validate_goal_path(filepath, user["id"])
    tracker = _get_tracker(user["id"])
    success = tracker.check_in_goal(resolved, notes=body.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Invalidate greeting cache on check-in
    try:
        from advisor.context_cache import ContextCache
        from advisor.greeting import invalidate_greeting
        from web.deps import get_user_paths as _gup

        paths = _gup(user["id"])
        cache_db = paths["intel_db"].parent / "context_cache.db"
        cache = ContextCache(cache_db)
        invalidate_greeting(user["id"], cache)
    except Exception:
        pass

    return {"ok": True}


@router.put("/{filepath:path}/status")
async def update_status(
    filepath: str,
    body: GoalStatusUpdate,
    user: dict = Depends(get_current_user),
):
    resolved = _validate_goal_path(filepath, user["id"])
    tracker = _get_tracker(user["id"])
    success = tracker.update_goal_status(resolved, body.status)
    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True}


@router.post("/{filepath:path}/milestones")
async def add_milestone(
    filepath: str,
    body: MilestoneAdd,
    user: dict = Depends(get_current_user),
):
    resolved = _validate_goal_path(filepath, user["id"])
    tracker = _get_tracker(user["id"])
    success = tracker.add_milestone(resolved, body.title)
    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"ok": True}


@router.post("/{filepath:path}/milestones/complete")
async def complete_milestone(
    filepath: str,
    body: MilestoneComplete,
    user: dict = Depends(get_current_user),
):
    resolved = _validate_goal_path(filepath, user["id"])
    tracker = _get_tracker(user["id"])
    success = tracker.complete_milestone(resolved, body.milestone_index)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid milestone")
    return {"ok": True}


@router.get("/{filepath:path}/progress")
async def get_progress(
    filepath: str,
    user: dict = Depends(get_current_user),
):
    resolved = _validate_goal_path(filepath, user["id"])
    tracker = _get_tracker(user["id"])
    return tracker.get_progress(resolved)

"""User profile (name, email) routes."""

import shutil
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from web.auth import get_current_user
from web.deps import safe_user_id
from web.models import UserMe, UserMeUpdate
from web.user_store import delete_user, get_user_name, log_event, update_user_name

logger = structlog.get_logger()

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/me", response_model=UserMe)
async def get_me(user: dict = Depends(get_current_user)):
    # Prefer DB name (set during onboarding) over JWT/OAuth name
    db_name = get_user_name(user["id"])
    return UserMe(name=db_name or user.get("name"), email=user.get("email"))


@router.patch("/me", response_model=UserMe)
async def update_me(body: UserMeUpdate, user: dict = Depends(get_current_user)):
    if body.name is not None:
        update_user_name(user["id"], body.name.strip())
        logger.info("user.name_updated", user_id=user["id"])
    name = get_user_name(user["id"])
    return UserMe(name=name, email=user.get("email"))


@router.delete("/me", status_code=204)
async def delete_me(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    log_event("account_deleted", user_id=user_id)
    delete_user(user_id)
    # Best-effort filesystem cleanup
    user_dir = Path.home() / "coach" / "users" / safe_user_id(user_id)
    try:
        if user_dir.exists():
            shutil.rmtree(user_dir)
    except Exception:
        logger.warning("user.data_dir_cleanup_failed", user_id=user_id, path=str(user_dir))
    return Response(status_code=204)

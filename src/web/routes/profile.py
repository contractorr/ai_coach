"""Profile view/edit API routes."""

import structlog
from fastapi import APIRouter, Depends, HTTPException

from services.profile import get_profile_payload, update_profile_fields
from web.auth import get_current_user
from web.deps import get_profile_embedding_manager, get_profile_storage
from web.models import ProfileResponse, ProfileUpdate

logger = structlog.get_logger()

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _embed_profile(user_id: str, profile) -> None:
    """Re-embed profile in ChromaDB after update."""
    try:
        em = get_profile_embedding_manager(user_id)
        parts = [profile.summary()]
        if profile.goals_short_term:
            parts.append(f"Short-term goals: {profile.goals_short_term}")
        if profile.goals_long_term:
            parts.append(f"Long-term vision: {profile.goals_long_term}")
        if profile.fears_risks:
            parts.append("Concerns: " + ", ".join(profile.fears_risks))
        if profile.active_projects:
            parts.append("Active projects: " + ", ".join(profile.active_projects))
        text = "\n".join(parts)
        em.add_entry(f"profile:{user_id}", text, {"type": "profile", "user_id": user_id})
    except Exception as e:
        logger.warning("profile.embed_failed", error=str(e))


@router.get("", response_model=ProfileResponse)
async def get_profile(user: dict = Depends(get_current_user)):
    storage = get_profile_storage(user["id"])
    payload = get_profile_payload(storage)
    if not payload["exists"]:
        return ProfileResponse()
    return ProfileResponse(**payload["profile"])


@router.patch("")
async def update_profile(
    body: ProfileUpdate,
    user: dict = Depends(get_current_user),
):
    storage = get_profile_storage(user["id"])
    updates = body.model_dump(exclude_none=True)

    try:
        profile, updated_fields = update_profile_fields(
            storage,
            updates,
            embed_callback=lambda profile: _embed_profile(user["id"], profile),
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 400
        raise HTTPException(status_code=status_code, detail=detail)

    return {"ok": True, "updated_fields": updated_fields}

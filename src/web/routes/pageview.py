"""Page view tracking route."""

from fastapi import APIRouter, Depends

from web.auth import get_current_user
from web.user_store import log_event

router = APIRouter(tags=["analytics"])

_ALLOWED_PATHS = {
    "/",
    "/journal",
    "/focus",
    "/goals",
    "/radar",
    "/intel",
    "/library",
    "/settings",
}


@router.post("/api/page-view", status_code=204)
async def track_page_view(body: dict, user: dict = Depends(get_current_user)):
    path = body.get("path", "")
    if path in _ALLOWED_PATHS:
        log_event("page_view", user["id"], {"path": path})

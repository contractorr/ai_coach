"""Thread routes ? journal recurrence detection."""

from fastapi import APIRouter, Depends, HTTPException

from web.auth import get_current_user
from web.deps import get_thread_store
from web.models import ThreadDetail, ThreadEntryItem, ThreadSummary

router = APIRouter(prefix="/api/threads", tags=["threads"])


def _get_store(user_id: str):
    return get_thread_store(user_id)


@router.get("", response_model=list[ThreadSummary])
async def list_threads(
    min_entries: int = 2,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    threads = await store.get_active_threads(min_entries=min_entries)

    result = []
    for t in threads:
        entries = await store.get_thread_entries(t.id)
        dates = [e.entry_date.strftime("%Y-%m-%d") for e in entries]
        result.append(
            ThreadSummary(
                id=t.id,
                label=t.label,
                entry_count=t.entry_count,
                first_date=min(dates) if dates else "",
                last_date=max(dates) if dates else "",
                status=t.status,
            )
        )
    return result


@router.get("/{thread_id}", response_model=ThreadDetail)
async def get_thread(
    thread_id: str,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    thread = await store.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    entries = await store.get_thread_entries(thread_id)
    return ThreadDetail(
        id=thread.id,
        label=thread.label,
        entry_count=thread.entry_count,
        entries=[
            ThreadEntryItem(
                entry_id=e.entry_id,
                entry_date=e.entry_date.strftime("%Y-%m-%d"),
                similarity=round(e.similarity, 3),
            )
            for e in entries
        ],
    )

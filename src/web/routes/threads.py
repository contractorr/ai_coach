"""Thread routes ? journal recurrence detection."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException

from web.auth import get_current_user
from web.deps import (
    get_thread_inbox_service,
    get_thread_inbox_state_store,
    get_thread_store,
    get_user_paths,
)
from web.models import (
    ThreadDetail,
    ThreadInboxDetail,
    ThreadInboxStateUpdate,
    ThreadInboxSummary,
    ThreadSummary,
)

router = APIRouter(prefix="/api/threads", tags=["threads"])


def _get_store(user_id: str):
    return get_thread_store(user_id)


def _get_inbox(user_id: str):
    return get_thread_inbox_service(user_id)


@router.get("", response_model=list[ThreadSummary])
async def list_threads(
    min_entries: int = 2,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    threads = await store.get_active_threads(min_entries=min_entries)

    result = []
    for t in threads:
        detail = await _get_inbox(user["id"]).get_thread_detail(t.id)
        if detail:
            result.append(
                ThreadSummary(
                    **{
                        key: value
                        for key, value in detail.items()
                        if key != "entries" and key != "available_actions"
                    }
                )
            )
    return result


@router.get("/inbox", response_model=list[ThreadInboxSummary])
async def list_thread_inbox(
    state: str | None = None,
    query: str = "",
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    rows = await _get_inbox(user["id"]).list_inbox(state=state, query=query, limit=limit)
    return [
        ThreadInboxSummary(
            **{
                key: value
                for key, value in row.items()
                if key != "entries" and key != "available_actions"
            }
        )
        for row in rows
    ]


@router.get("/{thread_id}", response_model=ThreadDetail)
async def get_thread(
    thread_id: str,
    user: dict = Depends(get_current_user),
):
    detail = await _get_inbox(user["id"]).get_thread_detail(thread_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadDetail(**detail)


@router.patch("/{thread_id}/state", response_model=ThreadInboxDetail)
async def update_thread_state(
    thread_id: str,
    body: ThreadInboxStateUpdate,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    thread = await store.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    get_thread_inbox_state_store(user["id"]).upsert_state(
        thread_id,
        inbox_state=body.inbox_state,
        linked_goal_path=body.linked_goal_path,
        linked_dossier_id=body.linked_dossier_id,
        last_action=body.last_action,
    )
    detail = await _get_inbox(user["id"]).get_thread_detail(thread_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadInboxDetail(**detail)


@router.post("/{thread_id}/actions/make-goal")
async def make_goal_from_thread(
    thread_id: str,
    user: dict = Depends(get_current_user),
):
    from advisor.goals import get_goal_defaults
    from journal.storage import JournalStorage

    detail = await _get_inbox(user["id"]).get_thread_detail(thread_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Thread not found")
    paths = get_user_paths(user["id"])
    storage = JournalStorage(paths["journal_dir"])
    filepath = storage.create(
        content=f"Goal created from recurring thread: {detail['label']}",
        entry_type="goal",
        title=detail["label"],
        metadata=get_goal_defaults(),
    )
    get_thread_inbox_state_store(user["id"]).upsert_state(
        thread_id,
        inbox_state="goal_created",
        linked_goal_path=str(filepath),
        last_action="goal_created",
    )
    return {"path": str(filepath), "title": detail["label"]}


@router.post("/{thread_id}/actions/run-research")
async def run_research_from_thread(
    thread_id: str,
    user: dict = Depends(get_current_user),
):
    from web.routes.research import _get_agent

    detail = await _get_inbox(user["id"]).get_thread_detail(thread_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Thread not found")
    agent = _get_agent(user["id"])
    results = await asyncio.to_thread(agent.run, specific_topic=detail["label"], dossier_id=None)
    get_thread_inbox_state_store(user["id"]).upsert_state(
        thread_id,
        inbox_state="research_started",
        last_action="research_started",
    )
    return {"results": results}


@router.post("/{thread_id}/actions/start-dossier")
async def start_dossier_from_thread(
    thread_id: str,
    user: dict = Depends(get_current_user),
):
    from web.routes.research import _get_agent

    detail = await _get_inbox(user["id"]).get_thread_detail(thread_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Thread not found")
    agent = _get_agent(user["id"])
    dossier = await asyncio.to_thread(
        agent.create_dossier,
        topic=detail["label"],
        scope=f"Created from recurring thread '{detail['label']}'",
    )
    get_thread_inbox_state_store(user["id"]).upsert_state(
        thread_id,
        inbox_state="dossier_started",
        linked_dossier_id=(dossier or {}).get("dossier_id"),
        last_action="dossier_started",
    )
    return dossier


@router.post("/reindex")
async def reindex_threads(
    user: dict = Depends(get_current_user),
):
    from journal.embeddings import EmbeddingManager
    from journal.threads import ThreadDetector
    from web.deps import get_config, safe_user_id

    paths = get_user_paths(user["id"])
    config = get_config()
    threads_cfg = config.threads
    embeddings = EmbeddingManager(
        paths["chroma_dir"], collection_name=f"journal_{safe_user_id(user['id'])}"
    )
    store = get_thread_store(user["id"])
    detector = ThreadDetector(
        embeddings,
        store,
        {
            "similarity_threshold": threads_cfg.similarity_threshold,
            "candidate_count": threads_cfg.candidate_count,
            "min_entries_for_thread": threads_cfg.min_entries_for_thread,
        },
    )
    stats = await detector.reindex_all()
    get_thread_inbox_state_store(user["id"]).clear_all()
    return stats

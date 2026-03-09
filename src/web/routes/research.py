"""Research routes wrapping `src/research/agent.py` for each user."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from web.auth import get_current_user
from web.deps import (
    get_config,
    get_intel_storage,
    get_user_paths,
    require_personal_research_key,
    safe_user_id,
)

router = APIRouter(prefix="/api/research", tags=["research"])


class DossierCreateRequest(BaseModel):
    topic: str
    scope: str = ""
    core_questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    related_goals: list[str] = Field(default_factory=list)
    tracked_subtopics: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


def _get_agent(user_id: str):
    from journal.embeddings import EmbeddingManager
    from journal.storage import JournalStorage
    from research.agent import DeepResearchAgent

    config = get_config()
    paths = get_user_paths(user_id)

    journal_storage = JournalStorage(paths["journal_dir"])
    embeddings = EmbeddingManager(
        paths["chroma_dir"],
        collection_name=f"journal_{safe_user_id(user_id)}",
    )
    intel_storage = get_intel_storage()

    cfg = config.to_dict()

    from web.deps import get_secret_key
    from web.user_store import get_user_secret

    try:
        tavily_key = get_user_secret(user_id, "tavily_api_key", get_secret_key())
        if tavily_key:
            cfg.setdefault("research", {})["api_key"] = tavily_key
    except Exception:
        pass

    return DeepResearchAgent(
        journal_storage=journal_storage,
        intel_storage=intel_storage,
        embeddings=embeddings,
        config=cfg,
    )


@router.get("/topics")
async def get_topics(
    user: dict = Depends(get_current_user),
    _private_key: None = Depends(require_personal_research_key),
):
    try:
        agent = _get_agent(user["id"])
        return await asyncio.to_thread(agent.get_suggested_topics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_research(
    topic: str | None = None,
    dossier_id: str | None = None,
    user: dict = Depends(get_current_user),
    _private_key: None = Depends(require_personal_research_key),
):
    try:
        agent = _get_agent(user["id"])
        results = await asyncio.to_thread(agent.run, specific_topic=topic, dossier_id=dossier_id)
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dossiers")
async def list_dossiers(
    include_archived: bool = False,
    limit: int = 50,
    user: dict = Depends(get_current_user),
    _private_key: None = Depends(require_personal_research_key),
):
    try:
        agent = _get_agent(user["id"])
        return await asyncio.to_thread(agent.list_dossiers, include_archived, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dossiers")
async def create_dossier(
    payload: DossierCreateRequest,
    user: dict = Depends(get_current_user),
    _private_key: None = Depends(require_personal_research_key),
):
    try:
        agent = _get_agent(user["id"])
        return await asyncio.to_thread(
            agent.create_dossier,
            topic=payload.topic,
            scope=payload.scope,
            core_questions=payload.core_questions,
            assumptions=payload.assumptions,
            related_goals=payload.related_goals,
            tracked_subtopics=payload.tracked_subtopics,
            open_questions=payload.open_questions,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dossiers/{dossier_id}")
async def get_dossier(
    dossier_id: str,
    user: dict = Depends(get_current_user),
    _private_key: None = Depends(require_personal_research_key),
):
    try:
        agent = _get_agent(user["id"])
        dossier = await asyncio.to_thread(agent.get_dossier, dossier_id)
        if not dossier:
            raise HTTPException(status_code=404, detail="Dossier not found")
        return dossier
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

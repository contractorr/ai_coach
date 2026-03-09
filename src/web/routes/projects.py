"""Project discovery routes — matching issues + idea generation."""

import asyncio

import structlog
from fastapi import APIRouter, Depends, HTTPException

from services.projects import discover_matching_project_issues, generate_project_ideas
from web.auth import get_current_user
from web.deps import (
    get_api_key_for_user,
    get_config,
    get_intel_storage,
    get_profile_path,
    get_profile_storage,
    get_user_paths,
    safe_user_id,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/issues")
async def get_issues(
    limit: int = 20,
    days: int = 14,
    user: dict = Depends(get_current_user),
):
    """Get GitHub issues matching user profile."""
    try:
        intel = get_intel_storage()

        profile = None
        try:
            profile = get_profile_storage(user["id"]).load()
        except Exception:
            pass

        payload = discover_matching_project_issues(intel, profile=profile, limit=limit, days=days)
        return payload["issues"]
    except Exception as e:
        logger.error("projects.issues_error", error=str(e))
        return []


@router.post("/ideas")
async def generate_ideas(
    user: dict = Depends(get_current_user),
):
    """Generate project ideas via LLM."""
    user_id = user["id"]
    config = get_config()
    api_key = get_api_key_for_user(user_id, config.llm.provider)
    if not api_key:
        raise HTTPException(status_code=400, detail="No LLM API key configured")

    try:
        from advisor.rag import RAGRetriever
        from journal.embeddings import EmbeddingManager
        from journal.fts import JournalFTSIndex
        from journal.search import JournalSearch
        from journal.storage import JournalStorage
        from llm.factory import create_llm_provider

        paths = get_user_paths(user_id)
        journal_storage = JournalStorage(paths["journal_dir"])
        embeddings = EmbeddingManager(
            paths["chroma_dir"],
            collection_name=f"journal_{safe_user_id(user_id)}",
        )
        fts_index = JournalFTSIndex(paths["journal_dir"])
        journal_search = JournalSearch(journal_storage, embeddings, fts_index=fts_index)

        rag = RAGRetriever(
            journal_search=journal_search,
            intel_db_path=paths["intel_db"],
            profile_path=str(get_profile_path(user_id)),
        )

        provider = create_llm_provider(
            provider=config.llm.provider,
            api_key=api_key,
            model=config.llm.model,
        )

        def llm_caller(system, prompt, max_tokens=2000):
            return provider.generate(system=system, prompt=prompt, max_tokens=max_tokens)

        ideas = await asyncio.to_thread(generate_project_ideas, rag, llm_caller)
        return {"ideas": ideas}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("projects.ideas_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

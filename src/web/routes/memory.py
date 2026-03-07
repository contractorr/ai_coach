"""Memory routes ? list, search, delete facts, stats, backfill."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from memory.models import FactCategory
from web.auth import get_current_user
from web.deps import get_memory_store
from web.models import MemoryFact, MemoryStats

logger = structlog.get_logger()

router = APIRouter(prefix="/api/memory", tags=["memory"])


def _get_store(user_id: str):
    return get_memory_store(user_id)


@router.get("/facts", response_model=list[MemoryFact])
async def list_facts(
    category: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    """List active facts, optionally filtered by category."""
    store = _get_store(user["id"])

    if category:
        try:
            cat = FactCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        facts = store.get_by_category(cat)[:limit]
    else:
        facts = store.get_all_active()[:limit]

    return [
        MemoryFact(
            id=f.id,
            text=f.text,
            category=f.category.value,
            source_type=f.source_type.value,
            source_id=f.source_id,
            confidence=f.confidence,
            created_at=f.created_at.isoformat() if f.created_at else "",
            updated_at=f.updated_at.isoformat() if f.updated_at else "",
        )
        for f in facts
    ]


@router.get("/facts/{fact_id}", response_model=MemoryFact)
async def get_fact(
    fact_id: str,
    user: dict = Depends(get_current_user),
):
    """Get a single fact with details."""
    store = _get_store(user["id"])
    fact = store.get(fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    return MemoryFact(
        id=fact.id,
        text=fact.text,
        category=fact.category.value,
        source_type=fact.source_type.value,
        source_id=fact.source_id,
        confidence=fact.confidence,
        created_at=fact.created_at.isoformat() if fact.created_at else "",
        updated_at=fact.updated_at.isoformat() if fact.updated_at else "",
    )


@router.delete("/facts/{fact_id}")
async def delete_fact(
    fact_id: str,
    user: dict = Depends(get_current_user),
):
    """Soft-delete a fact."""
    store = _get_store(user["id"])
    fact = store.get(fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    store.delete(fact_id, reason="web_delete")
    return {"ok": True}


@router.get("/stats", response_model=MemoryStats)
async def get_stats(
    user: dict = Depends(get_current_user),
):
    """Get fact counts by category."""
    store = _get_store(user["id"])
    stats = store.get_stats()
    return MemoryStats(
        total_active=stats["total_active"],
        total_superseded=stats["total_superseded"],
        by_category=stats["by_category"],
    )

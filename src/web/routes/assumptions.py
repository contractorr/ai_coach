"""Assumption watchlist routes."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from advisor.assumptions import AssumptionSignalMatcher, MemoryAdapter
from web.auth import get_current_user
from web.deps import (
    get_assumption_store,
    get_company_movement_store,
    get_hiring_signal_store,
    get_memory_store,
    get_regulatory_alert_store,
)
from web.models import AssumptionCreate, AssumptionResponse, AssumptionUpdate

router = APIRouter(prefix="/api/assumptions", tags=["assumptions"])


def _candidate_signals() -> list[dict]:
    signals = []
    try:
        signals.extend(
            get_company_movement_store().get_since(datetime.now() - timedelta(days=30), limit=100)
        )
    except Exception:
        pass
    try:
        signals.extend(get_hiring_signal_store().get_recent(limit=100))
    except Exception:
        pass
    try:
        signals.extend(
            get_regulatory_alert_store().get_recent(datetime.now() - timedelta(days=60), limit=100)
        )
    except Exception:
        pass
    return signals


@router.get("", response_model=list[AssumptionResponse])
async def list_assumptions(user: dict = Depends(get_current_user)):
    store = get_assumption_store(user["id"])
    matcher = AssumptionSignalMatcher(store)
    signals = _candidate_signals()
    assumptions = store.list_active(limit=100)
    for assumption in assumptions:
        for evidence in matcher.evaluate(assumption, signals)[:3]:
            if not any(
                existing.get("source_ref") == evidence["source_ref"]
                for existing in assumption.get("evidence") or []
            ):
                store.append_evidence(assumption["id"], evidence)
        refreshed = store.get(assumption["id"])
        if refreshed:
            if any(
                item.get("evidence_state") == "confirming"
                for item in refreshed.get("evidence") or []
            ):
                store.update_status(assumption["id"], "confirmed")
            elif any(
                item.get("evidence_state") == "invalidating"
                for item in refreshed.get("evidence") or []
            ):
                store.update_status(assumption["id"], "invalidated")
    return [AssumptionResponse(**item) for item in store.list_active(limit=100)]


@router.post("", response_model=AssumptionResponse)
async def create_assumption(body: AssumptionCreate, user: dict = Depends(get_current_user)):
    store = get_assumption_store(user["id"])
    assumption_id = store.create(body.model_dump())
    assumption = store.get(assumption_id)
    if not assumption:
        raise HTTPException(status_code=500, detail="Failed to create assumption")
    return AssumptionResponse(**assumption)


@router.patch("/{assumption_id}", response_model=AssumptionResponse)
async def update_assumption(
    assumption_id: str, body: AssumptionUpdate, user: dict = Depends(get_current_user)
):
    store = get_assumption_store(user["id"])
    assumption = store.get(assumption_id)
    if not assumption:
        raise HTTPException(status_code=404, detail="Assumption not found")
    status = body.status or assumption["status"]
    updated = store.update_status(assumption_id, status)
    if body.latest_evidence_summary:
        store.append_evidence(
            assumption_id,
            {
                "evidence_kind": "manual",
                "evidence_state": "informational",
                "source_ref": assumption_id,
                "excerpt": body.latest_evidence_summary,
                "confidence": 1.0,
            },
        )
    refreshed = store.get(assumption_id)
    if not updated or not refreshed:
        raise HTTPException(status_code=404, detail="Assumption not found")
    return AssumptionResponse(**refreshed)


def _transition_assumption(user_id: str, assumption_id: str, status: str) -> dict:
    store = get_assumption_store(user_id)
    updated = store.update_status(assumption_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Assumption not found")
    try:
        MemoryAdapter(get_memory_store(user_id)).write_for_assumption(updated)
    except Exception:
        pass
    refreshed = store.get(assumption_id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="Assumption not found")
    return refreshed


@router.post("/{assumption_id}/activate", response_model=AssumptionResponse)
async def activate_assumption(assumption_id: str, user: dict = Depends(get_current_user)):
    return AssumptionResponse(**_transition_assumption(user["id"], assumption_id, "active"))


@router.post("/{assumption_id}/resolve", response_model=AssumptionResponse)
async def resolve_assumption(assumption_id: str, user: dict = Depends(get_current_user)):
    return AssumptionResponse(**_transition_assumption(user["id"], assumption_id, "resolved"))


@router.post("/{assumption_id}/archive", response_model=AssumptionResponse)
async def archive_assumption(assumption_id: str, user: dict = Depends(get_current_user)):
    return AssumptionResponse(**_transition_assumption(user["id"], assumption_id, "archived"))

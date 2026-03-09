"""Dossier escalation routes."""

import asyncio
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from research.escalation import DossierEscalationEngine
from web.auth import get_current_user
from web.deps import (
    get_dossier_escalation_store,
)
from web.dossier_escalation_context import load_dossier_escalation_context
from web.models import DossierEscalationResponse, DossierEscalationSnoozeRequest
from web.routes.research import _get_agent

router = APIRouter(prefix="/api/dossier-escalations", tags=["dossier-escalations"])


async def _build_engine(user_id: str):
    store = get_dossier_escalation_store(user_id)
    context = await load_dossier_escalation_context(user_id, goals=[])
    return DossierEscalationEngine(store), context


@router.get("", response_model=list[DossierEscalationResponse])
async def list_dossier_escalations(user: dict = Depends(get_current_user)):
    engine, context = await _build_engine(user["id"])
    rows = engine.refresh(context)
    return [DossierEscalationResponse(**row) for row in rows]


@router.post("/{escalation_id}/dismiss", response_model=DossierEscalationResponse)
async def dismiss_dossier_escalation(escalation_id: str, user: dict = Depends(get_current_user)):
    store = get_dossier_escalation_store(user["id"])
    if not store.dismiss(escalation_id):
        raise HTTPException(status_code=404, detail="Escalation not found")
    row = store.get(escalation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return DossierEscalationResponse(**row)


@router.post("/{escalation_id}/snooze", response_model=DossierEscalationResponse)
async def snooze_dossier_escalation(
    escalation_id: str,
    body: DossierEscalationSnoozeRequest,
    user: dict = Depends(get_current_user),
):
    until = body.until or (datetime.now() + timedelta(days=14)).isoformat()
    store = get_dossier_escalation_store(user["id"])
    if not store.snooze(escalation_id, until):
        raise HTTPException(status_code=404, detail="Escalation not found")
    row = store.get(escalation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return DossierEscalationResponse(**row)


@router.post("/{escalation_id}/accept", response_model=DossierEscalationResponse)
async def accept_dossier_escalation(escalation_id: str, user: dict = Depends(get_current_user)):
    store = get_dossier_escalation_store(user["id"])
    existing = store.get(escalation_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if existing.get("state") == "accepted" and existing.get("accepted_dossier_id"):
        return DossierEscalationResponse(**existing)
    prefill = DossierEscalationEngine(store).build_prefill(escalation_id)
    if not prefill or not prefill.get("topic"):
        raise HTTPException(status_code=400, detail="Escalation is missing topic data")
    dossier = await asyncio.to_thread(
        _get_agent(user["id"]).create_dossier,
        topic=prefill["topic"],
        scope=prefill.get("scope", ""),
        core_questions=prefill.get("core_questions") or [],
        assumptions=prefill.get("assumptions") or [],
        tracked_subtopics=prefill.get("tracked_subtopics") or [],
    )
    dossier_id = (dossier or {}).get("dossier_id")
    if not dossier_id:
        raise HTTPException(status_code=500, detail="Failed to create dossier")
    store.accept(escalation_id, dossier_id)
    row = store.get(escalation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return DossierEscalationResponse(**row)

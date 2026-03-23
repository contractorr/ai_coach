"""Advisor routes wrapping AdvisorEngine (per-user)."""

import asyncio
import json
from contextlib import suppress
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from starlette.responses import StreamingResponse

from advisor.council import CouncilMember
from library.pdf_text import extract_text_from_pdf_bytes
from library.reports import ReportStore
from services.advice import (
    ConversationNotFoundError,
    finish_conversation_turn,
    run_advice,
    start_conversation_turn,
)
from web.auth import get_current_user
from web.conversation_store import (
    add_message,
    conversation_belongs_to,
    create_conversation,
    delete_conversation,
    delete_message,
    get_conversation,
    get_messages,
    list_conversations,
)
from web.deps import (
    SHARED_LLM_MODEL,
    enforce_shared_key_usage_limit,
    get_coach_paths,
    get_config,
    get_council_members_for_user,
    get_intel_storage,
    get_library_index,
    get_memory_store,
    get_profile_path,
    get_thread_store,
    get_user_paths,
    resolve_llm_credentials_for_user,
    safe_user_id,
)
from web.models import (
    AdvisorAsk,
    AdvisorResponse,
    ChatAttachmentResponse,
    ConversationDetail,
    ConversationListItem,
    ConversationMessage,
    TraceDetail,
    TraceListItem,
)
from web.user_store import get_default_db_path, log_event

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


def _get_library_store(user_id: str) -> ReportStore:
    paths = get_user_paths(user_id)
    return ReportStore(Path(paths["data_dir"]) / "library")


def _get_library_index(user_id: str):
    return get_library_index(user_id)


def _resolve_attachment_records(user_id: str, attachment_ids: list[str] | None) -> list[dict]:
    if not attachment_ids:
        return []

    records: list[dict] = []
    seen: set[str] = set()
    store = _get_library_store(user_id)
    for attachment_id in attachment_ids:
        if attachment_id in seen:
            continue
        seen.add(attachment_id)
        record = store.get_report(attachment_id)
        if not record or record.get("source_kind") != "uploaded_pdf":
            raise HTTPException(status_code=404, detail=f"Attachment not found: {attachment_id}")
        if record.get("index_status") not in {"ready", "limited_text"}:
            raise HTTPException(status_code=422, detail=f"Attachment is not ready: {attachment_id}")
        records.append(
            {
                "library_item_id": record["id"],
                "file_name": record.get("file_name"),
                "mime_type": record.get("mime_type"),
            }
        )
    return records


def _validate_attachment_upload(
    file_name: str | None, payload: bytes, content_type: str | None
) -> None:
    from web.routes.library import _validate_pdf_upload

    _validate_pdf_upload(file_name, payload, content_type)


@router.post("/attachments", response_model=ChatAttachmentResponse)
async def upload_chat_attachment(
    file: UploadFile = File(...),
    conversation_id: str | None = Form(default=None),
    user: dict = Depends(get_current_user),
):
    from web.routes.library import (
        _derive_document_title,
        _get_index,
        _get_store,
        _index_record,
        _process_document_memory,
    )

    if conversation_id and not conversation_belongs_to(conversation_id, user["id"]):
        raise HTTPException(status_code=404, detail="Conversation not found")

    payload = await file.read()
    _validate_attachment_upload(file.filename, payload, file.content_type)
    extracted_text = extract_text_from_pdf_bytes(payload)
    extraction_status = "ready" if extracted_text.strip() else "empty"
    index_status = "ready" if extracted_text.strip() else "limited_text"
    store = _get_store(user["id"])
    report = store.create_uploaded_pdf(
        title=_derive_document_title(file.filename or "document.pdf"),
        file_name=file.filename or "document.pdf",
        file_bytes=payload,
        mime_type=file.content_type or "application/pdf",
        extracted_text=extracted_text,
        extraction_status=extraction_status,
        origin_surface="chat",
        visibility_state="hidden",
        index_status=index_status,
    )
    _index_record(report, store, _get_index(user["id"]))
    _process_document_memory(user["id"], report, extracted_text)
    return ChatAttachmentResponse(
        attachment_id=report["id"],
        file_name=report.get("file_name"),
        mime_type=report.get("mime_type"),
        index_status=report.get("index_status") or index_status,
        visibility_state=report.get("visibility_state") or "hidden",
        extracted_chars=report.get("extracted_chars") or 0,
        warning=None if index_status == "ready" else "Limited text extracted from PDF.",
    )


@router.post("/attachments/{attachment_id}/save", response_model=ChatAttachmentResponse)
async def save_chat_attachment(
    attachment_id: str,
    user: dict = Depends(get_current_user),
):
    from web.routes.library import _get_index, _get_store, _index_record

    store = _get_store(user["id"])
    report = store.get_report(attachment_id)
    if not report or report.get("source_kind") != "uploaded_pdf":
        raise HTTPException(status_code=404, detail="Attachment not found")

    if report.get("visibility_state") != "saved":
        report = store.update_report(attachment_id, visibility_state="saved")
        if not report:
            raise HTTPException(status_code=404, detail="Attachment not found")
        _index_record(report, store, _get_index(user["id"]))
        log_event("library_report_saved_from_chat", user["id"], {"report_id": attachment_id})

    return ChatAttachmentResponse(
        attachment_id=report["id"],
        file_name=report.get("file_name"),
        mime_type=report.get("mime_type"),
        index_status=report.get("index_status") or "ready",
        visibility_state=report.get("visibility_state") or "saved",
        extracted_chars=report.get("extracted_chars") or 0,
        warning=None
        if (report.get("index_status") or "ready") == "ready"
        else "Limited text extracted from PDF.",
    )


def _get_engine(user_id: str, use_tools: bool = False):
    from advisor.engine import AdvisorEngine
    from advisor.rag import RAGRetriever
    from journal.embeddings import EmbeddingManager
    from journal.fts import JournalFTSIndex
    from journal.search import JournalSearch
    from journal.storage import JournalStorage

    config = get_config()
    paths = get_user_paths(user_id)

    journal_storage = JournalStorage(paths["journal_dir"])
    embeddings = EmbeddingManager(
        paths["chroma_dir"],
        user_id=safe_user_id(user_id),
    )
    intel_storage = get_intel_storage()
    fts_index = JournalFTSIndex(paths["journal_dir"])
    journal_search = JournalSearch(journal_storage, embeddings, fts_index=fts_index)

    # Build user-scoped intel search for RAG
    intel_search = None
    try:
        from intelligence.embeddings import IntelEmbeddingManager
        from intelligence.search import IntelSearch

        intel_emb = IntelEmbeddingManager(paths["chroma_dir"])
        intel_search = IntelSearch(intel_storage, embedding_manager=intel_emb, user_id=user_id)
    except Exception:
        pass

    fact_store = None
    thread_store = None
    memory_config = None
    if config.memory.enabled:
        fact_store = get_memory_store(user_id)
        memory_config = {
            "max_context_facts": config.memory.max_context_facts,
            "high_confidence_threshold": config.memory.high_confidence_threshold,
        }
    if config.threads.enabled:
        thread_store = get_thread_store(user_id)

    # Entity graph components (best-effort — fallback to no entities on failure)
    entity_store = None
    entity_retriever = None
    query_analyzer = None
    try:
        from advisor.entity_retriever import EntityRetriever
        from intelligence.entity_store import EntityStore

        entity_store = EntityStore(get_coach_paths()["intel_db"])
        entity_retriever = EntityRetriever(entity_store, fact_store=fact_store)
        from advisor.query_analyzer import QueryAnalyzer

        query_analyzer = QueryAnalyzer(entity_store=entity_store)
    except Exception as exc:
        import structlog

        structlog.get_logger().warning("entity_components_init_failed", error=str(exc))

    users_db = get_default_db_path()
    rag = RAGRetriever(
        journal_search=journal_search,
        intel_db_path=paths["intel_db"],
        intel_search=intel_search,
        profile_path=str(get_profile_path(user_id)),
        users_db_path=users_db,
        user_id=user_id,
        fact_store=fact_store,
        memory_config=memory_config,
        thread_store=thread_store,
        library_index=_get_library_index(user_id),
        entity_store=entity_store,
        entity_retriever=entity_retriever,
        query_analyzer=query_analyzer,
    )

    provider_name, api_key, source = resolve_llm_credentials_for_user(user_id)
    is_shared = source == "shared"
    council_members = [] if is_shared else get_council_members_for_user(user_id)

    model = SHARED_LLM_MODEL if is_shared else config.llm.model
    effective_use_tools = False if is_shared else use_tools

    components = None
    if effective_use_tools:
        components = {
            "storage": journal_storage,
            "embeddings": embeddings,
            "intel_storage": intel_storage,
            "rag": rag,
            "profile_path": str(get_profile_path(user_id)),
            "recommendations_dir": paths["recommendations_dir"],
            "user_id": user_id,
        }

    rag_config = {
        "structured_profile": True,
        "xml_delimiters": True,
        "inject_documents": True,
        "inject_curriculum": True,
    }
    if config.memory.enabled:
        rag_config["inject_memory"] = True
    if config.threads.enabled:
        rag_config["inject_recurring_thoughts"] = True

    return AdvisorEngine(
        rag=rag,
        api_key=api_key,
        model=model,
        provider=provider_name or config.llm.provider,
        use_tools=effective_use_tools,
        components=components,
        rag_config=rag_config,
        council_members=[
            CouncilMember(provider=member["provider"], api_key=member["api_key"])
            for member in council_members
        ],
        council_enabled=not is_shared,
        council_lead_provider=provider_name or config.llm.provider,
    )


@router.post("/ask", response_model=AdvisorResponse)
async def ask_advisor(
    body: AdvisorAsk,
    use_tools: bool = Query(True),
    user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(enforce_shared_key_usage_limit),
):
    created_conversation = body.conversation_id is None
    conv_id: str | None = None
    user_message_id: str | None = None
    try:
        user_id = user["id"]
        attachments = _resolve_attachment_records(user_id, body.attachment_ids)
        conv_id, history, user_message_id = start_conversation_turn(
            user_id=user_id,
            conversation_id=body.conversation_id,
            question=body.question,
            attachments=attachments,
            create_conversation_fn=create_conversation,
            conversation_belongs_to_fn=conversation_belongs_to,
            get_messages_fn=get_messages,
            add_message_fn=add_message,
        )

        engine = _get_engine(user_id, use_tools=use_tools)
        paths = get_user_paths(user_id)
        result = await asyncio.to_thread(
            run_advice,
            engine,
            body.question,
            advice_type=body.advice_type,
            conversation_history=history or None,
            attachment_ids=body.attachment_ids,
            trace_data_dir=Path(paths["data_dir"]),
        )

        finish_conversation_turn(
            conv_id=conv_id,
            user_id=user_id,
            answer=result["answer"],
            latency_ms=result["latency_ms"],
            add_message_fn=add_message,
            log_event_fn=log_event,
            usage=result.get("usage"),
            model=result.get("model"),
        )

        return AdvisorResponse(
            answer=result["answer"],
            advice_type=body.advice_type,
            conversation_id=conv_id,
            council_used=result.get("council_used", False),
            council_member_count=result.get("council_member_count", 0),
            council_providers=result.get("council_providers", []),
            council_failed_providers=result.get("council_failed_providers", []),
            council_partial=result.get("council_partial", False),
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as exc:
        if conv_id is not None:
            try:
                if user_message_id is not None:
                    delete_message(user_message_id, conv_id)
                if created_conversation:
                    delete_conversation(conv_id, user_id)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ask/stream")
async def ask_advisor_stream(
    body: AdvisorAsk,
    use_tools: bool = Query(True),
    user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(enforce_shared_key_usage_limit),
):
    """SSE streaming version of /ask — emits tool_start/tool_done/answer events."""
    user_id = user["id"]
    created_conversation = body.conversation_id is None

    try:
        attachments = _resolve_attachment_records(user_id, body.attachment_ids)
        conv_id, history, user_message_id = start_conversation_turn(
            user_id=user_id,
            conversation_id=body.conversation_id,
            question=body.question,
            attachments=attachments,
            create_conversation_fn=create_conversation,
            conversation_belongs_to_fn=conversation_belongs_to,
            get_messages_fn=get_messages,
            add_message_fn=add_message,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")

    queue: asyncio.Queue[dict | None] = asyncio.Queue()
    answer_sent = False
    stream_closed = False
    event_loop = asyncio.get_running_loop()

    def _queue_event(event: dict | None) -> None:
        if stream_closed:
            return
        event_loop.call_soon_threadsafe(queue.put_nowait, event)

    def _event_callback(event: dict):
        nonlocal answer_sent
        if event.get("type") == "answer":
            answer_sent = True
        _queue_event(event)

    async def _run_engine():
        try:
            engine = _get_engine(user_id, use_tools=use_tools)
            paths = get_user_paths(user_id)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: run_advice(
                    engine,
                    body.question,
                    advice_type=body.advice_type,
                    conversation_history=history or None,
                    attachment_ids=body.attachment_ids,
                    event_callback=_event_callback,
                    trace_data_dir=Path(paths["data_dir"]),
                ),
            )
            msg_id = finish_conversation_turn(
                conv_id=conv_id,
                user_id=user_id,
                answer=result["answer"],
                latency_ms=result["latency_ms"],
                add_message_fn=add_message,
                log_event_fn=log_event,
                usage=result.get("usage"),
                model=result.get("model"),
            )
            if not answer_sent:
                _queue_event(
                    {
                        "type": "answer",
                        "content": result["answer"],
                        "conversation_id": conv_id,
                        "advice_type": body.advice_type,
                        "message_id": msg_id,
                        "council_used": result.get("council_used", False),
                        "council_member_count": result.get("council_member_count", 0),
                        "council_providers": result.get("council_providers", []),
                        "council_failed_providers": result.get("council_failed_providers", []),
                        "council_partial": result.get("council_partial", False),
                    }
                )
            else:
                _queue_event({"type": "message_persisted", "message_id": msg_id})
        except Exception as exc:
            try:
                if user_message_id is not None:
                    delete_message(user_message_id, conv_id)
                if created_conversation:
                    delete_conversation(conv_id, user_id)
            except Exception:
                pass
            _queue_event({"type": "error", "detail": str(exc)})
        finally:
            _queue_event(None)

    async def _sse_generator():
        nonlocal stream_closed
        task = asyncio.create_task(_run_engine())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                if event.get("type") == "answer":
                    event.setdefault("conversation_id", conv_id)
                    event.setdefault("advice_type", body.advice_type)
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            stream_closed = True
            if not task.done():
                task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await task

    return StreamingResponse(_sse_generator(), media_type="text/event-stream")


@router.get("/conversations", response_model=list[ConversationListItem])
async def list_user_conversations(
    user: dict = Depends(get_current_user),
):
    rows = list_conversations(user["id"])
    return [ConversationListItem(**row) for row in rows]


@router.get("/conversations/{conv_id}", response_model=ConversationDetail)
async def get_user_conversation(
    conv_id: str,
    user: dict = Depends(get_current_user),
):
    conv = get_conversation(conv_id, user["id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDetail(
        id=conv["id"],
        title=conv["title"],
        messages=[ConversationMessage(**message) for message in conv["messages"]],
    )


@router.delete("/conversations/{conv_id}")
async def delete_user_conversation(
    conv_id: str,
    user: dict = Depends(get_current_user),
):
    deleted = delete_conversation(conv_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


# --- Trace endpoints ---


@router.get("/traces", response_model=list[TraceListItem])
async def list_advisor_traces(
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    from advisor.trace_store import list_traces

    paths = get_user_paths(user["id"])
    return [TraceListItem(**t) for t in list_traces(paths["data_dir"], limit=limit)]


@router.get("/traces/{session_id}", response_model=TraceDetail)
async def get_advisor_trace(
    session_id: str,
    from_line: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    from advisor.trace_store import InvalidSessionIdError, read_trace

    paths = get_user_paths(user["id"])
    try:
        entries = list(read_trace(paths["data_dir"], session_id, from_line=from_line))
    except InvalidSessionIdError:
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    if not entries and from_line == 0:
        raise HTTPException(status_code=404, detail="Trace not found")
    return TraceDetail(session_id=session_id, entries=entries, from_line=from_line)

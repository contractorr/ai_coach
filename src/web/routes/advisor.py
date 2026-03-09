"""Advisor routes wrapping AdvisorEngine (per-user)."""

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from starlette.responses import StreamingResponse

from library.index import LibraryIndex
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
    get_conversation,
    get_messages,
    list_conversations,
)
from web.deps import (
    SHARED_LLM_MODEL,
    enforce_shared_key_usage_limit,
    get_api_key_with_source,
    get_config,
    get_intel_storage,
    get_memory_store,
    get_profile_path,
    get_thread_store,
    get_user_paths,
    safe_user_id,
)
from web.models import (
    AdvisorAsk,
    AdvisorResponse,
    ChatAttachmentResponse,
    ConversationDetail,
    ConversationListItem,
    ConversationMessage,
)
from web.user_store import get_default_db_path, log_event

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


def _get_library_store(user_id: str) -> ReportStore:
    paths = get_user_paths(user_id)
    return ReportStore(Path(paths["data_dir"]) / "library")


def _get_library_index(user_id: str) -> LibraryIndex:
    paths = get_user_paths(user_id)
    return LibraryIndex(Path(paths["data_dir"]) / "library")


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
        collection_name=f"journal_{safe_user_id(user_id)}",
    )
    intel_storage = get_intel_storage()
    fts_index = JournalFTSIndex(paths["journal_dir"])
    journal_search = JournalSearch(journal_storage, embeddings, fts_index=fts_index)

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

    users_db = get_default_db_path()
    rag = RAGRetriever(
        journal_search=journal_search,
        intel_db_path=paths["intel_db"],
        profile_path=str(get_profile_path(user_id)),
        users_db_path=users_db,
        user_id=user_id,
        fact_store=fact_store,
        memory_config=memory_config,
        thread_store=thread_store,
        library_index=_get_library_index(user_id),
    )

    api_key, source = get_api_key_with_source(user_id)
    is_shared = source == "shared"

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
    }
    if config.memory.enabled:
        rag_config["inject_memory"] = True
    if config.threads.enabled:
        rag_config["inject_recurring_thoughts"] = True

    return AdvisorEngine(
        rag=rag,
        api_key=api_key,
        model=model,
        provider=config.llm.provider,
        use_tools=effective_use_tools,
        components=components,
        rag_config=rag_config,
    )


@router.post("/ask", response_model=AdvisorResponse)
async def ask_advisor(
    body: AdvisorAsk,
    use_tools: bool = Query(True),
    user: dict = Depends(get_current_user),
    _rate_limit: None = Depends(enforce_shared_key_usage_limit),
):
    try:
        user_id = user["id"]
        attachments = _resolve_attachment_records(user_id, body.attachment_ids)
        conv_id, history = start_conversation_turn(
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
        result = await asyncio.to_thread(
            run_advice,
            engine,
            body.question,
            advice_type=body.advice_type,
            conversation_history=history or None,
            attachment_ids=body.attachment_ids,
        )

        finish_conversation_turn(
            conv_id=conv_id,
            user_id=user_id,
            answer=result["answer"],
            latency_ms=result["latency_ms"],
            add_message_fn=add_message,
            log_event_fn=log_event,
        )

        return AdvisorResponse(
            answer=result["answer"],
            advice_type=body.advice_type,
            conversation_id=conv_id,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as exc:
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

    try:
        attachments = _resolve_attachment_records(user_id, body.attachment_ids)
        conv_id, history = start_conversation_turn(
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

    def _event_callback(event: dict):
        nonlocal answer_sent
        if event.get("type") == "answer":
            answer_sent = True
        queue.put_nowait(event)

    async def _run_engine():
        try:
            engine = _get_engine(user_id, use_tools=use_tools)
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
                ),
            )
            finish_conversation_turn(
                conv_id=conv_id,
                user_id=user_id,
                answer=result["answer"],
                latency_ms=result["latency_ms"],
                add_message_fn=add_message,
                log_event_fn=log_event,
            )
            if not answer_sent:
                queue.put_nowait(
                    {
                        "type": "answer",
                        "content": result["answer"],
                        "conversation_id": conv_id,
                        "advice_type": body.advice_type,
                    }
                )
        except Exception as exc:
            queue.put_nowait({"type": "error", "detail": str(exc)})
        finally:
            queue.put_nowait(None)

    async def _sse_generator():
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
            task.cancel()

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

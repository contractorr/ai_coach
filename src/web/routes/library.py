"""Library routes for durable AI-generated reports and uploaded PDFs."""

from datetime import datetime
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from advisor.goals import GoalTracker
from journal.storage import JournalStorage
from library.index import LibraryIndex
from library.pdf_text import extract_text_from_pdf_bytes
from library.reports import ReportStore
from llm.factory import create_llm_provider
from web.auth import get_current_user
from web.deps import (
    SHARED_LLM_MODEL,
    enforce_shared_key_usage_limit,
    get_config,
    get_library_index,
    get_memory_store,
    get_profile_storage,
    get_user_paths,
    resolve_llm_credentials_for_user,
)
from web.models import (
    LibraryReportCreate,
    LibraryReportListItem,
    LibraryReportResponse,
    LibraryReportUpdate,
)
from web.user_store import log_event

logger = structlog.get_logger()
router = APIRouter(prefix="/api/library", tags=["library"])


def _get_store(user_id: str) -> ReportStore:
    paths = get_user_paths(user_id)
    return ReportStore(Path(paths["data_dir"]) / "library")


def _get_index(user_id: str):
    return get_library_index(user_id)


def _active_goal_titles(user_id: str) -> list[str]:
    try:
        paths = get_user_paths(user_id)
        tracker = GoalTracker(JournalStorage(paths["journal_dir"]))
        goals = tracker.get_goals(include_inactive=False)
        return [goal["title"] for goal in goals[:5] if goal.get("title")]
    except Exception:
        return []


def _profile_summary(user_id: str) -> str | None:
    try:
        profile = get_profile_storage(user_id).load()
        return profile.structured_summary() or profile.summary()
    except Exception:
        return None


def _derive_title(prompt: str, report_type: str) -> str:
    cleaned = prompt.strip().rstrip("?.! ")
    if len(cleaned) <= 70:
        return cleaned[:1].upper() + cleaned[1:]
    prefix = report_type.replace("_", " ").title()
    return f"{prefix}: {cleaned[:70]}"


def _derive_document_title(file_name: str, explicit_title: str | None = None) -> str:
    if explicit_title and explicit_title.strip():
        return explicit_title.strip()
    stem = Path(file_name or "document.pdf").stem.replace("_", " ").replace("-", " ").strip()
    return stem or "Uploaded document"


def _generate_report_content(user_id: str, prompt: str, report_type: str) -> str:
    config = get_config()
    provider_name, api_key, source = resolve_llm_credentials_for_user(user_id)
    if not api_key:
        raise HTTPException(status_code=400, detail="No LLM API key configured")
    model = SHARED_LLM_MODEL if source == "shared" else config.llm.model
    provider = create_llm_provider(
        provider=provider_name or config.llm.provider,
        api_key=api_key,
        model=model,
    )

    profile_summary = _profile_summary(user_id)
    goals = _active_goal_titles(user_id)
    context_parts = []
    if profile_summary:
        context_parts.append("[PROFILE]\n" + profile_summary)
    if goals:
        context_parts.append("[ACTIVE GOALS]\n- " + "\n- ".join(goals))
    context_text = (
        "\n\n".join(context_parts) if context_parts else "No saved personal context is available."
    )

    system = (
        "You write clear, practical markdown reports for a single user. "
        "Use descriptive headings, concise explanations, and actionable takeaways. "
        "When context is provided, tailor the report to that context without inventing facts."
    )
    user_prompt = (
        f"Create a {report_type.replace('_', ' ')} report in markdown.\n\n"
        f"USER REQUEST:\n{prompt}\n\n"
        f"AVAILABLE USER CONTEXT:\n{context_text}\n\n"
        "Structure the answer with a short summary, 3-6 clear sections, and a closing section called 'What to do next'."
    )
    return provider.generate(
        messages=[{"role": "user", "content": user_prompt}],
        system=system,
        max_tokens=2500,
    )


def _shape_report(record: dict) -> LibraryReportResponse:
    return LibraryReportResponse(**record)


def _shape_list_item(record: dict) -> LibraryReportListItem:
    payload = {key: value for key, value in record.items() if key not in {"content", "path"}}
    return LibraryReportListItem(**payload)


def _index_record(record: dict, store: ReportStore, index: LibraryIndex) -> None:
    index.upsert_item(
        report_id=record["id"],
        title=record["title"],
        source_kind=record.get("source_kind") or "generated",
        report_type=record.get("report_type") or "custom",
        status=record.get("status") or "ready",
        collection=record.get("collection"),
        file_name=record.get("file_name"),
        body_text=record.get("content") or "",
        extracted_text=store.get_extracted_text(record["id"]),
        updated_at=record.get("updated") or record.get("created") or "",
    )


def _sync_index(store: ReportStore, index: LibraryIndex) -> None:
    for record in store.list_reports(limit=10_000):
        _index_record(record, store, index)


def _search_reports(
    store: ReportStore,
    index: LibraryIndex,
    search: str,
    *,
    status_filter: str | None,
    collection: str | None,
    limit: int,
) -> list[dict]:
    _sync_index(store, index)
    hits = index.search(
        search,
        limit=limit,
        status=status_filter,
        collection=collection,
    )
    if not hits:
        return []

    records_by_id = {
        record["id"]: record
        for record in store.list_reports(status=status_filter, collection=collection, limit=10_000)
    }
    results: list[dict] = []
    for hit in hits:
        record = records_by_id.get(hit["id"])
        if not record:
            continue
        if hit.get("snippet"):
            record = {**record, "preview": hit["snippet"]}
        results.append(record)
    return results


def _process_document_memory(user_id: str, report: dict, extracted_text: str) -> None:
    if not extracted_text.strip():
        return

    try:
        config = get_config()
        if not config.memory.enabled:
            return

        from memory.pipeline import MemoryPipeline

        pipeline = MemoryPipeline(get_memory_store(user_id))
        pipeline.reextract_document(
            report["id"],
            extracted_text,
            {
                "title": report["title"],
                "file_name": report.get("file_name"),
                "mime_type": report.get("mime_type"),
                "collection": report.get("collection"),
                "document_type": report.get("report_type"),
            },
        )
    except Exception as exc:
        logger.warning(
            "library_document_memory_failed",
            user_id=user_id,
            report_id=report["id"],
            error=str(exc),
        )


def _validate_pdf_upload(file_name: str | None, payload: bytes, content_type: str | None) -> None:
    normalized_name = (file_name or "").lower()
    normalized_type = (content_type or "").lower()
    if not normalized_name.endswith(".pdf") and normalized_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    if not payload.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF")


@router.get("/reports", response_model=list[LibraryReportListItem])
async def list_reports(
    search: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    collection: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    if search and search.strip():
        reports = _search_reports(
            store,
            _get_index(user["id"]),
            search.strip(),
            status_filter=status_filter,
            collection=collection,
            limit=limit,
        )
    else:
        reports = store.list_reports(status=status_filter, collection=collection, limit=limit)
    return [_shape_list_item(report) for report in reports]


@router.post(
    "/reports",
    response_model=LibraryReportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_shared_key_usage_limit)],
)
async def create_report(
    body: LibraryReportCreate,
    user: dict = Depends(get_current_user),
):
    title = (body.title or "").strip() or _derive_title(body.prompt, body.report_type)
    content = _generate_report_content(user["id"], body.prompt, body.report_type)
    store = _get_store(user["id"])
    report = store.create(
        title=title,
        prompt=body.prompt,
        report_type=body.report_type,
        content=content,
        collection=(body.collection or "").strip() or None,
    )
    _index_record(report, store, _get_index(user["id"]))
    log_event(
        "library_report_created",
        user["id"],
        {
            "report_id": report["id"],
            "report_type": report["report_type"],
            "collection": report.get("collection"),
        },
    )
    return _shape_report(report)


@router.post(
    "/reports/upload",
    response_model=LibraryReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_report_pdf(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    collection: str | None = Form(default=None),
    user: dict = Depends(get_current_user),
):
    payload = await file.read()
    _validate_pdf_upload(file.filename, payload, file.content_type)

    extracted_text = extract_text_from_pdf_bytes(payload)
    extraction_status = "ready" if extracted_text.strip() else "empty"
    index_status = "ready" if extracted_text.strip() else "limited_text"

    store = _get_store(user["id"])
    report = store.create_uploaded_pdf(
        title=_derive_document_title(file.filename or "document.pdf", title),
        file_name=file.filename or "document.pdf",
        file_bytes=payload,
        mime_type=file.content_type or "application/pdf",
        collection=(collection or "").strip() or None,
        extracted_text=extracted_text,
        extraction_status=extraction_status,
        origin_surface="library",
        visibility_state="saved",
        index_status=index_status,
    )
    _index_record(report, store, _get_index(user["id"]))
    _process_document_memory(user["id"], report, extracted_text)
    log_event(
        "library_pdf_uploaded",
        user["id"],
        {
            "report_id": report["id"],
            "file_name": report.get("file_name"),
            "collection": report.get("collection"),
            "has_extracted_text": report.get("has_extracted_text", False),
        },
    )
    return _shape_report(report)


@router.get("/reports/{report_id}", response_model=LibraryReportResponse)
async def get_report(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    report = store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _shape_report(report)


@router.get("/reports/{report_id}/file")
async def download_report_file(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    report = store.get_report(report_id)
    if not report or not report.get("has_attachment"):
        raise HTTPException(status_code=404, detail="File not found")

    path = store.get_attachment_path(report_id)
    if not path:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path,
        media_type=report.get("mime_type") or "application/octet-stream",
        filename=report.get("file_name") or path.name,
    )


@router.put("/reports/{report_id}", response_model=LibraryReportResponse)
async def update_report(
    report_id: str,
    body: LibraryReportUpdate,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    report = store.update_report(
        report_id,
        title=body.title,
        content=body.content,
        collection=body.collection,
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _index_record(report, store, _get_index(user["id"]))
    log_event("library_report_updated", user["id"], {"report_id": report_id})
    return _shape_report(report)


@router.post(
    "/reports/{report_id}/refresh",
    response_model=LibraryReportResponse,
    dependencies=[Depends(enforce_shared_key_usage_limit)],
)
async def refresh_report(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    existing = store.get_report(report_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Report not found")
    if existing.get("source_kind") != "generated":
        raise HTTPException(status_code=400, detail="Only generated reports can be refreshed")
    content = _generate_report_content(user["id"], existing["prompt"], existing["report_type"])
    report = store.update_report(
        report_id,
        content=content,
        last_generated_at=datetime.now().isoformat(),
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _index_record(report, store, _get_index(user["id"]))
    log_event("library_report_refreshed", user["id"], {"report_id": report_id})
    return _shape_report(report)


@router.post("/reports/{report_id}/archive", response_model=LibraryReportResponse)
async def archive_report(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    report = store.archive_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _index_record(report, store, _get_index(user["id"]))
    log_event("library_report_archived", user["id"], {"report_id": report_id})
    return _shape_report(report)


@router.post("/reports/{report_id}/restore", response_model=LibraryReportResponse)
async def restore_report(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    store = _get_store(user["id"])
    report = store.restore_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _index_record(report, store, _get_index(user["id"]))
    log_event("library_report_restored", user["id"], {"report_id": report_id})
    return _shape_report(report)

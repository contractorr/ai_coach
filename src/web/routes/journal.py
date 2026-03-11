"""Journal CRUD routes wrapping src/journal/storage.py (per-user)."""

import asyncio
from datetime import datetime
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from journal.storage import JournalStorage
from web.auth import get_current_user
from web.deps import (
    get_assumption_store,
    get_config,
    get_memory_store,
    get_receipt_store,
    get_thread_store,
    get_thread_inbox_state_store,
    get_user_paths,
    safe_user_id,
)
from web.models import (
    ExtractionReceiptEnvelope,
    JournalCreate,
    JournalEntry,
    JournalUpdate,
    QuickCapture,
)
from web.user_store import log_event

logger = structlog.get_logger()

router = APIRouter(prefix="/api/journal", tags=["journal"])


def _generate_title(content: str, user_id: str) -> str | None:
    """Try to generate an LLM title; returns None on failure."""
    try:
        from journal.titler import generate_title
        from llm import create_cheap_provider
        from web.deps import get_api_key_for_user

        api_key = get_api_key_for_user(user_id)
        if not api_key:
            return None
        llm = create_cheap_provider(api_key=api_key)
        return generate_title(content, llm)
    except Exception:
        logger.debug("title_generation_skipped", user_id=user_id)
        return None


def _get_storage(user_id: str) -> JournalStorage:
    paths = get_user_paths(user_id)
    return JournalStorage(paths["journal_dir"])


def _invalidate_greeting_cache(user_id: str, paths: dict) -> None:
    try:
        from advisor.context_cache import ContextCache
        from advisor.greeting import invalidate_greeting

        cache_db = paths["intel_db"].parent / "context_cache.db"
        cache = ContextCache(cache_db)
        invalidate_greeting(user_id, cache)
    except Exception as exc:
        logger.warning("journal.greeting_invalidate_failed", error=str(exc), user=user_id)


async def _run_post_create_hooks(
    user_id: str, filepath: Path, content: str, metadata: dict
) -> None:
    """Embed + thread detect + memory extract in background (best-effort)."""
    paths = get_user_paths(user_id)
    entry_id = str(filepath)
    warnings: list[str] = []
    thread_match_payload: dict | None = None
    memory_facts: list[dict] = []

    # 1. ChromaDB embedding (per-user collection)
    try:
        from journal.embeddings import EmbeddingManager

        chroma_dir = paths.get("chroma_dir")
        if chroma_dir:
            em = EmbeddingManager(chroma_dir, collection_name=f"journal_{safe_user_id(user_id)}")
            em.add_entry(entry_id, content, metadata)
    except Exception as exc:
        logger.warning("post_create.embed_failed", error=str(exc), user=user_id)
        warnings.append("Embedding failed")
        try:
            from journal.extraction_receipts import ReceiptBuilder

            receipt_builder = ReceiptBuilder(get_receipt_store(user_id))
            receipt_builder.finalize(
                entry={
                    "path": entry_id,
                    "title": metadata.get("title", filepath.stem),
                    "content": content,
                    "tags": metadata.get("tags", []),
                },
                thread_match=None,
                memory_facts=[],
                theme_candidates=[],
                goal_candidates=[],
                warnings=warnings,
            )
        except Exception:
            pass
        return  # threads needs the embedding, skip if embed fails

    # 1b. FTS index upsert
    try:
        from journal.fts import JournalFTSIndex

        fts_index = JournalFTSIndex(paths["journal_dir"])
        fts_index.upsert(
            entry_id,
            metadata.get("title", ""),
            metadata.get("type", ""),
            content,
            ",".join(metadata.get("tags", [])),
            filepath.stat().st_mtime,
        )
    except Exception as exc:
        logger.warning("post_create.fts_failed", error=str(exc), user=user_id)
        warnings.append("Search indexing failed")

    # 2. Thread detection
    try:
        config = get_config()
        threads_cfg = config.threads
        if threads_cfg.enabled and chroma_dir:
            result = em.collection.get(ids=[entry_id], include=["embeddings"])
            if result["embeddings"] and result["embeddings"][0]:
                embedding = result["embeddings"][0]
                entry_date = datetime.now()
                created = metadata.get("created", "")
                if created:
                    try:
                        entry_date = datetime.fromisoformat(
                            str(created).replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                    except (ValueError, OSError):
                        pass

                from journal.threads import ThreadDetector

                store = get_thread_store(user_id)
                detector = ThreadDetector(
                    em,
                    store,
                    {
                        "similarity_threshold": threads_cfg.similarity_threshold,
                        "candidate_count": threads_cfg.candidate_count,
                        "min_entries_for_thread": threads_cfg.min_entries_for_thread,
                    },
                )
                match = await detector.detect(entry_id, embedding, entry_date)
                if match.thread_id:
                    thread = await store.get_thread(match.thread_id)
                    thread_match_payload = {
                        "thread_id": match.thread_id,
                        "thread_label": thread.label
                        if thread
                        else metadata.get("title", "Recurring topic"),
                        "match_type": match.match_type,
                    }
    except Exception as exc:
        logger.warning("post_create.thread_detect_failed", error=str(exc), user=user_id)
        warnings.append("Thread detection failed")

    # 3. Memory pipeline
    try:
        config = get_config()
        if config.memory.enabled:
            from memory.pipeline import MemoryPipeline

            fact_store = get_memory_store(user_id)
            pipeline = MemoryPipeline(fact_store)
            pipeline.process_journal_entry(entry_id, content, metadata)
            memory_facts = [
                {
                    "fact_id": fact.id,
                    "text": fact.text,
                    "category": getattr(fact.category, "value", fact.category),
                    "confidence": fact.confidence,
                }
                for fact in fact_store.get_by_source("journal", entry_id)
            ]
    except Exception as exc:
        logger.warning("post_create.memory_failed", error=str(exc), user=user_id)
        warnings.append("Memory extraction failed")

    # 3b. Assumption extraction suggestions
    try:
        from advisor.assumptions import AssumptionExtractor

        extractor = AssumptionExtractor()
        assumption_store = get_assumption_store(user_id)
        for candidate in extractor.extract_from_journal(
            {
                "path": entry_id,
                "title": metadata.get("title", filepath.stem),
                "content": content,
                "tags": metadata.get("tags", []),
            }
        ):
            assumption_store.create(
                {
                    "statement": candidate["statement"],
                    "status": "suggested",
                    "source_type": candidate.get("source_type") or "journal",
                    "source_id": candidate.get("source_id") or entry_id,
                    "extraction_confidence": candidate.get("confidence"),
                    "linked_entities": candidate.get("linked_entities") or [],
                }
            )
    except Exception as exc:
        logger.warning("post_create.assumptions_failed", error=str(exc), user=user_id)
        warnings.append("Assumption extraction failed")

    # 3c. Extraction receipt finalization
    try:
        from journal.extraction_receipts import ReceiptBuilder

        receipt_builder = ReceiptBuilder(get_receipt_store(user_id))
        theme_candidates, goal_candidates = receipt_builder.derive_theme_goal_candidates(
            {
                "path": entry_id,
                "title": metadata.get("title", filepath.stem),
                "content": content,
                "tags": metadata.get("tags", []),
            },
            memory_facts,
        )
        receipt_builder.finalize(
            entry={
                "path": entry_id,
                "title": metadata.get("title", filepath.stem),
                "content": content,
                "tags": metadata.get("tags", []),
            },
            thread_match=thread_match_payload,
            memory_facts=memory_facts,
            theme_candidates=theme_candidates,
            goal_candidates=goal_candidates,
            warnings=warnings,
        )
    except Exception as exc:
        logger.warning("post_create.receipt_failed", error=str(exc), user=user_id)

    # 4. Invalidate greeting cache
    _invalidate_greeting_cache(user_id, paths)


async def _cleanup_deleted_entry_state(user_id: str, filepath: Path) -> None:
    paths = get_user_paths(user_id)
    entry_id = str(filepath)

    try:
        get_receipt_store(user_id).delete_by_entry(entry_id)
    except Exception as exc:
        logger.warning("journal.delete_receipt_failed", error=str(exc), user=user_id, entry=entry_id)

    try:
        from journal.embeddings import EmbeddingManager

        chroma_dir = paths.get("chroma_dir")
        if chroma_dir:
            manager = EmbeddingManager(
                chroma_dir,
                collection_name=f"journal_{safe_user_id(user_id)}",
            )
            manager.remove_entry(entry_id)
    except Exception as exc:
        logger.warning("journal.delete_embedding_failed", error=str(exc), user=user_id, entry=entry_id)

    try:
        from journal.fts import JournalFTSIndex

        JournalFTSIndex(paths["journal_dir"]).delete(entry_id)
    except Exception as exc:
        logger.warning("journal.delete_fts_failed", error=str(exc), user=user_id, entry=entry_id)

    deleted_thread_ids: list[str] = []
    try:
        deleted_thread_ids = await get_thread_store(user_id).remove_entry(entry_id)
    except Exception as exc:
        logger.warning("journal.delete_threads_failed", error=str(exc), user=user_id, entry=entry_id)

    if deleted_thread_ids:
        try:
            inbox_state_store = get_thread_inbox_state_store(user_id)
            for thread_id in deleted_thread_ids:
                inbox_state_store.clear_state(thread_id)
        except Exception as exc:
            logger.warning(
                "journal.delete_thread_state_failed",
                error=str(exc),
                user=user_id,
                entry=entry_id,
            )

    try:
        from memory.models import FactSource

        get_memory_store(user_id).delete_by_source(FactSource.JOURNAL, entry_id)
    except Exception as exc:
        logger.warning("journal.delete_memory_failed", error=str(exc), user=user_id, entry=entry_id)

    _invalidate_greeting_cache(user_id, paths)


def _schedule_post_create_hooks(user_id: str, filepath: Path, content: str, metadata: dict):
    """Schedule post-create hooks without blocking the write request."""
    return asyncio.create_task(_run_post_create_hooks(user_id, filepath, content, metadata))


def _validate_journal_path(filepath: str, storage: JournalStorage) -> Path:
    """Validate path is inside journal dir (prevent traversal)."""
    resolved = Path(filepath).resolve()
    if not resolved.is_relative_to(storage.journal_dir):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Entry not found")
    return resolved


@router.get("", response_model=list[JournalEntry])
async def list_entries(
    entry_type: str | None = None,
    tag: str | None = None,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    tags = [tag] if tag else None
    entries = storage.list_entries(entry_type=entry_type, tags=tags, limit=limit)
    return [
        JournalEntry(
            path=str(e["path"]),
            title=e["title"],
            type=e["type"],
            created=e.get("created"),
            tags=e.get("tags", []),
            preview=e.get("preview", ""),
        )
        for e in entries
    ]


@router.post("", response_model=JournalEntry, status_code=status.HTTP_201_CREATED)
async def create_entry(
    body: JournalCreate,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])

    title = body.title
    if not title:
        title = _generate_title(body.content, user["id"])

    try:
        filepath = storage.create(
            content=body.content,
            entry_type=body.entry_type,
            title=title,
            tags=body.tags,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    log_event("journal_entry_created", user["id"])

    post = storage.read(filepath)

    try:
        from journal.extraction_receipts import ReceiptBuilder

        ReceiptBuilder(get_receipt_store(user["id"])).seed_pending(
            str(filepath),
            post.get("title", filepath.stem),
        )
    except Exception:
        logger.debug("journal.receipt_seed_skipped", user=user["id"])

    # Fire post-create hooks (embed, threads, memory) in background
    _schedule_post_create_hooks(user["id"], filepath, post.content, dict(post.metadata))

    return JournalEntry(
        path=str(filepath),
        title=post.get("title", filepath.stem),
        type=post.get("type", "unknown"),
        created=post.get("created"),
        tags=post.get("tags", []),
        content=post.content,
    )


@router.post("/quick", response_model=JournalEntry, status_code=status.HTTP_201_CREATED)
async def quick_capture(
    body: QuickCapture,
    user: dict = Depends(get_current_user),
):
    """Minimal journal entry — auto-title from content, type=quick, embed in ChromaDB."""
    storage = _get_storage(user["id"])
    text = body.content.strip()
    title = _generate_title(text, user["id"])
    if not title:
        title = text[:50].rstrip() + ("..." if len(text) > 50 else "")

    try:
        filepath = storage.create(
            content=text,
            entry_type="quick",
            title=title,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    log_event("journal_entry_created", user["id"])

    post = storage.read(filepath)

    try:
        from journal.extraction_receipts import ReceiptBuilder

        ReceiptBuilder(get_receipt_store(user["id"])).seed_pending(
            str(filepath),
            post.get("title", filepath.stem),
        )
    except Exception:
        logger.debug("journal.receipt_seed_skipped", user=user["id"])

    # Fire post-create hooks (embed, threads, memory) in background
    _schedule_post_create_hooks(user["id"], filepath, post.content, dict(post.metadata))

    return JournalEntry(
        path=str(filepath),
        title=post.get("title", filepath.stem),
        type=post.get("type", "quick"),
        created=post.get("created"),
        tags=post.get("tags", []),
        content=post.content,
    )


@router.get("/{filepath:path}/receipt", response_model=ExtractionReceiptEnvelope)
async def get_entry_receipt(
    filepath: str,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    resolved = _validate_journal_path(filepath, storage)
    receipt = get_receipt_store(user["id"]).get_by_entry(str(resolved))
    if not receipt:
        return ExtractionReceiptEnvelope(status="pending", receipt=None)
    return ExtractionReceiptEnvelope(status=receipt.get("status") or "pending", receipt=receipt)


@router.get("/{filepath:path}", response_model=JournalEntry)
async def read_entry(
    filepath: str,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    resolved = _validate_journal_path(filepath, storage)
    post = storage.read(resolved)
    return JournalEntry(
        path=str(resolved),
        title=post.get("title", resolved.stem),
        type=post.get("type", "unknown"),
        created=post.get("created"),
        tags=post.get("tags", []),
        content=post.content,
    )


@router.put("/{filepath:path}", response_model=JournalEntry)
async def update_entry(
    filepath: str,
    body: JournalUpdate,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    resolved = _validate_journal_path(filepath, storage)
    try:
        storage.update(resolved, content=body.content, metadata=body.metadata)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    post = storage.read(resolved)

    # Re-embed + re-index updated entry
    _schedule_post_create_hooks(user["id"], resolved, post.content, dict(post.metadata))

    return JournalEntry(
        path=str(resolved),
        title=post.get("title", resolved.stem),
        type=post.get("type", "unknown"),
        created=post.get("created"),
        tags=post.get("tags", []),
        content=post.content,
    )


@router.delete("/{filepath:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    filepath: str,
    user: dict = Depends(get_current_user),
):
    storage = _get_storage(user["id"])
    resolved = _validate_journal_path(filepath, storage)
    storage.delete(resolved)
    await _cleanup_deleted_entry_state(user["id"], resolved)

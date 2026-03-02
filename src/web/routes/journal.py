"""Journal CRUD routes wrapping src/journal/storage.py (per-user)."""

import asyncio
from datetime import datetime
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from journal.storage import JournalStorage
from web.auth import get_current_user
from web.deps import get_config, get_user_paths
from web.models import JournalCreate, JournalEntry, JournalUpdate, QuickCapture
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


async def _run_post_create_hooks(
    user_id: str, filepath: Path, content: str, metadata: dict
) -> None:
    """Embed + thread detect + memory extract in background (best-effort)."""
    paths = get_user_paths(user_id)
    entry_id = str(filepath)

    # 1. ChromaDB embedding
    try:
        from journal.embeddings import EmbeddingManager

        chroma_dir = paths.get("chroma_dir")
        if chroma_dir:
            em = EmbeddingManager(chroma_dir)
            em.add_entry(entry_id, content, metadata)
    except Exception as exc:
        logger.warning("post_create.embed_failed", error=str(exc), user=user_id)
        return  # threads needs the embedding, skip if embed fails

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

                from journal.thread_store import ThreadStore
                from journal.threads import ThreadDetector

                intel_db = paths.get("intel_db", Path.home() / "coach" / "intel.db")
                db_path = Path(intel_db).parent / "threads.db"
                store = ThreadStore(db_path)
                detector = ThreadDetector(
                    em,
                    store,
                    {
                        "similarity_threshold": threads_cfg.similarity_threshold,
                        "candidate_count": threads_cfg.candidate_count,
                        "min_entries_for_thread": threads_cfg.min_entries_for_thread,
                    },
                )
                await detector.detect(entry_id, embedding, entry_date)
    except Exception as exc:
        logger.warning("post_create.thread_detect_failed", error=str(exc), user=user_id)

    # 3. Memory pipeline
    try:
        config = get_config()
        if config.memory.enabled:
            from memory.pipeline import MemoryPipeline
            from memory.store import FactStore

            intel_db = paths.get("intel_db", Path.home() / "coach" / "intel.db")
            memory_db = Path(intel_db).parent / "memory.db"
            fact_store = FactStore(memory_db)
            pipeline = MemoryPipeline(fact_store)
            pipeline.process_journal_entry(entry_id, content, metadata)
    except Exception as exc:
        logger.warning("post_create.memory_failed", error=str(exc), user=user_id)


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

    # Fire post-create hooks (embed, threads, memory) in background
    asyncio.create_task(
        _run_post_create_hooks(user["id"], filepath, post.content, dict(post.metadata))
    )

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

    # Fire post-create hooks (embed, threads, memory) in background
    asyncio.create_task(
        _run_post_create_hooks(user["id"], filepath, post.content, dict(post.metadata))
    )

    return JournalEntry(
        path=str(filepath),
        title=post.get("title", filepath.stem),
        type=post.get("type", "quick"),
        created=post.get("created"),
        tags=post.get("tags", []),
        content=post.content,
    )


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

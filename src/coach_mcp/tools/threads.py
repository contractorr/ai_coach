"""Thread MCP tools — list, search, and manage journal recurrence threads."""

import asyncio

from coach_mcp.bootstrap import get_components, get_thread_store


def _list_threads(args: dict) -> dict:
    """List active threads with entry count and date range."""
    get_components()
    min_entries = args.get("min_entries", 2)

    store = get_thread_store()

    loop = asyncio.get_event_loop()
    threads = loop.run_until_complete(store.get_active_threads(min_entries=min_entries))

    result = []
    for t in threads:
        entries = loop.run_until_complete(store.get_thread_entries(t.id))
        dates = [e.entry_date.strftime("%Y-%m-%d") for e in entries]
        result.append(
            {
                "id": t.id,
                "label": t.label,
                "entry_count": t.entry_count,
                "first_date": min(dates) if dates else "",
                "last_date": max(dates) if dates else "",
                "status": t.status,
            }
        )

    return {"threads": result, "count": len(result)}


def _get_thread_entries(args: dict) -> dict:
    """Get all entries in a specific thread."""
    get_components()
    thread_id = args["thread_id"]

    store = get_thread_store()

    loop = asyncio.get_event_loop()
    thread = loop.run_until_complete(store.get_thread(thread_id))
    if not thread:
        return {"error": f"Thread not found: {thread_id}"}

    entries = loop.run_until_complete(store.get_thread_entries(thread_id))
    return {
        "thread": {
            "id": thread.id,
            "label": thread.label,
            "entry_count": thread.entry_count,
        },
        "entries": [
            {
                "entry_id": e.entry_id,
                "entry_date": e.entry_date.strftime("%Y-%m-%d"),
                "similarity": round(e.similarity, 3),
            }
            for e in entries
        ],
    }


def _reindex_threads(args: dict) -> dict:
    """Rebuild all threads from scratch."""
    c = get_components()

    from journal.threads import ThreadDetector

    config_model = c.get("config_model")
    threads_cfg = config_model.threads if config_model else None

    store = get_thread_store()
    detector = ThreadDetector(
        c["embeddings"],
        store,
        {
            "similarity_threshold": threads_cfg.similarity_threshold if threads_cfg else 0.78,
            "candidate_count": threads_cfg.candidate_count if threads_cfg else 10,
            "min_entries_for_thread": threads_cfg.min_entries_for_thread if threads_cfg else 2,
        },
    )

    loop = asyncio.get_event_loop()
    stats = loop.run_until_complete(detector.reindex_all())
    return stats


TOOLS = [
    (
        "threads_list",
        {
            "description": "List active journal recurrence threads — topics the user writes about repeatedly.",
            "type": "object",
            "properties": {
                "min_entries": {
                    "type": "integer",
                    "description": "Minimum entries for a thread to be included",
                    "default": 2,
                },
            },
            "required": [],
        },
        _list_threads,
    ),
    (
        "threads_get_entries",
        {
            "description": "Get all journal entries belonging to a specific thread.",
            "type": "object",
            "properties": {
                "thread_id": {
                    "type": "string",
                    "description": "Thread ID",
                },
            },
            "required": ["thread_id"],
        },
        _get_thread_entries,
    ),
    (
        "threads_reindex",
        {
            "description": "Rebuild all threads from scratch using current similarity threshold.",
            "type": "object",
            "properties": {},
            "required": [],
        },
        _reindex_threads,
    ),
]

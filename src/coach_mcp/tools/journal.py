"""Journal MCP tools — CRUD, search, RAG context retrieval, proactive coaching."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

import structlog

from coach_mcp.bootstrap import get_components

logger = structlog.get_logger()


def _get_context(args: dict) -> dict:
    """Core RAG context retrieval or proactive daily brief."""
    mode = args.get("mode", "rag")
    if mode == "proactive":
        return _get_proactive_context(args)

    c = get_components()
    query = args["query"]
    include_research = args.get("include_research", True)

    # Override weights if provided
    journal_weight = args.get("journal_weight")
    max_chars = args.get("max_chars")

    rag = c["rag"]
    if journal_weight is not None:
        rag.journal_weight = journal_weight
    if max_chars is not None:
        rag.max_context_chars = max_chars

    journal_ctx, intel_ctx, research_ctx = rag.get_full_context(
        query, include_research=include_research
    )

    return {
        "journal_context": journal_ctx,
        "intel_context": intel_ctx,
        "research_context": research_ctx,
    }


def _get_proactive_context(args: dict) -> dict:
    """Daily brief: signals + patterns + priorities for Claude to act on."""
    c = get_components()
    storage = c["storage"]
    config = c.get("config", {})
    max_signals = args.get("max_signals", 10)

    result = {
        "_instruction": (
            "You are a proactive personal coach. Lead with the highest-severity signal. "
            "Be direct and specific — reference actual entries/goals by name."
        ),
    }

    # Insights (signals + patterns → InsightStore, then query back)
    try:
        from advisor.insights import InsightStore
        from advisor.signals import SignalDetector

        paths_config = config.get("paths", {})
        db_path = Path(paths_config.get("intel_db", "~/coach/intel.db")).expanduser()

        # Run signal detection (also writes to InsightStore)
        detector = SignalDetector(storage, db_path, config)
        detector.detect_all()

        # Run pattern detection (also writes to InsightStore)
        from advisor.patterns import PatternDetector

        insight_store = InsightStore(db_path)
        pd = PatternDetector(storage, c.get("embeddings"), config, insight_store=insight_store)
        pd.detect_all()

        # Read back from unified store
        result["insights"] = insight_store.get_active(limit=max_signals)
    except Exception as e:
        result["insights"] = []
        result["_insight_error"] = str(e)

    # Goals summary
    try:
        from advisor.goals import GoalTracker

        tracker = GoalTracker(storage)
        goals = tracker.get_goals(include_inactive=False)
        result["stale_goals"] = [
            {"title": g["title"], "days_since_check": g.get("days_since_check")}
            for g in goals
            if g.get("is_stale")
        ]
        result["active_goals_summary"] = [
            {"title": g["title"], "status": g["status"]} for g in goals if g["status"] == "active"
        ]
    except Exception:
        result["stale_goals"] = []
        result["active_goals_summary"] = []

    # Journal health
    try:
        entries = storage.list_entries(limit=10)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        recent = [e for e in entries if e.get("created", "") >= week_ago]
        if entries:
            latest = entries[0].get("created", "")
            try:
                dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
                if dt.tzinfo:
                    dt = dt.replace(tzinfo=None)
                days_ago = (datetime.now() - dt).days
            except (ValueError, OSError):
                days_ago = -1
        else:
            days_ago = -1
        result["journal_health"] = {
            "entries_this_week": len(recent),
            "last_entry_days_ago": days_ago,
        }
    except Exception:
        result["journal_health"] = {"entries_this_week": 0, "last_entry_days_ago": -1}

    return result


def _create(args: dict) -> dict:
    """Create journal entry + sync embeddings."""
    c = get_components()
    storage = c["storage"]
    embeddings = c["embeddings"]

    content = args["content"]
    entry_type = args.get("entry_type", "daily")
    title = args.get("title")
    tags = args.get("tags")

    # Auto-generate title if not provided
    if not title:
        try:
            from journal.titler import generate_title
            from llm import create_cheap_provider

            llm = create_cheap_provider()
            title = generate_title(content, llm)
        except Exception:
            pass

    # Import goal defaults if creating a goal
    metadata = None
    if entry_type == "goal":
        from advisor.goals import get_goal_defaults

        metadata = get_goal_defaults()

    filepath = storage.create(
        content=content,
        entry_type=entry_type,
        title=title,
        tags=tags,
        metadata=metadata,
    )

    # Sync embedding
    import frontmatter

    post = frontmatter.load(filepath)
    embeddings.add_entry(
        entry_id=str(filepath),
        content=post.content,
        metadata=dict(post.metadata),
    )

    result = {
        "path": str(filepath),
        "filename": filepath.name,
        "title": post.get("title", ""),
        "type": entry_type,
    }

    # Thread detection
    thread_info = _detect_thread(c, str(filepath))
    if thread_info:
        result["thread"] = thread_info

    return result


def _detect_thread(c: dict, entry_id: str) -> dict | None:
    """Post-write thread detection for MCP journal creates."""
    try:
        config_model = c.get("config_model")
        if not config_model or not config_model.threads.enabled:
            return None

        emb_result = c["embeddings"].collection.get(ids=[entry_id], include=["embeddings"])
        if not emb_result["embeddings"] or not emb_result["embeddings"][0]:
            return None
        embedding = emb_result["embeddings"][0]

        entry_date = datetime.now()
        try:
            entry = c["storage"].read(Path(entry_id))
            created = entry.get("created", "")
            if created:
                entry_date = datetime.fromisoformat(str(created).replace("Z", "+00:00")).replace(
                    tzinfo=None
                )
        except Exception:
            pass

        from journal.thread_store import ThreadStore
        from journal.threads import ThreadDetector

        paths = c.get("paths", {})
        intel_db = Path(paths.get("intel_db", "~/coach/intel.db")).expanduser()
        db_path = intel_db.parent / "threads.db"
        store = ThreadStore(db_path)
        threads_cfg = config_model.threads
        detector = ThreadDetector(
            c["embeddings"],
            store,
            {
                "similarity_threshold": threads_cfg.similarity_threshold,
                "candidate_count": threads_cfg.candidate_count,
                "min_entries_for_thread": threads_cfg.min_entries_for_thread,
            },
        )

        loop = asyncio.get_event_loop()
        match = loop.run_until_complete(detector.detect(entry_id, embedding, entry_date))

        if match.match_type == "unthreaded":
            return None

        thread = loop.run_until_complete(store.get_thread(match.thread_id))
        entries = loop.run_until_complete(store.get_thread_entries(match.thread_id))
        dates = sorted(
            set(te.entry_date.strftime("%Y-%m-%d") for te in entries if te.entry_id != entry_id)
        )

        return {
            "thread_id": match.thread_id,
            "match_type": match.match_type,
            "entry_count": thread.entry_count if thread else 0,
            "related_dates": dates[:10],
        }
    except Exception as e:
        logger.debug("mcp_thread_detection_failed", error=str(e))
        return None


def _list(args: dict) -> dict:
    """List journal entries with metadata."""
    c = get_components()
    entry_type = args.get("entry_type")
    tag = args.get("tag")
    limit = args.get("limit", 20)

    tags = [tag] if tag else None
    entries = c["storage"].list_entries(entry_type=entry_type, tags=tags, limit=limit)

    return {
        "entries": [
            {
                "path": str(e["path"]),
                "filename": Path(e["path"]).name,
                "title": e["title"],
                "type": e["type"],
                "created": e["created"],
                "tags": e["tags"],
                "preview": e["preview"],
            }
            for e in entries
        ],
        "count": len(entries),
    }


def _read(args: dict) -> dict:
    """Read full entry content + frontmatter."""
    c = get_components()
    filename = args["filename"]

    # Resolve filename to full path
    journal_dir = c["storage"].journal_dir
    filepath = journal_dir / filename
    filepath = filepath.resolve()

    # Path traversal check
    if not filepath.is_relative_to(journal_dir):
        return {"error": "Path escapes journal directory"}

    if not filepath.exists():
        return {"error": f"Entry not found: {filename}"}

    post = c["storage"].read(filepath)
    return {
        "path": str(filepath),
        "filename": filepath.name,
        "title": post.get("title", ""),
        "type": post.get("type", ""),
        "created": post.get("created", ""),
        "tags": post.get("tags", []),
        "content": post.content,
        "metadata": {k: v for k, v in post.metadata.items()},
    }


def _search(args: dict) -> dict:
    """Semantic search over journal entries."""
    c = get_components()
    query = args["query"]
    limit = args.get("limit", 5)

    results = c["search"].semantic_search(query, n_results=limit)

    return {
        "results": [
            {
                "path": str(r["path"]),
                "filename": Path(r["path"]).name,
                "title": r["title"],
                "type": r["type"],
                "created": r["created"],
                "tags": r["tags"],
                "relevance": r.get("relevance"),
                "preview": r["content"][:300] if r.get("content") else "",
            }
            for r in results
        ],
        "count": len(results),
    }


def _delete(args: dict) -> dict:
    """Delete entry + remove embeddings."""
    c = get_components()
    filename = args["filename"]

    journal_dir = c["storage"].journal_dir
    filepath = journal_dir / filename
    filepath = filepath.resolve()

    if not filepath.is_relative_to(journal_dir):
        return {"error": "Path escapes journal directory"}

    if not filepath.exists():
        return {"error": f"Entry not found: {filename}"}

    # Remove embedding first
    c["embeddings"].remove_entry(str(filepath))
    deleted = c["storage"].delete(filepath)

    return {"deleted": deleted, "filename": filename}


# Tool definitions: (name, schema, handler)
TOOLS = [
    (
        "journal_get_context",
        {
            "description": "Get RAG context for a query, or proactive daily brief with signals/patterns/coaching. Use mode='proactive' for the daily coaching brief.",
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query (required for rag mode, optional for proactive)",
                },
                "mode": {
                    "type": "string",
                    "enum": ["rag", "proactive"],
                    "description": "rag = standard RAG context, proactive = daily coaching brief with signals/patterns",
                    "default": "rag",
                },
                "journal_weight": {
                    "type": "number",
                    "description": "Proportion of context budget for journal (0-1, rag mode only)",
                    "default": 0.7,
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Max total context characters (rag mode only)",
                    "default": 8000,
                },
                "include_research": {
                    "type": "boolean",
                    "description": "Include research reports in context (rag mode only)",
                    "default": True,
                },
                "max_signals": {
                    "type": "integer",
                    "description": "Max signals to return (proactive mode only)",
                    "default": 10,
                },
            },
            "required": [],
        },
        _get_context,
    ),
    (
        "journal_create",
        {
            "description": "Create a journal entry and sync embeddings. For goals, auto-adds goal metadata.",
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Entry body text"},
                "entry_type": {
                    "type": "string",
                    "description": "Entry type",
                    "enum": [
                        "daily",
                        "project",
                        "goal",
                        "reflection",
                        "insight",
                        "note",
                        "research",
                        "action_brief",
                    ],
                    "default": "daily",
                },
                "title": {"type": "string", "description": "Entry title (defaults to date)"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for the entry",
                },
            },
            "required": ["content"],
        },
        _create,
    ),
    (
        "journal_list",
        {
            "description": "List journal entries with metadata, optionally filtered by type or tag.",
            "type": "object",
            "properties": {
                "entry_type": {
                    "type": "string",
                    "description": "Filter by entry type",
                    "enum": [
                        "daily",
                        "project",
                        "goal",
                        "reflection",
                        "insight",
                        "note",
                        "research",
                        "action_brief",
                    ],
                },
                "tag": {"type": "string", "description": "Filter by tag"},
                "limit": {"type": "integer", "description": "Max entries to return", "default": 20},
            },
            "required": [],
        },
        _list,
    ),
    (
        "journal_read",
        {
            "description": "Read full content and frontmatter of a journal entry.",
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename of the entry (e.g. 2024-01-15_daily_meeting-notes.md)",
                },
            },
            "required": ["filename"],
        },
        _read,
    ),
    (
        "journal_search",
        {
            "description": "Semantic search over journal entries. Returns entries ranked by relevance.",
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {
                    "type": "integer",
                    "description": "Max results",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        _search,
    ),
    (
        "journal_delete",
        {
            "description": "Delete a journal entry and remove its embeddings.",
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename of the entry to delete"},
            },
            "required": ["filename"],
        },
        _delete,
    ),
]

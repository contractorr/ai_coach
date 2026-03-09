"""Research MCP tools — topic suggestions, dossiers, and deep research runs."""

from coach_mcp.bootstrap import get_components


def _get_scheduler():
    from intelligence.scheduler import IntelScheduler

    c = get_components()
    return IntelScheduler(
        storage=c["intel_storage"],
        config=c["config"].get("intelligence", {}),
        journal_storage=c["storage"],
        embeddings=c["embeddings"],
        full_config=c["config"],
    )


def _topics(args: dict) -> dict:
    """Auto-suggested research topics from journal/goals."""
    scheduler = _get_scheduler()
    topics = scheduler.get_research_topics()
    return {"topics": topics, "count": len(topics)}


def _run(args: dict) -> dict:
    """Trigger deep research or update a dossier."""
    scheduler = _get_scheduler()
    topic = args.get("topic")
    dossier_id = args.get("dossier_id")
    results = scheduler.run_research_now(topic=topic, dossier_id=dossier_id)
    return {
        "reports": [
            {
                "topic": result.get("topic", ""),
                "title": result.get("title", ""),
                "summary": (result.get("summary") or result.get("content", ""))[:1000],
                "sources_count": len(result.get("sources", [])),
                "saved_path": str(result.get("saved_path", "")),
                "dossier_id": result.get("dossier_id", ""),
            }
            for result in results
        ],
        "count": len(results),
    }


def _dossiers(args: dict) -> dict:
    """List persistent research dossiers."""
    scheduler = _get_scheduler()
    dossiers = scheduler.list_research_dossiers(
        include_archived=bool(args.get("include_archived", False)),
        limit=int(args.get("limit", 20) or 20),
    )
    return {"dossiers": dossiers, "count": len(dossiers)}


def _create_dossier(args: dict) -> dict:
    """Create a persistent research dossier."""
    scheduler = _get_scheduler()
    dossier = scheduler.create_research_dossier(
        topic=args.get("topic", ""),
        scope=args.get("scope", ""),
        core_questions=args.get("core_questions", []),
        assumptions=args.get("assumptions", []),
        related_goals=args.get("related_goals", []),
        tracked_subtopics=args.get("tracked_subtopics", []),
        open_questions=args.get("open_questions", []),
    )
    return dossier or {}


TOOLS = [
    (
        "research_topics",
        {
            "description": "[Experimental] Get auto-suggested research topics based on journal entries and goals.",
            "type": "object",
            "properties": {},
            "required": [],
        },
        _topics,
    ),
    (
        "research_run",
        {
            "description": "[Experimental] Run deep research on a topic or update an existing dossier.",
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Specific topic to research (auto-selects if omitted)",
                },
                "dossier_id": {
                    "type": "string",
                    "description": "Existing dossier ID to update instead of running standalone research",
                },
            },
            "required": [],
        },
        _run,
    ),
    (
        "research_dossiers_list",
        {
            "description": "List persistent research dossiers and their latest change summaries.",
            "type": "object",
            "properties": {
                "include_archived": {"type": "boolean"},
                "limit": {"type": "integer"},
            },
            "required": [],
        },
        _dossiers,
    ),
    (
        "research_dossier_create",
        {
            "description": "Create a persistent research dossier for an ongoing topic.",
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic for the dossier"},
                "scope": {"type": "string", "description": "Optional scope or thesis"},
                "core_questions": {"type": "array", "items": {"type": "string"}},
                "assumptions": {"type": "array", "items": {"type": "string"}},
                "related_goals": {"type": "array", "items": {"type": "string"}},
                "tracked_subtopics": {"type": "array", "items": {"type": "string"}},
                "open_questions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["topic"],
        },
        _create_dossier,
    ),
]

"""Memory MCP tools — list, search, delete facts, get stats."""

from coach_mcp.bootstrap import get_memory_store


def _get_store():
    return get_memory_store()


def _list_facts(args: dict) -> dict:
    """List active facts, optionally filtered by category."""
    store = _get_store()
    category = args.get("category")

    if category:
        from memory.models import FactCategory

        try:
            cat = FactCategory(category)
        except ValueError:
            return {"error": f"Invalid category: {category}"}
        facts = store.get_by_category(cat)
    else:
        facts = store.get_all_active()

    limit = args.get("limit", 50)
    return {
        "facts": [
            {
                "id": f.id,
                "text": f.text,
                "category": f.category.value,
                "confidence": f.confidence,
                "source": f"{f.source_type.value}:{f.source_id}",
            }
            for f in facts[:limit]
        ],
        "count": len(facts),
    }


def _search_facts(args: dict) -> dict:
    """Semantic search over facts."""
    store = _get_store()
    query = args.get("query", "")
    if not query:
        return {"error": "query is required"}

    facts = store.search(query, limit=args.get("limit", 10))
    return {
        "facts": [
            {
                "id": f.id,
                "text": f.text,
                "category": f.category.value,
                "confidence": f.confidence,
            }
            for f in facts
        ],
        "count": len(facts),
    }


def _delete_fact(args: dict) -> dict:
    """Soft-delete a fact."""
    store = _get_store()
    fact_id = args.get("fact_id", "")
    if not fact_id:
        return {"error": "fact_id is required"}

    fact = store.get(fact_id)
    if not fact:
        return {"error": f"Fact not found: {fact_id}"}

    store.delete(fact_id, reason="mcp_delete")
    return {"deleted": True, "fact_id": fact_id}


def _get_stats(args: dict) -> dict:
    """Get fact counts by category."""
    store = _get_store()
    return store.get_stats()


def _list_observations(args: dict) -> dict:
    """List synthesized observations from memory consolidation."""
    store = _get_store()
    observations = store.get_all_active_observations()
    limit = args.get("limit", 20)
    results = []
    for obs in observations[:limit]:
        source_ids = store.get_observation_source_ids(obs.id)
        results.append(
            {
                "id": obs.id,
                "text": obs.text,
                "abstract": obs.abstract,
                "confidence": obs.confidence,
                "group_key": obs.source_id,
                "supporting_facts": source_ids,
                "updated_at": obs.updated_at.isoformat(),
            }
        )
    return {"observations": results, "count": len(observations)}


TOOLS = [
    (
        "memory_list_facts",
        {
            "description": "List active distilled memory facts about the user. Facts are extracted from journal entries and feedback. Optionally filter by category.",
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by fact category",
                    "enum": [
                        "preference",
                        "skill",
                        "constraint",
                        "pattern",
                        "context",
                        "goal_context",
                    ],
                },
                "limit": {
                    "type": "integer",
                    "description": "Max facts to return",
                    "default": 50,
                },
            },
            "required": [],
        },
        _list_facts,
    ),
    (
        "memory_search_facts",
        {
            "description": "Semantic search over distilled memory facts. Use this to find what the system knows about the user related to a topic.",
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
        _search_facts,
    ),
    (
        "memory_delete_fact",
        {
            "description": "Delete a specific fact from distilled memory.",
            "type": "object",
            "properties": {
                "fact_id": {
                    "type": "string",
                    "description": "ID of the fact to delete",
                },
            },
            "required": ["fact_id"],
        },
        _delete_fact,
    ),
    (
        "memory_get_stats",
        {
            "description": "Get distilled memory statistics — fact counts by category and totals.",
            "type": "object",
            "properties": {},
            "required": [],
        },
        _get_stats,
    ),
    (
        "memory_list_observations",
        {
            "description": "List synthesized observations — higher-level insights consolidated from individual memory facts. Each observation summarizes a pattern across multiple related facts.",
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max observations to return",
                    "default": 20,
                },
            },
            "required": [],
        },
        _list_observations,
    ),
]

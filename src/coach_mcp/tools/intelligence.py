"""Intelligence MCP tools — search, recent items, trigger scrape."""

from coach_mcp.bootstrap import get_components, get_profile_storage, get_watchlist_store


def _get_watchlist_store():
    return get_watchlist_store()


def _search(args: dict) -> dict:
    """Semantic search over scraped intelligence."""
    c = get_components()
    query = args["query"]
    limit = args.get("limit", 10)

    results = c["intel_search"].semantic_search(query, n_results=limit)

    return {
        "results": [
            {
                "id": r.get("id"),
                "source": r.get("source", ""),
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "summary": (r.get("summary") or "")[:500],
                "scraped_at": r.get("scraped_at", ""),
                "score": r.get("score"),
            }
            for r in results
        ],
        "count": len(results),
    }


def _get_recent(args: dict) -> dict:
    """Get recent intelligence items."""
    c = get_components()
    days = args.get("days", 7)
    limit = args.get("limit", 50)
    source = args.get("source")

    items = c["intel_storage"].get_recent(days=days, limit=limit)

    # Filter by source if specified
    if source:
        items = [i for i in items if i.get("source") == source]

    return {
        "items": [
            {
                "id": i.get("id"),
                "source": i.get("source", ""),
                "title": i.get("title", ""),
                "url": i.get("url", ""),
                "summary": (i.get("summary") or "")[:500],
                "scraped_at": i.get("scraped_at", ""),
            }
            for i in items
        ],
        "count": len(items),
    }


def _scrape_now(args: dict) -> dict:
    """Trigger all scrapers immediately."""
    c = get_components()

    from intelligence.scheduler import IntelScheduler

    scheduler = IntelScheduler(
        storage=c["intel_storage"],
        config=c["config"].get("intelligence", {}),
        journal_storage=c["storage"],
        embeddings=c["embeddings"],
        full_config=c["config"],
    )

    results = scheduler.run_now()

    # Sync intel embeddings after scrape
    synced = c["intel_search"].sync_embeddings()

    return {
        "scrape_results": results,
        "embeddings_synced": {"added": synced[0], "removed": synced[1]},
    }


def _events_upcoming(args: dict) -> dict:
    """Get upcoming events ranked by relevance."""
    c = get_components()
    from advisor.events import get_upcoming_events

    profile = None
    try:
        profile = get_profile_storage().load()
    except Exception:
        pass

    days = args.get("days", 90)
    limit = args.get("limit", 20)
    events = get_upcoming_events(c["intel_storage"], profile=profile, days=days, limit=limit)

    return {
        "events": [
            {
                "title": e.get("title", ""),
                "url": e.get("url", ""),
                "score": e.get("_score", 0),
                "event_date": e.get("_metadata", {}).get("event_date", ""),
                "location": e.get("_metadata", {}).get("location", ""),
                "cfp_deadline": e.get("_metadata", {}).get("cfp_deadline", ""),
                "online": e.get("_metadata", {}).get("online", False),
            }
            for e in events
        ],
        "count": len(events),
    }


def _trending_radar(args: dict) -> dict:
    """Get cross-source trending topics."""
    c = get_components()
    from intelligence.trending_radar import TrendingRadar

    radar = TrendingRadar(c["intel_storage"].db_path)
    snapshot = radar.get_or_compute(
        days=args.get("days", 7),
        min_sources=args.get("min_sources", 2),
        max_topics=args.get("max_topics", 15),
    )

    # Truncate to top-1 item per topic for MCP context budget
    for topic in snapshot.get("topics", []):
        topic["items"] = topic.get("items", [])[:1]

    return snapshot


def _watchlist_list(args: dict) -> dict:
    """List tracked watchlist items."""
    items = _get_watchlist_store().list_items()
    return {"items": items, "count": len(items)}


def _watchlist_upsert(args: dict) -> dict:
    """Create or update a watchlist item."""
    item_id = args.get("item_id")
    store = _get_watchlist_store()
    payload = {
        "label": args["label"],
        "kind": args.get("kind", "theme"),
        "aliases": args.get("aliases", []),
        "why": args.get("why", ""),
        "priority": args.get("priority", "medium"),
        "tags": args.get("tags", []),
        "goal": args.get("goal", ""),
        "time_horizon": args.get("time_horizon", "quarter"),
        "source_preferences": args.get("source_preferences", []),
    }
    if item_id:
        item = store.update_item(item_id, payload)
        if item is None:
            payload["id"] = item_id
            item = store.save_item(payload)
    else:
        item = store.save_item(payload)
    return {"item": item}


def _watchlist_delete(args: dict) -> dict:
    """Delete a watchlist item."""
    item_id = args["item_id"]
    return {"success": _get_watchlist_store().delete_item(item_id), "item_id": item_id}


TOOLS = [
    (
        "intel_search",
        {
            "description": "Semantic search over scraped intelligence articles and items.",
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10},
            },
            "required": ["query"],
        },
        _search,
    ),
    (
        "intel_get_recent",
        {
            "description": "Get recently scraped intelligence items, optionally filtered by source.",
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Lookback days", "default": 7},
                "limit": {"type": "integer", "description": "Max items", "default": 50},
                "source": {
                    "type": "string",
                    "description": "Filter by source (hackernews, reddit, rss, etc.)",
                },
            },
            "required": [],
        },
        _get_recent,
    ),
    (
        "intel_scrape_now",
        {
            "description": "Trigger all configured scrapers immediately and sync embeddings.",
            "type": "object",
            "properties": {},
            "required": [],
        },
        _scrape_now,
    ),
    (
        "events_upcoming",
        {
            "description": "Get upcoming tech events (conferences, meetups, workshops) ranked by relevance to user profile.",
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Lookback/forward window in days",
                    "default": 90,
                },
                "limit": {"type": "integer", "description": "Max events to return", "default": 20},
            },
            "required": [],
        },
        _events_upcoming,
    ),
    (
        "intel_trending_radar",
        {
            "description": "Get cross-source trending topics — surfaces terms appearing across multiple scraped sources regardless of user goals.",
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Lookback window in days", "default": 7},
                "min_sources": {
                    "type": "integer",
                    "description": "Minimum distinct sources for a topic to qualify",
                    "default": 2,
                },
                "max_topics": {
                    "type": "integer",
                    "description": "Max trending topics to return",
                    "default": 15,
                },
            },
            "required": [],
        },
        _trending_radar,
    ),
    (
        "watchlist_list",
        {
            "description": "List tracked watchlist items used to boost bespoke intelligence ranking.",
            "type": "object",
            "properties": {},
            "required": [],
        },
        _watchlist_list,
    ),
    (
        "watchlist_upsert",
        {
            "description": "Create or update a watchlist item for bespoke intelligence monitoring.",
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Existing item id to update"},
                "label": {"type": "string", "description": "Primary watched entity or theme"},
                "kind": {"type": "string", "description": "Item kind such as company or technology"},
                "aliases": {"type": "array", "items": {"type": "string"}},
                "why": {"type": "string", "description": "Why it matters to the user"},
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "tags": {"type": "array", "items": {"type": "string"}},
                "goal": {"type": "string", "description": "Optional linked goal"},
                "time_horizon": {"type": "string", "description": "Optional horizon label"},
                "source_preferences": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["label"],
        },
        _watchlist_upsert,
    ),
    (
        "watchlist_delete",
        {
            "description": "Delete a watchlist item by id.",
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "Watchlist item id"},
            },
            "required": ["item_id"],
        },
        _watchlist_delete,
    ),
]

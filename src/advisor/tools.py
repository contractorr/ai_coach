"""Shared tool registration for the agentic advisor."""

from __future__ import annotations

from pathlib import Path

import frontmatter
import structlog

from services.tool_registry import ToolRegistry

logger = structlog.get_logger()


def build_tool_registry(components: dict) -> ToolRegistry:
    """Build a shared ToolRegistry populated with advisor tools."""
    registry = ToolRegistry(components)
    register_advisor_tools(registry, components)
    return registry


def register_advisor_tools(registry: ToolRegistry, components: dict) -> None:
    """Register advisor tools onto a shared registry instance."""
    _register_journal_tools(registry, components)
    _register_goal_tools(registry, components)
    _register_intel_tools(registry, components)
    _register_rss_tools(registry, components)
    _register_web_search_tools(registry)
    _register_misc_tools(registry, components)


def _register_journal_tools(registry: ToolRegistry, components: dict) -> None:
    storage = components.get("storage")
    embeddings = components.get("embeddings")
    storage_check = lambda: components.get("storage") is not None
    search_check = lambda: components.get("storage") is not None and components.get("embeddings") is not None

    def journal_search(args: dict) -> dict:
        query = args["query"]
        limit = args.get("limit", 5)
        results = embeddings.query(query, n_results=limit)
        return {
            "results": [
                {
                    "id": r.get("id", ""),
                    "content": (r.get("content") or "")[:1500],
                    "metadata": r.get("metadata", {}),
                    "distance": r.get("distance"),
                }
                for r in results
            ],
            "count": len(results),
        }

    registry.register(
        name="journal_search",
        toolset="journal",
        description="Semantic search over journal entries. Returns entries ranked by relevance.",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 5},
            },
            "required": ["query"],
        },
        handler=journal_search,
        check_fn=search_check,
    )

    def journal_list(args: dict) -> dict:
        entry_type = args.get("entry_type")
        tag = args.get("tag")
        limit = args.get("limit", 20)
        tags = [tag] if tag else None
        entries = storage.list_entries(entry_type=entry_type, tags=tags, limit=limit)
        return {
            "entries": [
                {
                    "filename": Path(e["path"]).name,
                    "title": e.get("title", ""),
                    "type": e.get("type", ""),
                    "created": e.get("created", ""),
                    "tags": e.get("tags", []),
                    "preview": e.get("preview", "")[:300],
                }
                for e in entries
            ],
            "count": len(entries),
        }

    registry.register(
        name="journal_list",
        toolset="journal",
        description="List journal entries with metadata, optionally filtered by type or tag.",
        schema={
            "type": "object",
            "properties": {
                "entry_type": {
                    "type": "string",
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
                "tag": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": [],
        },
        handler=journal_list,
        check_fn=storage_check,
    )

    def journal_read(args: dict) -> dict:
        filename = args["filename"]
        journal_dir = Path(storage.journal_dir)
        filepath = journal_dir / filename
        try:
            filepath.resolve().relative_to(journal_dir.resolve())
        except ValueError:
            return {"error": "Invalid path"}
        if not filepath.exists():
            return {"error": f"Entry not found: {filename}"}
        post = storage.read(filepath)
        return {
            "filename": filename,
            "title": post.get("title", ""),
            "type": post.get("type", ""),
            "created": post.get("created", ""),
            "tags": post.get("tags", []),
            "content": post.content,
        }

    registry.register(
        name="journal_read",
        toolset="journal",
        description="Read full content and frontmatter of a journal entry.",
        schema={
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "e.g. 2024-01-15_daily_meeting-notes.md",
                },
            },
            "required": ["filename"],
        },
        handler=journal_read,
        check_fn=storage_check,
    )

    def journal_create(args: dict) -> dict:
        content = args["content"]
        entry_type = args.get("entry_type", "daily")
        title = args.get("title")
        tags = args.get("tags", [])
        filepath = storage.create(content=content, entry_type=entry_type, title=title, tags=tags)
        try:
            post = storage.read(filepath)
            if embeddings:
                embeddings.add_entry(str(filepath), post.content, dict(post.metadata))
        except Exception:
            pass
        return {
            "path": str(filepath),
            "filename": filepath.name,
            "title": title or filepath.stem,
            "type": entry_type,
        }

    registry.register(
        name="journal_create",
        toolset="journal",
        description="Create a journal entry and sync embeddings. For goals use goals_add instead.",
        schema={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Entry body text"},
                "entry_type": {
                    "type": "string",
                    "enum": ["daily", "project", "reflection", "insight", "note"],
                    "default": "daily",
                },
                "title": {"type": "string", "description": "Entry title"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["content"],
        },
        handler=journal_create,
        check_fn=storage_check,
    )


def _register_goal_tools(registry: ToolRegistry, components: dict) -> None:
    storage = components.get("storage")
    check_fn = lambda: components.get("storage") is not None

    def _get_tracker():
        from advisor.goals import GoalTracker

        return GoalTracker(storage)

    def goals_list(args: dict) -> dict:
        tracker = _get_tracker()
        include_inactive = args.get("include_inactive", False)
        goals = tracker.get_goals(include_inactive=include_inactive)
        enriched = []
        for goal in goals:
            goal_path = Path(goal["path"])
            progress = tracker.get_progress(goal_path)
            enriched.append(
                {
                    "path": str(goal_path),
                    "filename": goal_path.name,
                    "title": goal["title"],
                    "status": goal["status"],
                    "created": goal["created"],
                    "days_since_check": goal["days_since_check"],
                    "is_stale": goal["is_stale"],
                    "progress": progress,
                    "preview": (goal.get("content") or "")[:200],
                }
            )
        return {"goals": enriched, "count": len(enriched)}

    registry.register(
        name="goals_list",
        toolset="goals",
        description="List all goals with staleness info, progress, and milestones.",
        schema={
            "type": "object",
            "properties": {
                "include_inactive": {
                    "type": "boolean",
                    "description": "Include completed/abandoned goals",
                    "default": False,
                },
            },
            "required": [],
        },
        handler=goals_list,
        check_fn=check_fn,
    )

    def goals_add(args: dict) -> dict:
        title = args["title"]
        description = args.get("description", "")
        tags = args.get("tags", [])
        filepath = storage.create(content=description, entry_type="goal", title=title, tags=tags)
        check_days = args.get("check_days", 14)
        if check_days != 14:
            post = frontmatter.load(filepath)
            post["check_in_days"] = check_days
            with open(filepath, "w") as handle:
                handle.write(frontmatter.dumps(post))
        try:
            embeddings = components.get("embeddings")
            if embeddings:
                post = storage.read(filepath)
                embeddings.add_entry(str(filepath), post.content, dict(post.metadata))
        except Exception:
            pass
        return {
            "path": str(filepath),
            "filename": filepath.name,
            "title": title,
            "type": "goal",
        }

    registry.register(
        name="goals_add",
        toolset="goals",
        description="Create a new goal with optional milestones tracking.",
        schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Goal title"},
                "description": {"type": "string", "description": "Goal description/body"},
                "check_days": {
                    "type": "integer",
                    "description": "Days between expected check-ins",
                    "default": 14,
                },
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title"],
        },
        handler=goals_add,
        check_fn=check_fn,
    )

    def goals_check_in(args: dict) -> dict:
        tracker = _get_tracker()
        goal_path = Path(args["goal_path"])
        notes = args.get("notes")
        success = tracker.check_in_goal(goal_path, notes=notes)
        return {"success": success, "goal_path": str(goal_path)}

    registry.register(
        name="goals_check_in",
        toolset="goals",
        description="Record a check-in on a goal, optionally with notes.",
        schema={
            "type": "object",
            "properties": {
                "goal_path": {"type": "string", "description": "Full path to the goal file"},
                "notes": {"type": "string", "description": "Check-in notes"},
            },
            "required": ["goal_path"],
        },
        handler=goals_check_in,
        check_fn=check_fn,
    )

    def goals_update_status(args: dict) -> dict:
        tracker = _get_tracker()
        goal_path = Path(args["goal_path"])
        status = args["status"]
        success = tracker.update_goal_status(goal_path, status)
        return {"success": success, "goal_path": str(goal_path), "status": status}

    registry.register(
        name="goals_update_status",
        toolset="goals",
        description="Update goal status (active/paused/completed/abandoned).",
        schema={
            "type": "object",
            "properties": {
                "goal_path": {"type": "string", "description": "Full path to the goal file"},
                "status": {
                    "type": "string",
                    "enum": ["active", "paused", "completed", "abandoned"],
                },
            },
            "required": ["goal_path", "status"],
        },
        handler=goals_update_status,
        check_fn=check_fn,
    )

    def goal_next_steps(args: dict) -> dict:
        goal_path = Path(args["goal_path"])
        journal_dir = Path(storage.journal_dir)
        try:
            goal_path.resolve().relative_to(journal_dir.resolve())
        except ValueError:
            return {"error": "Invalid path"}
        if not goal_path.exists():
            return {"error": f"Goal not found: {goal_path}"}

        tracker = _get_tracker()
        try:
            post = frontmatter.load(goal_path)
        except Exception as exc:
            return {"error": f"Failed to read goal: {exc}"}

        meta = dict(post.metadata)
        progress = tracker.get_progress(goal_path)

        intel_matches = []
        try:
            intel_storage = components.get("intel_storage")
            if intel_storage:
                from intelligence.goal_intel_match import GoalIntelMatchStore

                match_store = GoalIntelMatchStore(intel_storage.db_path)
                intel_matches = match_store.get_matches(goal_paths=[str(goal_path)], limit=5)
        except Exception:
            pass

        related_entries = []
        try:
            embeddings = components.get("embeddings")
            if embeddings:
                query_text = f"{meta.get('title', '')} {(post.content or '')[:200]}"
                results = embeddings.query(query_text, n_results=5)
                for result in results:
                    result_meta = result.get("metadata", {})
                    if result_meta.get("type") == "goal":
                        continue
                    related_entries.append(
                        {
                            "id": result.get("id", ""),
                            "content": (result.get("content") or "")[:200],
                            "metadata": result_meta,
                        }
                    )
        except Exception:
            pass

        return {
            "title": meta.get("title", ""),
            "status": meta.get("status", "active"),
            "content": (post.content or "")[:1000],
            "milestones": progress.get("milestones", []),
            "progress_percent": progress.get("percent", 0),
            "intel_matches": [
                {
                    "title": match.get("title", ""),
                    "summary": (match.get("summary") or "")[:200],
                    "urgency": match.get("urgency", ""),
                    "url": match.get("url", ""),
                }
                for match in intel_matches
            ],
            "related_journal": related_entries,
        }

    registry.register(
        name="goal_next_steps",
        toolset="goals",
        description="Get enriched context for a goal: full content, milestones, progress, matching intel items, and related journal entries. Use before coaching on a specific goal.",
        schema={
            "type": "object",
            "properties": {
                "goal_path": {"type": "string", "description": "Full path to the goal file"},
            },
            "required": ["goal_path"],
        },
        handler=goal_next_steps,
        check_fn=check_fn,
    )


def _register_intel_tools(registry: ToolRegistry, components: dict) -> None:
    intel_storage = components.get("intel_storage")
    check_fn = lambda: components.get("intel_storage") is not None

    def intel_search(args: dict) -> dict:
        query = args["query"]
        limit = args.get("limit", 10)
        hybrid_search = components.get("intel_search")
        if hybrid_search is not None:
            results = hybrid_search.hybrid_search(query, n_results=limit)
        else:
            results = intel_storage.search(query, limit=limit)
        return {
            "results": [
                {
                    "source": r.get("source", ""),
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "summary": (r.get("summary") or "")[:500],
                    "scraped_at": r.get("scraped_at", ""),
                }
                for r in results
            ],
            "count": len(results),
        }

    registry.register(
        name="intel_search",
        toolset="intel",
        description="Keyword or hybrid search over scraped intelligence articles and items.",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10},
            },
            "required": ["query"],
        },
        handler=intel_search,
        check_fn=check_fn,
    )

    def intel_get_recent(args: dict) -> dict:
        days = args.get("days", 7)
        limit = args.get("limit", 50)
        source = args.get("source")
        items = intel_storage.get_recent(days=days, limit=limit)
        if source:
            items = [item for item in items if item.get("source") == source]
        return {
            "items": [
                {
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

    registry.register(
        name="intel_get_recent",
        toolset="intel",
        description="Get recently scraped intelligence items, optionally filtered by source.",
        schema={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Lookback days", "default": 7},
                "limit": {"type": "integer", "description": "Max items", "default": 50},
                "source": {
                    "type": "string",
                    "description": "Filter: hackernews, reddit, rss, etc.",
                },
            },
            "required": [],
        },
        handler=intel_get_recent,
        check_fn=check_fn,
    )


def _register_rss_tools(registry: ToolRegistry, components: dict) -> None:
    def rss_check() -> bool:
        return bool(components.get("user_id") and components.get("intel_storage") is not None)

    def intel_list_rss_feeds(args: dict) -> dict:
        from user_state_store import get_user_rss_feeds

        feeds = get_user_rss_feeds(components["user_id"])
        return {
            "feeds": [
                {"url": f["url"], "name": f["name"], "added_by": f["added_by"]} for f in feeds
            ],
            "count": len(feeds),
        }

    registry.register(
        name="intel_list_rss_feeds",
        toolset="intel",
        description="List the user's custom RSS feeds. Check before suggesting duplicates.",
        schema={"type": "object", "properties": {}, "required": []},
        handler=intel_list_rss_feeds,
        check_fn=rss_check,
    )

    def intel_add_rss_feed(args: dict) -> dict:
        import asyncio
        from urllib.parse import urlparse

        import httpx

        from user_state_store import add_user_rss_feed

        url = args["url"]
        name = args.get("name")
        reason = args.get("reason", "")

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return {"error": "URL must be http or https"}

        try:
            with httpx.Client(timeout=10, follow_redirects=True) as client:
                response = client.get(url, headers={"User-Agent": "CoachBot/1.0"})
                response.raise_for_status()
                snippet = response.text[:2048].lower()
                if "<rss" not in snippet and "<feed" not in snippet and "<channel" not in snippet:
                    return {"error": "URL does not appear to be a valid RSS/Atom feed"}
        except httpx.HTTPError as exc:
            return {"error": f"Failed to fetch feed: {exc}"}

        feed = add_user_rss_feed(components["user_id"], url, name, added_by="advisor")

        items_scraped = 0
        try:
            from intelligence.sources import RSSFeedScraper

            intel_storage = components["intel_storage"]
            scraper = RSSFeedScraper(intel_storage, url, name=name)
            items = asyncio.get_event_loop().run_until_complete(scraper.scrape())
            items_scraped, _ = asyncio.get_event_loop().run_until_complete(scraper.save_items(items))
            asyncio.get_event_loop().run_until_complete(scraper.close())
        except Exception as exc:
            logger.warning("rss_oneshot_scrape_failed", url=url, error=str(exc))

        return {
            "added": True,
            "feed": feed,
            "items_scraped": items_scraped,
            "reason": reason,
        }

    registry.register(
        name="intel_add_rss_feed",
        toolset="intel",
        description="Add an RSS/Atom feed to the user's custom intel sources. Validates the URL and does an immediate scrape.",
        schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "RSS/Atom feed URL"},
                "name": {"type": "string", "description": "Display name for the feed"},
                "reason": {"type": "string", "description": "Why this feed is relevant to the user"},
            },
            "required": ["url"],
        },
        handler=intel_add_rss_feed,
        check_fn=rss_check,
    )


def _register_web_search_tools(registry: ToolRegistry) -> None:
    def web_search_check() -> bool:
        try:
            from research.web_search import WebSearchClient

            client = WebSearchClient()
            client.close()
            return True
        except Exception:
            return False

    def web_search(args: dict) -> dict:
        from research.web_search import WebSearchClient

        query = args["query"]
        max_results = args.get("max_results", 5)
        with WebSearchClient(max_results=max_results) as search_client:
            results = search_client.search(query)
        return {
            "results": [
                {"title": r.title, "url": r.url, "content": r.content[:500]} for r in results
            ],
            "count": len(results),
        }

    registry.register(
        name="web_search",
        toolset="web_search",
        description="Search the internet for current information. Use when the user's question requires up-to-date info beyond journal/intel, or when you need to research a topic, verify facts, or find resources.",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Max results to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        handler=web_search,
        check_fn=web_search_check,
    )


def _register_misc_tools(registry: ToolRegistry, components: dict) -> None:
    rag = components.get("rag")
    profile_path = components.get("profile_path")

    def recommendations_list(args: dict) -> dict:
        from advisor.recommendation_storage import RecommendationStorage

        rec_dir = components.get("recommendations_dir")
        if not rec_dir:
            return {"recommendations": [], "count": 0}
        rec_storage = RecommendationStorage(Path(rec_dir))
        limit = args.get("limit", 20)
        category = args.get("category")
        status = args.get("status")
        if category:
            recs = rec_storage.list_by_category(category, status=status, limit=limit)
        else:
            recs = rec_storage.list_recent(days=90, status=status, limit=limit)
        return {
            "recommendations": [
                {
                    "id": r.id,
                    "category": r.category,
                    "title": r.title,
                    "description": r.description,
                    "score": r.score,
                    "status": r.status,
                }
                for r in recs
            ],
            "count": len(recs),
        }

    registry.register(
        name="recommendations_list",
        toolset="recommendations",
        description="List recent recommendations, optionally filtered by category or status.",
        schema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20},
                "category": {
                    "type": "string",
                    "description": "learning, career, entrepreneurial, investment",
                },
                "status": {
                    "type": "string",
                    "enum": ["suggested", "in_progress", "completed", "dismissed"],
                },
            },
            "required": [],
        },
        handler=recommendations_list,
        check_fn=lambda: components.get("recommendations_dir") is not None,
    )

    def profile_get(args: dict) -> dict:
        from profile.storage import ProfileStorage

        ps = ProfileStorage(profile_path or "~/coach/profile.yaml")
        profile = ps.load()
        if not profile:
            return {"exists": False, "profile": None}
        return {"exists": True, "summary": profile.summary(), "is_stale": profile.is_stale()}

    registry.register(
        name="profile_get",
        toolset="profile",
        description="Get the user's professional profile including skills, interests, career stage, and aspirations.",
        schema={"type": "object", "properties": {}, "required": []},
        handler=profile_get,
    )

    def get_context(args: dict) -> dict:
        query = args["query"]
        max_chars = args.get("max_chars", 8000)
        journal_ctx, intel_ctx = rag.get_combined_context(query)
        return {
            "journal_context": journal_ctx[:max_chars],
            "intel_context": intel_ctx[:max_chars],
        }

    registry.register(
        name="get_context",
        toolset="context",
        description="Get RAG context (journal + intel) for a query. Use for broad context retrieval.",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language query"},
                "max_chars": {"type": "integer", "default": 8000},
            },
            "required": ["query"],
        },
        handler=get_context,
        check_fn=lambda: components.get("rag") is not None,
    )

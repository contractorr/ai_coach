"""Tool registry for agentic advisor — per-user component-aware handlers."""

import json
from pathlib import Path
from typing import Callable

import frontmatter
import structlog

from llm.base import ToolDefinition

logger = structlog.get_logger()

# Max chars returned per tool result to manage context window
TOOL_RESULT_MAX_CHARS = 4000


class ToolRegistry:
    """Registry of tools the agentic advisor can call.

    Initialized with per-user components dict (not the CLI singleton).
    """

    def __init__(self, components: dict):
        """
        Args:
            components: {
                "storage": JournalStorage,
                "embeddings": EmbeddingManager,
                "intel_storage": IntelStorage,
                "rag": RAGRetriever,
                "profile_path": Path,
                "recommendations_dir": Path,
            }
        """
        self.components = components
        self._tools: dict[str, tuple[ToolDefinition, Callable]] = {}
        self._register_all()

    def get_definitions(self) -> list[ToolDefinition]:
        return [defn for defn, _ in self._tools.values()]

    def execute(self, name: str, arguments: dict) -> str:
        if name not in self._tools:
            return json.dumps({"error": f"Unknown tool: {name}"})

        _, handler = self._tools[name]
        try:
            result = handler(arguments)
            text = json.dumps(result, default=str)
            if len(text) > TOOL_RESULT_MAX_CHARS:
                text = text[:TOOL_RESULT_MAX_CHARS] + "... (truncated)"
            return text
        except Exception as e:
            logger.error("tool_execution_failed", tool=name, error=str(e))
            return json.dumps({"error": str(e)})

    def _register(self, name: str, description: str, schema: dict, handler: Callable):
        defn = ToolDefinition(name=name, description=description, input_schema=schema)
        self._tools[name] = (defn, handler)

    def _register_all(self):
        self._register_journal_tools()
        self._register_goal_tools()
        self._register_intel_tools()
        self._register_rss_tools()
        self._register_web_search_tools()
        self._register_misc_tools()

    # --- Journal tools ---

    def _register_journal_tools(self):
        storage = self.components["storage"]
        embeddings = self.components["embeddings"]

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

        self._register(
            "journal_search",
            "Semantic search over journal entries. Returns entries ranked by relevance.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results", "default": 5},
                },
                "required": ["query"],
            },
            journal_search,
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

        self._register(
            "journal_list",
            "List journal entries with metadata, optionally filtered by type or tag.",
            {
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
            journal_list,
        )

        def journal_read(args: dict) -> dict:
            filename = args["filename"]
            journal_dir = Path(storage.journal_dir)
            filepath = journal_dir / filename
            # Path traversal check
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

        self._register(
            "journal_read",
            "Read full content and frontmatter of a journal entry.",
            {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "e.g. 2024-01-15_daily_meeting-notes.md",
                    },
                },
                "required": ["filename"],
            },
            journal_read,
        )

        def journal_create(args: dict) -> dict:
            content = args["content"]
            entry_type = args.get("entry_type", "daily")
            title = args.get("title")
            tags = args.get("tags", [])
            filepath = storage.create(
                content=content, entry_type=entry_type, title=title, tags=tags
            )
            # Incrementally index the new entry instead of re-syncing the whole journal
            try:
                post = storage.read(filepath)
                embeddings.add_entry(str(filepath), post.content, dict(post.metadata))
            except Exception:
                pass
            return {
                "path": str(filepath),
                "filename": filepath.name,
                "title": title or filepath.stem,
                "type": entry_type,
            }

        self._register(
            "journal_create",
            "Create a journal entry and sync embeddings. For goals use goals_add instead.",
            {
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
            journal_create,
        )

    # --- Goal tools ---

    def _register_goal_tools(self):
        storage = self.components["storage"]

        def _get_tracker():
            from advisor.goals import GoalTracker

            return GoalTracker(storage)

        def goals_list(args: dict) -> dict:
            tracker = _get_tracker()
            include_inactive = args.get("include_inactive", False)
            goals = tracker.get_goals(include_inactive=include_inactive)
            enriched = []
            for g in goals:
                goal_path = Path(g["path"])
                progress = tracker.get_progress(goal_path)
                enriched.append(
                    {
                        "path": str(goal_path),
                        "filename": goal_path.name,
                        "title": g["title"],
                        "status": g["status"],
                        "created": g["created"],
                        "days_since_check": g["days_since_check"],
                        "is_stale": g["is_stale"],
                        "progress": progress,
                        "preview": (g.get("content") or "")[:200],
                    }
                )
            return {"goals": enriched, "count": len(enriched)}

        self._register(
            "goals_list",
            "List all goals with staleness info, progress, and milestones.",
            {
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
            goals_list,
        )

        def goals_add(args: dict) -> dict:
            title = args["title"]
            description = args.get("description", "")
            tags = args.get("tags", [])
            filepath = storage.create(
                content=description, entry_type="goal", title=title, tags=tags
            )
            # Set check_in_days if non-default
            check_days = args.get("check_days", 14)
            if check_days != 14:
                import frontmatter

                post = frontmatter.load(filepath)
                post["check_in_days"] = check_days
                with open(filepath, "w") as f:
                    f.write(frontmatter.dumps(post))
            # Incrementally index the new goal instead of re-syncing the whole journal
            try:
                embeddings = self.components["embeddings"]
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

        self._register(
            "goals_add",
            "Create a new goal with optional milestones tracking.",
            {
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
            goals_add,
        )

        def goals_check_in(args: dict) -> dict:
            tracker = _get_tracker()
            goal_path = Path(args["goal_path"])
            notes = args.get("notes")
            success = tracker.check_in_goal(goal_path, notes=notes)
            return {"success": success, "goal_path": str(goal_path)}

        self._register(
            "goals_check_in",
            "Record a check-in on a goal, optionally with notes.",
            {
                "type": "object",
                "properties": {
                    "goal_path": {"type": "string", "description": "Full path to the goal file"},
                    "notes": {"type": "string", "description": "Check-in notes"},
                },
                "required": ["goal_path"],
            },
            goals_check_in,
        )

        def goals_update_status(args: dict) -> dict:
            tracker = _get_tracker()
            goal_path = Path(args["goal_path"])
            status = args["status"]
            success = tracker.update_goal_status(goal_path, status)
            return {"success": success, "goal_path": str(goal_path), "status": status}

        self._register(
            "goals_update_status",
            "Update goal status (active/paused/completed/abandoned).",
            {
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
            goals_update_status,
        )

        def goal_next_steps(args: dict) -> dict:
            """Enriched goal context: progress, matching intel, related journal entries."""
            goal_path_str = args["goal_path"]
            goal_path = Path(goal_path_str)
            journal_dir = Path(storage.journal_dir)

            # Path traversal check
            try:
                goal_path.resolve().relative_to(journal_dir.resolve())
            except ValueError:
                return {"error": "Invalid path"}

            if not goal_path.exists():
                return {"error": f"Goal not found: {goal_path_str}"}

            tracker = _get_tracker()

            # Read full goal content
            try:
                post = frontmatter.load(goal_path)
            except Exception as e:
                return {"error": f"Failed to read goal: {e}"}

            meta = dict(post.metadata)
            progress = tracker.get_progress(goal_path)

            # Matching intel items
            intel_matches = []
            try:
                intel_storage = self.components.get("intel_storage")
                if intel_storage:
                    from intelligence.goal_intel_match import GoalIntelMatchStore

                    match_store = GoalIntelMatchStore(intel_storage.db_path)
                    intel_matches = match_store.get_matches(goal_paths=[str(goal_path)], limit=5)
            except Exception:
                pass

            # Related journal entries (semantic search on goal title+content)
            related_entries = []
            try:
                embeddings = self.components.get("embeddings")
                if embeddings:
                    query_text = f"{meta.get('title', '')} {(post.content or '')[:200]}"
                    results = embeddings.query(query_text, n_results=5)
                    for r in results:
                        # Exclude the goal itself and other goal-type entries
                        r_meta = r.get("metadata", {})
                        if r_meta.get("type") == "goal":
                            continue
                        related_entries.append(
                            {
                                "id": r.get("id", ""),
                                "content": (r.get("content") or "")[:200],
                                "metadata": r_meta,
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
                        "title": m.get("title", ""),
                        "summary": (m.get("summary") or "")[:200],
                        "urgency": m.get("urgency", ""),
                        "url": m.get("url", ""),
                    }
                    for m in intel_matches
                ],
                "related_journal": related_entries,
            }

        self._register(
            "goal_next_steps",
            "Get enriched context for a goal: full content, milestones, progress, matching intel items, and related journal entries. Use before coaching on a specific goal.",
            {
                "type": "object",
                "properties": {
                    "goal_path": {
                        "type": "string",
                        "description": "Full path to the goal file",
                    },
                },
                "required": ["goal_path"],
            },
            goal_next_steps,
        )

    # --- Intel tools ---

    def _register_intel_tools(self):
        intel_storage = self.components["intel_storage"]

        def intel_search(args: dict) -> dict:
            query = args["query"]
            limit = args.get("limit", 10)
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

        self._register(
            "intel_search",
            "Keyword search over scraped intelligence articles and items.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results", "default": 10},
                },
                "required": ["query"],
            },
            intel_search,
        )

        def intel_get_recent(args: dict) -> dict:
            days = args.get("days", 7)
            limit = args.get("limit", 50)
            source = args.get("source")
            items = intel_storage.get_recent(days=days, limit=limit)
            if source:
                items = [i for i in items if i.get("source") == source]
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

        self._register(
            "intel_get_recent",
            "Get recently scraped intelligence items, optionally filtered by source.",
            {
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
            intel_get_recent,
        )

    # --- RSS feed management tools ---

    def _register_rss_tools(self):
        user_id = self.components.get("user_id")
        if not user_id:
            return

        def intel_list_rss_feeds(args: dict) -> dict:
            from user_state_store import get_user_rss_feeds

            feeds = get_user_rss_feeds(user_id)
            return {
                "feeds": [
                    {"url": f["url"], "name": f["name"], "added_by": f["added_by"]} for f in feeds
                ],
                "count": len(feeds),
            }

        self._register(
            "intel_list_rss_feeds",
            "List the user's custom RSS feeds. Check before suggesting duplicates.",
            {
                "type": "object",
                "properties": {},
                "required": [],
            },
            intel_list_rss_feeds,
        )

        def intel_add_rss_feed(args: dict) -> dict:
            import asyncio
            from urllib.parse import urlparse

            import httpx

            from user_state_store import add_user_rss_feed

            url = args["url"]
            name = args.get("name")
            reason = args.get("reason", "")

            # Validate URL scheme
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return {"error": "URL must be http or https"}

            # Validate feed
            try:
                with httpx.Client(timeout=10, follow_redirects=True) as client:
                    resp = client.get(url, headers={"User-Agent": "CoachBot/1.0"})
                    resp.raise_for_status()
                    snippet = resp.text[:2048].lower()
                    if (
                        "<rss" not in snippet
                        and "<feed" not in snippet
                        and "<channel" not in snippet
                    ):
                        return {"error": "URL does not appear to be a valid RSS/Atom feed"}
            except httpx.HTTPError as e:
                return {"error": f"Failed to fetch feed: {e}"}

            # Persist
            feed = add_user_rss_feed(user_id, url, name, added_by="advisor")

            # One-shot scrape
            items_scraped = 0
            try:
                from intelligence.sources import RSSFeedScraper

                intel_storage = self.components["intel_storage"]
                scraper = RSSFeedScraper(intel_storage, url, name=name)
                items = asyncio.get_event_loop().run_until_complete(scraper.scrape())
                items_scraped, _ = asyncio.get_event_loop().run_until_complete(
                    scraper.save_items(items)
                )
                asyncio.get_event_loop().run_until_complete(scraper.close())
            except Exception as e:
                logger.warning("rss_oneshot_scrape_failed", url=url, error=str(e))

            return {
                "added": True,
                "feed": feed,
                "items_scraped": items_scraped,
                "reason": reason,
            }

        self._register(
            "intel_add_rss_feed",
            "Add an RSS/Atom feed to the user's custom intel sources. Validates the URL and does an immediate scrape.",
            {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "RSS/Atom feed URL",
                    },
                    "name": {
                        "type": "string",
                        "description": "Display name for the feed",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this feed is relevant to the user",
                    },
                },
                "required": ["url"],
            },
            intel_add_rss_feed,
        )

    # --- Web search tools ---

    def _register_web_search_tools(self):
        from research.web_search import WebSearchClient

        search_client = WebSearchClient()

        def web_search(args: dict) -> dict:
            query = args["query"]
            max_results = args.get("max_results", 5)
            search_client.max_results = max_results
            results = search_client.search(query)
            return {
                "results": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "content": r.content[:500],
                    }
                    for r in results
                ],
                "count": len(results),
            }

        self._register(
            "web_search",
            "Search the internet for current information. Use when the user's question requires up-to-date info beyond journal/intel, or when you need to research a topic, verify facts, or find resources.",
            {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max results to return",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
            web_search,
        )

    # --- Misc tools (recommendations, profile, context) ---

    def _register_misc_tools(self):
        rag = self.components["rag"]
        profile_path = self.components.get("profile_path")

        def recommendations_list(args: dict) -> dict:
            from advisor.recommendation_storage import RecommendationStorage

            rec_dir = self.components.get("recommendations_dir")
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

        self._register(
            "recommendations_list",
            "List recent recommendations, optionally filtered by category or status.",
            {
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
            recommendations_list,
        )

        def profile_get(args: dict) -> dict:
            from profile.storage import ProfileStorage

            ps = ProfileStorage(profile_path or "~/coach/profile.yaml")
            p = ps.load()
            if not p:
                return {"exists": False, "profile": None}
            return {"exists": True, "summary": p.summary(), "is_stale": p.is_stale()}

        self._register(
            "profile_get",
            "Get the user's professional profile including skills, interests, career stage, and aspirations.",
            {
                "type": "object",
                "properties": {},
                "required": [],
            },
            profile_get,
        )

        def get_context(args: dict) -> dict:
            query = args["query"]
            max_chars = args.get("max_chars", 8000)
            journal_ctx, intel_ctx = rag.get_combined_context(query)
            return {
                "journal_context": journal_ctx[:max_chars],
                "intel_context": intel_ctx[:max_chars],
            }

        self._register(
            "get_context",
            "Get RAG context (journal + intel) for a query. Use for broad context retrieval.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language query"},
                    "max_chars": {"type": "integer", "default": 8000},
                },
                "required": ["query"],
            },
            get_context,
        )

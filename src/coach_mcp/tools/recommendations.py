"""Recommendations MCP tools — list, execution actions, update status, rate."""

from coach_mcp.bootstrap import get_components


def _get_rec_storage():
    from advisor.recommendation_storage import RecommendationStorage
    from cli.utils import get_rec_db_path

    c = get_components()
    db_path = get_rec_db_path(c["config"])
    return RecommendationStorage(db_path)


def _list_recs(args: dict) -> dict:
    """List recent recommendations."""
    rec_storage = _get_rec_storage()
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
                "rationale": r.rationale,
                "score": r.score,
                "status": r.status,
                "created_at": r.created_at,
                "action_item": (r.metadata or {}).get("action_item"),
            }
            for r in recs
        ],
        "count": len(recs),
    }


def _create_action(args: dict) -> dict:
    """Create a tracked action item from a recommendation."""
    rec_storage = _get_rec_storage()
    rec_id = args["rec_id"]
    action_item = rec_storage.create_action_item(
        rec_id,
        goal_path=args.get("goal_path"),
        goal_title=args.get("goal_title"),
        effort=args.get("effort"),
        due_window=args.get("due_window"),
        next_step=args.get("next_step"),
        success_criteria=args.get("success_criteria"),
    )
    record = rec_storage.get_action_item(rec_id) if action_item else None
    return {
        "success": bool(action_item),
        "rec_id": rec_id,
        "action_item": record.action_item if record else None,
    }


def _update_action(args: dict) -> dict:
    """Update a tracked recommendation action item."""
    rec_storage = _get_rec_storage()
    rec_id = args["rec_id"]
    action_item = rec_storage.update_action_item(
        rec_id,
        status=args.get("status"),
        effort=args.get("effort"),
        due_window=args.get("due_window"),
        blockers=args.get("blockers"),
        review_notes=args.get("review_notes"),
        next_step=args.get("next_step"),
        success_criteria=args.get("success_criteria"),
        goal_path=args.get("goal_path"),
        goal_title=args.get("goal_title"),
    )
    return {"success": bool(action_item), "rec_id": rec_id, "action_item": action_item}


def _list_actions(args: dict) -> dict:
    """List tracked recommendation action items."""
    rec_storage = _get_rec_storage()
    actions = rec_storage.list_action_items(
        status=args.get("status"),
        goal_path=args.get("goal_path"),
        limit=args.get("limit", 20),
    )
    return {
        "actions": [
            {
                "rec_id": action.recommendation_id,
                "title": action.recommendation_title,
                "category": action.category,
                "score": action.score,
                "recommendation_status": action.recommendation_status,
                "action_item": action.action_item,
            }
            for action in actions
        ],
        "count": len(actions),
    }


def _weekly_plan(args: dict) -> dict:
    """Build a weekly plan from accepted action items."""
    rec_storage = _get_rec_storage()
    plan = rec_storage.build_weekly_plan(
        capacity_points=args.get("capacity_points", 6),
        goal_path=args.get("goal_path"),
    )
    return {
        "items": [
            {
                "rec_id": action.recommendation_id,
                "title": action.recommendation_title,
                "category": action.category,
                "score": action.score,
                "action_item": action.action_item,
            }
            for action in plan["items"]
        ],
        "capacity_points": plan["capacity_points"],
        "used_points": plan["used_points"],
        "remaining_points": plan["remaining_points"],
    }


def _update_status(args: dict) -> dict:
    """Update recommendation status."""
    rec_storage = _get_rec_storage()
    rec_id = args["rec_id"]
    status = args["status"]

    success = rec_storage.update_status(rec_id, status)
    return {"success": success, "rec_id": rec_id, "status": status}


def _rate(args: dict) -> dict:
    """Rate a recommendation's usefulness."""
    rec_storage = _get_rec_storage()
    rec_id = args["rec_id"]
    rating = args["rating"]
    comment = args.get("comment")

    success = rec_storage.add_feedback(rec_id, rating, comment=comment)
    return {"success": success, "rec_id": rec_id, "rating": rating}


TOOLS = [
    (
        "recommendations_list",
        {
            "description": "List recent recommendations, optionally filtered by category or status.",
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max results", "default": 20},
                "category": {
                    "type": "string",
                    "description": "Filter: learning, career, entrepreneurial, investment",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status",
                    "enum": ["suggested", "in_progress", "completed", "dismissed"],
                },
            },
            "required": [],
        },
        _list_recs,
    ),
    (
        "recommendations_update_status",
        {
            "description": "Update a recommendation's status.",
            "type": "object",
            "properties": {
                "rec_id": {"type": "integer", "description": "Recommendation ID"},
                "status": {
                    "type": "string",
                    "enum": ["suggested", "in_progress", "completed", "dismissed"],
                    "description": "New status",
                },
            },
            "required": ["rec_id", "status"],
        },
        _update_status,
    ),
    (
        "recommendations_action_create",
        {
            "description": "Convert a recommendation into a tracked action item.",
            "type": "object",
            "properties": {
                "rec_id": {"type": "string", "description": "Recommendation ID"},
                "goal_path": {"type": "string", "description": "Optional linked goal path"},
                "goal_title": {"type": "string", "description": "Optional linked goal title"},
                "effort": {
                    "type": "string",
                    "enum": ["small", "medium", "large"],
                    "description": "Effort estimate",
                },
                "due_window": {
                    "type": "string",
                    "enum": ["today", "this_week", "later"],
                    "description": "Planning bucket",
                },
                "next_step": {"type": "string", "description": "Optional override for next step"},
                "success_criteria": {
                    "type": "string",
                    "description": "Optional override for success criteria",
                },
            },
            "required": ["rec_id"],
        },
        _create_action,
    ),
    (
        "recommendations_action_update",
        {
            "description": "Update a tracked action item for a recommendation.",
            "type": "object",
            "properties": {
                "rec_id": {"type": "string", "description": "Recommendation ID"},
                "status": {
                    "type": "string",
                    "enum": ["accepted", "deferred", "blocked", "completed", "abandoned"],
                },
                "effort": {"type": "string", "enum": ["small", "medium", "large"]},
                "due_window": {"type": "string", "enum": ["today", "this_week", "later"]},
                "blockers": {"type": "array", "items": {"type": "string"}},
                "review_notes": {"type": "string"},
                "next_step": {"type": "string"},
                "success_criteria": {"type": "string"},
                "goal_path": {"type": "string"},
                "goal_title": {"type": "string"},
            },
            "required": ["rec_id"],
        },
        _update_action,
    ),
    (
        "recommendations_action_list",
        {
            "description": "List tracked recommendation action items.",
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max results", "default": 20},
                "status": {
                    "type": "string",
                    "enum": ["accepted", "deferred", "blocked", "completed", "abandoned"],
                },
                "goal_path": {"type": "string", "description": "Optional linked goal path filter"},
            },
            "required": [],
        },
        _list_actions,
    ),
    (
        "recommendations_action_weekly_plan",
        {
            "description": "Build a weekly plan from accepted tracked recommendation actions.",
            "type": "object",
            "properties": {
                "capacity_points": {
                    "type": "integer",
                    "description": "Weekly capacity budget",
                    "default": 6,
                },
                "goal_path": {"type": "string", "description": "Optional linked goal path filter"},
            },
            "required": [],
        },
        _weekly_plan,
    ),
    (
        "recommendations_rate",
        {
            "description": "Rate a recommendation's usefulness (1-5).",
            "type": "object",
            "properties": {
                "rec_id": {"type": "integer", "description": "Recommendation ID"},
                "rating": {
                    "type": "integer",
                    "description": "Rating from 1 to 5",
                    "minimum": 1,
                    "maximum": 5,
                },
                "comment": {"type": "string", "description": "Optional feedback comment"},
            },
            "required": ["rec_id", "rating"],
        },
        _rate,
    ),
]

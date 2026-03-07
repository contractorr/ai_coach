"""Project discovery MCP tools."""

from coach_mcp.bootstrap import get_components, get_profile_storage
from services.projects import (
    build_project_ideas_context,
    discover_matching_project_issues,
    list_project_issues,
)


def _projects_discover(args: dict) -> dict:
    """Find matching open-source issues."""
    c = get_components()

    profile = None
    try:
        profile = get_profile_storage().load()
    except Exception:
        pass

    limit = args.get("limit", 20)
    days = args.get("days", 14)
    return discover_matching_project_issues(
        c["intel_storage"],
        profile=profile,
        limit=limit,
        days=days,
        summary_limit=300,
    )


def _projects_ideas(args: dict) -> dict:
    """Get journal context for side-project idea generation (no LLM in MCP layer)."""
    c = get_components()
    return build_project_ideas_context(
        profile_storage=get_profile_storage(),
        journal_search=c["search"],
    )


def _projects_list(args: dict) -> dict:
    """List tracked project opportunities."""
    c = get_components()
    days = args.get("days", 14)
    return list_project_issues(c["intel_storage"], days=days, limit=50, include_scraped_at=True)


TOOLS = [
    (
        "projects_discover",
        {
            "description": "Find open-source issues matching user's skills and interests.",
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max issues", "default": 20},
                "days": {
                    "type": "integer",
                    "description": "Lookback window in days",
                    "default": 14,
                },
            },
            "required": [],
        },
        _projects_discover,
    ),
    (
        "projects_ideas",
        {
            "description": "Get context for generating side-project ideas from journal pain points.",
            "type": "object",
            "properties": {},
            "required": [],
        },
        _projects_ideas,
    ),
    (
        "projects_list",
        {
            "description": "List tracked project opportunities from GitHub issue scraping.",
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Lookback days", "default": 14},
            },
            "required": [],
        },
        _projects_list,
    ),
]

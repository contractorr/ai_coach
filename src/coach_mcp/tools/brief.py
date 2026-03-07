"""Daily brief MCP tool."""

from coach_mcp.bootstrap import get_components, get_recommendation_storage
from services.daily_brief import build_daily_brief_payload, collect_daily_brief_inputs


def _get_daily_brief(args: dict) -> dict:
    """Build time-budgeted daily action plan."""
    from cli.utils import get_profile_storage

    c = get_components()

    brief_inputs = collect_daily_brief_inputs(
        c["storage"],
        profile_storage=get_profile_storage(c["config"], storage_paths=c.get("storage_paths")),
        recommendation_storage=get_recommendation_storage(),
    )
    return build_daily_brief_payload(**brief_inputs)


TOOLS = [
    (
        "get_daily_brief",
        {
            "description": "Get a time-budgeted daily action plan based on stale goals and recommendations. No LLM needed — pure structured data.",
            "type": "object",
            "properties": {},
            "required": [],
        },
        _get_daily_brief,
    ),
]

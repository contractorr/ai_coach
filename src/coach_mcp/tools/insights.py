"""Insights MCP tool — unified view of signals, patterns, and heartbeat output."""

from coach_mcp.bootstrap import get_insight_store


def _get_insights(args: dict) -> dict:
    """Query active insights (unexpired, filtered by type/severity)."""
    store = get_insight_store()
    rows = store.get_active(
        insight_type=args.get("type"),
        min_severity=args.get("min_severity", 1),
        limit=args.get("limit", 20),
    )
    return {"insights": rows, "count": len(rows)}


TOOLS = [
    (
        "get_insights",
        {
            "description": "Get active insights — unified view of detected signals, patterns, and intel-to-goal matches. Insights auto-expire after 14 days.",
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Filter by insight type (e.g. goal_stale, intel_match, pattern_blind_spot)",
                },
                "min_severity": {
                    "type": "integer",
                    "description": "Minimum severity (1-10)",
                    "default": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": "Max insights to return",
                    "default": 20,
                },
            },
            "required": [],
        },
        _get_insights,
    ),
]

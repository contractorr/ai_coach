"""Profile MCP tools — get profile, update fields."""

from coach_mcp.bootstrap import get_components, get_profile_storage
from services.profile import get_profile_payload, serialize_profile, update_profile_fields


def _profile_get(args: dict) -> dict:
    """Get current user profile."""
    get_components()
    ps = get_profile_storage()
    return get_profile_payload(ps)


def _profile_update_field(args: dict) -> dict:
    """Update a single profile field."""
    get_components()
    ps = get_profile_storage()
    field = args["field"]
    value = args["value"]

    try:
        profile, _updated_fields = update_profile_fields(ps, {field: value})
        return {"success": True, "profile": serialize_profile(profile)}
    except ValueError as e:
        return {"success": False, "error": str(e)}


TOOLS = [
    (
        "profile_get",
        {
            "description": "Get the user's professional profile including skills, interests, career stage, location, and aspirations.",
            "type": "object",
            "properties": {},
            "required": [],
        },
        _profile_get,
    ),
    (
        "profile_update_field",
        {
            "description": "Update a single field on the user's profile.",
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "Field name (skills, interests, career_stage, current_role, aspirations, location, languages_frameworks, learning_style, weekly_hours_available)",
                },
                "value": {
                    "description": "New value for the field. For list fields (interests, languages_frameworks), pass comma-separated string.",
                },
            },
            "required": ["field", "value"],
        },
        _profile_update_field,
    ),
]

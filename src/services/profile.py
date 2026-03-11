"""Shared profile read/update orchestration for delivery surfaces."""

from profile.storage import Skill
from pydantic import ValidationError
from typing import Any

from shared_types import CareerStage

PROFILE_LIST_FIELDS = {
    "interests",
    "languages_frameworks",
    "industries_watching",
    "technologies_watching",
    "fears_risks",
    "active_projects",
}


def normalize_profile_value(field: str, value: Any) -> Any:
    """Normalize raw profile updates into domain-friendly values."""
    if field == "skills" and isinstance(value, list):
        return [Skill(**item) if isinstance(item, dict) else item for item in value]
    if field == "career_stage" and isinstance(value, str):
        return CareerStage(value)
    if field in PROFILE_LIST_FIELDS and isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


def serialize_profile(profile) -> dict[str, Any]:
    """Serialize a profile for web/MCP responses."""
    data = profile.model_dump()
    data["career_stage"] = str(data["career_stage"])
    data["skills"] = [
        {"name": skill["name"], "proficiency": skill["proficiency"]} for skill in data["skills"]
    ]
    data["summary"] = profile.summary()
    data["is_stale"] = profile.is_stale()
    return data


def get_profile_payload(storage) -> dict[str, Any]:
    """Load and serialize a profile with exists metadata."""
    profile = storage.load()
    if not profile:
        return {"exists": False, "profile": None}
    return {
        "exists": True,
        "profile": serialize_profile(profile),
        "summary": profile.summary(),
        "is_stale": profile.is_stale(),
    }


def update_profile_fields(storage, updates: dict[str, Any], embed_callback=None):
    """Apply normalized updates to a profile, save it, and optionally re-embed it."""
    profile = storage.get_or_empty()
    if not updates:
        raise ValueError("No fields to update")

    normalized_updates = {}
    for field, value in updates.items():
        if not hasattr(profile, field):
            raise ValueError(f"Unknown field: {field}")
        normalized_value = normalize_profile_value(field, value)
        normalized_updates[field] = normalized_value

    merged_profile_data = profile.model_dump()
    merged_profile_data.update(normalized_updates)
    try:
        validated_profile = type(profile).model_validate(merged_profile_data)
    except ValidationError as exc:
        first_error = exc.errors()[0]
        field_path = ".".join(str(part) for part in first_error.get("loc", ()))
        message = first_error.get("msg", "Invalid value")
        if field_path:
            raise ValueError(f"Invalid value for {field_path}: {message}") from exc
        raise ValueError(message) from exc

    storage.save(validated_profile)
    if embed_callback is not None:
        embed_callback(validated_profile)
    return validated_profile, list(normalized_updates.keys())

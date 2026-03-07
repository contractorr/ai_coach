"""Shared recommendation action-item orchestration for all delivery surfaces."""

from typing import Any


def serialize_action_record(record) -> dict[str, Any] | None:
    """Serialize a tracked recommendation action record into surface DTOs."""
    if not record:
        return None

    action_item = getattr(record, "action_item", None)
    if not isinstance(action_item, dict):
        return None

    return {
        "recommendation_id": record.recommendation_id,
        "recommendation_title": record.recommendation_title,
        "category": record.category,
        "score": record.score,
        "recommendation_status": record.recommendation_status,
        "created_at": record.created_at or "",
        "action_item": dict(action_item),
    }


def create_action_item(storage, rec_id: str, **kwargs) -> dict[str, Any]:
    """Create a tracked action item and return a serialized result."""
    action_item = storage.create_action_item(rec_id, **kwargs)
    record = storage.get_action_item(rec_id) if action_item else None
    serialized = serialize_action_record(record)
    return {
        "success": bool(action_item),
        "persisted": serialized is not None,
        "record": serialized,
        "action_item": serialized["action_item"] if serialized else action_item,
        "rec_id": rec_id,
    }


def update_action_item(storage, rec_id: str, **kwargs) -> dict[str, Any]:
    """Update a tracked action item and return a serialized result."""
    action_item = storage.update_action_item(rec_id, **kwargs)
    record = storage.get_action_item(rec_id) if action_item else None
    serialized = serialize_action_record(record)
    return {
        "success": bool(action_item),
        "persisted": serialized is not None,
        "record": serialized,
        "action_item": serialized["action_item"] if serialized else action_item,
        "rec_id": rec_id,
    }


def list_action_items(storage, *, status: str | None = None, goal_path: str | None = None, limit: int = 20) -> dict[str, Any]:
    """List tracked recommendation action items as serialized DTOs."""
    actions = storage.list_action_items(status=status, goal_path=goal_path, limit=limit)
    serialized = [serialize_action_record(action) for action in actions]
    return {"actions": serialized, "count": len(serialized)}


def build_weekly_plan(storage, *, capacity_points: int = 6, goal_path: str | None = None) -> dict[str, Any]:
    """Build a weekly plan and serialize the selected action items."""
    plan = storage.build_weekly_plan(capacity_points=capacity_points, goal_path=goal_path)
    capacity_points = plan["capacity_points"]
    used_points = plan["used_points"]
    return {
        "items": [serialize_action_record(action) for action in plan["items"]],
        "capacity_points": capacity_points,
        "used_points": used_points,
        "remaining_points": plan.get("remaining_points", max(0, capacity_points - used_points)),
        "generated_at": plan.get("generated_at", ""),
    }

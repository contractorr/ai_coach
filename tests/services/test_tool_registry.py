"""Tests for the shared tool registry."""

import json

from services.tool_registry import ToolRegistry


def test_check_fn_gates_definitions():
    registry = ToolRegistry()
    registry.register(
        name="hidden",
        toolset="test",
        description="hidden",
        schema={"type": "object", "properties": {}, "required": []},
        handler=lambda _args: {"ok": True},
        check_fn=lambda: False,
    )

    assert registry.get_definitions() == []
    assert registry.execute("hidden", {}) == json.dumps({"error": "Unknown tool: hidden"})


def test_check_fn_error_treated_as_unavailable():
    registry = ToolRegistry()
    registry.register(
        name="broken_check",
        toolset="test",
        description="broken",
        schema={"type": "object", "properties": {}, "required": []},
        handler=lambda _args: {"ok": True},
        check_fn=lambda: 1 / 0,
    )

    assert registry.is_tool_available("broken_check") is False


def test_execute_wraps_errors_with_tool_name():
    registry = ToolRegistry()
    registry.register(
        name="boom",
        toolset="test",
        description="boom",
        schema={"type": "object", "properties": {}, "required": []},
        handler=lambda _args: (_ for _ in ()).throw(ValueError("failed")),
    )

    assert registry.execute("boom", {}) == json.dumps({"error": "boom: failed"})


def test_execute_truncates_large_results():
    registry = ToolRegistry()
    registry.register(
        name="large",
        toolset="test",
        description="large",
        schema={"type": "object", "properties": {}, "required": []},
        handler=lambda _args: {"payload": "x" * 5000},
    )

    result = registry.execute("large", {})
    assert len(result) <= registry.TOOL_RESULT_MAX_CHARS
    parsed = json.loads(result)
    assert parsed["truncated"] is True
    assert parsed["original_length"] > registry.TOOL_RESULT_MAX_CHARS
    assert parsed["result_preview"].startswith("{\"payload\":")

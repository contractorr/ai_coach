"""Tests for MCP tool registry helpers."""

from coach_mcp.tools import TOOL_MODULES, build_tool_registry


def test_build_tool_registry_matches_tool_modules():
    tools, handlers = build_tool_registry()

    expected = sum(len(module.TOOLS) for module in TOOL_MODULES)
    assert len(tools) == expected
    assert set(tool.name for tool in tools) == set(handlers)

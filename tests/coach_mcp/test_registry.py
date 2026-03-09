"""Tests for MCP tool registry helpers."""

from coach_mcp.tools import TOOL_MODULES, build_tool_registry


def test_build_tool_registry_matches_tool_modules():
    registry = build_tool_registry()
    tools = registry.get_mcp_definitions()

    expected = sum(len(module.TOOLS) for module in TOOL_MODULES)
    assert len(tools) == expected
    assert set(tool.name for tool in tools) == set(entry[0] for module in TOOL_MODULES for entry in module.TOOLS)

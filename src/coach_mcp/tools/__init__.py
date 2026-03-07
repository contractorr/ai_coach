"""MCP tool registry helpers."""

from mcp.types import Tool

from . import (
    brief,
    goals,
    insights,
    intelligence,
    journal,
    memory,
    profile,
    projects,
    recommendations,
    reflect,
    research,
    threads,
)

TOOL_MODULES = (
    journal,
    goals,
    intelligence,
    recommendations,
    research,
    reflect,
    profile,
    projects,
    insights,
    brief,
    memory,
    threads,
)


def build_tool_registry() -> tuple[list[Tool], dict]:
    """Build tool definitions and handlers from all tool modules."""
    tools = []
    handlers = {}
    for mod in TOOL_MODULES:
        for name, schema, handler in mod.TOOLS:
            tools.append(Tool(name=name, description=schema["description"], inputSchema=schema))
            handlers[name] = handler
    return tools, handlers

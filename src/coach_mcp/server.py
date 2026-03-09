"""MCP server entry point — stdio transport, tool routing by prefix."""

import json

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from coach_mcp.tools import build_tool_registry

logger = structlog.get_logger()

app = Server("stewardme")

# Cache shared registry at module level (populated on first use)
_registry = None


def _load_tools():
    """Load the shared tool registry."""
    return build_tool_registry()


@app.list_tools()
async def list_tools() -> list[Tool]:
    global _registry
    if _registry is None:
        _registry = _load_tools()
    return _registry.get_mcp_definitions()


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    global _registry
    if _registry is None:
        _registry = _load_tools()
    text = _registry.execute(name, arguments)
    return [TextContent(type="text", text=text)]


async def run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    import asyncio

    asyncio.run(run())


if __name__ == "__main__":
    main()

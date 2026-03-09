"""MCP server entry point — stdio transport, tool routing by prefix."""

import json
import traceback

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from coach_mcp.tools import build_tool_registry

logger = structlog.get_logger()

app = Server("stewardme")

# Cache tool definitions at module level (populated on first list_tools call)
_tool_defs: list[Tool] | None = None
_handlers: dict | None = None


def _load_tools() -> tuple[list[Tool], dict]:
    """Load tool definitions and handlers from the shared tool registry."""
    return build_tool_registry()


@app.list_tools()
async def list_tools() -> list[Tool]:
    global _tool_defs, _handlers
    if _tool_defs is None:
        _tool_defs, _handlers = _load_tools()
    return _tool_defs


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    global _tool_defs, _handlers
    if _handlers is None:
        _tool_defs, _handlers = _load_tools()

    handler = _handlers.get(name)
    if not handler:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    try:
        result = handler(arguments)
        text = json.dumps(result, default=str)
    except Exception as e:
        logger.error("tool_error", tool=name, error=str(e))
        text = json.dumps({"error": str(e), "traceback": traceback.format_exc()})

    return [TextContent(type="text", text=text)]


async def run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    import asyncio

    asyncio.run(run())


if __name__ == "__main__":
    main()

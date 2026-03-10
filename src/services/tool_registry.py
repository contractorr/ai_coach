"""Shared tool registry for advisor and MCP surfaces."""

from __future__ import annotations

import json
from collections.abc import Callable

import structlog
from mcp.types import Tool

from llm.base import ToolDefinition

logger = structlog.get_logger()


class ToolEntry:
    """Lightweight registered tool metadata."""

    __slots__ = ("name", "toolset", "description", "schema", "handler", "check_fn", "is_async")

    def __init__(
        self,
        *,
        name: str,
        toolset: str,
        description: str,
        schema: dict,
        handler: Callable[[dict], object],
        check_fn: Callable[[], bool] | None = None,
        is_async: bool = False,
    ) -> None:
        self.name = name
        self.toolset = toolset
        self.description = description
        self.schema = schema
        self.handler = handler
        self.check_fn = check_fn
        self.is_async = is_async


class ToolRegistry:
    """Central tool registry with availability gates and uniform execution."""

    TOOL_RESULT_MAX_CHARS = 4000

    def __init__(self, components: dict | None = None):
        self.components = components or {}
        self._tools: dict[str, ToolEntry] = {}

    def register(
        self,
        *,
        name: str,
        toolset: str,
        description: str,
        schema: dict,
        handler: Callable[[dict], object],
        check_fn: Callable[[], bool] | None = None,
        is_async: bool = False,
    ) -> None:
        self._tools[name] = ToolEntry(
            name=name,
            toolset=toolset,
            description=description,
            schema=schema,
            handler=handler,
            check_fn=check_fn,
            is_async=is_async,
        )

    def _is_available(self, entry: ToolEntry) -> bool:
        if entry.check_fn is None:
            return True
        try:
            return bool(entry.check_fn())
        except Exception as exc:
            logger.debug("tool_availability_check_failed", tool=entry.name, error=str(exc))
            return False

    def is_tool_available(self, name: str) -> bool:
        entry = self._tools.get(name)
        return bool(entry and self._is_available(entry))

    def get_definitions(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name=entry.name,
                description=entry.description,
                input_schema=entry.schema,
            )
            for entry in sorted(self._tools.values(), key=lambda item: item.name)
            if self._is_available(entry)
        ]

    def get_mcp_definitions(self) -> list[Tool]:
        return [
            Tool(name=entry.name, description=entry.description, inputSchema=entry.schema)
            for entry in sorted(self._tools.values(), key=lambda item: item.name)
            if self._is_available(entry)
        ]

    def execute(self, name: str, arguments: dict) -> str:
        entry = self._tools.get(name)
        if not entry or not self._is_available(entry):
            return json.dumps({"error": f"Unknown tool: {name}"})

        try:
            result = entry.handler(arguments)
            text = json.dumps(result, default=str)
            if len(text) > self.TOOL_RESULT_MAX_CHARS:
                text = text[: self.TOOL_RESULT_MAX_CHARS] + "... (truncated)"
            return text
        except Exception as exc:
            logger.error("tool_execution_failed", tool=name, error=str(exc), exc_info=True)
            return json.dumps({"error": f"{name}: {exc}"})

    def get_toolset_for_tool(self, name: str) -> str | None:
        entry = self._tools.get(name)
        return entry.toolset if entry else None

    def get_available_toolsets(self) -> dict[str, bool]:
        toolsets = {entry.toolset for entry in self._tools.values()}
        return {
            toolset: any(
                entry.toolset == toolset and self._is_available(entry)
                for entry in self._tools.values()
            )
            for toolset in sorted(toolsets)
        }

    def __iter__(self):
        """Support legacy `(tools, handlers)` unpacking used by older tests/callers."""
        yield self.get_mcp_definitions()
        yield {
            name: entry.handler for name, entry in self._tools.items() if self._is_available(entry)
        }

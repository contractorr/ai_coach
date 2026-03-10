"""MCP tool registry helpers."""

from __future__ import annotations

from pathlib import Path

import structlog

from services.tool_registry import ToolRegistry

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

logger = structlog.get_logger()


def _toolset_name(module) -> str:
    name = module.__name__.rsplit(".", 1)[-1]
    return "intel" if name == "intelligence" else name


def _legacy_check_fn(name: str, toolset: str, components: dict):
    if toolset == "goals":
        return lambda: components.get("storage") is not None
    if toolset == "journal":
        return lambda: components.get("storage") is not None
    if toolset == "intel":
        return lambda: components.get("intel_storage") is not None
    return None


def _metadata_only_components() -> dict:
    """Fallback registry components for metadata-only use when bootstrap init is unavailable."""
    coach_home = Path.home() / ".stewardme-mcp-registry"
    return {
        "config": {"paths": {"intel_db": str(coach_home / "intel.db")}},
        "config_model": None,
        "paths": {
            "journal_dir": coach_home / "journal",
            "chroma_dir": coach_home / "chroma",
            "intel_db": coach_home / "intel.db",
        },
        "storage": object(),
        "embeddings": None,
        "search": None,
        "intel_storage": object(),
        "intel_search": None,
        "rag": None,
        "advisor": None,
    }


def build_tool_registry(components: dict | None = None) -> ToolRegistry:
    """Build the shared ToolRegistry from all MCP tool modules."""
    if components is None:
        from coach_mcp.bootstrap import get_components

        try:
            components = get_components()
        except Exception as exc:
            logger.warning("mcp_registry_metadata_fallback", error=str(exc))
            components = _metadata_only_components()

    registry = ToolRegistry(components)
    for module in TOOL_MODULES:
        register_tools = getattr(module, "register_tools", None)
        if callable(register_tools):
            register_tools(registry, components)
            continue

        toolset = _toolset_name(module)
        for name, schema, handler in getattr(module, "TOOLS", []):
            registry.register(
                name=name,
                toolset=toolset,
                description=schema["description"],
                schema=schema,
                handler=handler,
                check_fn=_legacy_check_fn(name, toolset, components),
            )
    return registry

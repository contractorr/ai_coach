# Unified Tool Registry

**Status:** Draft
**Author:** Raj
**Date:** 2026-03-09

## Problem

Two parallel tool registries exist: the MCP layer uses tuple-based `TOOLS = [(name, schema, handler)]` lists across 12 modules with `build_tool_registry()` flattening them, while the advisor uses `ToolRegistry` with method-based `_register()` calls and per-user component injection. They share no infrastructure, have inconsistent error handling (MCP returns tracebacks, advisor doesn't), and neither supports availability checks — tools that require missing API keys or unavailable services error at call time instead of being excluded from the tool list.

Reference: [hermes-agent `tools/registry.py`](https://github.com/NousResearch/hermes-agent) — singleton registry with `check_fn` availability gates, `__slots__` on entries, centralized dispatch with uniform exception handling.

## Users

Developers adding or maintaining tools. Indirectly, end users who encounter errors from tools that should have been excluded.

## Desired Behavior

1. A single `ToolRegistry` class is used by both the MCP server and the agentic advisor
2. Each tool declares an optional `check_fn` — a zero-arg callable that returns `True` if the tool's prerequisites are met (API key set, service reachable, etc.)
3. `get_definitions()` only returns tools whose `check_fn` passes (or have no check_fn)
4. `execute()` catches all handler exceptions uniformly and returns `{"error": "ToolName: message"}` — no tracebacks
5. Tools are grouped into toolsets (e.g., `journal`, `intel`, `goals`, `web_search`) for bulk enable/disable
6. MCP server and advisor both consume the same registry, with the advisor passing per-user components at construction time

## Acceptance Criteria

- [ ] Single `ToolRegistry` class in `src/services/tool_registry.py` replaces both `src/advisor/tools.py::ToolRegistry` and `src/coach_mcp/tools/__init__.py::build_tool_registry()`
- [ ] `ToolEntry` uses `__slots__` for memory efficiency
- [ ] Each tool has an optional `check_fn`; tools failing the check are excluded from `get_definitions()`
- [ ] `execute()` returns consistent `{"error": "..."}` JSON on all exceptions, no tracebacks
- [ ] MCP `call_tool` delegates to the shared registry's `execute()`
- [ ] Advisor `AgenticOrchestrator` receives a registry instance with per-user components
- [ ] All 46 MCP tools and all advisor tools register through the same `register()` API
- [ ] Tool result truncation (`TOOL_RESULT_MAX_CHARS = 4000`) is applied uniformly in `execute()`
- [ ] At least `web_search` (requires Tavily or DuckDuckGo), `intel_add_rss_feed` (requires network), and `goals_*` (requires journal storage) have `check_fn` implementations

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| `check_fn` raises an exception | Tool treated as unavailable, logged at DEBUG |
| Tool registered twice with same name | Second registration overwrites first (last-write-wins) |
| MCP client calls a tool that check_fn excluded | Returns `{"error": "Unknown tool: {name}"}` |
| Per-user components not set for a tool | Tool's check_fn returns False, excluded from definitions |

## Out of Scope

- Async tool handlers (all handlers remain synchronous; async bridging not needed today)
- Tool-level rate limiting
- Dynamic tool loading/unloading during a session
- Toolset enable/disable via user config (infrastructure only — UI controls are separate)

## Open Questions

- Should the MCP server expose toolset availability metadata via a custom resource? Low priority but would help IDE integrations.

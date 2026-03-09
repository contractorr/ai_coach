# Unified Tool Registry

## Overview

Replaces the two parallel tool registration systems (MCP tuple lists + advisor method-based registry) with a single `ToolRegistry` class that both MCP server and agentic advisor consume. Adds availability gates (`check_fn`), toolset grouping, and uniform error handling. Modeled on [hermes-agent `tools/registry.py`](https://github.com/NousResearch/hermes-agent).

## Dependencies

**Depends on:** `llm/base.py` (for `ToolDefinition`), individual tool handler modules
**Depended on by:** `coach_mcp/server.py`, `advisor/agentic.py`, `advisor/engine.py`

---

## Components

### ToolEntry

**File:** `src/services/tool_registry.py` (new)
**Status:** New

#### Behavior

Lightweight value object for a registered tool. Uses `__slots__` for memory efficiency across 50+ tools.

```python
class ToolEntry:
    __slots__ = (
        "name", "toolset", "description", "schema",
        "handler", "check_fn", "is_async",
    )

    def __init__(self, name, toolset, description, schema, handler,
                 check_fn=None, is_async=False):
        ...
```

Fields:
- `name`: unique tool name (e.g., `journal_search`)
- `toolset`: grouping key (e.g., `journal`, `intel`, `goals`, `web`)
- `description`: human-readable description
- `schema`: JSON Schema dict for input validation (OpenAI function calling format)
- `handler`: `Callable[[dict], dict]` — synchronous handler
- `check_fn`: `Optional[Callable[[], bool]]` — returns True if tool's prerequisites are met
- `is_async`: reserved for future async handlers (False for all current tools)

---

### ToolRegistry

**File:** `src/services/tool_registry.py` (new)
**Status:** New

#### Behavior

Central registry. Instantiated with optional `components` dict for per-user tools.

**Constructor:**
```python
class ToolRegistry:
    TOOL_RESULT_MAX_CHARS = 4000

    def __init__(self, components: dict | None = None):
        self._tools: dict[str, ToolEntry] = {}
        self._toolset_checks: dict[str, Callable] = {}
        self.components = components or {}
```

**Registration:**
```python
def register(self, name, toolset, description, schema, handler,
             check_fn=None, is_async=False):
    self._tools[name] = ToolEntry(...)
    if check_fn and toolset not in self._toolset_checks:
        self._toolset_checks[toolset] = check_fn
```

Tools self-register by calling `registry.register()`. For MCP tools, this replaces the `TOOLS = [(...)]` tuple pattern. For advisor tools, this replaces the `_register()` method.

**Definition retrieval:**
```python
def get_definitions(self) -> list[ToolDefinition]:
    """Return definitions for available tools only."""
    result = []
    for entry in sorted(self._tools.values(), key=lambda e: e.name):
        if entry.check_fn:
            try:
                if not entry.check_fn():
                    continue
            except Exception:
                continue
        result.append(ToolDefinition(
            name=entry.name,
            description=entry.description,
            input_schema=entry.schema,
        ))
    return result
```

For MCP, also provide:
```python
def get_mcp_definitions(self) -> list[Tool]:
    """Return mcp.types.Tool objects for available tools."""
```

**Dispatch:**
```python
def execute(self, name: str, arguments: dict) -> str:
    if name not in self._tools:
        return json.dumps({"error": f"Unknown tool: {name}"})
    entry = self._tools[name]
    try:
        result = entry.handler(arguments)
        text = json.dumps(result, default=str)
        if len(text) > self.TOOL_RESULT_MAX_CHARS:
            text = text[:self.TOOL_RESULT_MAX_CHARS] + "... (truncated)"
        return text
    except Exception as e:
        logger.error("tool_execution_failed", tool=name, error=str(e))
        return json.dumps({"error": str(e)})
```

No tracebacks in return value. Truncation applied uniformly.

**Query helpers:**
```python
def get_toolset_for_tool(self, name: str) -> str | None
def get_available_toolsets(self) -> dict[str, bool]
def is_tool_available(self, name: str) -> bool
```

#### Inputs / Outputs

| Method | Input | Output |
|--------|-------|--------|
| `register(...)` | tool metadata + handler | None (mutates internal state) |
| `get_definitions()` | — | `list[ToolDefinition]` (available tools only) |
| `get_mcp_definitions()` | — | `list[mcp.types.Tool]` |
| `execute(name, args)` | tool name + arguments dict | JSON string (result or error) |

#### Invariants

- `execute()` never raises — always returns a JSON string
- `get_definitions()` excludes tools whose `check_fn` returns False or raises
- Tool result truncation is applied in `execute()`, not in individual handlers (handlers can remove their own truncation)
- `check_fn` is called on every `get_definitions()` call (not cached) — tools become available dynamically as API keys are set

#### Error Handling

| Trigger | Behavior |
|---------|----------|
| Unknown tool name in `execute()` | Returns `{"error": "Unknown tool: {name}"}` |
| Handler raises any exception | Logged at ERROR, returns `{"error": "{message}"}` |
| `check_fn` raises | Tool treated as unavailable, logged at DEBUG |
| `check_fn` returns False | Tool excluded from definitions, no log |

---

### Migration: MCP tool modules

**Files:** `src/coach_mcp/tools/*.py` (12 modules, modified)
**Status:** Stable

#### Behavior

Each module changes from:
```python
# Before
TOOLS = [
    ("tool_name", {"description": "...", ...}, handler_fn),
]
```

To:
```python
# After
from services.tool_registry import ToolRegistry

def register_tools(registry: ToolRegistry, components: dict):
    def handler(args: dict) -> dict:
        ...
    registry.register(
        name="tool_name",
        toolset="journal",
        description="...",
        schema={...},
        handler=handler,
        check_fn=lambda: components.get("storage") is not None,
    )
```

`build_tool_registry()` in `src/coach_mcp/tools/__init__.py` becomes:
```python
def build_tool_registry(components: dict) -> ToolRegistry:
    registry = ToolRegistry(components)
    for register_fn in TOOL_MODULES:
        register_fn(registry, components)
    return registry
```

### Migration: Advisor tools

**File:** `src/advisor/tools.py` (modified)
**Status:** Stable

#### Behavior

The advisor's `ToolRegistry` class is removed. `AgenticOrchestrator` receives a `services.tool_registry.ToolRegistry` instance instead.

Tool registration moves from method-based (`_register_journal_tools()`, etc.) to the same `register()` calls. Per-user components are passed via the registry's `components` dict.

The `_register_all()` pattern becomes a `register_advisor_tools(registry, components)` function that advisor-specific tools call.

---

### MCP server integration

**File:** `src/coach_mcp/server.py` (modified)
**Status:** Stable

#### Behavior

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    registry = _get_registry()
    text = registry.execute(name, arguments)
    return [TextContent(type="text", text=text)]
```

No more `try/except` in `call_tool` itself — `execute()` handles all exceptions internally.

---

## Cross-Cutting Concerns

- **Import chain**: `services/tool_registry.py` imports nothing from tool modules or MCP/advisor code → tool modules import from `services/tool_registry` → `coach_mcp/server.py` and `advisor/agentic.py` import tool modules. This prevents circular imports.
- **Per-user isolation**: In web mode, each request creates a fresh `ToolRegistry` with that user's components. The MCP singleton registry is separate (uses the bootstrap components).
- **Backward compatibility**: The `TOOLS = [...]` lists can coexist during migration. `build_tool_registry()` can consume both old-style tuples and new-style `register_tools()` functions.

## Test Expectations

- **Registration**: register a tool, verify it appears in `get_definitions()`
- **check_fn gating**: register with `check_fn=lambda: False`, verify excluded from definitions
- **check_fn error**: register with `check_fn` that raises, verify excluded (not crashed)
- **execute**: happy path returns JSON, exception path returns `{"error": "..."}` with no traceback
- **truncation**: tool returning >4000 chars gets truncated with `... (truncated)` suffix
- **MCP integration**: mock tool, call via MCP `call_tool`, verify response format
- **Advisor integration**: mock tool, run `AgenticOrchestrator.run()`, verify tool was called

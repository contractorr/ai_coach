# Advisor

**Status:** Updated for the simplified product model

## Overview

Advisor remains the conversational engine, but Home is now the primary entry point. The full chat page exists as a continuation surface for longer threads.

## Key Modules

- `src/web/routes/advisor.py`
- `web/src/app/(dashboard)/page.tsx`
- `web/src/app/(dashboard)/advisor/page.tsx`
- `web/src/components/MessageRenderer.tsx`

## Interfaces

- `POST /api/advisor/ask/stream`
- conversation continuation via `/advisor?conv=...`
- attachment ids passed from the Home Ask flow

## Unified Prompt Assembly

`_build_advice_prompt()` always uses `build_context_for_ask()` + `_build_user_prompt()` for all advice types except `skill_gap` (which has its own dedicated path).

- No `use_extended` flag; the extended template is always used for `general` prompts.
- `build_context_for_ask()` internally calls `get_enhanced_context()`, so no separate call is needed.
- `rag_config` flags (`inject_memory`, `inject_documents`, etc.) control what `build_context_for_ask` retrieves, not which prompt branch runs.
- `_build_user_prompt()` collapses empty context slots via blank-line removal, so missing data is harmless.

## Agentic Tool Execution

`AgenticOrchestrator` runs tool calls with:
- **Per-tool timeout** (`tool_timeout`, default 60s): each `registry.execute()` runs in a thread with `concurrent.futures.ThreadPoolExecutor`. Timeout produces a structured JSON error `{"error": "...timed out..."}`.
- **Structured error detection** (`_is_tool_error()`): JSON-parses tool results and checks for an `"error"` key. Replaces previous string-match heuristic that had false positives on content containing the word "error".

## Simplified Product Notes

- Home defaults to capture and upgrades into advisor only when input clearly looks like a question or the user toggles Ask.
- The advisor page is no longer part of the primary navigation model.
- Home keeps the current thread inline for short exchanges and only links to `/advisor` when the user needs a longer continuation surface.

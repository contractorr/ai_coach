---
id: llm
category: tracked_module
status: stable
implements:
- settings-account
code_paths:
- src/llm
- src/web/routes/settings.py
- tests/llm
last_reviewed: '2026-03-30'
---

# LLM

## Overview

The `src/llm/` module is a multi-provider LLM abstraction layer that presents a uniform `LLMProvider` interface across Anthropic Claude, OpenAI GPT, and Google Gemini. A factory handles provider instantiation with auto-detection from environment variables or API key prefixes, and exposes a separate cheap-tier factory for background/critic calls. All provider-specific message formats, tool-calling conventions, error types, and system-prompt placement are normalized internally so callers interact with a single consistent interface.

## Dependencies

**Depends on:** `anthropic` (optional, lazy import), `openai` (optional, lazy import), `google-genai` (optional, lazy import), `uuid` (GeminiProvider tool call IDs)

**Depended on by:** every module that makes LLM calls — `advisor` (AdvisorEngine, AgenticOrchestrator), `memory` (FactExtractor, ConflictResolver), `research` (ResearchSynthesizer), `intelligence` (TrendingRadar.compute_llm, GoalIntelLLMEvaluator, HeartbeatEvaluator, CapabilityHorizonModel), `profile` (ProfileInterviewer, web onboarding), `journal` (generate_title, TrendDetector.summarize_trends), `coach_mcp` (research_run transitively)

## Components

### Error Hierarchy
**File:** `src/llm/base.py`

#### Behavior
Three exception classes form a simple hierarchy. All LLM errors in the system inherit from `LLMError`, so callers can catch either the base class or specific subtypes.

```
LLMError(Exception)            — base; all LLM errors inherit from this
  LLMRateLimitError(LLMError)  — rate limit hit
  LLMAuthError(LLMError)       — authentication failure
```

#### Inputs / Outputs
Standard Python exceptions; constructed with a string message.

#### Invariants

- All provider-raised exceptions must be instances of `LLMError` or its subclasses — no raw SDK exceptions should escape a provider's `generate()` / `generate_with_tools()`.
- `LLMRateLimitError` and `LLMAuthError` are both catchable as `LLMError` — callers can narrow or widen the catch.

#### Error Handling
These are the errors raised by providers, not raised themselves.

#### Configuration
None.

---

### Data Classes
**File:** `src/llm/base.py`

#### Behavior
Four dataclasses carry structured data across the provider boundary.

**`ToolDefinition`** — describes a tool the LLM may call:
```python
@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict  # JSON Schema
```

**`ToolCall`** — a single tool invocation requested by the LLM:
```python
@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict
```

**`ToolResult`** — result of executing a tool, sent back to the LLM:
```python
@dataclass
class ToolResult:
    tool_call_id: str
    content: str
    is_error: bool = False
```

**`GenerateResponse`** — return value of `generate_with_tools`:
```python
@dataclass
class GenerateResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"  # "stop" | "tool_calls" | "max_tokens"
```

#### Inputs / Outputs
Pure data holders; no methods beyond dataclass defaults.

#### Invariants

- `GenerateResponse.content` may be `None` when `finish_reason == "tool_calls"` — callers must null-check.
- `GenerateResponse.tool_calls` is always a list (never `None`) — may be empty.
- `ToolCall.arguments` is always a `dict` — providers must deserialize JSON strings before constructing.
- `ToolResult.is_error` defaults to `False` — only set explicitly for error results.

#### Error Handling
None.

#### Configuration
`GenerateResponse.finish_reason` defaults to `"stop"`. The three valid values are `"stop"`, `"tool_calls"`, and `"max_tokens"`.

---

### LLMProvider Abstract Interface
**File:** `src/llm/base.py`

#### Behavior
Abstract base class all provider implementations must satisfy.

```python
class LLMProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    def generate(
        self,
        messages: list[dict],       # [{"role": ..., "content": ...}, ...]
        system: str | None = None,
        max_tokens: int = 2000,
        use_thinking: bool = False,
    ) -> str: ...

    @abstractmethod
    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[ToolDefinition],
        system: str | None = None,
        max_tokens: int = 2000,
        tool_choice: str = "auto",  # "auto" or "required"
    ) -> GenerateResponse: ...
```

`count_tokens` is not part of the abstract interface and is not defined here.

#### Inputs / Outputs
- `generate` returns `str` (the generated text).
- `generate_with_tools` returns `GenerateResponse`.
- `use_thinking` is a hint to the provider; providers that do not support extended thinking silently ignore it.
- `tool_choice` values: `"auto"` (model decides whether to call a tool) or `"required"` (model must call a tool).

#### Invariants

- `generate()` always returns `str` — never `None` or raises on empty model response (provider must handle).
- `use_thinking` is a hint only — providers that don't support it must silently ignore (not raise).
- `tool_choice="required"` must guarantee at least one tool call in the response (provider-enforced).
- `count_tokens` is NOT part of the abstract interface — callers must check for its existence.

#### Error Handling
Implementations are expected to catch provider SDK exceptions and re-raise as `LLMError`, `LLMAuthError`, or `LLMRateLimitError`.

#### Configuration
`max_tokens` default: `2000`. `tool_choice` default: `"auto"`.

---

### Factory
**File:** `src/llm/factory.py`

#### Behavior

Constants:

```python
_PROVIDER_ENV_KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}

_AUTO_DETECT_ORDER = ["claude", "openai", "gemini"]  # priority order for env scan

_CHEAP_MODELS = {
    "claude": "claude-haiku-4-5",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}
```

**`create_llm_provider`:**

```python
def create_llm_provider(
    provider: str | None = None,    # "claude","openai","gemini","auto",None → auto
    api_key: str | None = None,     # overrides env var if given
    model: str | None = None,       # None = provider default
    client=None,                    # pre-built SDK client (for DI/testing)
    extended_thinking: bool = False, # Claude only; ignored for other providers
) -> LLMProvider
```

Resolution steps:
1. `provider=None` or `"auto"` → calls `_auto_detect_provider(api_key)`.
2. If no `api_key` and no `client`, reads `os.getenv(_PROVIDER_ENV_KEYS[resolved])`.
3. Imports the provider class lazily and instantiates it.
4. Unknown provider string → raises `LLMError("Unknown provider: {resolved}. Use: claude, openai, gemini")`.

**Note:** `create_llm_provider` does NOT handle custom OpenAI-compatible providers. Custom providers must be instantiated directly via `OpenAICompatibleProvider(base_url=..., api_key=..., model=..., display_name=...)` or via council/settings integration which constructs them separately.

**`create_cheap_provider`:**

```python
def create_cheap_provider(
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,   # if None, uses _CHEAP_MODELS[resolved]
    client=None,
) -> LLMProvider
```

Delegates entirely to `create_llm_provider` after substituting the cheap model. Does not accept `extended_thinking`.

**Auto-detection logic (`_auto_detect_provider`):**

1. If `api_key` is supplied, attempt prefix inference (`_detect_provider_from_key`):
   - Starts with `"sk-ant-"` → `"claude"`
   - Starts with `"sk-"` → `"openai"`
   - Starts with `"AI"` → `"gemini"`
   - No prefix match → fall through to env scan
2. Iterate `_AUTO_DETECT_ORDER`; return first name whose env var is non-empty.
3. If nothing found → raises `LLMError("No LLM API key found. Set one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY")`.

#### Inputs / Outputs
Both factory functions return an `LLMProvider` instance.

#### Invariants

- Auto-detection priority is fixed: `claude → openai → gemini`. The first env var found wins.
- API key prefix inference only runs when a key is explicitly passed; env-var keys are not inspected for prefixes.
- `create_cheap_provider()` always uses `_CHEAP_MODELS[resolved]` when `model=None`; explicit `model` overrides it.
- Both factory functions raise `LLMError` (not `ValueError` or `KeyError`) for invalid/missing providers.

#### Error Handling
- Unknown provider string: `LLMError`.
- No API key and no client found: `LLMError`.
- All provider-level import errors are deferred to the provider constructor.

#### Configuration
Cheap model overrides per provider (cannot be changed without modifying `_CHEAP_MODELS`): `claude-haiku-4-5`, `gpt-4o-mini`, `gemini-2.0-flash`.

---

### ClaudeProvider
**File:** `src/llm/providers/claude.py`

#### Behavior

```python
class ClaudeProvider(LLMProvider):
    provider_name = "claude"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,            # default: "claude-sonnet-4-6"
        client=None,
        extended_thinking: bool = False,
    )
```

Default model: `"claude-sonnet-4-6"`.

**`generate` — extended thinking:**

Activated only when both `use_thinking=True` AND `self.extended_thinking=True`:
- `budget_tokens = 8000` (hardcoded constant)
- If `max_tokens <= 8000`, it is bumped to `budget_tokens + 1024 = 9024` (API requires `max_tokens` strictly greater than `budget_tokens`)
- Adds `thinking={"type": "enabled", "budget_tokens": 8000}` to the API kwargs

**`generate` — response extraction:**

Iterates `response.content` blocks and returns the first block where `block.type == "text"`. Falls back to `response.content[0].text` if no typed text block is found (handles the case where thinking blocks are present).

**`generate_with_tools` — tool_choice mapping:**

| Input value | Anthropic API value |
|---|---|
| `"required"` | `{"type": "any"}` |
| anything else | `{"type": "auto"}` |

**`generate_with_tools` — finish_reason mapping:**

| `response.stop_reason` | `GenerateResponse.finish_reason` |
|---|---|
| `"tool_use"` | `"tool_calls"` |
| `"max_tokens"` | `"max_tokens"` |
| anything else | `"stop"` |

`content` field: `None` if no text blocks present; multiple text blocks joined with `"\n"`.

**`_convert_messages` (internal) — message format conversion:**

- `{"role": "assistant", "tool_calls": [...]}` → assistant message with content block list: optional `{"type": "text"}` block followed by `{"type": "tool_use", "id": ..., "name": ..., "input": ...}` blocks.
- `{"role": "tool", "tool_call_id": ..., "content": ...}` → consecutive tool-role messages are collapsed into a single `{"role": "user"}` message containing a list of `{"type": "tool_result", "tool_use_id": ..., "content": ...}` blocks. `is_error: True` is included only when the source message has a truthy `is_error` key.
- All other messages pass through unchanged.

#### Inputs / Outputs
- `generate` → `str`
- `generate_with_tools` → `GenerateResponse`

#### Invariants

- Extended thinking requires BOTH `self.extended_thinking=True` (constructor) AND `use_thinking=True` (call-time) — either alone is insufficient.
- When extended thinking is active and `max_tokens <= 8000`, it is silently bumped to `9024` — callers cannot prevent this.
- Consecutive tool-role messages are always collapsed into a single user message — Anthropic API requirement.
- `content` in `GenerateResponse` is `None` when no text blocks exist (e.g. pure tool-call response).
- `tool_choice="required"` maps to `{"type": "any"}` (not `"required"`) — Anthropic API difference.

#### Caveats

- `max_tokens` mutation on extended thinking is a side effect callers may not expect; log if debugging token usage.

#### Error Handling
Uses `anthropic` SDK exception types (imported lazily via `_get_exceptions()`):

| SDK exception | Raised as |
|---|---|
| `anthropic.AuthenticationError` | `LLMAuthError("Claude auth failed: ...")` |
| `anthropic.RateLimitError` | `LLMRateLimitError("Claude rate limit: ...")` |
| `anthropic.APIError` | `LLMError("Claude API error: ...")` |
| Any other exception | `LLMError("Claude error: ...")` |

Missing package (ImportError at init): `LLMError("anthropic package not installed. Run: pip install anthropic")`.

#### Configuration
- Default model: `"claude-sonnet-4-6"`
- Extended thinking budget: `8000` tokens (hardcoded)
- Extended thinking `max_tokens` floor: `budget + 1024 = 9024`
- `extended_thinking` flag must be set at construction time; `use_thinking` at call time

---

### OpenAIProvider
**File:** `src/llm/providers/openai.py`

#### Behavior

```python
class OpenAIProvider(LLMProvider):
    provider_name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,   # default: "gpt-4o"
        client=None,
    )
```

Default model: `"gpt-4o"`.

**`generate`:**

System prompt is prepended as `{"role": "system", "content": system}` before the messages list. `use_thinking` is accepted but silently ignored. Returns `response.choices[0].message.content`.

**`generate_with_tools` — tool format:**

`ToolDefinition` is wrapped in OpenAI's function format:
```python
{
    "type": "function",
    "function": {
        "name": t.name,
        "description": t.description,
        "parameters": t.input_schema,   # full schema, not filtered
    }
}
```

**`generate_with_tools` — tool_choice passthrough:**

Accepts `"auto"`, `"required"`, `"none"` verbatim. Any other value is coerced to `"auto"`.

**`generate_with_tools` — message conversion:**

- `{"role": "assistant", "tool_calls": [...]}` → assistant message with `tool_calls` list; `arguments` dict is JSON-serialized via `json.dumps`.
- `{"role": "tool", ...}` → passed through unchanged (OpenAI format matches the generic format).
- Others pass through unchanged.

**`generate_with_tools` — finish_reason mapping:**

| `choice.finish_reason` | `GenerateResponse.finish_reason` |
|---|---|
| `"tool_calls"` | `"tool_calls"` |
| `"length"` | `"max_tokens"` |
| anything else | `"stop"` |

#### Inputs / Outputs
- `generate` → `str`
- `generate_with_tools` → `GenerateResponse`

#### Invariants

- System prompt is always the first message — prepended as `{"role": "system"}`, never appended.
- `use_thinking` is silently ignored — no extended thinking support.
- `tool_choice` values outside `{"auto", "required", "none"}` are coerced to `"auto"` silently.
- `finish_reason="length"` (OpenAI) is normalized to `"max_tokens"` — callers see the unified value.
- Tool call `arguments` are JSON-serialized from dict → string for the OpenAI API.

#### Caveats

- If the `openai` package is missing at runtime, all SDK exceptions fall through to the generic `LLMError` branch (since `_openai_exceptions = ()`) — error classification is lost.

#### Error Handling
Exception types are lazily cached in module-level `_openai_exceptions` (populated on first call, set to `()` if `openai` package is absent):

| SDK exception | Raised as |
|---|---|
| `openai.AuthenticationError` | `LLMAuthError("OpenAI auth failed: ...")` |
| `openai.RateLimitError` | `LLMRateLimitError("OpenAI rate limit: ...")` |
| `openai.APIError` | `LLMError("OpenAI API error: ...")` |
| Any other exception | `LLMError("OpenAI error: ...")` |

If the `openai` package is missing at runtime, all exceptions fall through to the generic `LLMError` branch (since `_openai_exceptions` is `()`).

Missing package (ImportError at init): `LLMError("openai package not installed. Run: pip install 'stewardme[openai]'")`.

#### Configuration
Default model: `"gpt-4o"`. No `extended_thinking` support.

---

### GeminiProvider
**File:** `src/llm/providers/gemini.py`

#### Behavior

```python
class GeminiProvider(LLMProvider):
    provider_name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,   # default: "gemini-2.5-flash"
        client=None,
    )
```

Default model: `"gemini-2.5-flash"`. API key stored as `self._api_key` but not used after client construction.

**`generate` — system prompt handling:**

System prompt is prepended as the plain string `f"System: {system}\n"` into a flat `parts` list. All message `content` values are appended to the same list and joined with `"\n"` as a single string prompt. This is a flat concatenation, not a multi-turn structured call. `use_thinking` is accepted but silently ignored.

Config passed: `types.GenerateContentConfig(max_output_tokens=max_tokens)`. Returns `response.text`.

**`generate_with_tools` — system prompt handling:**

Unlike `generate`, uses the proper SDK parameter: `system_instruction=system` inside `GenerateContentConfig`.

**`generate_with_tools` — schema filtering:**

Only the keys `"type"`, `"properties"`, and `"required"` are passed from `input_schema` to `FunctionDeclaration.parameters`. If the filtered schema has no `"properties"` key, `parameters` is set to `None`.

**`generate_with_tools` — tool_choice:**

The `tool_choice` parameter is accepted but silently ignored (no Gemini SDK equivalent is mapped).

**`generate_with_tools` — tool call IDs:**

Gemini does not return tool call IDs. A synthetic ID is generated: `f"call_{uuid.uuid4().hex[:8]}"` (8-character hex suffix).

**`generate_with_tools` — finish_reason:**

`"tool_calls"` if any tool calls were found in the response, else `"stop"`. `"max_tokens"` is never returned.

**`_convert_messages` (internal):**

| Generic role | Gemini SDK type | Notes |
|---|---|---|
| `"user"` | `Content(role="user", parts=[Part.from_text(...)])` | |
| `"assistant"` | `Content(role="model", parts=[...])` | Text + function_call parts; message skipped if no parts |
| `"tool"` | `Content(role="user", parts=[Part.from_function_response(...)])` | `name` defaults to `"tool"` if absent; response wrapped as `{"result": msg["content"]}` |

#### Inputs / Outputs
- `generate` → `str`
- `generate_with_tools` → `GenerateResponse`

#### Invariants

- `generate()` uses flat string concatenation — NOT a multi-turn conversation; system prompt becomes part of the flat string.
- `generate_with_tools()` uses proper `system_instruction` — the two methods handle system prompts differently.
- `tool_choice` is silently ignored — Gemini SDK has no equivalent mapping.
- `finish_reason="max_tokens"` is never returned — Gemini does not expose this.
- Synthetic tool call IDs (`call_XXXXXXXX`) are not globally unique across calls — only unique within a single response.
- Tool schema is filtered to `{type, properties, required}` only — additional JSON Schema fields are dropped.

#### Caveats

- Error detection via string heuristics (`str(e).lower()`) is fragile — error classification may be wrong if Gemini SDK changes its error message format.
- `generate()` flat concatenation means multi-turn context in `messages` is not truly multi-turn for Gemini.

#### Error Handling
Uses string heuristic detection on `str(e).lower()` (no SDK exception type checking):

| Condition | Raised as |
|---|---|
| `"api key"` OR `"authentication"` OR `"permission"` in error string | `LLMAuthError("Gemini auth failed: ...")` |
| (`"resource"` AND `"exhausted"`) OR `"rate"` in error string | `LLMRateLimitError("Gemini rate limit: ...")` |
| All other exceptions | `LLMError("Gemini API error: ...")` |

Missing package (ImportError at init): `LLMError("google-genai package not installed. Run: pip install 'stewardme[gemini]'")`.

#### Configuration
Default model: `"gemini-2.5-flash"`. Cheap model: `"gemini-2.0-flash"`. No `extended_thinking` support.

---

### OpenAICompatibleProvider
**File:** `src/llm/providers/openai_compatible.py`

#### Behavior

```python
class OpenAICompatibleProvider(LLMProvider):
    provider_name = "openai_compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        display_name: str | None = None,
    )
```

A generic provider for any service implementing the OpenAI `/v1/chat/completions` API specification. Uses the `openai` SDK's client with custom `base_url` override.

**`__init__`:**

- Constructs an `OpenAI` client with `base_url` and `api_key` overrides
- Stores `model` and `display_name` for identification
- No default model — `model` is required
- `display_name` used for council UI labels; defaults to `provider_name` if `None`

**`generate` and `generate_with_tools`:**

Identical to `OpenAIProvider` implementation — delegates to `self.client.chat.completions.create()` with standard OpenAI request format. System prompt prepended as `{"role": "system"}` message.

**Tool format:**

Same as `OpenAIProvider` — wraps `ToolDefinition` in OpenAI function format.

**Message conversion:**

Same as `OpenAIProvider` — no custom message format conversion needed since the provider is OpenAI-compatible.

**Finish reason mapping:**

| `choice.finish_reason` | `GenerateResponse.finish_reason` |
|---|---|
| `"tool_calls"` | `"tool_calls"` |
| `"length"` | `"max_tokens"` |
| anything else | `"stop"` |

#### Inputs / Outputs
- `generate` → `str`
- `generate_with_tools` → `GenerateResponse`

#### Invariants

- `base_url` must be provided and valid
- `api_key` must be provided
- `model` must be provided (no default)
- Behavior identical to `OpenAIProvider` except for endpoint location
- `use_thinking` is silently ignored (same as OpenAI)

#### Error Handling

Uses the same exception handling as `OpenAIProvider`:

| SDK exception | Raised as |
|---|---|
| `openai.AuthenticationError` | `LLMAuthError(f"{display_name} auth failed: ...")` |
| `openai.RateLimitError` | `LLMRateLimitError(f"{display_name} rate limit: ...")` |
| `openai.APIError` | `LLMError(f"{display_name} API error: ...")` |
| `httpx.TimeoutException` | `LLMError(f"{display_name} timeout: ...")` |
| `httpx.ConnectError` | `LLMError(f"{display_name} connection failed: ...")` |
| Any other exception | `LLMError(f"{display_name} error: ...")` |

Missing package (ImportError at init): `LLMError("openai package required for OpenAI-compatible providers")`.

#### Configuration

No default model. Model must be explicitly provided by the user.

---

## Cross-Provider Comparison

| Concern | ClaudeProvider | OpenAIProvider | GeminiProvider |
|---|---|---|---|
| Default model | `claude-sonnet-4-6` | `gpt-4o` | `gemini-2.5-flash` |
| Cheap model (factory) | `claude-haiku-4-5` | `gpt-4o-mini` | `gemini-2.0-flash` |
| Extended thinking | Supported; budget=8000 tokens; bumps `max_tokens` to 9024 if needed | Silently ignored | Silently ignored |
| System prompt in `generate` | Native `system` kwarg | Prepended as `{"role":"system"}` message | Concatenated as `"System: ...\n"` string prefix |
| System prompt in `generate_with_tools` | Native `system` kwarg | Prepended as `{"role":"system"}` message | `system_instruction` param in `GenerateContentConfig` |
| `tool_choice="required"` | Maps to `{"type":"any"}` | Passed as `"required"` string verbatim | Silently ignored |
| Tool call IDs | Returned by API | Returned by API | Synthetic `uuid4` 8-char hex prefix |
| `finish_reason="max_tokens"` source | `stop_reason=="max_tokens"` | `finish_reason=="length"` | Never returned |
| `finish_reason` never returned | — | — | `"max_tokens"` |
| Error detection method | SDK exception isinstance checks | SDK exception isinstance checks (lazy-cached) | String heuristics on `str(e).lower()` |
| Tool schema fields sent | All fields from `input_schema` | All fields from `input_schema` | Only `type`, `properties`, `required`; `None` if no `properties` |
| Multi-turn message format | Consecutive tool msgs collapsed into one user msg | Tool messages pass through natively | Tool results mapped to `role="user"` function_response parts |
| `generate` call shape | Structured multi-turn messages | Structured multi-turn messages | Flat string concatenation |
| `tool` role name fallback | n/a | n/a | Defaults to `"tool"` if `name` key absent |
---

## Test Expectations

- Factory auto-detection: verify priority order (claude → openai → gemini); verify API key prefix inference for each prefix; verify `LLMError` when no key found.
- Factory unknown provider string: verify `LLMError` raised.
- `ClaudeProvider.generate()`: mock anthropic client; verify extended thinking bumps `max_tokens` to 9024; verify text block extraction fallback when thinking blocks present.
- `ClaudeProvider._convert_messages()`: verify consecutive tool messages collapsed into single user message; verify `is_error` only set when truthy.
- `OpenAIProvider.generate_with_tools()`: verify `"length"` → `"max_tokens"` finish reason mapping; verify `arguments` dict JSON-serialized.
- `GeminiProvider.generate()`: verify flat string concatenation for system prompt; verify synthetic tool call ID format.
- `GeminiProvider`: verify string-heuristic error detection for auth/rate-limit strings.
- All providers: mock SDK clients; verify each SDK exception type maps to correct `LLMError` subclass.
- `create_cheap_provider()`: verify correct cheap model selected per provider.

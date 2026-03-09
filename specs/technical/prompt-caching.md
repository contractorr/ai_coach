# Prompt Caching

## Overview

Enables Anthropic prompt caching for Claude models in the agentic advisor loop. The system prompt and early conversation turns are marked with `cache_control` so repeated input tokens are served from cache at zero cost (writes at 1.25x, reads at 0x). Modeled on [hermes-agent `run_agent.py`](https://github.com/NousResearch/hermes-agent) prompt caching logic.

## Dependencies

**Depends on:** `llm/providers/anthropic.py` (Claude provider implementation)
**Depended on by:** `advisor/agentic.py` (via provider), `observability.py` (cache hit tracking)

---

## Components

### Claude provider prompt caching

**File:** `src/llm/providers/anthropic.py` (modified)
**Status:** Stable

#### Behavior

When `generate_with_tools()` is called, inject `cache_control` on the system message and the first few conversation messages.

**Strategy: `system_and_first_3`**

Anthropic allows up to 4 cache breakpoints per request. We place them on:
1. The system prompt (largest, most stable content — profile XML, memory, recurring thoughts)
2. The first user message (establishes the query context)
3. The first assistant response (if present — establishes conversation pattern)
4. The second user message (if present)

Implementation in `generate_with_tools()`:

```python
def generate_with_tools(self, messages, tools, system, **kwargs):
    # Build system param with cache_control
    system_blocks = [
        {
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    # Mark first 3 eligible messages with cache_control
    cache_eligible_count = 0
    api_messages = []
    for msg in messages:
        api_msg = self._format_message(msg)
        if cache_eligible_count < 3 and msg["role"] in ("user", "assistant"):
            # Add cache_control to the last content block
            if isinstance(api_msg["content"], list) and api_msg["content"]:
                api_msg["content"][-1]["cache_control"] = {"type": "ephemeral"}
            elif isinstance(api_msg["content"], str):
                api_msg["content"] = [
                    {
                        "type": "text",
                        "text": api_msg["content"],
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            cache_eligible_count += 1
        api_messages.append(api_msg)

    response = self.client.messages.create(
        model=self.model,
        system=system_blocks,
        messages=api_messages,
        tools=tools_param,
        max_tokens=kwargs.get("max_tokens", 4096),
    )
    ...
```

**Cache-aware usage tracking:**

The Anthropic response includes:
- `usage.cache_creation_input_tokens` — tokens written to cache (billed at 1.25x)
- `usage.cache_read_input_tokens` — tokens read from cache (billed at 0x)
- `usage.input_tokens` — tokens not from cache (billed at 1x)

Log these at DEBUG level:
```python
logger.debug(
    "anthropic_usage",
    input_tokens=response.usage.input_tokens,
    cache_write=getattr(response.usage, 'cache_creation_input_tokens', 0),
    cache_read=getattr(response.usage, 'cache_read_input_tokens', 0),
    output_tokens=response.usage.output_tokens,
)
```

Feed observability with actual billed tokens:
```python
from observability import metrics
effective_input = (
    response.usage.input_tokens
    + int(getattr(response.usage, 'cache_creation_input_tokens', 0) * 1.25)
    # cache_read tokens are free
)
metrics.token_usage(self.model, effective_input, response.usage.output_tokens)
```

#### Inputs / Outputs

No public API change. `generate_with_tools()` signature is unchanged. The `cache_control` injection is internal to the Anthropic provider.

#### Invariants

- Cache control is only added for Anthropic Claude models — never for OpenAI or Gemini providers
- If the Anthropic SDK doesn't support `cache_control` (old version), the field is silently ignored by the API
- System prompt content determines cache key — changing the profile or memory invalidates the cache naturally
- Maximum 4 cache breakpoints per request (Anthropic limit)

#### Error Handling

| Trigger | Behavior |
|---------|----------|
| Anthropic API rejects cache_control | Unlikely (field is optional). If it errors, the provider's existing retry logic handles it |
| `cache_creation_input_tokens` missing from response | Default to 0, no crash |
| Non-Anthropic provider | No cache_control injected, no change in behavior |

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| Cache breakpoint strategy | `system_and_first_3` | Hardcoded |
| Cache TTL | 5 minutes | Anthropic server-side default, not configurable by client |

#### Caveats

- **Extended thinking**: When `extended_thinking` is enabled, the thinking content is not cacheable (it varies per turn). The system prompt and early turns still cache normally.
- **First turn of a session**: Always a cache write (1.25x cost). Subsequent turns within 5 minutes are cache reads (0x). Sessions with >5 min gaps between turns see repeated cache writes.
- **Cost accounting**: `metrics.token_usage()` should reflect *billed* tokens, not raw tokens. Cache reads should be excluded from cost calculation.

---

## Cross-Cutting Concerns

- **Provider interface**: No change to `LLMProvider` base class. Caching is an implementation detail of the Anthropic provider.
- **Observability integration**: The `token_usage()` call must distinguish billed vs raw tokens for accurate cost estimation. The `Metrics` pricing table should account for cache write premium (1.25x) but this is handled at the provider level before calling `metrics.token_usage()`.
- **Testing**: Mock the Anthropic client's `messages.create()` to return a response with `cache_creation_input_tokens` and `cache_read_input_tokens` fields. Verify the cost calculation.

## Test Expectations

- **Cache control injection**: mock Anthropic client, verify `system` param has `cache_control` on the text block
- **First 3 messages marked**: 5-message conversation → verify messages 0, 1, 2 (user/assistant) have `cache_control`, messages 3+ don't
- **Usage logging**: verify DEBUG log includes `cache_write` and `cache_read` fields
- **Cost calculation**: 1000 cache_creation tokens → billed as 1250; 1000 cache_read tokens → billed as 0
- **Non-Claude provider**: verify no `cache_control` in OpenAI/Gemini calls

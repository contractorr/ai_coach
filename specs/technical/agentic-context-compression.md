# Agentic Context Compression

## Overview

Adds token-aware context management to `AgenticOrchestrator`. When input tokens exceed a threshold, older turns are evicted in boundary-aligned pairs and optionally summarized via `cheap_llm`. Modeled on [hermes-agent `agent/context_compressor.py`](https://github.com/NousResearch/hermes-agent).

## Dependencies

**Depends on:** `advisor/agentic.py`, `llm/base.py` (LLMProvider, usage tracking)
**Depended on by:** `advisor/engine.py` (passes cheap_llm to orchestrator)

---

## Components

### ContextCompressor

**File:** `src/advisor/context_compressor.py` (new)
**Status:** New

#### Behavior

Stateless utility class. Takes a message list and returns a compressed message list.

**Constructor:**
```python
class ContextCompressor:
    def __init__(
        self,
        cheap_llm: LLMProvider | None = None,
        token_threshold: int = 100_000,
        protect_first_n: int = 2,
        protect_last_n: int = 3,
        summary_target_chars: int = 2000,
    ):
```

**Core method:**
```python
def compress_if_needed(
    self,
    messages: list[dict],
    current_input_tokens: int,
) -> list[dict]:
    """Return (possibly compressed) message list.

    If current_input_tokens < token_threshold, returns messages unchanged.
    Otherwise, evicts middle turns and inserts a summary.
    """
```

**Algorithm:**

1. Check `current_input_tokens >= token_threshold`. If under, return unchanged.
2. Identify protected ranges: `messages[:protect_first_n]` and `messages[-protect_last_n:]`
3. The eviction window is `messages[protect_first_n:-protect_last_n]`
4. Within the eviction window, identify **tool pairs**: each `assistant` message with `tool_calls` is grouped with the subsequent `tool` role messages that match its call IDs
5. Evict the oldest 50% of the eviction window (by message index), rounding up to the nearest tool-pair boundary
6. Generate a summary of evicted messages via `cheap_llm` (if available)
7. Return: `protected_first + [summary_message] + remaining_middle + protected_last`

**Boundary alignment:**

```python
def _align_eviction_boundary(self, messages: list[dict], raw_boundary: int) -> int:
    """Adjust boundary forward to avoid splitting a tool_call from its results.

    Scans forward from raw_boundary until we find a message that is NOT
    a tool-result belonging to a tool_call before the boundary.
    """
```

A tool_call message at index `i` owns all subsequent `tool` messages whose `tool_call_id` matches one of its call IDs. If the boundary falls between the tool_call and its last result, move the boundary forward past the last result.

**Orphan sanitization:**

After eviction, scan the remaining messages for:
- `tool` messages with no preceding `assistant` message containing a matching `tool_call_id` → insert a stub assistant message: `{"role": "assistant", "tool_calls": [{"id": orphan_id, "name": "unknown", "arguments": "{}"}]}`
- `assistant` messages with `tool_calls` but no subsequent `tool` message with matching ID → insert a stub tool result: `{"role": "tool", "tool_call_id": missing_id, "name": "unknown", "content": "{\"note\": \"result omitted during context compression\"}"}`

**Summary generation:**

```python
def _generate_summary(self, evicted: list[dict]) -> str | None:
    """Use cheap_llm to summarize evicted turns. Returns None on failure."""
    if not self.cheap_llm:
        return None
    # Truncate each message content to 1000 chars for the summary prompt
    # Prompt: "Summarize this conversation segment concisely, preserving
    #          key facts, tool results, and decisions."
    try:
        response = self.cheap_llm.generate(
            messages=[{"role": "user", "content": prompt}],
            system="You are a conversation summarizer. Be concise.",
            max_tokens=800,
        )
        return response.content[:self.summary_target_chars]
    except Exception:
        logger.warning("context_compression_summary_failed", exc_info=True)
        return None
```

**Fallback when summary fails:**
```python
summary_msg = {
    "role": "user",
    "content": f"[Earlier context omitted — {len(evicted)} turns summarized. "
               f"Key tools called: {', '.join(tool_names)}]",
}
```

#### Inputs / Outputs

| Method | Input | Output |
|--------|-------|--------|
| `compress_if_needed(messages, tokens)` | message list + current token count | compressed message list |
| `_align_eviction_boundary(msgs, idx)` | message list + raw boundary index | aligned boundary index |
| `_generate_summary(evicted)` | evicted message list | summary string or None |

#### Invariants

- Output message list always has valid tool_call/tool_result pairing
- Protected first N and last M messages are never evicted
- If input tokens are under threshold, output === input (no mutation)
- Summary generation failure never crashes the orchestrator

#### Error Handling

| Trigger | Behavior |
|---------|----------|
| cheap_llm is None | No summary generated, uses fallback marker |
| cheap_llm.generate() raises | Caught, logged at WARNING, uses fallback marker |
| Message list shorter than protect_first + protect_last | No compression possible, returns unchanged |

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| `token_threshold` | 100,000 | Constructor param |
| `protect_first_n` | 2 | Constructor param |
| `protect_last_n` | 3 | Constructor param |
| `summary_target_chars` | 2000 | Constructor param |

---

### AgenticOrchestrator changes

**File:** `src/advisor/agentic.py` (modified)
**Status:** Stable

#### Behavior

New constructor param:
```python
def __init__(
    self,
    llm: LLMProvider,
    registry: ToolRegistry,
    system_prompt: str,
    max_iterations: int = 10,
    cheap_llm: LLMProvider | None = None,  # NEW
    token_threshold: int = 100_000,         # NEW
):
    ...
    self.compressor = ContextCompressor(
        cheap_llm=cheap_llm,
        token_threshold=token_threshold,
    )
    self._total_input_tokens = 0
```

In the main loop, after each LLM response:
```python
response = self.llm.generate_with_tools(...)

# Track token usage
if hasattr(response, 'usage') and response.usage:
    self._total_input_tokens = response.usage.get('input_tokens', 0)
    # Also feed observability
    from observability import metrics
    metrics.token_usage(
        model=self.llm.model_name,
        input_tokens=response.usage.get('input_tokens', 0),
        output_tokens=response.usage.get('output_tokens', 0),
    )

# Compress before next iteration if needed
messages = self.compressor.compress_if_needed(messages, self._total_input_tokens)
```

### AdvisorEngine wiring

**File:** `src/advisor/engine.py` (modified)
**Status:** Stable

#### Behavior

Pass `self.cheap_llm` to the orchestrator when constructing it for agentic mode:

```python
orchestrator = AgenticOrchestrator(
    llm=self.llm,
    registry=registry,
    system_prompt=system_prompt,
    cheap_llm=self.cheap_llm,  # existing dual-LLM instance
)
```

---

## Cross-Cutting Concerns

- **LLM provider contract**: `generate_with_tools()` must return a response object with a `usage` dict containing `input_tokens` and `output_tokens`. Verify all three providers (Claude, OpenAI, Gemini) return this.
- **Token threshold is model-dependent**: 100k default suits Claude (200k window). For GPT-4o (128k) or smaller models, callers should pass a lower threshold. Future: read from provider's model metadata.
- **Compression is idempotent**: calling `compress_if_needed` when already under threshold is a no-op.

## Test Expectations

- **No compression needed**: 5-message conversation with 5000 tokens → returns unchanged
- **Basic compression**: 20-message conversation exceeding threshold → returns fewer messages with summary
- **Pair alignment**: tool_call at boundary → boundary moved forward past all its results
- **Orphan cleanup**: delete a tool_call, verify stub is inserted for orphaned tool result
- **Summary failure**: mock cheap_llm to raise → verify fallback marker used
- **No cheap_llm**: pass None → verify fallback marker used
- **Token tracking**: verify `metrics.token_usage()` called after each LLM response
- **Protected messages**: verify first 2 and last 3 messages are never evicted regardless of conversation length

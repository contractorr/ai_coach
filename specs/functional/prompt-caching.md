# Prompt Caching

**Status:** Draft
**Author:** Raj
**Date:** 2026-03-09

## Problem

Every agentic turn re-sends the full system prompt (profile XML, memory XML, recurring thoughts, tool definitions) as input tokens. For a 10-turn agentic conversation with a ~4000-token system prompt, that's ~40k redundant input tokens per query. Anthropic's prompt caching can reduce this cost by ~90% on cache hits (free to read cached prefixes, 1.25x write cost on first cache).

Reference: [hermes-agent `run_agent.py`](https://github.com/NousResearch/hermes-agent) — auto-enables prompt caching for Claude models with `cache_control` breakpoints on system prompt + first 3 conversation turns.

## Users

All users of the agentic advisor mode. Cost reduction is invisible to the user.

## Desired Behavior

1. When the LLM provider is Anthropic Claude, prompt caching is automatically enabled
2. The system prompt is marked with `cache_control: {"type": "ephemeral"}` so it is cached across turns within a session
3. The first 2-3 conversation messages (after system) are also cache-eligible to maximize prefix reuse
4. Cache TTL is Anthropic's default (5 minutes) — no custom TTL management needed
5. Non-Anthropic providers (OpenAI, Gemini) are unaffected — no cache_control is sent

## Acceptance Criteria

- [ ] Claude provider's `generate_with_tools()` sets `cache_control` on the system message
- [ ] Cache hits are observable via `response.usage.cache_read_input_tokens` logged at DEBUG level
- [ ] Non-Claude providers ignore caching entirely (no errors, no behavioral change)
- [ ] Token cost tracking in observability reflects the actual billed tokens (cache writes at 1.25x, cache reads at 0x)
- [ ] Existing tests pass (mock provider returns usage dict with cache fields)

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Session idle >5 min between turns | Cache expires, next turn is a full cache write (1.25x cost) — still cheaper than repeated full sends |
| System prompt changes mid-session (e.g., profile update) | Cache invalidated naturally, new prefix cached on next call |
| Provider auto-detection fails | Falls back to no caching — safe default |
| Extended thinking enabled | Cache control still applies to non-thinking content blocks |

## Out of Scope

- Cross-session caching (Anthropic caches are per-conversation, 5-min TTL)
- OpenRouter routing (ai-coach uses direct Anthropic SDK)
- Cache analytics dashboard

## Open Questions

- Should we expose cache hit/miss rates in `metrics.summary()`? Low effort, useful for cost monitoring.

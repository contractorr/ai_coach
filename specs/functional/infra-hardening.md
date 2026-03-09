# Infrastructure Hardening

**Status:** Draft
**Author:** Raj
**Date:** 2026-03-09

## Problem

Several internal infrastructure gaps discovered via comparison with [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent). Secret redaction covers only 5 patterns (Anthropic, OpenAI, Bearer, generic api_key, emails) — missing GitHub PATs, AWS keys, Slack tokens, DB connection strings, private keys, and 15+ other common formats. MCP error responses leak full Python tracebacks to external callers. Observability metrics are not thread-safe and lack cost tracking.

## Users

Operators deploying the web app or MCP server. Indirectly, all users whose secrets flow through logs or error responses.

## Desired Behavior

### Secret redaction

1. All log output (structlog + stdlib logging) redacts 20+ known API key prefixes, ENV assignments, JSON credential fields, Authorization headers, DB connection strings, and private key blocks
2. Redacted tokens preserve first 6 + last 4 chars for debuggability (e.g., `sk-ant...xY9z`) instead of full replacement with `...REDACTED`
3. Redaction is applied at the logging formatter level so third-party library logs are also covered

### MCP error responses

1. MCP `call_tool` errors return only the exception message, not the traceback
2. Full tracebacks continue to be logged server-side at ERROR level

### Observability

1. `Metrics.counter()` and `Metrics.timer()` are thread-safe under concurrent uvicorn workers
2. New `Metrics.token_usage(model, input_tokens, output_tokens)` method tracks per-model token consumption
3. `Metrics.summary()` includes estimated cost per model using a pricing lookup table
4. Cost estimation covers Claude (Haiku/Sonnet/Opus), GPT-4o, Gemini at known published rates; unknown models report tokens only with $0 cost

## Acceptance Criteria

- [ ] Redaction matches all prefix patterns from hermes-agent's `_PREFIX_PATTERNS` list (sk-, ghp_, github_pat_, xox[baprs]-, AIza, AKIA, sk_live_, sk_test_, SG., hf_, etc.)
- [ ] `_mask_token()` returns `***` for tokens <18 chars, `{first6}...{last4}` otherwise
- [ ] ENV assignment patterns (`OPENAI_API_KEY=sk-abc...`) are redacted
- [ ] JSON field patterns (`"apiKey": "value"`) are redacted
- [ ] DB connection strings (`postgres://user:PASSWORD@host`) have passwords redacted
- [ ] Private key blocks (`-----BEGIN...PRIVATE KEY-----`) are fully replaced
- [ ] stdlib `logging` calls from third-party libs (httpx, openai, etc.) pass through redaction
- [ ] MCP `call_tool` error payloads contain no `traceback` field
- [ ] `Metrics` operations do not raise under concurrent access from multiple threads
- [ ] `metrics.summary()` includes a `token_usage` section with per-model counts and estimated cost
- [ ] Existing tests pass; new tests cover redaction patterns and thread safety

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Token shorter than 18 chars (e.g., `sk-short`) | Fully masked as `***` |
| Log message contains multiple different key types | All are independently redacted |
| Unknown model in token_usage | Tokens tracked, cost = $0.00, flagged as `has_pricing: false` |
| `HERMES_REDACT_SECRETS=false` equivalent | Not supported — redaction is always on in ai-coach |
| Private key spanning multiple log lines | Multiline regex matches and replaces entire block |

## Out of Scope

- Encryption at rest for SQLite databases
- Redaction of tool result content before it enters the LLM context window (hermes does this via `redact_sensitive_text()` on file reads — worth considering separately)
- Prometheus/Datadog export for metrics

## Open Questions

- Should we add phone number redaction (hermes does E.164)? Low relevance for ai-coach.

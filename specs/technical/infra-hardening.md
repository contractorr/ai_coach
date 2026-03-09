# Infrastructure Hardening

## Overview

Expands secret redaction from 5 patterns to 25+, adds a stdlib-compatible `RedactingFormatter`, removes tracebacks from MCP error responses, and makes `Metrics` thread-safe with token/cost tracking. Modeled on [hermes-agent `agent/redact.py`](https://github.com/NousResearch/hermes-agent) and `agent/insights.py`.

## Dependencies

**Depends on:** `cli/logging_config.py`, `observability.py`, `coach_mcp/server.py`
**Depended on by:** all modules that log, MCP clients, web API

---

## Components

### SecretRedactor

**File:** `src/services/redact.py` (new)
**Status:** New

#### Behavior

Extracted from `cli/logging_config.py` into a standalone module so both structlog processors and stdlib formatters can use it.

Pattern categories (ported from hermes-agent `agent/redact.py`):

1. **Known prefixes** — 22 compiled regexes joined into one alternation with word-boundary guards:
   ```
   sk-[A-Za-z0-9_-]{10,}          # OpenAI / Anthropic
   ghp_[A-Za-z0-9]{10,}           # GitHub PAT classic
   github_pat_[A-Za-z0-9_]{10,}   # GitHub PAT fine-grained
   xox[baprs]-[A-Za-z0-9-]{10,}   # Slack
   AIza[A-Za-z0-9_-]{30,}         # Google
   AKIA[A-Z0-9]{16}               # AWS Access Key ID
   sk_live_[A-Za-z0-9]{10,}       # Stripe live
   sk_test_[A-Za-z0-9]{10,}       # Stripe test
   SG\.[A-Za-z0-9_-]{10,}         # SendGrid
   hf_[A-Za-z0-9]{10,}            # HuggingFace
   # + others from hermes _PREFIX_PATTERNS
   ```

2. **ENV assignments** — `KEY=value` where KEY matches `API_?KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH`

3. **JSON fields** — `"apiKey": "value"`, `"token": "value"`, etc.

4. **Authorization headers** — `Authorization: Bearer <token>`

5. **DB connection strings** — `postgres://user:PASSWORD@host` → `postgres://user:***@host`

6. **Private key blocks** — `-----BEGIN...PRIVATE KEY-----...-----END...` → `[REDACTED PRIVATE KEY]`

Masking function:
```python
def _mask_token(token: str) -> str:
    if len(token) < 18:
        return "***"
    return f"{token[:6]}...{token[-4:]}"
```

Public API:
```python
def redact_sensitive_text(text: str) -> str: ...
```

No config to disable — always on in ai-coach (hermes has a `HERMES_REDACT_SECRETS` env toggle; we skip that).

#### Inputs / Outputs

| Function | Input | Output |
|----------|-------|--------|
| `redact_sensitive_text(text)` | `str` | `str` with secrets masked |
| `_mask_token(token)` | `str` | `***` or `{first6}...{last4}` |

#### Invariants

- Non-matching text passes through unchanged
- Empty/None input returns unchanged
- All compiled regexes are module-level constants (no per-call compilation)

#### Error Handling

- Regex errors (should not occur with static patterns): caught, original text returned unmodified

---

### Structlog redaction processor

**File:** `src/cli/logging_config.py` (modified)
**Status:** Stable

#### Behavior

Replace inline `_REDACT_PATTERNS` and `_redact_sensitive` with:
```python
from services.redact import redact_sensitive_text

def _redact_sensitive(_, __, event_dict: dict) -> dict:
    for key, value in event_dict.items():
        if isinstance(value, str):
            event_dict[key] = redact_sensitive_text(value)
    return event_dict
```

Additionally, add a `RedactingFormatter` to the stdlib root logger so third-party library logs (httpx, openai SDK, etc.) also pass through redaction:

```python
class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact_sensitive_text(super().format(record))
```

Wire this into `setup_logging()` alongside the existing structlog handler.

---

### MCP error cleanup

**File:** `src/coach_mcp/server.py` (modified)
**Status:** Stable

#### Behavior

Change the exception handler in `call_tool`:

```python
# Before
text = json.dumps({"error": str(e), "traceback": traceback.format_exc()})

# After
logger.error("tool_error", tool=name, error=str(e), exc_info=True)
text = json.dumps({"error": str(e)})
```

`exc_info=True` ensures the traceback reaches the log file (via structlog) but not the MCP client.

---

### Thread-safe Metrics with token tracking

**File:** `src/observability.py` (modified)
**Status:** Stable

#### Behavior

Add `threading.Lock` to all mutating operations. Add `token_usage()` method and cost estimation.

```python
import threading

class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}
        self._timers: dict[str, list[float]] = {}
        self._tokens: dict[str, dict] = {}  # model -> {input, output, cost}

    def counter(self, name: str, value: int = 1):
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def timer(self, name: str):
        # context manager; append under lock in finally

    def token_usage(self, model: str, input_tokens: int, output_tokens: int):
        with self._lock:
            entry = self._tokens.setdefault(model, {"input": 0, "output": 0})
            entry["input"] += input_tokens
            entry["output"] += output_tokens

    def summary(self) -> dict:
        with self._lock:
            # existing counters + timers
            # + token_usage with cost estimation
```

Cost estimation lookup (per 1M tokens):

| Model pattern | Input $/M | Output $/M |
|---------------|-----------|------------|
| `haiku` | $0.25 | $1.25 |
| `sonnet` | $3.00 | $15.00 |
| `opus` | $15.00 | $75.00 |
| `gpt-4o` | $2.50 | $10.00 |
| `gpt-4o-mini` | $0.15 | $0.60 |
| `gemini` | $0.00 | $0.00 |
| unknown | $0.00 | $0.00 |

Matching: lowercase model name, check if it contains the pattern string. First match wins.

#### Configuration

| Key | Default | Source |
|-----|---------|--------|
| (none) | — | Pricing is hardcoded; update on provider price changes |

---

## Cross-Cutting Concerns

- `redact_sensitive_text` is intentionally stateless and side-effect-free — safe to call from any thread, any context
- The `RedactingFormatter` must be added *after* structlog's formatter in the handler chain so both log paths are covered
- Token tracking requires callers (LLM provider implementations) to call `metrics.token_usage()` after each API call — this is a new convention

## Test Expectations

- **Redaction**: parametrized tests for each of the 6 pattern categories with known inputs → expected masked outputs
- **Mask function**: test boundary at 17 chars (full mask) vs 18 chars (partial mask)
- **Thread safety**: spawn 10 threads incrementing the same counter 1000 times, assert final value = 10000
- **MCP error**: mock a handler that raises, assert response JSON has no `traceback` key
- **Token cost**: assert known model names produce expected cost calculations
- **Integration**: assert that a structlog call containing `sk-ant-api03-longkey` is logged with the key masked

# LLM Council

## Overview

The LLM Council feature enables multi-model deliberation for important or open-ended questions by querying multiple LLM providers in parallel and synthesizing their responses into a single coherent answer. Council members include built-in providers (Claude, OpenAI, Gemini) and user-configured custom OpenAI-compatible providers.

## Dependencies

**Depends on:** `src/llm/` (provider factory and base classes), `src/advisor/prompts.py` (PromptTemplates), `concurrent.futures` (ThreadPoolExecutor)

**Depended on by:** `src/web/routes/advisor.py` (advisor ask endpoint), `src/advisor/engine.py` (AdvisorEngine)

## Components

### CouncilMember
**File:** `src/advisor/council.py`

#### Behavior

```python
@dataclass
class CouncilMember:
    provider: str
    api_key: str
    model: str | None = None
    display_name: str | None = None
    base_url: str | None = None
```

Represents a single council member with credentials and optional configuration.

**Fields:**
- `provider`: Provider name (`"claude"`, `"openai"`, `"gemini"`, or `"openai_compatible"`)
- `api_key`: API key for authentication
- `model`: Optional model override (None = provider default for built-in providers; required for custom providers)
- `display_name`: Optional display name for UI (used for custom providers; defaults to provider name for built-in providers)
- `base_url`: Optional base URL override (only used for `openai_compatible` provider)

#### Invariants

- For built-in providers (`claude`, `openai`, `gemini`): `base_url` must be `None`
- For custom providers: `provider` must be `"openai_compatible"`, `base_url` must be non-empty, `model` must be non-empty, `display_name` should be set
- `api_key` must always be non-empty

---

### CouncilMemberResponse
**File:** `src/advisor/council.py`

#### Behavior

```python
@dataclass
class CouncilMemberResponse:
    provider: str
    content: str | None = None
    error: str | None = None
    display_name: str | None = None

    @property
    def ok(self) -> bool:
        return bool(self.content) and not self.error
```

Represents the result of querying a single council member.

**Fields:**
- `provider`: Provider name (may be `"openai_compatible"` for custom providers)
- `content`: Generated response text (None if error occurred)
- `error`: Error message (None if successful)
- `display_name`: Display name for UI (especially important for custom providers)

**`ok` property:** Returns `True` if the response contains content and no error.

---

### CouncilResult
**File:** `src/advisor/council.py`

#### Behavior

```python
@dataclass
class CouncilResult:
    answer: str
    used: bool = False
    providers: list[str] = field(default_factory=list)
    failed_providers: list[str] = field(default_factory=list)
    partial: bool = False
    member_responses: list[CouncilMemberResponse] = field(default_factory=list)
```

Final synthesized council answer with metadata.

**Fields:**
- `answer`: Synthesized final answer
- `used`: `True` if full council synthesis was used (2+ successful responses); `False` if fallback to single provider
- `providers`: List of provider names that succeeded
- `failed_providers`: List of provider names that failed
- `partial`: `True` if at least one provider failed but council still ran
- `member_responses`: Full list of all member responses (successful and failed)

---

### CouncilOrchestrator
**File:** `src/advisor/council.py`

#### Behavior

```python
class CouncilOrchestrator:
    def __init__(
        self,
        members: list[CouncilMember],
        lead_provider: str | None = None,
        provider_factory: Callable[..., object] = create_llm_provider,
    )

    def run(
        self,
        *,
        system: str,
        user_prompt: str,
        conversation_history: list[dict] | None = None,
        max_tokens: int = 2200,
    ) -> CouncilResult
```

Orchestrates parallel provider invocation and synthesis.

**Initialization:**
- `members`: List of `CouncilMember` instances (must have at least 2 members)
- `lead_provider`: Optional preferred provider for synthesis (defaults to first successful response if None)
- `provider_factory`: Dependency injection for provider creation (default: `create_llm_provider`)

**`run()` method:**

1. **Validation**: Requires at least 2 members (raises `LLMError` otherwise)
2. **Parallel invocation**: Uses `ThreadPoolExecutor` with `max_workers=len(members)` to invoke all members concurrently via `_invoke_member`
3. **Response collection**: Gathers all responses (both successful and failed)
4. **Synthesis decision**:
   - 0 successful → raises `LLMError`
   - 1 successful → returns `CouncilResult(used=False, ...)` with fallback answer
   - 2+ successful → synthesizes via `_synthesize()` and returns `CouncilResult(used=True, ...)`

**`_invoke_member()` internal method:**

For each `CouncilMember`:
1. Creates provider instance:
   - Built-in providers: `self.provider_factory(provider=member.provider, api_key=member.api_key, model=member.model)`
   - Custom providers: `OpenAICompatibleProvider(base_url=member.base_url, api_key=member.api_key, model=member.model, display_name=member.display_name)`
2. Builds messages: appends council member prompt from `PromptTemplates.build_council_member_prompt(user_prompt)`
3. Calls `provider.generate()` with council member system prompt from `PromptTemplates.build_council_member_system(system)`
4. Returns `CouncilMemberResponse` with content or error

**`_select_synthesis_member()` internal method:**

Selects which member should perform synthesis:
- If `lead_provider` is set and that provider succeeded, use it
- Otherwise, use first successful member

**`_synthesize()` internal method:**

1. Selects synthesis member via `_select_synthesis_member()`
2. Creates provider instance for that member
3. Builds synthesis prompt via `PromptTemplates.build_council_synthesis_prompt()` with all successful member responses
4. Calls `provider.generate()` with synthesis system prompt
5. Returns synthesized answer string

**`_fallback_answer()` internal method:**

When only 1 provider succeeds, returns that provider's answer prefixed with a note about partial council if any providers failed.

#### Inputs / Outputs

- `run()` returns `CouncilResult`
- `_invoke_member()` returns `CouncilMemberResponse`
- `_synthesize()` returns `str`

#### Invariants

- At least 2 members required (enforced in `run()`)
- All members invoked in parallel (no serial fallback)
- Synthesis always uses one of the successful members (never creates a new provider)
- Failed providers do not block council operation if at least 1 provider succeeds
- When `display_name` is set, it is used in responses instead of the raw provider name

#### Caveats

- Custom providers with the same `display_name` are indistinguishable in the final result
- No retry logic — each member gets exactly one attempt
- No timeout per member — relies on provider-level timeouts
- Synthesis happens serially after all members complete (synthesis is not parallelized)

#### Error Handling

- `LLMError`: Raised if fewer than 2 members provided at init
- `LLMError`: Raised if all members fail
- Individual member failures are caught and recorded in `CouncilMemberResponse.error`
- Provider-level exceptions (`LLMAuthError`, `LLMRateLimitError`) are caught and converted to error strings

#### Configuration

- Default `max_tokens`: `2200`
- ThreadPoolExecutor `max_workers`: set to number of members (no thread pool reuse between runs)

---

### is_council_eligible()
**File:** `src/advisor/council.py`

#### Behavior

```python
def is_council_eligible(
    question: str,
    advice_type: str = "general",
) -> bool
```

Heuristic gate for determining whether a question should trigger council mode.

**Logic:**

1. Returns `True` if `advice_type` in `{"career", "goals", "opportunities", "skill_gap"}`
2. Returns `False` if question starts with low-risk prefixes: `"rewrite"`, `"rephrase"`, `"fix grammar"`, `"summarize"`, `"what is"`, `"who is"`, `"when is"`, `"where is"`, `"define"`
3. Returns `True` if question length >= 120 characters OR contains strategy markers: `"should i"`, `"help me decide"`, `"best path"`, `"path forward"`, `"tradeoff"`, `"trade-off"`, `"strategy"`, `"strategic"`, `"roadmap"`, `"prioritize"`, `"career move"`, `"next move"`, `"important"`, `"plan"`, `"compare"`, `"which option"`, `"big decision"`
4. Otherwise returns `False`

#### Invariants

- Empty question returns `False`
- All comparisons are case-insensitive
- Length threshold is fixed at 120 characters
- Advice type matching is exact (no prefix/suffix matching)

---

## Web API Integration

### Custom Provider Storage
**File:** `src/web/user_store.py`

#### Behavior

Custom providers are stored in user secrets as a JSON-encoded list under the key `"llm_custom_providers"`.

**Schema:**

```python
[
    {
        "id": str,           # UUID v4
        "display_name": str,
        "base_url": str,
        "api_key": str,      # encrypted with Fernet
        "model": str,
    },
    ...
]
```

**Operations:**

- **Get**: `get_user_secret(user_id, "llm_custom_providers", fernet_key)` → JSON string → list of dicts
- **Set**: list of dicts → JSON string → `set_user_secret(user_id, "llm_custom_providers", json_string, fernet_key)`
- **Delete**: `delete_user_secret(user_id, "llm_custom_providers")`

#### Invariants

- Each provider must have a unique `id` within the user's list
- `id` is a UUID v4 string generated on creation, immutable
- All fields are required (no optional fields)
- Empty list is valid (user has no custom providers)
- If secret does not exist, treat as empty list

---

### Settings Routes
**File:** `src/web/routes/settings.py`

#### Endpoints

**`GET /api/settings`**

Returns `SettingsResponse` including:
- `llm_custom_providers_count`: int (number of custom providers)
- `llm_council_ready`: bool (includes custom providers in count)

**`PUT /api/settings`**

Accepts `SettingsUpdate` with:
- `llm_custom_providers_add`: Optional dict with `{display_name, base_url, api_key, model}`
- `llm_custom_providers_update`: Optional dict with `{id, display_name, base_url, api_key, model}` (api_key optional)
- `llm_custom_providers_remove`: Optional list of provider IDs to remove

**`POST /api/settings/test-custom-provider`**

Query params: `provider_id` (string, UUID)

Tests connection for an existing custom provider by:
1. Loading custom providers from user secrets
2. Finding provider by ID
3. Creating `OpenAICompatibleProvider` instance
4. Calling `provider.generate(messages=[{"role": "user", "content": "ping"}], system="Reply with exactly: ok", max_tokens=5)`
5. Returning `{"ok": True, "provider": display_name, "response": response}` or raising HTTPException(422)

#### Error Handling

- Invalid `base_url`: HTTPException(400, "Invalid base URL")
- Missing required fields: HTTPException(400, "All fields required")
- Provider ID not found: HTTPException(404, "Provider not found")
- Test connection failure: HTTPException(422, error message from provider)

---

### Dependency Injection Updates
**File:** `src/web/deps.py`

#### New Functions

**`get_custom_providers_for_user(user_id: str) -> list[dict]`**

Returns list of custom provider configs from user secrets. Each dict contains `{id, display_name, base_url, api_key, model}`.

**`get_council_members_for_user(user_id: str) -> list[CouncilMember]`**

Updated to include both built-in and custom providers:
1. Gets personal keys for built-in providers via `_get_personal_llm_keys_from_secrets()`
2. Gets custom providers via `get_custom_providers_for_user()`
3. Constructs `CouncilMember` for each:
   - Built-in: `CouncilMember(provider=name, api_key=key, model=None)`
   - Custom: `CouncilMember(provider="openai_compatible", api_key=config["api_key"], model=config["model"], display_name=config["display_name"], base_url=config["base_url"])`
4. Returns combined list

**Council readiness:** Updated to count built-in + custom providers. Ready if `len(get_council_members_for_user(user_id)) >= 2`.

---

## Frontend Integration

### Data Models
**File:** `web/src/app/(dashboard)/settings/page.tsx`

#### Interfaces

```typescript
interface CustomProvider {
  id: string;
  display_name: string;
  base_url: string;
  model: string;
  // api_key never sent to frontend (security)
}

interface Settings {
  // ... existing fields ...
  llm_custom_providers: CustomProvider[];
}
```

#### State Management

- `customProviders`: `CustomProvider[]` — list of user's custom providers
- `customProviderForm`: `{ display_name, base_url, api_key, model }` — form state for add/edit
- `editingCustomProviderId`: `string | null` — ID of provider being edited (null = adding new)
- `testingCustomProviderId`: `string | null` — ID of provider being tested

#### UI Components

**Custom Providers Section:**

- Card titled "Custom Providers (OpenAI-compatible)"
- Description explaining compatible providers (Together, Groq, Fireworks, etc.)
- List of existing custom providers (if any)
- "Add Provider" button

**Provider List Item:**

Each custom provider shows:
- Display name (bold)
- Base URL + model (muted text)
- "Test", "Edit", "Remove" action buttons

**Add/Edit Form:**

Four input fields:
1. Display Name (text input, required)
2. Base URL (text input, required, validated as URL)
3. API Key (password input, required, masked)
4. Model ID (text input, required)

Buttons:
- "Save" (primary)
- "Cancel" (if editing)
- "Test Connection" (after save, or while editing)

#### Validation

- All fields required before save
- Base URL validated with URL regex: `^https?://[^\s/$.?#].[^\s]*$`
- Error displayed inline if validation fails

#### API Integration

**Load custom providers:**
```typescript
GET /api/settings → settings.llm_custom_providers
```

**Add custom provider:**
```typescript
PUT /api/settings
Body: { llm_custom_providers_add: { display_name, base_url, api_key, model } }
```

**Update custom provider:**
```typescript
PUT /api/settings
Body: { llm_custom_providers_update: { id, display_name, base_url, model, api_key? } }
```

**Remove custom provider:**
```typescript
PUT /api/settings
Body: { llm_custom_providers_remove: [id] }
```

**Test connection:**
```typescript
POST /api/settings/test-custom-provider?provider_id={id}
```

---

## Test Expectations

### Unit Tests

**`src/advisor/council.py`:**
- `CouncilOrchestrator.__init__()`: verify `LLMError` raised if fewer than 2 members
- `CouncilOrchestrator.run()`: verify parallel execution with ThreadPoolExecutor
- `CouncilOrchestrator.run()`: verify synthesis when 2+ members succeed
- `CouncilOrchestrator.run()`: verify fallback when only 1 member succeeds
- `CouncilOrchestrator.run()`: verify `LLMError` when all members fail
- `CouncilOrchestrator._invoke_member()`: verify custom provider instantiation with `OpenAICompatibleProvider`
- `CouncilOrchestrator._invoke_member()`: verify built-in provider uses factory
- `CouncilOrchestrator._invoke_member()`: verify error caught and returned in `CouncilMemberResponse`
- `CouncilOrchestrator._select_synthesis_member()`: verify lead provider preference
- `is_council_eligible()`: verify advice type filtering
- `is_council_eligible()`: verify low-risk prefix exclusion
- `is_council_eligible()`: verify length threshold
- `is_council_eligible()`: verify strategy markers

**`src/llm/providers/openai_compatible.py`:**
- `OpenAICompatibleProvider.__init__()`: verify OpenAI client constructed with custom `base_url`
- `OpenAICompatibleProvider.generate()`: verify standard OpenAI request format
- `OpenAICompatibleProvider.generate_with_tools()`: verify tool format matches OpenAI
- Error handling: verify `AuthenticationError` → `LLMAuthError`
- Error handling: verify `RateLimitError` → `LLMRateLimitError`
- Error handling: verify `APIError` → `LLMError`
- Error handling: verify `TimeoutException` → `LLMError`
- Error handling: verify `ConnectError` → `LLMError`

### Integration Tests

**`src/web/routes/settings.py`:**
- `GET /api/settings`: verify `llm_custom_providers` returned
- `PUT /api/settings`: verify `llm_custom_providers_add` creates new provider with UUID
- `PUT /api/settings`: verify `llm_custom_providers_update` updates existing provider
- `PUT /api/settings`: verify `llm_custom_providers_remove` deletes provider
- `PUT /api/settings`: verify invalid `base_url` returns 400
- `PUT /api/settings`: verify missing fields return 400
- `POST /api/settings/test-custom-provider`: verify test connection success path
- `POST /api/settings/test-custom-provider`: verify test connection failure returns 422
- `POST /api/settings/test-custom-provider`: verify invalid provider ID returns 404

**`src/web/deps.py`:**
- `get_council_members_for_user()`: verify built-in providers included
- `get_council_members_for_user()`: verify custom providers included with correct fields
- `get_council_members_for_user()`: verify council readiness with 1 built-in + 1 custom = ready

### E2E Tests

**Frontend:**
- Add custom provider form: fill all fields, save, verify appears in list
- Edit custom provider: change display name, save, verify updated
- Remove custom provider: click remove, verify removed from list
- Test connection: valid provider → success toast
- Test connection: invalid API key → error toast with "Authentication failed"
- Test connection: invalid model → error toast with "Model not available"
- Council readiness badge: 0 providers → "Need 2 providers"
- Council readiness badge: 1 built-in + 1 custom → "Council ready"
- Validation: empty field → "All fields required" error
- Validation: invalid URL → "Invalid URL" error

---

## Performance Considerations

- ThreadPoolExecutor creates `len(members)` threads per council run — may be resource-intensive with many members
- Synthesis happens serially after all members complete — total latency is max(all_member_times) + synthesis_time
- No caching of provider instances — each council run creates new provider objects
- Custom provider credentials are decrypted from secrets on every request — Fernet decryption overhead

---

## Security Considerations

- Custom provider API keys stored encrypted with Fernet (same security as built-in providers)
- API keys never sent to frontend — only provider ID, display name, base URL, and model exposed
- Base URL validation prevents injection of non-HTTP(S) protocols
- No SSRF protection on base URL — user can point to internal endpoints (accepted risk for self-hosted use cases)
- Test connection sends minimal prompt ("ping") — no user data exposed during test
- Council synthesis includes member responses in prompt — sensitive data from one provider visible to synthesis provider

---

## Migration Notes

- Existing council functionality unchanged — custom providers are additive
- No data migration required — custom providers start as empty list
- Existing `get_council_members_for_user()` signature preserved — return type unchanged
- Frontend `SettingsResponse` schema backward compatible — `llm_custom_providers` defaults to empty list

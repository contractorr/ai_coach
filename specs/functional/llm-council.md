# Multi-Provider Model Access and LLM Council

**Status:** Draft

## Purpose

Users can currently rely on one model provider at a time, which creates a single point of failure for both quality and judgment. When a user brings multiple provider keys, steward should be able to compare perspectives on important or open-ended questions so answers are more nuanced, less brittle, and more action-oriented.

## Product Placement

- Setup surface: `Settings`
- Primary answer surfaces: `Home` Ask mode, `/advisor`, and deep-research style strategic queries
- Primary job: turn multiple saved provider keys into better decision support, not just more configuration

## Desired Behavior

- Settings lets the user connect one API key per supported provider (Claude, OpenAI, Gemini) and manage each key independently.
- Settings lets the user add multiple custom OpenAI-compatible providers (Together AI, Groq, Fireworks, OpenRouter, Ollama, vLLM, LM Studio, etc.) by providing display name, base URL, API key, and model ID.
- Settings clearly communicates which providers are currently available for use.
- Users can choose a default lead provider for normal single-provider answers.
- If the user has only one working provider key, steward answers normally with that provider.
- If the user has two or more working provider keys, steward can use a council for eligible prompts that are important, ambiguous, strategic, or otherwise open-ended.
- Council mode is framed as a quality feature, not a default for every prompt. Fast, low-risk requests should still return a normal single-provider answer unless the user explicitly asks for broader deliberation.
- In v1, users cannot manually force council mode for an individual prompt; steward decides automatically when council mode applies.
- When council mode is used, the returned answer should feel like one coherent steward response rather than a dump of multiple model transcripts.
- Council synthesis style remains system-defined in v1 rather than user-configurable.
- A council answer should explicitly include:
  - the main conclusion or recommendation
  - important areas of agreement across providers
  - meaningful disagreement, uncertainty, or tradeoffs when they exist
  - a recommended path forward with concrete next steps
- The UI should make it obvious when a response was council-assisted so users understand why it may have taken longer.
- The UI should explain that council answers can consume more tokens and cost more across the user's own provider accounts.

## Eligible Questions

Council mode is intended for prompts such as:

- important decisions with multiple tradeoffs
- career, project, or strategy questions where the user wants the best path forward
- ambiguous questions where one confident answer may hide uncertainty
- planning requests that benefit from critique and synthesis rather than a single instant response

Council mode is not intended for:

- quick factual lookups
- short rewrite or formatting requests
- routine follow-up messages where deliberation adds little value

## Custom OpenAI-Compatible Providers

Users can extend council capabilities beyond the three built-in providers (Claude, OpenAI, Gemini) by adding custom providers that implement the OpenAI `/v1/chat/completions` API specification.

### Supported Providers

Any provider implementing OpenAI's chat completions API is compatible, including:
- Together AI
- Fireworks AI
- Groq
- OpenRouter
- Ollama (local)
- vLLM (self-hosted)
- LM Studio (local)
- Any other OpenAI-compatible endpoint

### Configuration Requirements

Each custom provider requires four fields:
1. **Display Name**: User-chosen label (e.g., "Together – Llama 3")
2. **Base URL**: Provider's API root (e.g., `https://api.together.xyz/v1`)
3. **API Key**: Provider's authentication key
4. **Model ID**: Model string to send (e.g., `meta-llama/Llama-3-70b-chat-hf`)

### Custom Provider Behavior

- Multiple custom providers can be configured (no hard limit beyond UI/UX considerations)
- Each custom provider participates in council mode alongside built-in providers
- Custom providers use the display name chosen by the user in council UI
- Custom providers support the same test connection flow as built-in providers
- API keys for custom providers are encrypted and stored with the same security as built-in provider keys
- Custom providers can be edited or removed independently without affecting other providers
- If a custom provider times out or fails, council continues with remaining providers

### Validation

Before saving a custom provider:
- Base URL must be a valid URL format
- All four fields must be non-empty
- Optional: Test connection verifies URL, key, and model work together

### Error Handling

Common failure modes handled gracefully:
- Invalid base URL → "Base URL must be a valid URL"
- Authentication failure (401) → "Authentication failed. Check your API key."
- Model not found (404) → "Model not available at this provider."
- Network timeout → "Provider did not respond in time."
- Rate limit → Treated same as built-in provider rate limits

## User Flows

### Standard Provider Flow
1. The user opens `Settings` and connects API keys for two or more supported providers (Claude, OpenAI, Gemini).
2. The user selects a default lead provider for normal fast answers.
3. The user sees that multiple providers are available and that steward may use council mode for eligible prompts in `Home`, `/advisor`, or deep-research style strategic queries.
4. The user asks an important or open-ended question in one of those eligible surfaces.
5. Steward automatically decides whether council mode applies and returns a single synthesized answer that highlights shared conclusions, disagreements, and the best recommended next step.
6. The user can act on the recommendation without having to reconcile multiple raw model replies themselves.

### Custom Provider Flow
1. The user opens `Settings` and navigates to the "Custom Providers (OpenAI-compatible)" section.
2. The user clicks "Add Provider" and fills in: display name, base URL, API key, and model ID.
3. Optionally, the user clicks "Test Connection" to verify the configuration before saving.
4. The user saves the custom provider. It now appears in the provider list and is eligible for council mode.
5. The user can edit or remove custom providers independently.
6. When council mode triggers, custom providers participate alongside built-in providers, with their display names shown in the council UI.

## Acceptance Criteria

- [ ] A user can save provider keys independently for multiple supported providers from `Settings`.
- [ ] Saving or editing one provider key does not overwrite other saved provider keys.
- [ ] Each saved provider can be tested, replaced, or removed on its own.
- [ ] The user can choose a default lead provider for normal single-provider responses.
- [ ] When two or more provider keys are working, steward can use council mode for eligible prompts.
- [ ] In v1, council mode is eligible in `Home` Ask, `/advisor`, and deep-research style strategic queries.
- [ ] In v1, users cannot manually force council mode for a single prompt.
- [ ] Council-assisted answers present one synthesized response with agreement, disagreement or uncertainty, and a recommended path forward.
- [ ] When council mode is not used, the answer flow remains fast and behaves like a normal single-provider response.
- [ ] If one provider fails during a council run, steward still returns the best available answer from the remaining providers and tells the user that fewer voices were available.
- [ ] If only one working provider remains, steward falls back to a single-provider answer instead of failing the request.
- [ ] The user can understand the latency and cost tradeoff before relying on council mode.

### Custom Provider Criteria

- [ ] A user can add multiple custom OpenAI-compatible providers from `Settings`.
- [ ] Each custom provider requires display name, base URL, API key, and model ID.
- [ ] All four fields must be non-empty before saving.
- [ ] Base URL is validated for correct URL format.
- [ ] Custom provider API keys are encrypted and stored with the same security as built-in provider keys.
- [ ] Each custom provider has a "Test Connection" button that validates the configuration.
- [ ] Test connection returns clear error messages for common failure modes (invalid URL, auth failure, model not found, timeout).
- [ ] Custom providers can be edited independently.
- [ ] Custom providers can be removed independently without affecting other providers.
- [ ] Custom providers participate in council mode alongside built-in providers.
- [ ] Custom providers use their user-defined display name in council UI and responses.
- [ ] Council readiness calculation includes both built-in and custom providers.
- [ ] If a custom provider fails during council, council continues with remaining providers.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User has only one saved provider key | Steward uses the normal answer flow and does not mention council mode. |
| User has multiple saved keys but one is invalid or expired | The invalid provider is clearly marked in Settings and does not block the others. |
| One provider times out or rate-limits during a council response | Steward continues with the remaining providers and discloses that the response used a partial council. |
| Providers materially disagree | The answer surfaces the disagreement clearly and avoids pretending there is a false consensus. |
| User asks for a simple formatting or factual task | Steward uses the normal answer path and does not expose a manual `force council` override in v1. |
| User removes a provider after using council mode previously | Future answers only use the providers that are still configured and healthy. |
| Custom provider base URL is invalid | Settings shows clear validation error and prevents saving. |
| Custom provider API key is incorrect | Test connection shows "Authentication failed" error. |
| Custom provider model ID doesn't exist | Test connection shows "Model not available" error. |
| Custom provider endpoint times out | Test connection shows timeout error; during council, provider is skipped. |
| User adds two custom providers with same display name | Allowed; display names are user-chosen labels and need not be unique (though unique names are recommended for clarity). |
| User's custom provider endpoint goes offline | Council skips that provider and continues with others; UI shows partial council indicator. |

## Out of Scope

- Multiple keys for the same built-in provider (Claude/OpenAI/Gemini)
- User-facing display of raw hidden reasoning or full internal debate transcripts
- Automatic optimization for provider pricing beyond clear user messaging about extra cost
- User-configurable council synthesis styles in the first release
- Manual per-prompt `force council` controls in the first release
- Auto-discovery of custom providers (user must manually configure each provider)
- OAuth or other auth flows for custom providers (API key auth only)

## Key System Components

- `web/src/app/(dashboard)/settings/page.tsx`
- `web/src/app/(dashboard)/page.tsx`
- `web/src/components/SettingsSheet.tsx`
- `src/web/routes/settings.py`
- `src/web/routes/advisor.py`
- `src/llm/`

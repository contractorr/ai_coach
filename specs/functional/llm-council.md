# Multi-Provider Model Access and LLM Council

**Status:** Draft

## Purpose

Users can currently rely on one model provider at a time, which creates a single point of failure for both quality and judgment. When a user brings multiple provider keys, steward should be able to compare perspectives on important or open-ended questions so answers are more nuanced, less brittle, and more action-oriented.

## Product Placement

- Setup surface: `Settings`
- Primary answer surfaces: `Home` Ask mode, `/advisor`, and deep-research style strategic queries
- Primary job: turn multiple saved provider keys into better decision support, not just more configuration

## Desired Behavior

- Settings lets the user connect one API key per supported provider and manage each key independently.
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

## User Flows

1. The user opens `Settings` and connects API keys for two or more supported providers.
2. The user selects a default lead provider for normal fast answers.
3. The user sees that multiple providers are available and that steward may use council mode for eligible prompts in `Home`, `/advisor`, or deep-research style strategic queries.
4. The user asks an important or open-ended question in one of those eligible surfaces.
5. Steward automatically decides whether council mode applies and returns a single synthesized answer that highlights shared conclusions, disagreements, and the best recommended next step.
6. The user can act on the recommendation without having to reconcile multiple raw model replies themselves.

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

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User has only one saved provider key | Steward uses the normal answer flow and does not mention council mode. |
| User has multiple saved keys but one is invalid or expired | The invalid provider is clearly marked in Settings and does not block the others. |
| One provider times out or rate-limits during a council response | Steward continues with the remaining providers and discloses that the response used a partial council. |
| Providers materially disagree | The answer surfaces the disagreement clearly and avoids pretending there is a false consensus. |
| User asks for a simple formatting or factual task | Steward uses the normal answer path and does not expose a manual `force council` override in v1. |
| User removes a provider after using council mode previously | Future answers only use the providers that are still configured and healthy. |

## Out of Scope

- Multiple keys for the same provider
- User-facing display of raw hidden reasoning or full internal debate transcripts
- Automatic optimization for provider pricing beyond clear user messaging about extra cost
- Self-hosted or custom model backends in the first release
- User-configurable council synthesis styles in the first release
- Manual per-prompt `force council` controls in the first release

## Key System Components

- `web/src/app/(dashboard)/settings/page.tsx`
- `web/src/app/(dashboard)/page.tsx`
- `web/src/components/SettingsSheet.tsx`
- `src/web/routes/settings.py`
- `src/web/routes/advisor.py`
- `src/llm/`

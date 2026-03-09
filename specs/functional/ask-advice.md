# Home Capture and Ask

**Status:** Updated for the simplified product model

## Purpose

Home is the default entry point for both note capture and grounded advice. The product should feel like one coherent assistant, so users start with one composer instead of choosing between separate chat and capture workspaces.

## Product Placement

- Workspace: `Home`
- Primary job: capture a thought or ask a question from one place
- Deep link: `/advisor` remains available only as a continuation surface for active conversations

## Current Behavior

- The Home composer defaults to capture.
- Explicit question syntax can preselect Ask, while an explicit toggle choice wins for the current draft.
- The composer shows a visible intent state so the user can tell whether Enter will save to Journal or send to the advisor.
- After a note is captured, Home offers a lightweight `Get advice on this` follow-up.
- Home also shows a short greeting/return brief and at most three prioritized next-step cards.
- When the user has multiple working provider keys, important or open-ended Ask prompts can use council-assisted answering instead of relying on a single provider.
- Council-assisted answers should surface the best path forward, not just a generic synthesis.
- PDF attachments stay available in Ask mode without turning document handling into a separate product concept.

## User Flows

- User writes a question on Home and receives a streamed answer.
- User asks a high-stakes or ambiguous question and receives one council-assisted answer that summarizes agreement, disagreement, and recommended next steps.
- User starts typing, sees Home preselect Ask for a question-shaped draft, and can still lock the draft back to Capture when they only want to save it.
- User writes a note, saves it, then upgrades it into advice with one click.
- User opens the full chat deep link only when a longer thread needs more space.

## Key System Components

- `web/src/app/(dashboard)/page.tsx`
- `src/web/routes/advisor.py`
- `src/llm/`
- `src/web/routes/greeting.py`
- `src/web/routes/suggestions.py`
- `web/src/components/ChatPdfAttachments.tsx`

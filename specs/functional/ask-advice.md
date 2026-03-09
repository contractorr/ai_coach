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
- Explicit question syntax or the Ask toggle routes the request to the advisor streaming API.
- After a note is captured, Home offers a lightweight `Get advice on this` follow-up.
- Home also shows a short greeting/return brief and at most three prioritized next-step cards.
- PDF attachments stay available in Ask mode without turning document handling into a separate product concept.

## User Flows

- User writes a question on Home and receives a streamed answer.
- User writes a note, saves it, then upgrades it into advice with one click.
- User opens the full chat deep link only when a longer thread needs more space.

## Key System Components

- `web/src/app/(dashboard)/page.tsx`
- `src/web/routes/advisor.py`
- `src/web/routes/greeting.py`
- `src/web/routes/suggestions.py`
- `web/src/components/ChatPdfAttachments.tsx`

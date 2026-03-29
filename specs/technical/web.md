# Web

**Status:** Updated for the simplified product model

## Overview

The web app presents six primary product jobs: `Home`, `Goals`, `Radar`, `Research`, `Learn`, and `Settings`. Today those map to `/home`, `/focus` (with `/goals` alias), `/radar`, `/library`, `/learn`, and `/settings`. Journal is a persistent shortcut, and advanced pages remain available without dominating the default experience.

The FastAPI surface now boots a single canonical user-state schema from `src/user_state_store.py`. `src/web/user_store.py` is a compatibility wrapper only, so fresh startup must initialize conversation, attachment, onboarding, usage, and user-secret tables through the shared store module.

## Key Modules

- `src/web/app.py`
- `src/user_state_store.py`
- `src/web/user_store.py`
- `src/web/routes/onboarding.py`
- `src/web/routes/recommendations.py`
- `src/web/services/journal_entries.py`
- `web/src/components/Sidebar.tsx`
- `web/src/app/page.tsx`
- `web/src/app/(dashboard)/home/page.tsx`
- `web/src/app/(dashboard)/focus/page.tsx`
- `web/src/app/(dashboard)/goals/page.tsx`
- `web/src/app/(dashboard)/radar/page.tsx`
- `web/src/app/(dashboard)/library/page.tsx`
- `web/src/app/(dashboard)/learn/page.tsx`
- `web/src/app/(dashboard)/settings/page.tsx`

## Interfaces

- Public root route: `/`
- Primary app routes: `/home`, `/focus`, `/goals`, `/radar`, `/library`, `/learn`, `/settings`
- Shortcut route: `/journal`
- Secondary deep-link routes: `/advisor`, `/intel`, `/projects`
- Page-view tracking includes the simplified paths
- Startup must initialize the canonical user-state DB before any chat or onboarding traffic
- Conversation persistence includes attachment rows in `conversation_message_attachments`
- Shared journal-entry validation for goal-linked flows lives in `src/web/services/journal_entries.py`

## Simplified Product Notes

- Home is the default landing page after onboarding.
- The sidebar should teach the product through the six jobs, not through internal subsystem names.
- Journal is intentionally one tap away without being a top-level nav item.
- Onboarding sessions are still process-local in-memory state, but same-user requests are serialized with per-user async locks and forced finalization always clears the session.

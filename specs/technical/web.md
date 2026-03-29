# Web

**Status:** Updated for the simplified product model

## Overview

The web app presents four primary product surfaces: `Home`, `Radar`, `Learn`, and `Journal`. `Goals` and `Research` remain available as contextual secondary workspaces that users reach from those primary surfaces instead of from the main navigation. Today those map to `/home`, `/radar`, `/learn`, `/journal`, `/goals` (with `/focus` alias), `/research` (with `/library` alias), and `/settings`.

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
- `web/src/app/(dashboard)/research/page.tsx`
- `web/src/components/research/ResearchWorkspace.tsx`
- `web/src/app/(dashboard)/learn/page.tsx`
- `web/src/app/(dashboard)/settings/page.tsx`

## Interfaces

- Public root route: `/`
- Primary app routes: `/home`, `/radar`, `/learn`, `/journal`, `/settings`
- Secondary workspace routes: `/goals`, `/research`
- Legacy alias routes: `/focus`, `/library`
- Secondary deep-link routes: `/advisor`, `/intel`, `/projects`
- Page-view tracking includes the simplified paths
- Startup must initialize the canonical user-state DB before any chat or onboarding traffic
- Conversation persistence includes attachment rows in `conversation_message_attachments`
- Shared journal-entry validation for goal-linked flows lives in `src/web/services/journal_entries.py`

## Simplified Product Notes

- Home is the default landing page after onboarding.
- The sidebar should teach the product through the four primary surfaces plus `Settings`, not through internal subsystem names.
- Goals and Research should stay accessible through contextual links from Home, Radar, Journal, onboarding, and guided flows rather than as first-class sidebar destinations.
- Onboarding, help, and page-view tracking should mirror the same information architecture.
- Research and Settings should prefer progressive disclosure over always-open advanced forms and control panels.
- Onboarding sessions are still process-local in-memory state, but same-user requests are serialized with per-user async locks and forced finalization always clears the session.

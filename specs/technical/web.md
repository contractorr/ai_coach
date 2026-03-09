# Web

**Status:** Updated for the simplified product model

## Overview

The web app now presents five primary destinations: `/`, `/focus`, `/radar`, `/library`, and `/settings`. Journal is a persistent shortcut, and advanced pages remain available without dominating the default experience.

## Key Modules

- `web/src/components/Sidebar.tsx`
- `web/src/app/(dashboard)/page.tsx`
- `web/src/app/(dashboard)/focus/page.tsx`
- `web/src/app/(dashboard)/radar/page.tsx`
- `web/src/app/(dashboard)/library/page.tsx`
- `web/src/app/(dashboard)/settings/page.tsx`

## Interfaces

- Primary routes: `/`, `/focus`, `/radar`, `/library`, `/settings`
- Shortcut route: `/journal`
- Secondary deep-link routes: `/advisor`, `/intel`, `/projects`
- Page-view tracking includes the new simplified paths

## Simplified Product Notes

- Home is the default landing page after onboarding.
- The sidebar should teach the product through the five jobs, not through internal subsystem names.
- Journal is intentionally one tap away without being a top-level nav item.

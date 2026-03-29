# Landing Page

**Status:** Implemented

## Overview

The landing page is a server-rendered public marketing surface at `/` for
unauthenticated visitors. Authenticated visitors hitting `/` are redirected to
`/home`. The implementation keeps the public message aligned with the current
product story: StewardMe is a personal intelligence steward that helps the user
know what matters next.

## Dependencies

**Depends on:** `web` (auth, layout, design system, metadata)
**Depended on by:** nothing

## Components

### Root route

**File:** `web/src/app/page.tsx`

#### Behavior

- exports page-level metadata for the public landing page
- reads auth state via `auth()`
- redirects authenticated users to `/home`
- renders `<Landing />` for unauthenticated users

#### Metadata

```typescript
export const metadata: Metadata = {
  title: "StewardMe - Know what matters next",
  description:
    "StewardMe turns your notes, goals, and live signals into a clear next step.",
};
```

The route also exports matching Open Graph and Twitter metadata.

### Shared layout metadata

**File:** `web/src/app/layout.tsx`

The root layout provides the broader default description:

`Your personal intelligence steward for focus, monitoring, learning, and reflection.`

That metadata remains the fallback for non-landing routes.

### Landing component

**File:** `web/src/components/landing.tsx`

Pure presentational server component. No client state, no data fetching, no
API dependency.

#### Section order

1. Hero
2. Pillars
3. Source icons
4. Feature grid
5. Comparison table
6. Developer section
7. Footer CTA

#### Hero

- icon: `Brain`
- headline: `Know what matters next`
- body: `StewardMe watches your world, remembers your context, and helps you decide what to do next.`
- badges: `Open source`, `Self-hostable`
- CTAs: `Get started` -> `/login`, `View GitHub` -> repo

#### Pillars

Backed by a `PILLARS` array:

- `Capture your context`
- `Monitor what changed`
- `Decide your next move`

Each pillar renders an icon, title, and short explanation.

#### Source icons

Backed by `SOURCE_ICONS`:

- Hacker News
- GitHub
- arXiv
- Reddit
- RSS

This section is visual proof of monitoring scope only; it has no interactions.

#### Feature grid

Imports `FEATURES` from `web/src/lib/features.ts`.

Current titles:

- `Radar`
- `Guidance`
- `Goals`
- `Guide Library`

#### Comparison table

Backed by `COMPARISON_ROWS` with eight rows:

- Grounded in your context
- Helps you decide next steps
- Scans live sources for you
- Your data stays local
- Structured learning
- Self-hosted
- Multi-provider LLM
- Open source

Competitor columns render `-`. StewardMe renders a `Check` icon plus detail
text. The table uses horizontal overflow for mobile.

#### Developer section

- icon: `Code2`
- heading: `Open source and easy to extend`
- tech stack pills from `TECH_STACK`
- GitHub links for `Good first issues` and `Contributing guide`

#### Footer

- primary CTA: `Get started free`
- secondary CTA: `Explore the code`
- links: Privacy Policy, Terms of Service, GitHub

### Shared features constant

**File:** `web/src/lib/features.ts`

Exports a single source of truth for login and landing-page feature copy.

```typescript
export const FEATURES: Feature[] = [
  { title: "Radar", ... },
  { title: "Guidance", ... },
  { title: "Goals", ... },
  { title: "Guide Library", ... },
];
```

## Invariants

- The landing page must remain server-rendered.
- Authenticated users should never stay on the public landing page.
- The landing and login pages should share the same feature taxonomy.
- Public messaging should stay aligned with the app labels `Goals`, `Research`,
  and `Learn`.
- CTA links on the public page should route to `/login`.

## Cross-Cutting Concerns

### Routing

- `/` is public for unauthenticated users.
- `/home` is the post-auth app destination.
- The dashboard lives under the `(dashboard)` route group and is not rendered
  for anonymous traffic.

### Auth and rendering

Using `auth()` in the root route makes the route dynamic. That is acceptable
because the page is lightweight and still server-rendered.

### Design-system usage

The landing page uses existing design-system primitives and Lucide icons:

- `Badge`
- `Button`
- semantic colors from the shared theme

## Test Expectations

- Unauthenticated fetch of `/` returns 200 and includes the hero headline.
- Authenticated fetch of `/` redirects to `/home`.
- Feature grid content matches `web/src/lib/features.ts`.
- Comparison table renders 8 rows.
- CTA links point to `/login` or GitHub as intended.
- Page content is visible with JavaScript disabled.
- Mobile layout preserves readable stacking and horizontal table scroll.

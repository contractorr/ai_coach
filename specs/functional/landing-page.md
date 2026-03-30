---
id: landing-page
category: tracked_feature
status: stable
technical_specs:
- specs/technical/landing-page.md
- specs/technical/web.md
foundations:
- specs/foundations/design-system.md
- specs/foundations/ux-guidelines.md
last_reviewed: '2026-03-30'
---

# Landing Page

**Status:** Draft
**Author:** -
**Date:** 2026-03-29

## Problem

Unauthenticated visitors need a clear public product story before they are asked
to authenticate. The landing page should explain StewardMe as a personal
intelligence steward with one simple promise: know what matters next.

## Users

First-time visitors arriving from search, social links, direct shares, or
developer communities. Secondary: returning users who want a lightweight page
that explains the product before sending someone to log in.

## Desired Behavior

### Page structure

A public page at `/` for unauthenticated visitors. Authenticated users hitting
`/` should still be redirected into the app at `/home`.

The page has seven sections in vertical scroll order:

### 1. Hero

1. Short tagline: `Know what matters next`.
2. One-sentence expansion: `StewardMe watches your world, remembers your
   context, and helps you decide what to do next.`
3. Two badges linking to GitHub: `Open source` and `Self-hostable`.
4. Primary CTA: `Get started` -> `/login`.
5. Secondary CTA: `View GitHub` -> repo link.

### 2. Pillars

1. Three supporting cards shown in a responsive grid:
   - `Capture your context`
   - `Monitor what changed`
   - `Decide your next move`
2. Each card has an icon, short title, and one-line explanation.

### 3. Source logos

1. A row of recognizable icons for the sources StewardMe watches: Hacker News,
   GitHub, arXiv, Reddit, RSS.
2. Label: `Watches the sources you care about`.
3. No interactivity; this is a trust and scope signal.

### 4. Feature grid

1. Reuse the existing 4-feature grid from `/login`.
2. Feature names are `Radar`, `Guidance`, `Goals`, and `Guide Library`.
3. Display in a 2x2 grid on desktop and a single column on mobile.

### 5. Why StewardMe?

1. A comparison table contrasting StewardMe with ChatGPT/Copilot and Notion AI.
2. The table renders 8 axes:
   - Grounded in your context
   - Helps you decide next steps
   - Scans live sources
   - Your data stays local
   - Structured learning
   - Self-hosted
   - Multi-provider LLM
   - Open source
3. Competitors show `-`; StewardMe shows a checkmark plus short detail text.
4. Section label above the table: `Why StewardMe?`
5. Table scrolls horizontally on mobile.

### 6. Built for developers

1. Icon: `Code2` in a primary-colored circle.
2. Heading: `Open source and easy to extend`.
3. Body: `RAG pipeline backed by Python + FastAPI, Next.js frontend, ChromaDB
   embeddings, SQLite intel storage. Add a scraper in under 50 lines.`
4. Tech stack pills: Python, FastAPI, Next.js, TypeScript, ChromaDB, SQLite,
   Tailwind CSS.
5. Two outline CTAs: `Good first issues` and `Contributing guide`.

### 7. Footer CTA + links

1. Repeat CTA: `Get started free` -> `/login`.
2. Secondary CTA: `Explore the code` -> repo link.
3. Links: Privacy Policy, Terms of Service, GitHub.

### Navigation behavior

- Unauthenticated visitors hitting `/` see the landing page.
- Authenticated visitors hitting `/` are redirected to `/home`.
- The `/login` page remains the lightweight auth surface for returning users.
- Landing-page CTA buttons link to `/login`.

## Acceptance Criteria

- [ ] Unauthenticated visitors to `/` see the landing page, not a redirect to
      `/login`.
- [ ] Authenticated visitors to `/` are redirected to `/home`.
- [ ] Hero section displays the tagline `Know what matters next`.
- [ ] Hero copy explains the product in one sentence.
- [ ] `Open source` and `Self-hostable` badges are visible and link to GitHub.
- [ ] Primary CTA navigates to `/login`.
- [ ] Pillar section displays `Capture your context`, `Monitor what changed`,
      and `Decide your next move`.
- [ ] Source logos section shows at least 5 recognizable source icons.
- [ ] Feature grid matches the existing `/login` feature tiles.
- [ ] Comparison table renders 8 rows with StewardMe-only checkmarks and mobile
      horizontal scroll.
- [ ] `Built for developers` renders tech stack pills and two GitHub CTAs.
- [ ] Footer repeats the CTA and includes Privacy, Terms, and GitHub links.
- [ ] Page is fully responsive and server-rendered without requiring client
      JavaScript for initial content.
- [ ] OG metadata on `/` is populated for sharing.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Authenticated user navigates to `/` | Redirects to `/home` |
| User clicks `Get started` while already logged in but the session expired | Redirected to `/login`, then back to `/home` after auth |
| JavaScript disabled | Page content is visible and CTA links still work |
| Slow connection | Source logos load as lightweight SVG or icon components |
| User shares the root URL on social media | OG card shows title and description |
| Search engine crawls `/` | Finds semantic HTML instead of an auth redirect |

## Out of Scope

- Pricing section
- Demo video or interactive tour
- Testimonials or social proof beyond open-source positioning
- Blog or changelog section
- Analytics experiments or A/B testing
- Dark/light mode toggle specific to the landing page

## Resolved Decisions

- The landing-page promise is `Know what matters next`.
- The supporting narrative is `StewardMe watches your world, remembers your
  context, and helps you decide what to do next.`
- The shared feature grid uses `Radar`, `Guidance`, `Goals`, and
  `Guide Library`.

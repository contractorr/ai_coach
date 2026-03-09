# Landing Page

**Status:** Draft
**Author:** —
**Date:** 2026-03-09

## Problem

Unauthenticated visitors to stewardme.ai are immediately redirected to `/login`, which is a login form with a brief tagline and 4 feature tiles. There is no pre-auth marketing page — no SEO-friendly content, no clear value proposition for first-time visitors, and no reason for someone arriving from a search result or shared link to understand the product before being asked to authenticate. The login page serves returning users well but fails as a top-of-funnel conversion surface.

## Users

First-time visitors arriving from search, social links, Product Hunt, HN Show posts, or direct URL sharing. Secondary: returning users who want to share a link that explains the product.

## Desired Behavior

### Page structure

A new public page at `/` for unauthenticated visitors, separate from the existing `/login` page. Authenticated users hitting `/` still see the dashboard home as today.

The page has five sections in vertical scroll order:

### 1. Hero

1. Short tagline (7 words max) — the one-line value proposition.
2. One-sentence expansion beneath it (the current tagline works here: "AI steward that scans the world, learns from your journal, and tells you what matters next").
3. Two pills/badges: "Open source" and "Self-hostable" — linking to the GitHub repo.
4. Primary CTA button: "Get started" → navigates to `/login`.
5. Secondary CTA: "View on GitHub" → links to the repo.

### 2. Source logos

1. A row of recognizable logos/icons for the data sources StewardMe scans: Hacker News, GitHub, arXiv, Reddit, RSS.
2. Label above or below: "Scans the sources you care about".
3. No interactivity — purely a trust/scope signal.

### 3. How it works

1. Three-step horizontal sequence (stacks vertical on mobile):
   - **Step 1 — "Sign up"**: "Connect with GitHub or Google. No credit card."
   - **Step 2 — "Tell it what matters"**: "Add topics, goals, or paste your first journal entry."
   - **Step 3 — "Get briefed"**: "Your steward surfaces what matters and tells you what to do next."
2. Each step has a number, short title, and one-line description.

### 4. Feature grid

1. Reuse the existing 4-feature grid from `/login` (Intelligence Radar, AI Steward, Goal Tracking, Journal) — same icons, same copy.
2. Displayed in a 2x2 grid on desktop, single column on mobile.

### 5. Footer CTA + links

1. Repeat CTA: "Get started free" → `/login`.
2. Links: Privacy Policy, Terms of Service, GitHub.

### Navigation behavior

- Unauthenticated visitors hitting `/` see this landing page.
- Authenticated visitors hitting `/` see the dashboard home (no change).
- The `/login` page remains unchanged — returning users bookmark or navigate to `/login` directly.
- The landing page CTA buttons link to `/login`.

## Acceptance Criteria

- [ ] Unauthenticated visitors to `/` see the landing page, not a redirect to `/login`.
- [ ] Authenticated visitors to `/` see the dashboard home (existing behavior preserved).
- [ ] Hero section displays a tagline of 7 words or fewer.
- [ ] "Open source" and "Self-hostable" badges are visible and link to GitHub.
- [ ] Primary CTA ("Get started") navigates to `/login`.
- [ ] Source logos section shows at least 5 recognizable data source icons.
- [ ] "How it works" section displays 3 steps.
- [ ] Feature grid matches the existing `/login` feature tiles (same icons, same copy).
- [ ] Footer repeats the CTA and links to Privacy, Terms, and GitHub.
- [ ] Page is fully responsive: hero stacks, steps go vertical, features go single-column on mobile.
- [ ] Page loads without JavaScript for SEO (server-rendered, no `"use client"` for the main content).
- [ ] OG metadata on `/` is populated for social sharing (title, description, image).
- [ ] Page follows the design system: semantic color roles, Geist font, shadcn primitives, calm-clarity-first principle.
- [ ] No authentication state is required to render the page — fully public.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Authenticated user navigates to `/` | Sees dashboard home, not the landing page |
| User clicks "Get started" while already logged in (edge: session expired mid-page) | Redirected to `/login`, then back to `/` (dashboard) after auth |
| JavaScript disabled | Page content is visible (SSR); CTA links still work as standard `<a>` tags |
| Slow connection | Source logos load as lightweight SVGs or inline icons, not external images |
| User shares stewardme.ai link on social media | OG card shows title, description, and image |
| Search engine crawls `/` | Finds semantic HTML with headings, paragraphs, links — not a redirect |

## Out of Scope

- Pricing section or tier comparison (no paid tier exists)
- Demo video or interactive product tour
- Testimonials or social proof beyond the open-source badge
- Blog or changelog section
- Analytics tracking on the landing page (can be added later)
- A/B testing of taglines or CTAs
- Dark/light mode toggle on the landing page (inherits system preference via existing theme)

## Open Questions

- What should the hero tagline be? Candidates: "Know what matters next", "Your personal intelligence briefing", "An AI steward for what matters". Needs a decision.
- Should the GitHub repo link point to the main repo or a specific landing/README?
- Should source logos be actual brand logos (trademark concerns) or stylized icons representing each source?

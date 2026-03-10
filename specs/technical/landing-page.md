# Landing Page

## Overview

A server-rendered public marketing page at `/` for unauthenticated visitors. Requires changes to the Next.js middleware (to allow unauthenticated access to `/`), a new page component, and conditional rendering based on auth state. No backend changes.

## Dependencies

**Depends on:** `web` (middleware, auth, layout, design system)
**Depended on by:** nothing — leaf page, no downstream consumers

---

## Components

### Middleware update

**File:** `web/src/middleware.ts`
**Status:** Draft

#### Behavior

Currently, the middleware matcher excludes `login`, `privacy`, `terms`, `api/auth`, and static assets. All other routes — including `/` — require auth and redirect to `/login`.

Change: the root path `/` must be excluded from the auth matcher so unauthenticated visitors can access it. The dashboard home at `/` (for authenticated users) already lives inside the `(dashboard)` route group and will continue to work — the landing page component handles the auth fork.

Updated matcher:
```typescript
export const config = {
  matcher: [
    "/((?!login|privacy|terms|api/auth|_next/static|_next/image|favicon\\.ico|$).*)",
  ],
};
```

The `|$` addition matches the empty path (root `/`), excluding it from auth protection.

**Alternative approach:** Keep the matcher as-is but add a root-level `page.tsx` outside the `(dashboard)` group that checks session and either renders the landing page or the dashboard. This avoids middleware changes but requires a client-side or server-side auth check in the component.

#### Invariants

- Authenticated users hitting `/` must still see the dashboard home.
- All other protected routes remain protected.
- `/login` behavior is unchanged.

---

### LandingPage component

**File:** `web/src/app/page.tsx` (new root-level page, outside `(dashboard)` group)
**Status:** Draft

#### Behavior

Server component. Checks auth state via `auth()` from `@/lib/auth`. If authenticated, renders the existing dashboard home (or redirects to `/(dashboard)`). If unauthenticated, renders the landing page.

```typescript
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import Landing from "@/components/landing";

export default async function RootPage() {
  const session = await auth();
  if (session?.user) {
    redirect("/home");  // or render DashboardHome inline
  }
  return <Landing />;
}
```

**Note:** This requires the existing dashboard home to be accessible at a sub-route (e.g., `/home`) or imported as a component. If the current `(dashboard)/page.tsx` cannot be reused, the simplest approach is to keep `(dashboard)/page.tsx` as-is and have the new root `page.tsx` redirect authenticated users into the dashboard route group.

#### Inputs / Outputs

No props. Auth state is read server-side. Renders static HTML for unauthenticated visitors (no client interactivity needed for the landing content).

---

### Landing component

**File:** `web/src/components/landing.tsx`
**Status:** Draft

#### Behavior

Pure presentational component. No `"use client"` — fully server-rendered for SEO. Composed of seven sections:

**Section 1: Hero**
```tsx
<section className="flex flex-col items-center text-center pt-[15vh] pb-16 px-4">
  <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
    {TAGLINE}
  </h1>
  <p className="mt-4 max-w-md text-lg text-muted-foreground">
    AI steward that scans the world, learns from your journal,
    and guides you through what's next.
  </p>
  <div className="mt-4 flex gap-2">
    <Badge variant="secondary">Open source</Badge>
    <Badge variant="secondary">Self-hostable</Badge>
  </div>
  <div className="mt-8 flex gap-3">
    <Button asChild><Link href="/login">Get started</Link></Button>
    <Button variant="outline" asChild>
      <a href={GITHUB_URL}>View on GitHub</a>
    </Button>
  </div>
</section>
```

**Section 2: Source logos**
```tsx
<section className="flex flex-col items-center py-12 px-4">
  <p className="text-sm text-muted-foreground mb-6">
    Scans the sources you care about
  </p>
  <div className="flex gap-8 items-center">
    {SOURCE_ICONS.map(({ name, icon: Icon }) => (
      <div key={name} className="flex flex-col items-center gap-1">
        <Icon className="h-6 w-6 text-muted-foreground" />
        <span className="text-xs text-muted-foreground">{name}</span>
      </div>
    ))}
  </div>
</section>
```

Icons: use Lucide icons where available (Github for GitHub, Newspaper for HN, BookOpen for arXiv, MessageCircle for Reddit, Rss for RSS). These are approximations — no trademark concerns with Lucide icons.

**Section 3: How it works**
```tsx
const STEPS = [
  { number: "1", title: "Sign up", description: "Connect with GitHub or Google. No credit card." },
  { number: "2", title: "Tell it what matters", description: "Add topics, goals, or paste your first journal entry." },
  { number: "3", title: "Get briefed", description: "Your steward cross-references live intel with your journal and goals — then tells you what to do next and why." },
];
```

Layout: `flex flex-col sm:flex-row` for responsive stacking. Each step is a card-like block with the number in a rounded circle, title bold, description muted.

**Section 4: Why StewardMe? (comparison table)**

Data-driven comparison table. Renders between "How it works" and Feature grid.

```tsx
const COMPARISON_ROWS = [
  { axis: "Your data stays local", detail: "SQLite + markdown files" },
  { axis: "Scans live sources for you", detail: "10 async scrapers (HN, arXiv, GitHub, Reddit, RSS, ...)" },
  { axis: "Learns from your feedback", detail: "Per-category scoring adjusts over time" },
  { axis: "Self-hosted", detail: "Docker one-liner or bare metal" },
  { axis: "Multi-provider LLM", detail: "Claude, OpenAI, Gemini (auto-detect)" },
  { axis: "Open source", detail: "AGPL-3.0" },
];
```

Layout: `overflow-x-auto rounded-xl border bg-card` wrapper for mobile horizontal scroll. Table uses `<table>` with `min-w-[600px]`. Column headers: (axis) | ChatGPT / Copilot | Notion AI | StewardMe. Competitors show "—" in muted text. StewardMe column shows `<Check />` icon + detail text.

Section label above table: `text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground` — "WHY STEWARDME?"

**Section 5: Feature grid**

Reuses the same `features` array from `/login/page.tsx`. Extract into a shared constant at `web/src/lib/features.ts` to avoid duplication:

```typescript
// web/src/lib/features.ts
export const FEATURES = [
  { icon: Newspaper, title: "Intelligence Radar", description: "..." },
  { icon: Sparkles, title: "AI Steward", description: "..." },
  { icon: Target, title: "Goal Tracking", description: "..." },
  { icon: BookOpen, title: "Journal", description: "..." },
];
```

Both `landing.tsx` and `login/page.tsx` import from this shared file.

**Section 6: Built for developers**

Contributor-focused section between Feature grid and Footer.

```tsx
const TECH_STACK = ["Python", "FastAPI", "Next.js", "TypeScript", "ChromaDB", "SQLite", "Tailwind CSS"];
```

Layout: centered column. `Code2` icon in `h-14 w-14 rounded-full bg-primary/10` circle (same style as hero Brain icon). Heading: "Open source and easy to extend". Body paragraph: "RAG pipeline backed by Python + FastAPI, Next.js frontend, ChromaDB embeddings, SQLite intel storage. Add a scraper in under 50 lines."

Tech pills: `Badge variant="secondary"` for each item, flex-wrap on mobile.

Two outline CTAs:
- "Good first issues" → `{GITHUB_URL}/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22`
- "Contributing guide" → `{GITHUB_URL}/blob/main/CONTRIBUTING.md`

New Lucide imports needed: `Check`, `Code2`.

**Section 7: Footer CTA + links**
```tsx
<section className="flex flex-col items-center py-16 px-4">
  <div className="flex gap-3">
    <Button asChild size="lg">
      <Link href="/login">Get started free</Link>
    </Button>
    <Button variant="outline" size="lg" asChild>
      <a href={GITHUB_URL}>
        <Github className="mr-2 h-4 w-4" />
        Explore the code
      </a>
    </Button>
  </div>
  <div className="mt-6 flex gap-3 text-xs text-muted-foreground">
    <Link href="/privacy">Privacy Policy</Link>
    <span>&middot;</span>
    <Link href="/terms">Terms of Service</Link>
    <span>&middot;</span>
    <a href={GITHUB_URL}>GitHub</a>
  </div>
</section>
```

#### Configuration

| Key | Value | Source |
|-----|-------|--------|
| `TAGLINE` | TBD (7 words max) | Hardcoded in component |
| `GITHUB_URL` | `https://github.com/contractorr/stewardme` | Hardcoded constant |
| `SOURCE_ICONS` | HN, GitHub, arXiv, Reddit, RSS | Hardcoded array |

#### Invariants

- No `"use client"` directive — fully server-rendered.
- No fetch calls or API dependencies — static content only.
- Uses only existing shadcn primitives (Button, Badge, Link) and Lucide icons.
- Follows design system: Geist font, semantic color roles, responsive spacing.

#### Error Handling

No error paths — static page with no data fetching.

---

### Metadata

**File:** `web/src/app/page.tsx` (or `web/src/app/layout.tsx` if shared)
**Status:** Draft

#### Behavior

Export page-level metadata for the landing page:

```typescript
export const metadata: Metadata = {
  title: "StewardMe — Know what matters next",
  description: "Open-source AI steward that scans HN, GitHub, arXiv, Reddit & RSS, learns from your journal, and guides you through what's next.",
  openGraph: {
    title: "StewardMe — Know what matters next",
    description: "Open-source AI steward that scans HN, GitHub, arXiv, Reddit & RSS, learns from your journal, and guides you through what's next.",
    url: "https://stewardme.ai",
    siteName: "StewardMe",
    images: [{ url: "/og-image.jpg", width: 1024, height: 1024 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "StewardMe — Know what matters next",
    description: "Open-source AI steward that scans HN, GitHub, arXiv, Reddit & RSS, learns from your journal, and guides you through what's next.",
    images: ["/og-image.jpg"],
  },
};
```

This overrides the root layout metadata for the `/` route specifically. The layout metadata remains as the default for all other pages.

**Note:** `metadata` export and `auth()` cannot coexist in the same server component if `auth()` causes dynamic rendering. If this conflicts, move the auth check to middleware or use `generateMetadata()` instead.

---

### Shared features constant

**File:** `web/src/lib/features.ts` (new)
**Status:** Draft

#### Behavior

Extracts the feature list currently hardcoded in `login/page.tsx` into a shared module. Both the landing page and login page import from here.

```typescript
import { BookOpen, Newspaper, Sparkles, Target } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
}

export const FEATURES: Feature[] = [
  {
    icon: Newspaper,
    title: "Intelligence Radar",
    description: "Scans HN, GitHub, arXiv, Reddit & RSS — surfaces what matters, skips the noise.",
  },
  {
    icon: Sparkles,
    title: "AI Steward",
    description: "Personalized guidance grounded in your journal, goals, and real-time intel.",
  },
  {
    icon: Target,
    title: "Goal Tracking",
    description: "Track objectives with milestones. Get nudged when priorities should shift.",
  },
  {
    icon: BookOpen,
    title: "Journal",
    description: "Capture reflections and decisions. Every entry sharpens your steward's guidance.",
  },
];
```

#### Invariants

- Single source of truth for feature copy — any update here propagates to both pages.
- No runtime logic — pure data export.

---

## Cross-Cutting Concerns

**Routing conflict:** The current `(dashboard)/page.tsx` serves as `/` for authenticated users via the route group. Adding a root-level `page.tsx` outside the group will take precedence. Two resolution strategies:

1. **Root page with auth fork (recommended):** New `app/page.tsx` checks auth, renders landing or redirects to `/home`. Move the existing dashboard page to `app/(dashboard)/home/page.tsx` and update sidebar nav links from `/` to `/home`. This is a small refactor but clean.

2. **Middleware-only approach:** Add `/` to the landing page matcher. In middleware, check auth: if authenticated, rewrite to `/(dashboard)`; if not, let the root `page.tsx` (landing) render. More complex middleware logic but avoids moving the dashboard page.

**SSR + auth:** `auth()` is an async server function from NextAuth v5. Calling it in the root page component causes dynamic rendering, which means no static generation. This is acceptable — the page is lightweight and renders fast. If static generation is desired later, the auth check can move to middleware with a cookie-based redirect.

**Shared layout:** The landing page should NOT use the dashboard sidebar layout. Ensure the root `page.tsx` is outside the `(dashboard)` layout group so it gets the root layout only (Geist font + SessionProvider + Toaster).

## Test Expectations

- Unauthenticated fetch of `/` returns 200 with landing page HTML containing the tagline, feature grid, and CTA links.
- Authenticated fetch of `/` redirects to dashboard or renders dashboard content.
- All CTA links point to `/login`.
- Page HTML includes OG meta tags for social sharing.
- Feature grid content matches `FEATURES` constant.
- "Why StewardMe?" comparison table renders 6 rows with check icons for StewardMe column.
- "Built for developers" section renders tech stack pills and two GitHub CTAs.
- No client-side JavaScript required for initial content render (check with JS disabled).
- Mobile viewport renders all sections in single-column layout; comparison table scrolls horizontally.
- Mock: auth session (authenticated vs unauthenticated).

# Test Harness Summary Report

3 personas, 13 total sessions analyzed (founder: 4, junior_dev: 3, switcher: 2).
Scope: founder all sessions; junior_dev sessions 3-5; switcher sessions 3-4 only.

---

## Common Bugs Across Personas

### Display name ignores onboarding name (all 3 personas, every session)
Dashboard greets with account name ("Junior Dev", "Switcher", "Founder") instead of the name entered during onboarding ("Alex", "Marcus", "Priya"). Sidebar also shows account name. Affects perceived personalization on every login.

### Sidebar nav links outside viewport (all 3 personas, intermittent)
At 1280x900, sidebar links (Journal, Goals, Conversations, Radar) are in DOM but positioned off-screen. Click fails with "element is outside of the viewport". Workaround: direct URL navigation. Reported in founder sessions 1-2, "fixed" in session 3, broken again in session 4. Present in all junior_dev and switcher sessions tested. Likely a CSS/layout flake tied to sidebar state or animation.

### Advisor auto-scrolls to bottom, clipping opening paragraph (junior_dev s3-s5, switcher s3-s4, founder s4)
When advisor response renders, chat scrolls to show the bottom. User must manually scroll up to read from the beginning. Consistent across all personas in later sessions.

### Feed tab shows only github_trending items (founder s4, switcher s3-s4)
Trending clusters pull from reddit, RSS, HN, deep_research — but Feed tab only shows GitHub repos. Users browsing Feed miss all non-GitHub content. Either Feed has a source filter bug or only shows the latest scrape batch.

### Feed tab empty state while Trending has data (founder s1-s2, junior_dev s2, switcher s2)
Feed showed "Your radar is quiet / I haven't scanned anything yet" while Trending had 212 items. Resolved by session 3 for all personas — likely a transient data/timing issue. Messaging was misleading regardless.

### No RAG retrieval from journal entries for founder persona (all 4 sessions)
Founder advisor never referenced journal entry content despite highly relevant entries (fundraising numbers, competitor analysis, hiring loss details, board prep). Junior_dev and switcher advisors pulled profile data well but also showed limited direct journal quoting. This is the single biggest personalization gap.

---

## UX Patterns

### Onboarding
- Profile interview is a standout feature — conversational, adaptive questions, auto-generates goals and RSS feeds. When it works, it's the strongest first-run experience.
- Founder hit 429 rate limit on lite mode in sessions 1-2, blocking profile completion for 2 full sessions. Everything downstream (Brief, personalization, goals) was gated on this. Critical path failure.
- Onboarding blank page bug (founder s3): `/onboarding` rendered empty `<main>` on client-side navigation. Hard refresh fixed it. Did not reproduce in s4.

### Journal
- Entry creation flow is reliable across all personas and sessions — dialog, save, toast, card appearance.
- Card grid layout scales well (tested up to 9 entries).
- Journal dialog stayed open after save (switcher s2-s3), then auto-closed in s4 — fixed.
- Card previews show raw markdown `##` headers instead of stripped/rendered text (founder all sessions).
- "1 entries" grammar bug (founder s1).

### Advisor
- Response quality is consistently high even on Haiku/lite mode.
- Well-structured formatting: section headers, bullet points, nested lists, bold emphasis.
- CTA cards ("What would you like to do next?") appeared from s3 onward — good engagement hook that improved in contextual relevance across sessions.
- Response times: 40-60s in lite mode. "Thinking..." shown but no progress bar.

### Radar
- Trending clusters with "For you" tags and match reasons (skill:data, goal:product) are the best personalization signal in the app.
- Source health indicator (23/23 → 29/29 over time) is reassuring.
- "Load more (N remaining)" pagination landed in s3 — better than s1's full dump.
- Feed tab now has "For you" tags on individual items (junior_dev s5: `docker/compose` and `microsoft/typescript-go` tagged with match reasons like `skill:typescript, tech:go`). Previously only Trending clusters had personalization tags — this is an improvement observed in later sessions.

### Goals
- Auto-creation from onboarding is impressive and specific.
- Page is static after creation — no progress bars, milestones, or links between journal entries and goals.
- Check-in timestamps don't update from advisor conversations (junior_dev s4: "Last check-in: 2d ago" despite advisor discussing goal progress that session).

---

## Advisor Quality Trends

### junior_dev (sessions 3-5)

| Dimension | S3 (Go vs React) | S4 (First ship) | S5 (Weekly summary) |
|---|---|---|---|
| Relevance | 5/5 — Go prioritization tied to goals | 5/5 — Recognized win, pivoted to momentum | 5/5 — Genuine weekly summary with dated timeline |
| Actionability | 5/5 — Week-by-week plan with resources | 5/5 — Per-goal next steps, two tiers | 4/5 — Reflective (appropriate for the ask), less prescriptive |
| Personalization | 5/5 — All 3 goals by name, learning budget, imposter syndrome reframe | 5/5 — Connected ship to goals, suggested backend optimization on shipped feature | 5/5 — Strongest yet: dated entries, quoted journal language verbatim, all goals mapped |
| Past context | 5/5 — Cross-session synthesis, "React Reality Check" novel insight | 5/5 — Implicit s2→s4 narrative arc (PR destruction → approval) | 5/5 — Synthesized all 5 sessions into coherent weekly narrative with emotional trajectory |
| Tone | 5/5 — Strategic, emoji headers for scannability | 5/5 — Celebratory but forward-looking | 5/5 — Evidence-based affirmation, "spiraling upward" reframe |

junior_dev shows the strongest adaptation arc. Advisor evolved from general career guidance (s1) → specific pain response (s2) → strategic prioritization with novel insights (s3) → momentum coaching connecting prior pain to current win (s4) → reflective weekly synthesis weaving all sessions into a narrative (s5). Cross-session coherence is excellent. Session 5's weekly summary is the best single response across all personas — it demonstrated genuine longitudinal analysis rather than single-entry retrieval.

### switcher (sessions 3-4)

| Dimension | S3 (Course→production) | S4 (Finance leverage) |
|---|---|---|
| Relevance | 5/5 — Direct answer to course-vs-production gap | 5/5 — Addressed all 4 numbered questions |
| Actionability | 5/5 — Week-by-week with code snippets | 5/5 — Resume-ready narrative bullets |
| Personalization | 4/5 — SEC pipeline, 12hr/wk, but no journal/conversation refs | 4/5 — Same: question-driven not context-retrieved |
| Past context | 3/5 — Didn't reference journal or prior advice | 3/5 — No cross-session synthesis |
| Tone | 4/5 — Technical, appropriate for tactical question | 5/5 — Direct with honest pushback maintained |

switcher advisor is consistently strong on individual responses but weaker on cross-session memory. Each conversation feels somewhat standalone. The advisor doesn't say "building on what we discussed last time" or "I notice you keep returning to imposter syndrome." Profile data is used well; journal entries and prior conversations are not.

### founder (sessions 1-4)

| Dimension | S1 | S2 | S3 | S4 |
|---|---|---|---|---|
| Relevance | 4/5 | 5/5 | 5/5 | 5/5 |
| Actionability | 4/5 | 5/5 | 5/5 | 5/5 |
| Personalization | 2/5 | 2/5 | 4/5 | 3.5/5 |
| Past context | N/A | 1/5 | 2/5 | 2/5 |
| Tone | 4/5 | 4/5 | 5/5 | 5/5 |

Founder shows a sharp inflection at session 3 when onboarding finally completed — profile data unlocked real personalization. But journal RAG retrieval never worked: the board-prep journal entry (s4) contained specific names, numbers, board composition, and deck structure that the advisor completely ignored. Across all 4 sessions, the advisor treated every question as standalone with no cross-conversation continuity. This is the weakest persona for adaptation despite having the richest journal content.

### Cross-persona patterns
- **Profile-driven personalization works well** — once onboarding completes, advisor references goals, constraints, and context from the profile interview.
- **Journal RAG retrieval varies by persona** — founder never saw journal content in advisor responses (P0 bug). junior_dev shows strong journal retrieval from s2 onward, peaking in s5 with verbatim quotes from multiple entries and a dated timeline. switcher saw none explicitly. The discrepancy suggests RAG retrieval may work for some profiles/configurations but not others.
- **Cross-conversation continuity varies** — junior_dev's advisor demonstrated strong cross-session synthesis by s5 (weaving all 5 sessions into a narrative). Founder and switcher advisors showed no cross-conversation references. The difference may relate to profile completeness or journal embedding quality.
- **Response quality on Haiku is surprisingly strong** — structured, opinionated, actionable advice even on the lite model.

---

## Prioritized Issues

### P0 — Critical

1. **Journal entries not retrieved in advisor context (RAG failure)**
   Founder wrote 4 detailed journal entries with specific numbers, names, and action items. None were referenced by the advisor. This is the core value proposition of the product — RAG-augmented advice from personal context. If journal content doesn't flow into advisor responses, the journal is just a diary with no feedback loop.
   *Personas affected: founder (confirmed), switcher (likely), junior_dev (partial — profile data works, journal content unclear)*

2. **Cross-conversation continuity missing**
   Advisor treats each conversation independently. No "building on our last discussion" or "I notice a recurring theme." For a coaching product, session-over-session memory is table stakes.
   *All 3 personas, all sessions*

3. **Onboarding rate limit on lite mode (founder s1-s2)**
   Profile interview consumed the lite mode token budget, failing after 1-2 questions. This blocked profile completion for 2 full sessions, cascading into: no Brief access, no personalization, no goals. First-time lite-mode users would abandon.
   *Confirmed fixed by s3 but root cause unclear — could recur*

### P1 — High

4. **Display name mismatch**
   Every persona sees their account name instead of the name they entered in onboarding. Undermines the personal feel of the product on every single page load.
   *All 3 personas, every session*

5. **Sidebar nav links off-viewport**
   Users can't navigate via sidebar at 1280x900 (common viewport). Must use direct URLs. Intermittent — sometimes works, sometimes doesn't. Likely CSS flake.
   *All 3 personas, most sessions*

6. **Feed tab missing non-GitHub sources**
   Trending clusters surface reddit, RSS, HN, deep_research items. Feed tab only shows github_trending. Users who browse Feed instead of Trending miss most of the scraped content.
   *founder s4, switcher s3-s4*

### P2 — Medium

7. **Advisor response auto-scrolls past opening paragraph**
   Chat scrolls to bottom on render. User must scroll up to read the response from the beginning. Minor but happens every session.
   *All 3 personas, s3-s5*

8. **Goals page has no progress tracking**
   Goals are created from onboarding but then static — no progress bars, milestones, journal-to-goal linking, or advisor-conversation-based check-ins. junior_dev's "Own a feature end-to-end" goal stayed at "0/1 done" even after shipping a feature.
   *junior_dev s3-s4, founder s3-s4*

9. **Journal card previews show raw markdown**
   `##` headers render as plaintext in card previews instead of being stripped or rendered.
   *founder all sessions*

10. **Feed tab items personalization inconsistent**
    Feed items now show "For you" tags with match reasons for junior_dev (s5: `microsoft/typescript-go` matched `skill:typescript, tech:go`). However, switcher (Python-focused) saw mostly Go/Rust repos with no "For you" tags in s3-s4. Personalization may depend on profile completeness or matching algorithm coverage.
    *switcher s3-s4 (no tags), junior_dev s5 (tags present)*

### P3 — Low

11. **"1 entries" grammar** — founder s1
12. **Onboarding blank page on client-side navigation** — founder s3, did not reproduce in s4
13. **Hydration mismatch warnings (Radix UI tab IDs)** — junior_dev s2, founder s2, resolved by s3
14. **Transient 404 on `/advisor/conversations/{id}`** — all personas s1-s2, resolved by s3
15. **Advisor response time (40-60s) with minimal progress indicator** — all personas, lite mode

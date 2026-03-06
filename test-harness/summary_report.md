# Test Harness Summary Report

> **Baseline reset: 2026-03-06** — Issue #57 (Phases 1-4) shipped. Chat-first home, goal milestones, insights, suggestions, and concept consolidation all landed. Past observations may no longer apply. Only observations from today onward are tracked below.

3 personas, sessions analyzed post-reset.

---

## Known Architecture Changes (Issue #57)

These changes affect what the test harness should exercise and observe:

- **Chat-first home** replaces dashboard Brief — greeting cached per-user, served instantly, regenerated every 4hrs or on data events
- **Goals now have milestones** — learning paths merged into goals with `type` field, auto-generated milestones via advisor
- **Insights** = merged signals + patterns + heartbeat output — TTL-based 14-day expiry, no dismiss UI
- **Suggestions** = merged recommendations + daily brief items — unified `/api/suggestions` endpoint
- **Predictions removed** — zero persona interaction in prior testing
- **Heartbeat = invisible infra** — no user-facing routes, output feeds Insights
- **SkillGapAnalyzer** → `advice_type="skill_gap"` in advisor

## New Endpoints to Exercise

| Endpoint | Purpose |
|----------|---------|
| `GET /api/greeting` | Cached personalized greeting (chat-first home) |
| `GET /api/suggestions` | Unified suggestions (brief items + recommendations) |
| `GET /api/insights` | Active insights (merged signals/patterns/heartbeat) |
| `POST /api/goals/{path}/milestones` | Add milestone to goal |
| `POST /api/goals/{path}/milestones/complete` | Complete a milestone |
| `POST /api/advisor/ask` with `advice_type=skill_gap` | Skill gap analysis via advisor |

---

## Common Bugs Across Personas

*(To be populated from today's test runs)*

---

## UX Patterns

### Onboarding
*(Carry forward: profile interview is a standout feature. Rate limit issue was fixed. Monitor for regressions.)*

### Chat-first Home
- **Greeting cache**: Does greeting load instantly (<100ms) when cached?
- **Staleness refresh**: Does greeting update after journal entry / goal check-in / scrape?
- **Static fallback**: On first visit, does fallback show while greeting generates?
- **Quick-capture**: Does chat input work as journal entry mode?

### Journal
*(Carry forward: entry creation is reliable. Monitor markdown preview rendering.)*

### Advisor
- **skill_gap advice type**: Does `--type skill_gap` produce meaningful analysis?
- **Cross-session context**: Still the biggest quality gap from prior testing — monitor.
- **Journal RAG retrieval**: Was inconsistent across personas — re-evaluate.

### Radar
*(Carry forward: trending clusters and "For you" tags work. Feed tab source filtering was a prior bug.)*

### Goals & Milestones
- **Milestone creation**: Does "break this down for me" generate sensible milestones?
- **Progress tracking**: Do milestone completions update the progress bar?
- **Goal types**: Are `type` fields (career, learning, project) set correctly?
- **Migration**: If old learning paths existed, were they migrated to goal milestones?

### Insights & Suggestions
- **Insights list**: Does `GET /api/insights` return active insights?
- **TTL expiry**: Do insights disappear after 14 days?
- **Suggestions ranking**: Are brief items ranked first, followed by remaining recommendations?
- **Dedup**: Are recommendations in the brief excluded from the remaining suggestions list?

---

## Advisor Quality Trends

*(To be populated from today's test runs)*

---

## Prioritized Issues

*(To be populated from today's test runs. Prior P0-P3 issues may no longer apply — re-evaluate each.)*

### Carry-forward candidates (re-test before confirming)

- **P0: Journal entries not retrieved in advisor context (RAG failure)** — Was the biggest issue. Re-test with current code.
- **P0: Cross-conversation continuity missing** — Memory and threads are now stable features. Re-test.
- **P1: Display name mismatch** — Check if onboarding name now shows correctly.
- **P1: Sidebar nav links off-viewport** — CSS flake. Re-test at 1280x900.
- **P2: Advisor auto-scrolls past opening paragraph** — Still relevant if chat UI unchanged.

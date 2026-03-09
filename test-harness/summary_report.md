# Test Harness Summary Report

> **Baseline reset: 2026-03-09** — Issue #67. Full wipe + 14-beat fresh run with LLM council. Prior Mar 1-6 observations cleared.

3 personas × 14 beats across 2 weeks.

---

## Architecture Changes Since Last Run

| Change | Impact on Testing |
|--------|-------------------|
| **LLM Council** | Per-user keys in Settings > LLM Providers (Fernet-encrypted). Response prefixed with "Council-assisted answer" when active. |
| **Settings key management** | Keys stored as user secrets, not env vars. Must be entered per-persona during run. |
| **Focus page** | Unified view: goals + milestones + memory facts + threads + insights |
| **Library** (`/library`) | Content collection / bookmarks. New sidebar route. |
| **Sidebar redesign** | Routes: Home `/`, Focus `/focus`, Radar `/radar`, Library `/library`, Settings `/settings`, Journal `/journal` |
| **Memory & Threads** | Stable features. Facts shown on Focus, threads detect recurring themes. |
| **Projects** | Route exists at `/projects` but not in sidebar. Discoverable via direct nav. |

---

## Carry-Forward Bugs (re-test to confirm)

| # | Bug | Prior Priority | Status |
|---|-----|---------------|--------|
| 1 | Display name mismatch — onboarding name doesn't show in UI | P1 | Re-test |
| 2 | Advisor auto-scrolls past opening paragraph | P1 | Re-test |
| 3 | Stale goal timestamps after check-in | P2 | Re-test |

---

## Week 1 Observations (Beats 1-7)

*(To be populated during run)*

### Common Bugs

### UX Patterns

### Advisor Quality

---

## Week 2 Observations (Beats 8-14)

*(To be populated during run)*

### Council

### Memory & Threads

### Milestones

### Insights & Suggestions

### Projects & Library

---

## Prioritized Issues

*(To be populated from run findings)*

---

## Advisor Quality Trends

*(To be populated — compare single-model vs council responses)*

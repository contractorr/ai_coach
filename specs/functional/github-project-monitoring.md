# GitHub Project Monitoring

**Status:** Draft
**Author:** Raj
**Date:** 2026-03-11

## Problem

Users set goals like "build X" or "ship feature Y" but the product has no visibility into their actual coding activity. Progress tracking relies entirely on self-reported journal entries and manual check-ins. Meanwhile, the product already authenticates via GitHub OAuth and scrapes *external* GitHub repos — but never looks at the user's own projects. Connecting repo health to goals, signals, and advice would give the system objective execution evidence without requiring the user to manually log every commit.

## Users

Users who write code and track goals related to building, shipping, or maintaining software projects. Most valuable for users with active repositories linked to current goals.

## Desired Behavior

### GitHub identity collection

1. During onboarding or from Settings, user can connect their GitHub account for project monitoring.
2. Since GitHub OAuth is already used for auth, the system can extract the user's GitHub username from the existing auth token.
3. If the user authenticated via Google instead of GitHub, they can manually enter a GitHub username in Settings.
4. The user can disconnect GitHub monitoring at any time without affecting their login.

### Repository discovery

1. After connecting, the system fetches the user's personal public repositories.
2. User sees a list of their repos and can select which ones to monitor.
3. User can also manually add a repo URL for repos they contribute to but don't own (e.g. org repos).
4. Selected repos appear in Settings under a "Monitored repos" section.
5. User can add or remove monitored repos at any time.
6. Only personal repos are discovered automatically. Org repos require manual URL entry.

### Private repository access

1. By default, only public repos are visible.
2. User can opt in to private repo access via a fine-grained personal access token or minimal read-only OAuth scope.
3. The product explains clearly what data is read and that no write operations are performed.
4. Private repo data is stored with the same per-user isolation as other user data.
5. The requested scope is the narrowest available for read-only repo metadata, commit history, issues, PRs, and CI status. No code-content or write scopes are requested.

### Activity monitoring

1. The system polls monitored repos on an adaptive schedule:
   - Active repos (commits within last 7 days): polled daily
   - Moderate repos (commits within last 30 days): polled every 3 days
   - Stale repos (no commits in 30+ days): polled weekly
2. Monitored signals per repo include:
   - commit frequency and recency
   - open issue and PR counts
   - recent releases or tags
   - contributor activity (for repos the user owns)
   - CI status when available via GitHub Actions
3. The system does not modify any repository data. All access is read-only.
4. Repo health snapshots are persisted to SQLite for trend analysis. Snapshots older than 90 days are pruned automatically.

### Goal linkage

1. User can link a monitored repo to an existing goal from Goals or Settings.
2. When a repo is linked to a goal, repo activity feeds into that goal's progress signals.
3. A goal linked to a repo can show:
   - last commit date
   - commit velocity trend (increasing, steady, declining) derived from stored snapshots
   - open issue count and direction
   - whether CI is passing
4. If a linked repo goes stale (no commits beyond a configurable threshold, default 14 days), a goal staleness signal fires.

### Signals and Radar integration

1. Repo activity generates signals that feed into the existing signal pipeline:
   - **Repo stale:** no commits in threshold window for a monitored repo
   - **Velocity change:** significant increase or decrease in commit frequency vs 30-day baseline
   - **Issue spike:** unusual increase in open issues
   - **CI failure:** latest CI run failing on default branch
2. These signals appear in Radar alongside intel and thread signals.
3. Repo signals carry the same severity scoring (1-10) as other signal types.

### Advisor context

1. When the user asks the advisor a question related to a linked goal or project, repo health data is included as retrieval context.
2. The advisor can reference concrete repo state: "Your repo hasn't had commits in 3 weeks" or "CI is currently failing on main."
3. Repo context is injected only when relevant to the query, not on every advisor call.

### Outcome harvester integration

1. Repo activity serves as objective execution evidence for the outcome harvester.
2. A recommendation that led to commits on a linked repo within the review window counts as positive evidence.
3. A goal with a linked repo that shows sustained commit activity counts as progress, even without a manual check-in.

## Acceptance Criteria

- [ ] User can connect GitHub username via OAuth extraction or manual entry in Settings.
- [ ] User can browse and select personal public repos to monitor.
- [ ] User can manually add org or third-party repo URLs.
- [ ] User can opt in to private repo access with a fine-grained read-only scope.
- [ ] Selected repos are polled on an adaptive schedule based on activity level.
- [ ] Monitored data includes commit recency, issue/PR counts, releases, and CI status.
- [ ] All GitHub API access is read-only. No write operations are ever performed.
- [ ] Repo health snapshots are persisted to SQLite; snapshots older than 90 days are pruned.
- [ ] User can link a monitored repo to a goal.
- [ ] Linked repo activity feeds into goal progress signals with trend data from stored snapshots.
- [ ] Repo staleness, velocity change, issue spike, and CI failure generate signals.
- [ ] Repo signals appear in Radar with severity scoring.
- [ ] Advisor can reference repo health data when answering goal-related questions.
- [ ] Repo activity counts as execution evidence in the outcome harvester.
- [ ] User can disconnect monitoring or remove individual repos at any time.
- [ ] Private repo data respects per-user isolation.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User authenticated via Google, not GitHub | Manual GitHub username entry available in Settings |
| Repo is archived or deleted after being monitored | Monitoring silently stops; stale signal fires once, then repo marked inactive |
| User has 200+ repos | Repo list is paginated; user selects which to monitor rather than monitoring all |
| GitHub API rate limit hit | Polling backs off; stale data served until next successful poll; no error shown to user |
| Repo linked to goal but user removes monitoring | Goal loses repo signals; reverts to manual-only progress tracking |
| User contributes to an org repo they don't own | Manual repo URL entry supports this; monitoring limited to public data unless user has granted private access |
| Private repo token revoked externally | System detects auth failure, falls back to public-only, notifies user in Settings |
| Repo has no commits ever | Shown as inactive; no misleading velocity or staleness signals |
| Multiple repos linked to same goal | Signals aggregated; any repo going stale triggers the signal |
| Snapshot DB grows large | 90-day pruning keeps storage bounded |

## Out of Scope

- Creating, forking, or modifying repositories (all access is strictly read-only)
- Issue or PR management from within the app
- Code review or diff display
- Dependency vulnerability scanning
- GitHub Actions workflow management
- Monitoring repos the user has no access to
- Cross-user repo comparisons
- GitHub Enterprise Server (cloud only in v1)
- Webhook-based real-time updates (polling only in v1)
- Automatic org repo discovery (manual URL entry only)

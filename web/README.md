# StewardMe Web App

The `web` workspace contains the Next.js dashboard for StewardMe.

## Stack

- Next.js App Router
- React 19
- Tailwind CSS 4
- `next-auth` for session handling
- Shared FastAPI backend on `http://localhost:8000`

## Local development

```bash
cd web
npm install
npm run dev
```

The frontend expects the API server to be running separately from the repo root:

```bash
uvicorn src.web.app:app --reload --port 8000
```

Open `http://localhost:3000` and sign in.

## Main dashboard areas

- `/` - Home for capture, ask, greeting/return brief, and top next steps
- `/focus` - Focus for goals, weekly plan, and best next moves
- `/radar` - Radar for signals, threads, dossiers, saved follow-ups, and tracked topics
- `/library` - Library for documents, reports, and archived dossiers
- `/settings` - Profile, keys, tracked topics, memory, and advanced controls
- `/journal` - Deeper Journal workspace reached from the sidebar shortcut
- Secondary deep links: `/advisor`, `/intel`, `/projects`

## Focus workspace

The Focus page is optimized for active work rather than archival browsing:

- `Focus` shows active and paused goals by default
- `Needs check-in` isolates stale goals that need attention
- `Archived` keeps completed and abandoned goals available without crowding current work
- Recommendation cards support inline tracking, feedback, and follow-through
- Search filters the currently loaded goal list by title

## Journal shortcut

The Journal page remains designed for quick retrieval after capture:

- Local search narrows loaded entries by title, preview text, tags, and content
- Type filters help separate daily, project, goal, and reflection entries
- Tag chips provide a fast way to pivot into a theme
- Empty states stay actionable and offer a one-click reset
- The composer clarifies that titles are optional and can be auto-generated

## Radar workspace

Radar is designed for triage, not just passive reading:

- `For you` highlights the strongest cross-source signals
- Tabs keep threads, dossiers, saved follow-ups, and tracked topics in one monitoring workspace
- Scan can be triggered on demand from the page header
- Saved items remain available as a lightweight follow-up queue
- The advanced `/intel` page still exists for deeper filtering when needed

## Advanced opportunities page

The advanced opportunities page supports deeper browsing when the lightweight Focus surface is not enough:

- `Issue matches` surfaces ranked GitHub opportunities from recent Radar data
- Filters let users widen or narrow the recent-day window and result count
- `Project ideas` stay available without becoming a primary navigation concept
- Empty and error states keep the page useful even when data or model access is thin

## Library workspace

The Library page is the durable reference workspace:

- Browse documents, reports, and archived dossiers
- Organize reports with simple collection labels
- Refresh a report in place instead of creating duplicates
- Edit, archive, and restore saved report artifacts
- Jump back to Journal when source notes are more useful than durable outputs

## Quality checks

```bash
npm run lint
npm run build
```

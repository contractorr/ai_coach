# Technical Spec Index

This index summarizes each file in `specs/technical/` after the v2 simplification pass.

| Filename | Purpose | Key system components referenced | Key user flows described |
| --- | --- | --- | --- |
| `action-plans.md` | Focus action tracking and weekly planning | Recommendations route, Focus page | Read weekly plan, update tracked action |
| `advisor.md` | Conversational engine behind Home Ask mode | Advisor route, Home page, full chat page | Ask question, stream answer, continue long thread |
| `architecture.md` | Five-job product architecture | Dashboard pages, route modules, ranking/storage services | Land on Home, move through Focus/Radar/Library/Settings |
| `assumption-watchlist.md` | Settings-driven tracked topics and assumptions | Assumptions route, intel route, suggestions | Add tracked topic, surface relevant signal |
| `attach-to-ask-bridge.md` | Same-turn attachment flow for Ask mode | Attachment hook, advisor route, Library storage | Attach, ask, retrieve later |
| `cli.md` | Operator/developer command surface | CLI entry points, config, ingestion jobs | Run maintenance, trigger ingestion, debug locally |
| `company-movement-pipeline.md` | Company-signal ingestion feeding Radar | Intel route, suggestions route, ranking pipeline | Scan and surface company changes |
| `dossier-escalation-engine.md` | Escalation logic from signal to dossier | Dossier routes, research routes, Radar page | Accept/snooze/dismiss escalation |
| `extraction-receipt.md` | Capture follow-up and extraction summary | Journal capture, threads, memory | Capture note, inspect extracted follow-up |
| `goal-learning-merge.md` | Merge goal context into prioritization | Goals, recommendations, ranking services | Read goal context, generate focused next move |
| `greeting-cache.md` | Home greeting and return-brief caching | Greeting route, Home page | Load greeting, show return brief, refresh stale cache |
| `hiring-activity-pipeline.md` | Hiring-signal ingestion for Radar | Intel route, suggestions route, ranking | Scan and rank hiring signals |
| `intelligence.md` | Unified intelligence layer for Radar/Home | Intel route, suggestions route, Radar page | Run scan, review feed, save follow-up |
| `journal.md` | Journal APIs for Home and deep Journal page | Journal route, Home page, Journal page | Quick capture, browse history, edit entry |
| `library.md` | Durable reports, docs, archived dossiers | Library route, research route, Library page | Browse reference items, refresh report |
| `llm.md` | Shared model/provider configuration | Settings route, advisor, onboarding, research | Set key, test model access, run generation |
| `mcp.md` | Advanced integration surface | MCP server, tool adapters, auth helpers | Call tools from integration clients |
| `memory.md` | Durable memory storage and management | Memory route, memory services, Settings page | List facts, show stats, delete fact |
| `outcome-harvester.md` | Background learning from outcomes | Journal/goal events, ranking services | Harvest signal, improve future prioritization |
| `profile.md` | User profile data and editing | Profile/user routes, Settings, onboarding | Read/update profile, personalize app |
| `recurring-thread-inbox.md` | Thread APIs now consumed by Radar | Threads route, Radar page | Review thread, convert to goal/research/dossier |
| `regulatory-change-pipeline.md` | Regulatory-signal ingestion for Radar | Intel route, suggestions route, ranking | Scan and prioritize regulatory changes |
| `research-dossiers.md` | Active/archived dossier lifecycle | Research route, escalation route, Radar, Library | Refresh dossier, archive to Library |
| `research.md` | Research orchestration and outputs | Research services, research route, Library | Start research, produce report, persist output |
| `since-you-were-away-why-now.md` | Timing/prioritization evidence | Greeting route, suggestions, why-now chips | Re-orient returning user, explain priority |
| `TEMPLATE.md` | Template for future technical docs | Module paths, interfaces, product mapping | Describe module, boundaries, consumers |
| `web.md` | Frontend route map and navigation model | Sidebar, dashboard pages, pageview tracking | Navigate five workspaces and deep links |

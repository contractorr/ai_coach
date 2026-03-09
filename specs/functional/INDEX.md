# Functional Spec Index

This index summarizes each file in `specs/functional/` after the v2 simplification pass.

| Filename | Purpose | Key system components referenced | Key user flows described |
| --- | --- | --- | --- |
| `action-plans.md` | Tracked execution steps inside Focus | Focus page, recommendations, weekly plan | Review plan, track action, complete work |
| `analytics-admin.md` | Product/admin analytics for the simplified app | Admin stats, pageview tracking, dashboard paths | Inspect usage, compare adoption, review health |
| `ask-advice.md` | One Home composer for capture and questions | Home page, advisor API, chat attachments | Ask question, capture note, upgrade note to advice |
| `assumption-watchlist.md` | Advanced tracked-topic configuration | Settings page, intel routes, suggestions | Add topic, review resulting signals, edit/delete topic |
| `attach-to-ask-bridge.md` | Same-turn PDF attachments in Ask mode | Attachment picker, advisor stream, Library storage | Attach file, ask grounded question, revisit stored file |
| `company-movement-pipeline.md` | Company/competitor monitoring signals | Intel feed, suggestions, Radar | Scan, review signal, save or escalate |
| `deep-research.md` | Advanced research started from live work | Research routes, Radar dossiers, Library | Start research, refresh work, archive outputs |
| `dossier-escalation-engine.md` | Promote repeated signals into dossiers | Escalation routes, Radar, research | Accept, snooze, dismiss, start dossier |
| `entity-extraction.md` | Extract entities and relationships from intel items | Intel pipeline, entity store, Radar tags, advisor retrieval | Background extraction, entity-filtered Radar, relational advisor queries |
| `extraction-receipt.md` | Lightweight follow-up after capture | Journal capture, threads, memory | Save note, review receipt, jump to next action |
| `goal-tracking.md` | Simplified Focus workspace | Goals routes, recommendations, Focus page | Review next moves, create goal, log progress |
| `hiring-activity-pipeline.md` | Hiring-signal ingestion for Radar | Intel feed, ranking, Radar | Scan, review, save or escalate |
| `hybrid-retrieval.md` | Multi-mode retrieval with sub-question decomposition and entity traversal | RAGRetriever, IntelSearch, EntityStore, advisor tools | Auto-mode selection, decomposed queries, entity-aware context |
| `intelligence-feed.md` | Unified Radar monitoring experience | Radar page, intel routes, suggestions | Review `For you`, manage saved items, run scan |
| `journaling.md` | Fast capture plus deeper Journal workspace | Home quick capture, Journal page, sidebar shortcut | Capture quickly, open Journal, search and filter history |
| `landing-page.md` | Public marketing page for unauthenticated visitors | Root route, login, hero, feature grid, source logos | View landing, click CTA, share link |
| `library-reports.md` | Durable reference workspace | Library page, reports API, archived dossiers | Filter by type, open report, review archived dossier |
| `memory-threads.md` | Settings memory + Radar threads | Memory routes, thread routes, Settings, Radar | Inspect memory, review thread, convert thread into action |
| `outcome-harvester.md` | Background learning from outcomes | Journal/goal signals, ranking systems | Capture progress, harvest outcomes, improve later suggestions |
| `profile-onboarding.md` | Short onboarding to Home | Onboarding page, settings, user profile | Save name, choose access mode, pick feed topics |
| `projects-opportunities.md` | Opportunity handling folded into Focus | Focus page, advanced projects page, projects route | Review opportunity, open deep dive, track promising idea |
| `recommendations.md` | Prioritized next steps across Home and Focus | Suggestions route, recommendations route, Home, Focus | Review next steps, track recommendation, give feedback |
| `recurring-thread-inbox.md` | Threads tab in Radar | Thread routes, Radar page, journal-derived clustering | Review thread, create goal/research/dossier, dismiss |
| `regulatory-change-pipeline.md` | Regulatory monitoring inside Radar | Intel feed, suggestions, Radar | Scan, review change, save or escalate |
| `research-dossiers.md` | Active-versus-archived dossier lifecycle | Research routes, dossier routes, Radar, Library | Start dossier, refresh dossier, archive dossier |
| `settings-account.md` | Account, keys, tracked topics, memory | Settings page, settings route, intel route, memory route | Manage account, track topics, delete memory facts |
| `since-you-were-away-why-now.md` | Return brief plus why-now context | Greeting route, suggestions, Home cards | Return after absence, inspect priorities, open related workspace |
| `TEMPLATE.md` | Template for future functional docs | Functional spec structure, workspace placement | Define problem, map workspace, list flows |
| `archive/v2-simplified-product.md` | Accepted simplification decision record | Home, Focus, Radar, Library, Settings, onboarding | Explain five jobs, define simplified flows, list acceptance criteria |

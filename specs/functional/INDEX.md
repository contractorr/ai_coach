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
| `library-reports.md` | Durable reference workspace + semantic search | Library page, reports API, archived dossiers, embeddings | Filter by type, open report, concept search via hybrid retrieval |
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
| `infra-hardening.md` | Expanded secret redaction, MCP error cleanup, thread-safe observability with cost tracking | Logging, MCP server, observability | Redact secrets, track token costs, remove tracebacks |
| `unified-tool-registry.md` | Single tool registry with availability checks for MCP + advisor | Tool registry, MCP server, agentic orchestrator | Register tool, check availability, execute with uniform errors |
| `agentic-context-compression.md` | Token-aware context window management for agentic mode | Agentic orchestrator, context compressor, cheap_llm | Compress old turns, summarize evicted context, protect recent turns |
| `prompt-caching.md` | Anthropic prompt caching for Claude to reduce input token costs | Claude provider, agentic orchestrator | Cache system prompt, track cache hits, reduce costs |
| `ai-capabilities.md` | AI capabilities KB and capability horizon model | AI KB, capability model, 6 scrapers | Inject AI context into advisor, track capability trajectories |
| `conversation-storage.md` | Per-user chat persistence | Conversation store, advisor chat | Create, continue, delete conversations |
| `engagement-scoring.md` | Event-based engagement tracking feeding dynamic weighting | Engagement routes, recommendation weighting | Record feedback, view stats, influence ranking |
| `goal-intel-matching.md` | Match intel items to active goals | Goal-intel matcher, ChromaDB, LLM evaluator | Surface goal-relevant intel, filter false positives |
| `heartbeat-hybrid.md` | Heartbeat LLM evaluation triggered by Home load | Heartbeat service, Home page | Trigger eval, surface stale data |
| `nudge-engine.md` | CLI behavioral nudges for profile/goals/journal | Nudge engine, CLI | Show profile staleness, stale goals, journal streak |
| `signals.md` | Proactive signal detection across all data sources | Signal detectors, signal store, insight store | Detect goal staleness, topic emergence, journal gaps |
| `suggestions-engine.md` | Unified suggestion endpoint merging all subsystems | Suggestions route, briefing data, WhyNowReasoner | Review prioritized next steps with timing context |
| `trending-radar.md` | Cross-source topic trend detection | Trending radar, intel items, NLP/LLM modes | Surface emerging topics from intelligence feeds |
| `usage-cost-estimation.md` | Per-user LLM cost estimation on settings page | Settings page, usage events | View cost breakdown by model |
| `configurable-embeddings.md` | Pluggable embedding provider (Gemini/OpenAI/hash) | Embedding factory, journal/intel/memory search | Auto-detect provider, configure model, rebuild after switch |
| `x-list-scraper.md` | X/Twitter List intelligence source | Intel scraper, Radar feed, config | Configure list, fetch tweets, review in Radar |
| `TEMPLATE.md` | Template for future functional docs | Functional spec structure, workspace placement | Define problem, map workspace, list flows |

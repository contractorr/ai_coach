# Specs

Primary spec system: functional specs define *what*, technical specs define *how*. Shared foundation docs capture cross-cutting UX and design rules used by both.

## Workflow

1. PM writes a functional spec in `functional/` using the template
2. Claude reads the functional spec + relevant technical specs + codebase
3. Claude produces/updates a technical spec in `technical/` + implementation plan
4. Review both → implement

For quick navigation from a feature name to specs, code, tests, and validation
commands, use `specs/manifest.yaml`.

## Structure

```
specs/
  functional/        # What & why (PM-authored)
    TEMPLATE.md
    {feature}.md
    archive/         # Accepted decision records and retired proposals
  technical/         # How (Claude-generated, developer-reviewed)
    TEMPLATE.md
    {module}.md
  foundations/       # Shared UX/design rules that span features/modules
    design-system.md
    ux-guidelines.md
```

## Functional Specs (features)

| Spec | Status | Covers |
|------|--------|--------|
| [journaling](functional/journaling.md) | Stable | CRUD, search, templates, trends, threads, sentiment |
| [ask-advice](functional/ask-advice.md) | Stable | RAG Q&A, agentic mode, advice types, chat surfaces, document-grounded answers, council-assisted answers, greeting, insights, suggestions |
| [llm-council](functional/llm-council.md) | Draft | Multi-provider API keys, council-assisted answers, synthesis of agreement/disagreement, path-forward guidance |
| [intelligence-feed](functional/intelligence-feed.md) | Stable | 15 scrapers, dedup, trending radar, scheduling |
| [recommendations](functional/recommendations.md) | Stable | Scoring, dedup, feedback loop, delivery |
| [action-plans](functional/action-plans.md) | Stable | Recommendation-to-execution workflow, weekly planning, goal linkage |
| [profile-onboarding](functional/profile-onboarding.md) | Stable | Interview flow, profile fields, staleness |
| [analytics-admin](functional/analytics-admin.md) | Stable | Lightweight usage analytics, page views, scraper health |
| [deep-research](functional/deep-research.md) | Experimental | Topic selection, web search, synthesis |
| [research-dossiers](functional/research-dossiers.md) | Experimental | Persistent research topics, timeline updates, advisor retrieval |
| [goal-tracking](functional/goal-tracking.md) | Experimental | Goals, milestones, check-ins |
| [projects-opportunities](functional/projects-opportunities.md) | Stable | Matched issues, project ideas, secondary workspace |
| [settings-account](functional/settings-account.md) | Stable | Multi-provider keys, council preferences, lite mode, watchlist, profile editing, account deletion |
| [memory-threads](functional/memory-threads.md) | Experimental | Persistent facts, recurring topic detection, document-derived memory |
| [library-reports](functional/library-reports.md) | Partially Implemented | Research workspace for durable AI-generated reports and uploaded PDFs, manual generation, document storage, refresh, collections |
| [curriculum](functional/curriculum.md) | Implemented | Learn workspace with guide library, chapter progress, reviews, and spaced repetition |
| [v2-simplified-product](functional/archive/v2-simplified-product.md) | Accepted (Archived decision) | Simplified information architecture, merged workflows, progressive disclosure across existing features |

## Technical Specs (modules)

| Spec | Covers |
|------|--------|
| [architecture](technical/architecture.md) | System topology, module boundaries, dependency graph, weak points |
| [advisor](technical/advisor.md) | AdvisorEngine, RAG retrieval, agentic orchestrator, prompts |
| [journal](technical/journal.md) | Storage, embeddings, search, FTS, threads, trends, sentiment |
| [intelligence](technical/intelligence.md) | Scrapers, IntelStorage, scheduler, dedup, trending radar |
| [profile](technical/profile.md) | UserProfile model, onboarding interview flow, profile storage and editing |
| [research](technical/research.md) | WebSearchClient, ResearchSynthesizer, DeepResearchAgent |
| [research-dossiers](technical/research-dossiers.md) | ResearchDossierStore, dossier update flow, cross-surface integrations |
| [action-plans](technical/action-plans.md) | Recommendation execution metadata, weekly plan assembly, goal-link validation, execution feedback |
| [memory](technical/memory.md) | FactStore, FactExtractor, ConflictResolver, MemoryPipeline |
| [llm](technical/llm.md) | Provider factory, Claude/OpenAI/Gemini adapters |
| [web](technical/web.md) | FastAPI app, JWT auth, route modules, canonical user-state storage, onboarding and attachment invariants |
| [library](technical/library.md) | ReportStore, Library routes, Research workspace MVP |
| [mcp](technical/mcp.md) | MCP server, bootstrap, 52 tools across 13 modules |
| [curriculum](technical/curriculum.md) | CurriculumScanner, CurriculumStore, SM-2, QuestionGenerator, 12 API endpoints |
| [cli](technical/cli.md) | Click commands, config validation, logging |

## Guidelines

- **Functional specs**: No code, no internal details. User-facing language only.
- **Technical specs**: Reference the functional spec they implement. Include component signatures, invariants, error paths.
- **Foundation docs**: Cross-cutting product and UI guidance. Use them to keep feature specs and implementations consistent.
- One functional spec per feature. One technical spec per module (may cover multiple features).
- Functional specs map to user-facing features; technical specs map to code modules. The mapping is many-to-many (e.g., journaling touches `journal`, `web`, `cli`, and `mcp` technical specs).

## Foundation Docs

| Doc | Covers |
|-----|--------|
| [design-system](foundations/design-system.md) | Tokens, component conventions, states, accessibility baseline |
| [ux-guidelines](foundations/ux-guidelines.md) | Page structure, actions, AI UX, feedback states, copy, responsiveness |

# Specs

Two-tier spec system: functional specs define *what*, technical specs define *how*.

## Workflow

1. PM writes a functional spec in `functional/` using the template
2. Claude reads the functional spec + relevant technical specs + codebase
3. Claude produces/updates a technical spec in `technical/` + implementation plan
4. Review both → implement

## Structure

```
specs/
  functional/        # What & why (PM-authored)
    TEMPLATE.md
    {feature}.md
  technical/         # How (Claude-generated, developer-reviewed)
    TEMPLATE.md
    {module}.md
```

## Functional Specs (features)

| Spec | Status | Covers |
|------|--------|--------|
| [journaling](functional/journaling.md) | Stable | CRUD, search, templates, trends, threads, sentiment |
| [ask-advice](functional/ask-advice.md) | Stable | RAG Q&A, agentic mode, advice types, greeting, insights, suggestions |
| [intelligence-feed](functional/intelligence-feed.md) | Stable | 15 scrapers, dedup, trending radar, scheduling |
| [recommendations](functional/recommendations.md) | Stable | Scoring, dedup, feedback loop, delivery |
| [profile-onboarding](functional/profile-onboarding.md) | Stable | Interview flow, profile fields, staleness |
| [deep-research](functional/deep-research.md) | Experimental | Topic selection, web search, synthesis |
| [goal-tracking](functional/goal-tracking.md) | Experimental | Goals, milestones, check-ins |
| [memory-threads](functional/memory-threads.md) | Experimental | Persistent facts, recurring topic detection |

## Technical Specs (modules)

| Spec | Covers |
|------|--------|
| [advisor](technical/advisor.md) | AdvisorEngine, RAG retrieval, agentic orchestrator, prompts |
| [journal](technical/journal.md) | Storage, embeddings, search, FTS, threads, trends, sentiment |
| [intelligence](technical/intelligence.md) | Scrapers, IntelStorage, scheduler, dedup, trending radar |
| [profile](technical/profile.md) | UserProfile model, ProfileInterviewer, storage |
| [research](technical/research.md) | WebSearchClient, ResearchSynthesizer, DeepResearchAgent |
| [memory](technical/memory.md) | FactStore, FactExtractor, ConflictResolver, MemoryPipeline |
| [llm](technical/llm.md) | Provider factory, Claude/OpenAI/Gemini adapters |
| [web](technical/web.md) | FastAPI app, JWT auth, route modules, user isolation |
| [mcp](technical/mcp.md) | MCP server, bootstrap, 37 tools across 12 modules |
| [cli](technical/cli.md) | Click commands, config validation, logging |

## Guidelines

- **Functional specs**: No code, no internal details. User-facing language only.
- **Technical specs**: Reference the functional spec they implement. Include component signatures, invariants, error paths.
- One functional spec per feature. One technical spec per module (may cover multiple features).
- Functional specs map to user-facing features; technical specs map to code modules. The mapping is many-to-many (e.g., journaling touches `journal`, `web`, `cli`, and `mcp` technical specs).

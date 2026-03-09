# Intelligence Feed

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-07

## Problem

Users need curated industry intelligence relevant to their interests without manually checking dozens of sources. The advisor also needs fresh external context to give timely advice.

## Users

All users. Power users configure custom RSS feeds and enable additional sources.

## Desired Behavior

### Automated scraping

1. System runs scrapers on a configurable schedule.
2. Each scraper normalizes items into a common format.
3. Items are deduplicated by URL and content hash before storage.
4. Semantic dedup can catch near-duplicates across sources when enabled.

Available sources include default Hacker News and RSS plus optional sources such as GitHub, arXiv, Reddit, Product Hunt, YC Jobs, Google Patents, AI capability trackers, events, GitHub Issues, Crunchbase, Google Trends, and Indeed Hiring Lab.

### Browsing intel

1. User lists recent intel items, optionally filtered by source or tags.
2. System returns items with title, source, summary, URL, publish date, and relevance indicators.
3. Watchlist-matched items are visibly labeled and can rank ahead of generic items.

### Web radar workspace

1. The web feed exposes quick client-side filters for `all`, `for_you`, `watchlist`, and `saved` items across the currently loaded result set.
2. The web feed surfaces lightweight counts so users can quickly see how much of the current feed is personalized or already saved.
3. Saving or annotating an intel item happens in-context from the feed.
4. Search and feed filters can be reset without leaving the page.

### Watchlists

1. User can create persistent watchlist items for companies, people, roles, sectors, technologies, geographies, events, and free-form themes.
2. Each watchlist item can store optional context: why it matters, priority, tags, goal linkage, time horizon, aliases, and preferred sources.
3. Watchlist items are available via web, CLI, and MCP.
4. Matching adds a plain-language explanation of why the item matters.
5. Watchlist matches can boost ranking in feed and search.

### Intel follow-up

1. User can save an intel item for later follow-up.
2. User can add or update a short note on a saved item.
3. Saved or annotated items persist across sessions for that user.

### Searching intel

1. User can search the intel corpus.
2. Keyword search is available through the current web route.
3. The intelligence module also contains semantic and hybrid ranking utilities that can be used by CLI, MCP, and retrieval-oriented consumers.

Current interface scope:
- Web `/api/intel/search` currently uses storage-backed search over the intel corpus.
- Semantic and hybrid ranking exist in the intelligence module, but the web route does not yet call that richer path directly.

### Trending topics

1. System detects cross-source topic convergence.
2. User can view trending topics with supporting items from each source.
3. Trending topics can be re-ranked by profile relevance in the web experience.

### Goal-intel matching

1. System matches intel items against active goals.
2. Matched items surface in heartbeat notifications and daily briefs.
3. Goal matching and watchlist matching coexist.

### Manual refresh

1. User can trigger an immediate scrape of all configured sources.
2. System reports items found, deduplicated, and saved.

Current interface scope:
- Web, CLI, and MCP currently expose whole-feed/manual scrape behavior.
- Source-specific manual refresh is not yet exposed.

## Acceptance Criteria

- [ ] Scheduled scrapes run automatically via `coach daemon`.
- [ ] Items are deduplicated by URL and content hash.
- [ ] Semantic dedup prevents near-identical items across different sources when enabled.
- [ ] User can browse and search intel via CLI, web, and MCP.
- [ ] The web radar feed supports quick filters for all, personalized, watchlist-matched, and saved items within the loaded result set.
- [ ] The web radar feed supports in-context note editing without leaving the page.
- [ ] User can CRUD watchlist items via CLI, web, and MCP.
- [ ] Intel items can be matched against watchlists and visibly labeled with a why-it-matters explanation.
- [ ] Matching watchlist items are ranked ahead of generic items when relevance is otherwise comparable.
- [ ] User can save or annotate intel for later follow-up.
- [ ] Trending radar detects topics appearing across multiple source families.
- [ ] User can manually trigger a scrape of all configured sources.
- [ ] Failed scrapes for one source do not block the rest.
- [ ] RSS feeds are configurable.
- [ ] Rate-limiting infrastructure exists, but scraper-wide rate limiting is not yet fully wired.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Source is down or returns error | Log error, skip source, continue with others |
| RSS feed returns malformed XML | Skip feed, log warning |
| Duplicate item from different sources | Deduplicated; only one canonical copy remains primary |
| No sources enabled | No scraping occurs; intel store stays empty |
| Very large RSS feed | Feed is capped rather than exhausting the run |
| No API key for paid source | Source is skipped or falls back where possible |
| Watchlist item duplicates an existing one | Upsert or merge by normalized label |
| Intel item matches multiple watchlist items | Show the strongest matches first |
| User saves an intel item without a note | Save succeeds with an empty note |
| Feed filter has no matching items | Web UI shows a contextual empty state and reset actions |
| Search returns no results | Web UI preserves query context and offers a quick reset |
| User clears note and unsaves item | Follow-up entry is removed or treated as inactive |

## Out of Scope

- User-submitted manual intel URLs
- Push notifications for new intel
- Source-specific configuration beyond the supported settings model

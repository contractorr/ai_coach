**Problem**
The intelligence system is strong at broad industry scanning, but it is not yet bespoke enough to act like a personal chief of staff. Users can configure RSS and enabled sources, but the product does not let them define persistent watchlists for the specific people, companies, sectors, technologies, geographies, roles, events, or themes they care about most.

Today the app monitors the world broadly, while recommendations are meant to be highly personalized. That creates a gap between the raw external data being collected and the user-specific advice the system can provide.

Relevant spec references:
- `specs/functional/intelligence-feed.md`: power users can configure RSS feeds, but manual URL submission, bookmarking/annotations, and richer source-specific configuration are out of scope.
- `specs/functional/recommendations.md`: recommendations should feel like "things the system suggests I do," but the upstream intel is not yet centered on user-defined watch targets.

**Proposed solution**
Add user-defined watchlists that shape intelligence collection, ranking, and downstream recommendations.

Suggested behavior:
- Let users create tracked entities and themes such as companies, competitors, job titles, industries, technologies, public figures, places, conferences, and keywords.
- Allow each watch item to store optional metadata: why it matters, priority, tags, goal linkage, time horizon, and source preferences.
- Add a watchlist-aware ranking layer so matching intel is boosted above generic feed items.
- Surface a dedicated "Why this matters to you" explanation when an intel item matched a watchlist.
- Feed watchlist matches into insights, recommendations, and deep research topic selection.
- Support simple actions on intel: save, dismiss, annotate, and convert into a research topic or goal.

MVP acceptance criteria:
- Users can CRUD watchlist items via web, CLI, and MCP.
- Intel items can be matched against watchlists and visibly labeled.
- Matching watchlist items are ranked ahead of generic feed items.
- Recommendations and insights can cite watchlist evidence.
- Users can save or annotate matched intel for later follow-up.

**Alternatives considered**
- Rely only on custom RSS feeds. This is too source-centric and still does not capture the user's actual priorities.
- Infer all watch targets from the profile and journal automatically. Useful as a starting point, but users still need explicit control over what the system monitors.

**Context**
This is the fastest path to making the existing intelligence system feel bespoke without adding intrusive live integrations.

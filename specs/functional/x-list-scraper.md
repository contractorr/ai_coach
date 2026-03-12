# X List Scraper

**Status:** Draft
**Author:** Claude
**Date:** 2026-03-12

## Problem

Users curate X/Twitter Lists to follow domain experts and industry voices, but must manually check X to stay current. Adding an X List scraper lets users pipe their curated feeds into the intelligence system for automatic summarization alongside other sources.

## Users

Users who maintain X Lists for professional intelligence gathering.

## Desired Behavior

1. User configures their X Bearer Token and List ID in `config.yaml` under `sources.x_list`
2. The scraper fetches tweets from the specified List via X API v2
3. Tweets appear in the Radar feed alongside other intel sources, tagged with author names
4. Dedup works via URL uniqueness (tweet permalink) and content hash
5. The scraper respects X API free-tier rate limits (1 request per 15 minutes)

## Acceptance Criteria

- [ ] New `x_list` source type appears in intel items
- [ ] Tweets stored with author name in title, full text in summary, permalink as URL
- [ ] Opt-in only: disabled by default in config, requires bearer token + list ID
- [ ] Handles missing/invalid bearer token gracefully — logs warning, returns empty
- [ ] Handles rate limit (429) responses with backoff
- [ ] Tags each tweet with the author's username
- [ ] Published timestamp preserved from tweet `created_at`

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Bearer token invalid/expired | HTTP 401/403 → log warning, return empty list |
| List ID does not exist | HTTP 404 → log warning, return empty list |
| Tweet has no text (media-only) | Skip tweet |
| Rate limited (429) | Respect `Retry-After` header or back off 15 minutes |
| List has fewer tweets than `max_tweets` | Return all available |

## Out of Scope

- OAuth 2.0 user-context auth (app-only bearer token only)
- Multiple list support (single list per config; run multiple instances via RSS if needed)
- Tweet media/image handling
- Thread/reply expansion

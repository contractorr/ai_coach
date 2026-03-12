# X List Scraper

## Overview

Standard `BaseScraper` subclass fetching tweets from an X/Twitter List via API v2. Opt-in source requiring bearer token and list ID configuration.

## Dependencies

**Depends on:** `intelligence.scraper.BaseScraper`, `httpx`, `shared_types.IntelSource`
**Depended on by:** `intelligence.scheduler`

---

## Components

### XListScraper
**File:** `src/intelligence/sources/x_list.py`
**Status:** Experimental

#### Behavior
- Constructor: `(storage, bearer_token, list_id, max_tweets=100)`
- `source_name` → `IntelSource.X_LIST`
- `scrape()`:
  1. Validate bearer_token and list_id present; return empty if missing
  2. `GET https://api.twitter.com/2/lists/{list_id}/tweets` with params: `tweet.fields=text,created_at,author_id,public_metrics`, `expansions=author_id`, `user.fields=username`, `max_results=min(max_tweets, 100)`
  3. Build author lookup from `includes.users` (author_id → username)
  4. Map each tweet to `IntelItem(source="x_list", title="{username}: {text[:80]}", url="https://x.com/{username}/status/{tweet_id}", summary=text, published=created_at, tags=[username])`
  5. Return items list
- Auth: `Authorization: Bearer {bearer_token}` header

#### Error Handling
| Error | Behavior |
|-------|----------|
| 401/403 | Log warning, return empty list |
| 404 | Log warning (bad list ID), return empty list |
| 429 | Handled by `@http_retry` decorator with exponential backoff |
| Network error | Handled by `@http_retry` |
| Empty response data | Return empty list |

#### Configuration
| Key | Default | Source |
|-----|---------|--------|
| `sources.x_list.bearer_token` | — | config.yaml / env |
| `sources.x_list.list_id` | — | config.yaml |
| `sources.x_list.max_tweets` | 100 | config.yaml |
| `sources.x_list.enabled` | false | config.yaml |

---

### IntelSource.X_LIST
**File:** `src/shared_types.py`

New enum member: `X_LIST = "x_list"`

---

### Scheduler Registration
**File:** `src/intelligence/scheduler.py`

Added in `_init_scrapers()` following existing pattern:
```python
x_list_config = self.config.get("x_list", {})
if "x_list" in enabled or x_list_config.get("enabled", False):
    bearer = x_list_config.get("bearer_token") or os.environ.get("X_BEARER_TOKEN")
    if bearer and x_list_config.get("list_id"):
        self._scrapers.append(XListScraper(...))
```

---

## Test Expectations

- Mock httpx responses for successful tweet fetch with user expansion
- Test empty/missing bearer token returns empty list
- Test 401/404 error responses handled gracefully
- Test tweet-to-IntelItem mapping (title truncation, URL format, tags)
- Test pagination param clamped to API max (100)

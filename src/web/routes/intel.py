"""Intelligence feed routes."""

from datetime import datetime, timedelta
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from intelligence.company_watch import CompanyMovementStore, WatchedCompanyResolver
from intelligence.hiring_signals import HiringSignalStore
from intelligence.regulatory import RegulatoryAlertStore, RegulatoryWatchResolver
from intelligence.watchlist import annotate_items, attach_follow_up_state, sort_ranked_items
from web.auth import get_current_user
from web.deps import (
    get_coach_paths,
    get_company_movement_store,
    get_config,
    get_follow_up_store,
    get_hiring_signal_store,
    get_intel_storage,
    get_profile_path,
    get_regulatory_alert_store,
    get_watchlist_store,
)
from web.models import (
    CompanyMovementResponse,
    HiringSignalResponse,
    IntelFollowUp,
    RegulatoryAlertResponse,
    WatchlistItem,
)
from web.user_store import (
    add_user_rss_feed,
    get_user_rss_feeds,
    remove_user_rss_feed,
)

router = APIRouter(prefix="/api/intel", tags=["intel"])


class RSSFeedAdd(BaseModel):
    url: str
    name: str | None = None


class RSSFeedRemove(BaseModel):
    url: str


class WatchlistUpsert(BaseModel):
    label: str
    kind: str = "theme"
    aliases: list[str] = []
    why: str = ""
    priority: str = "medium"
    tags: list[str] = []
    goal: str = ""
    time_horizon: str = "quarter"
    source_preferences: list[str] = []


class FollowUpUpsert(BaseModel):
    url: str
    title: str
    saved: bool = False
    note: str = ""
    watchlist_ids: list[str] = []


def _get_storage():
    return get_intel_storage()


def _get_watchlist_store(user_id: str):
    return get_watchlist_store(user_id)


def _get_follow_up_store(user_id: str):
    return get_follow_up_store(user_id)


def _get_company_store() -> CompanyMovementStore:
    return get_company_movement_store()


def _get_hiring_store() -> HiringSignalStore:
    return get_hiring_signal_store()


def _get_regulatory_store() -> RegulatoryAlertStore:
    return get_regulatory_alert_store()


def _apply_watchlist_state(items: list[dict], user_id: str) -> list[dict]:
    watchlist_items = _get_watchlist_store(user_id).list_items()
    if watchlist_items:
        annotate_items(items, watchlist_items)
        sort_ranked = sort_ranked_items(items)
        items[:] = sort_ranked
    attach_follow_up_state(items, _get_follow_up_store(user_id))
    return items


@router.get("/recent")
async def get_recent(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    storage = _get_storage()
    # Include semantic duplicates so Feed shows all sources, not just canonicals
    items = storage.get_recent(days=days, limit=limit, include_duplicates=True)
    # Fall back to broader window when narrow one returns empty — avoids
    # "Your radar is quiet" when data exists but is slightly older.
    if not items and days < 30:
        items = storage.get_recent(days=30, limit=limit, include_duplicates=True)

    # Personalize: score items against user profile (mirrors _personalize_trending)
    try:
        from intelligence.search import load_profile_terms, score_profile_relevance

        profile_path = get_profile_path(user["id"])
        terms = load_profile_terms(profile_path)
        if not terms.is_empty:
            for item in items:
                score, matches = score_profile_relevance(item, terms)
                item["relevance_score"] = round(score, 3)
                item["match_reasons"] = matches[:5]
    except Exception:
        pass

    _apply_watchlist_state(items, user["id"])

    return items


@router.get("/search")
async def search_intel(
    q: str = Query(..., max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    storage = _get_storage()
    items = storage.search(q, limit=limit)
    _apply_watchlist_state(items, user["id"])
    return items


@router.get("/watchlist", response_model=list[WatchlistItem])
async def list_watchlist(user: dict = Depends(get_current_user)):
    return _get_watchlist_store(user["id"]).list_items()


@router.post("/watchlist", response_model=WatchlistItem)
async def create_watchlist_item(body: WatchlistUpsert, user: dict = Depends(get_current_user)):
    item = _get_watchlist_store(user["id"]).save_item(body.model_dump())
    return WatchlistItem(**item)


@router.patch("/watchlist/{item_id}", response_model=WatchlistItem)
async def update_watchlist_item(
    item_id: str,
    body: WatchlistUpsert,
    user: dict = Depends(get_current_user),
):
    item = _get_watchlist_store(user["id"]).update_item(item_id, body.model_dump())
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return WatchlistItem(**item)


@router.delete("/watchlist/{item_id}")
async def delete_watchlist_item(item_id: str, user: dict = Depends(get_current_user)):
    deleted = _get_watchlist_store(user["id"]).delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {"ok": True}


@router.get("/follow-ups", response_model=list[IntelFollowUp])
async def list_follow_ups(user: dict = Depends(get_current_user)):
    return _get_follow_up_store(user["id"]).list_items()


@router.put("/follow-ups", response_model=IntelFollowUp)
async def save_follow_up(body: FollowUpUpsert, user: dict = Depends(get_current_user)):
    entry = _get_follow_up_store(user["id"]).upsert(**body.model_dump())
    return IntelFollowUp(**entry)


@router.get("/company-movements", response_model=list[CompanyMovementResponse])
async def list_company_movements(
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    resolver = WatchedCompanyResolver()
    companies = resolver.from_watchlist_items(_get_watchlist_store(user["id"]).list_items())
    company_keys = {company["company_key"] for company in companies}
    items = [
        item
        for item in _get_company_store().get_since(
            datetime.now() - timedelta(days=14), limit=limit * 4
        )
        if item.get("company_key") in company_keys
    ]
    return [CompanyMovementResponse(**item) for item in items[:limit]]


@router.get("/company-movements/{company_key}", response_model=list[CompanyMovementResponse])
async def get_company_movements(
    company_key: str,
    limit: int = Query(default=20, ge=1, le=100),
    _user: dict = Depends(get_current_user),
):
    return [
        CompanyMovementResponse(**item)
        for item in _get_company_store().get_recent_for_company(company_key, limit=limit)
    ]


@router.get("/hiring-signals", response_model=list[HiringSignalResponse])
async def list_hiring_signals(
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    resolver = WatchedCompanyResolver()
    companies = resolver.from_watchlist_items(_get_watchlist_store(user["id"]).list_items())
    company_keys = {company["company_key"] for company in companies}
    items = [
        item
        for item in _get_hiring_store().get_recent(limit=limit * 4)
        if item.get("entity_key") in company_keys
    ]
    return [HiringSignalResponse(**item) for item in items[:limit]]


@router.get("/hiring-signals/{entity_key}", response_model=list[HiringSignalResponse])
async def get_hiring_signals_for_entity(
    entity_key: str,
    limit: int = Query(default=20, ge=1, le=100),
    _user: dict = Depends(get_current_user),
):
    return [
        HiringSignalResponse(**item)
        for item in _get_hiring_store().get_recent(entity_key=entity_key, limit=limit)
    ]


@router.get("/regulatory-alerts", response_model=list[RegulatoryAlertResponse])
async def list_regulatory_alerts(
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    resolver = RegulatoryWatchResolver()
    targets = resolver.from_watchlist_items(_get_watchlist_store(user["id"]).list_items())
    target_keys = {target["target_key"] for target in targets}
    items = [
        item
        for item in _get_regulatory_store().get_recent(
            datetime.now() - timedelta(days=30), limit=limit * 4
        )
        if item.get("target_key") in target_keys
    ]
    return [RegulatoryAlertResponse(**item) for item in items[:limit]]


@router.get("/regulatory-alerts/{target_key}", response_model=list[RegulatoryAlertResponse])
async def get_regulatory_alerts_for_target(
    target_key: str,
    limit: int = Query(default=20, ge=1, le=100),
    _user: dict = Depends(get_current_user),
):
    items = [
        item
        for item in _get_regulatory_store().get_recent(
            datetime.now() - timedelta(days=90), limit=limit * 4
        )
        if item.get("target_key") == target_key
    ]
    return [RegulatoryAlertResponse(**item) for item in items[:limit]]


@router.get("/health")
async def get_health(user: dict = Depends(get_current_user)):
    """Get scraper health status for all sources."""
    from intelligence.health import ScraperHealthTracker

    paths = get_coach_paths()
    tracker = ScraperHealthTracker(paths["intel_db"])
    return {"scrapers": tracker.get_health_summary()}


@router.get("/rss-feeds")
async def list_rss_feeds(user: dict = Depends(get_current_user)):
    """List user's custom RSS feeds with per-feed health."""
    feeds = get_user_rss_feeds(user["id"])
    try:
        from intelligence.health import RSSFeedHealthTracker

        paths = get_coach_paths()
        fht = RSSFeedHealthTracker(paths["intel_db"])
        health_map = {h["feed_url"]: h for h in fht.get_all_health()}
        for feed in feeds:
            feed["health"] = health_map.get(feed["url"])
    except Exception:
        pass
    return feeds


@router.post("/rss-feeds")
async def add_rss_feed(body: RSSFeedAdd, user: dict = Depends(get_current_user)):
    """Validate and add an RSS feed."""
    parsed = urlparse(body.url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="URL must be http or https")

    # Validate feed is reachable and looks like RSS/Atom
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(body.url, headers={"User-Agent": "CoachBot/1.0"})
            resp.raise_for_status()
            snippet = resp.text[:2048].lower()
            if "<rss" not in snippet and "<feed" not in snippet and "<channel" not in snippet:
                raise HTTPException(
                    status_code=400,
                    detail="URL does not appear to be a valid RSS/Atom feed",
                )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch feed: {e}")

    feed = add_user_rss_feed(user["id"], body.url, body.name, added_by="user")
    return feed


@router.delete("/rss-feeds")
async def delete_rss_feed(body: RSSFeedRemove, user: dict = Depends(get_current_user)):
    """Remove a user's RSS feed."""
    removed = remove_user_rss_feed(user["id"], body.url)
    if not removed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return {"ok": True}


@router.get("/trending")
async def get_trending(user: dict = Depends(get_current_user)):
    """Get cross-source trending topics, personalized by user profile."""
    from intelligence.trending_radar import TrendingRadar

    paths = get_coach_paths()
    config = get_config()
    tr_config = config.to_dict().get("trending_radar", {})

    radar = TrendingRadar(paths["intel_db"])
    snapshot = radar.load()
    if not snapshot:
        llm = _get_cheap_llm(user["id"])
        snapshot = radar.refresh(
            llm=llm,
            days=tr_config.get("days", 7),
            min_source_families=tr_config.get(
                "min_source_families", tr_config.get("min_sources", 2)
            ),
            min_items=tr_config.get("min_items", 4),
            max_topics=tr_config.get("max_topics", 10),
        )

    # Personalize: score topics against user profile
    snapshot = _personalize_trending(snapshot, user["id"])
    return snapshot


def _personalize_trending(snapshot: dict, user_id: str) -> dict:
    """Re-rank trending topics by profile relevance."""
    try:
        from intelligence.search import load_profile_terms, score_profile_relevance

        profile_path = get_profile_path(user_id)
        terms = load_profile_terms(profile_path)
        if terms.is_empty:
            snapshot["personalized"] = False
            return snapshot

        for topic in snapshot.get("topics", []):
            scores = []
            all_matches: list[str] = []
            for item in topic.get("items", []):
                score, matches = score_profile_relevance(item, terms)
                scores.append(score)
                all_matches.extend(matches)
            topic["relevance_score"] = round(sum(scores) / max(len(scores), 1), 3)
            topic["relevance_matches"] = list(dict.fromkeys(all_matches))[:5]

        # Re-sort: 0.6 * original score + 0.4 * relevance
        for topic in snapshot.get("topics", []):
            original = topic.get("score", 0) or 0
            relevance = topic.get("relevance_score", 0)
            topic["_combined"] = 0.6 * original + 0.4 * relevance

        snapshot["topics"].sort(key=lambda t: t.get("_combined", 0), reverse=True)
        for topic in snapshot.get("topics", []):
            topic.pop("_combined", None)

        snapshot["personalized"] = True
    except Exception:
        snapshot["personalized"] = False
    return snapshot


def _get_cheap_llm(user_id: str):
    """Try to create a cheap LLM provider from user's key or env. Returns None on failure."""
    try:
        from llm import create_cheap_provider
        from web.deps import get_secret_key
        from web.user_store import get_user_secret

        fernet_key = get_secret_key()
        api_key = get_user_secret(user_id, "llm_api_key", fernet_key)
        provider_name = get_user_secret(user_id, "llm_provider", fernet_key) or "auto"
        if api_key:
            return create_cheap_provider(provider=provider_name, api_key=api_key)
        # Fall back to env-based provider
        return create_cheap_provider()
    except Exception:
        return None


@router.post("/scrape")
async def scrape_now(user: dict = Depends(get_current_user)):
    """Trigger immediate scrape of all sources."""
    try:
        from intelligence.scheduler import IntelScheduler
        from intelligence.sources import RSSFeedScraper
        from journal.embeddings import EmbeddingManager
        from journal.storage import JournalStorage
        from web.user_store import get_all_user_rss_feeds

        config = get_config()
        paths = get_coach_paths()
        storage = _get_storage()
        journal_storage = JournalStorage(paths["journal_dir"])
        embeddings = EmbeddingManager(paths["chroma_dir"])

        full = config.to_dict()

        # Overlay user's github_token if stored
        from web.deps import get_secret_key
        from web.user_store import get_user_secret

        try:
            gh_token = get_user_secret(user["id"], "github_token", get_secret_key())
            if gh_token:
                full.setdefault("projects", {}).setdefault("github_issues", {})["token"] = gh_token
        except Exception:
            pass

        scheduler = IntelScheduler(
            storage=storage,
            config=full.get("sources", {}),
            journal_storage=journal_storage,
            embeddings=embeddings,
            full_config=full,
        )

        # Merge user-added RSS feeds
        config_urls = set(config.to_dict().get("sources", {}).get("rss_feeds", []))
        for feed in get_all_user_rss_feeds():
            if feed["url"] not in config_urls:
                scheduler._scrapers.append(
                    RSSFeedScraper(storage, feed["url"], name=feed.get("name"))
                )

        result = await scheduler._run_async()
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

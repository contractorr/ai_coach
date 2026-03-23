"""Tests for ScraperFactory."""

from unittest.mock import MagicMock, patch

from intelligence.scraper import IntelStorage
from intelligence.scraper_factory import ScraperFactory
from intelligence.sources.hn import HackerNewsScraper


def test_factory_creates_hn_scraper_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    storage = IntelStorage(tmp_path / "intel.db")
    factory = ScraperFactory(storage, {"enabled": ["hn_top"]}, {})
    scrapers, emb_mgr, feed_health = factory.create_all()
    assert any(isinstance(s, HackerNewsScraper) for s in scrapers)
    assert emb_mgr is None
    assert feed_health is not None


def test_factory_creates_rss_scrapers(tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    storage = IntelStorage(tmp_path / "intel.db")
    factory = ScraperFactory(
        storage,
        {"enabled": ["rss_feeds"], "rss_feeds": ["https://example.com/feed.xml"]},
        {},
    )
    scrapers, _, _ = factory.create_all()
    from intelligence.sources.rss import RSSFeedScraper

    assert any(isinstance(s, RSSFeedScraper) for s in scrapers)


def test_factory_empty_config_returns_hn(tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    storage = IntelStorage(tmp_path / "intel.db")
    factory = ScraperFactory(storage, {}, {})
    scrapers, _, _ = factory.create_all()
    # Default enabled = ["hn_top", "rss_feeds"], so HN should be present
    assert any(isinstance(s, HackerNewsScraper) for s in scrapers)


@patch("intelligence.scraper_factory.GitHubTrendingScraper")
def test_factory_github_trending_when_enabled(mock_cls, tmp_path, monkeypatch):
    monkeypatch.setenv("COACH_HOME", str(tmp_path))
    storage = IntelStorage(tmp_path / "intel.db")
    mock_cls.return_value = MagicMock(source_name="github_trending")
    factory = ScraperFactory(
        storage,
        {"enabled": [], "github_trending": {"enabled": True}},
        {},
    )
    scrapers, _, _ = factory.create_all()
    assert any(s.source_name == "github_trending" for s in scrapers)

"""Shared test fixtures for AI Coach."""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_SLOW_NODEIDS = {}

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def pytest_collection_modifyitems(items):
    """Apply repo-wide test markers by path and known hotspots."""
    for item in items:
        nodeid = item.nodeid.replace("\\", "/")

        item.add_marker(pytest.mark.unit)

        if nodeid.startswith("tests/web/"):
            item.add_marker(pytest.mark.web)
            item.add_marker(pytest.mark.serial)

        if nodeid.startswith("tests/integration/"):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.serial)

        if nodeid in _SLOW_NODEIDS:
            item.add_marker(pytest.mark.slow)


@pytest.fixture
def hash_embedding_config():
    """Config that explicitly enables hash embeddings for testing."""
    return {"embeddings": {"provider": "hash"}}


@pytest.fixture(autouse=True)
def _default_hash_embeddings(monkeypatch):
    """Auto-patch build_embedding_function to return hash embeddings in tests.

    Without real API keys, the factory returns None (semantic search disabled).
    Tests that need actual embedding operations get hash embeddings automatically.
    Tests that verify the None/disabled path can override via monkeypatch.

    Patches every module that does ``from chroma_utils import build_embedding_function``.
    """
    from chroma_utils import SimpleHashEmbeddingFunction

    _hash_fn = SimpleHashEmbeddingFunction()
    _factory = lambda config=None: _hash_fn  # noqa: E731

    # Patch the source module + every consumer that does `from chroma_utils import ...`
    monkeypatch.setattr("chroma_utils.build_embedding_function", _factory)
    for mod in [
        "journal.embeddings",
        "intelligence.embeddings",
        "library.embeddings",
    ]:
        try:
            monkeypatch.setattr(f"{mod}.build_embedding_function", _factory)
        except AttributeError:
            pass


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temp directories for journal, chroma, and intel."""
    journal_dir = tmp_path / "journal"
    chroma_dir = tmp_path / "chroma"
    intel_db = tmp_path / "intel.db"

    journal_dir.mkdir()
    chroma_dir.mkdir()

    return {
        "journal_dir": journal_dir,
        "chroma_dir": chroma_dir,
        "intel_db": intel_db,
    }


@pytest.fixture
def mock_anthropic(monkeypatch):
    """Mock Claude API responses (legacy, prefer mock_llm_provider)."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is a mocked AI response.")]

    mock_client.messages.create.return_value = mock_response

    def mock_init(self, *args, **kwargs):
        self.client = mock_client

    monkeypatch.setattr("anthropic.Anthropic", lambda **kwargs: mock_client)
    return mock_client


@pytest.fixture
def mock_llm_provider():
    """Mock LLMProvider for testing any LLM-consuming code."""
    from llm import LLMProvider

    provider = MagicMock(spec=LLMProvider)
    provider.provider_name = "mock"
    provider.generate.return_value = "Mocked LLM response"
    return provider


@pytest.fixture
def sample_journal_entries():
    """Pre-populated test journal entries."""
    now = datetime.now()
    return [
        {
            "type": "reflection",
            "title": "Weekly Review",
            "content": "Made progress on the AI coach project. Need to focus more on testing.",
            "tags": ["work", "ai"],
            "created": now.isoformat(),
        },
        {
            "type": "goal",
            "title": "Learn Rust",
            "content": "Goal: Complete the Rust book by end of quarter. Start with ownership concepts.",
            "tags": ["learning", "programming"],
            "created": (now - timedelta(days=3)).isoformat(),
        },
        {
            "type": "insight",
            "title": "Career Strategy",
            "content": "Realized that building in public helps with accountability and networking.",
            "tags": ["career", "strategy"],
            "created": (now - timedelta(days=7)).isoformat(),
        },
    ]


@pytest.fixture
def sample_intel_items():
    """Pre-populated test intel items."""
    now = datetime.now()
    return [
        {
            "source": "hackernews",
            "title": "Show HN: I built an AI-powered code reviewer",
            "url": "https://example.com/ai-reviewer",
            "summary": "500 points | 120 comments | An AI tool that reviews pull requests",
            "published": now,
            "tags": ["ai", "show-hn", "programming"],
        },
        {
            "source": "rss:techcrunch",
            "title": "Rust adoption grows in enterprise",
            "url": "https://example.com/rust-enterprise",
            "summary": "Major companies are adopting Rust for systems programming",
            "published": (now - timedelta(days=1)),
            "tags": ["rust", "programming"],
        },
        {
            "source": "github_trending",
            "title": "langchain / langchain",
            "url": "https://github.com/langchain/langchain",
            "summary": "45000 stars | Building applications with LLMs through composability",
            "published": now,
            "tags": ["python", "ai", "llm"],
        },
    ]


@pytest.fixture
def mock_http_responses():
    """Mock HTTP responses for scrapers."""
    return {
        "hn_topstories": [1, 2, 3, 4, 5],
        "hn_story": {
            "id": 1,
            "type": "story",
            "title": "Show HN: New testing framework",
            "url": "https://example.com/test",
            "score": 100,
            "descendants": 50,
            "time": int(datetime.now().timestamp()),
        },
        "rss_feed": """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Test Article</title>
      <link>https://example.com/article</link>
      <description>Test description</description>
      <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>""",
        "github_trending": """
<html><body>
<article class="Box-row">
  <h2><a href="/test/repo">test / repo</a></h2>
  <p>A test repository</p>
  <a href="/test/repo/stargazers">1,234</a>
</article>
</body></html>""",
    }


@pytest.fixture
def populated_journal(temp_dirs, sample_journal_entries):
    """Journal storage with pre-populated entries."""
    from journal.storage import JournalStorage

    storage = JournalStorage(temp_dirs["journal_dir"])

    created_paths = []
    for entry in sample_journal_entries:
        path = storage.create(
            content=entry["content"],
            entry_type=entry["type"],
            title=entry["title"],
            tags=entry.get("tags"),
        )
        created_paths.append(path)

    return {"storage": storage, "paths": created_paths}


@pytest.fixture
def populated_intel(temp_dirs, sample_intel_items):
    """Intel storage with pre-populated items."""
    from intelligence.scraper import IntelItem, IntelStorage

    storage = IntelStorage(temp_dirs["intel_db"])

    for item in sample_intel_items:
        intel_item = IntelItem(
            source=item["source"],
            title=item["title"],
            url=item["url"],
            summary=item["summary"],
            published=item["published"],
            tags=item["tags"],
        )
        storage.save(intel_item)

    return storage


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for scraper tests."""
    mock = MagicMock()
    mock.get.return_value = MagicMock(
        status_code=200,
        json=MagicMock(return_value={}),
        text="",
    )
    return mock


@pytest.fixture
def mock_async_httpx_client():
    """Mock async httpx client for async scraper tests."""
    mock = AsyncMock()
    mock.get.return_value = MagicMock(
        status_code=200,
        json=MagicMock(return_value={}),
        text="",
    )
    return mock

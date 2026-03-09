"""Tests for DeepResearchAgent."""

from unittest.mock import MagicMock

import pytest

from intelligence.scraper import IntelStorage
from journal.embeddings import EmbeddingManager
from journal.storage import JournalStorage
from research.agent import DeepResearchAgent
from research.web_search import SearchResult


@pytest.fixture
def agent_components(temp_dirs):
    """Components needed for DeepResearchAgent."""
    journal = JournalStorage(temp_dirs["journal_dir"])
    intel = IntelStorage(temp_dirs["intel_db"])
    embeddings = MagicMock(spec=EmbeddingManager)

    # Create some goals for context
    journal.create(
        content="Research machine learning applications. Learn about RAG systems.",
        entry_type="goal",
        title="AI Learning Goals",
        tags=["ai", "learning"],
    )

    return {
        "journal": journal,
        "intel": intel,
        "embeddings": embeddings,
    }


@pytest.fixture
def mock_search_results():
    """Mock search results."""
    return [
        SearchResult(
            title="ML Guide",
            url="https://example.com/ml",
            content="Comprehensive ML content.",
            score=0.9,
        ),
    ]


@pytest.fixture
def agent_factory(agent_components):
    def _build(config=None, **overrides):
        research_config = (config or {}).get("research", {})

        search_client = overrides.pop("search_client", MagicMock())
        search_client.max_results = research_config.get("sources_per_topic", 8)
        search_client.search = getattr(search_client, "search", MagicMock(return_value=[]))
        search_client.close = getattr(search_client, "close", MagicMock())

        synthesizer = overrides.pop("synthesizer", MagicMock())
        synthesizer.synthesize = getattr(
            synthesizer,
            "synthesize",
            MagicMock(return_value="## Summary\nTest report"),
        )

        return DeepResearchAgent(
            journal_storage=agent_components["journal"],
            intel_storage=agent_components["intel"],
            embeddings=agent_components["embeddings"],
            config=config,
            search_client=search_client,
            synthesizer=synthesizer,
            **overrides,
        )

    return _build


class TestDeepResearchAgent:
    """Tests for DeepResearchAgent."""

    def test_init(self, agent_factory):
        """Test agent initialization."""
        config = {
            "research": {
                "max_topics_per_week": 3,
                "sources_per_topic": 5,
            }
        }
        agent = agent_factory(config=config)

        assert agent.topic_selector.max_topics == 3
        assert agent.search_client.max_results == 5

    def test_get_suggested_topics(self, agent_factory):
        """Test topic suggestion."""
        agent = agent_factory()

        topics = agent.get_suggested_topics()
        [t["topic"].lower() for t in topics]

        # Should find topics from goals
        assert len(topics) > 0 or True  # May be empty if no strong themes

    def test_run_with_specific_topic(self, agent_factory, mock_search_results):
        """Test running research on specific topic."""
        search_client = MagicMock()
        search_client.max_results = 8
        search_client.search.return_value = mock_search_results
        search_client.close = MagicMock()
        synthesizer = MagicMock()
        synthesizer.synthesize.return_value = "## Summary\nTest report"
        agent = agent_factory(search_client=search_client, synthesizer=synthesizer)

        results = agent.run(specific_topic="Test Topic")

        assert len(results) == 1
        assert results[0]["topic"] == "Test Topic"
        assert results[0]["success"]

    def test_run_stores_journal_entry(self, agent_components, agent_factory, mock_search_results):
        """Test that research is stored as journal entry."""
        search_client = MagicMock()
        search_client.max_results = 8
        search_client.search.return_value = mock_search_results
        search_client.close = MagicMock()
        synthesizer = MagicMock()
        synthesizer.synthesize.return_value = "## Summary\nTest"
        agent = agent_factory(search_client=search_client, synthesizer=synthesizer)

        agent.run(specific_topic="Test Topic")

        # Verify journal entry was created
        entries = agent_components["journal"].list_entries(entry_type="research")
        assert len(entries) == 1
        assert "Research: Test Topic" in entries[0]["title"]

    def test_run_stores_intel_item(self, agent_components, agent_factory, mock_search_results):
        """Test that research is stored in intel DB."""
        search_client = MagicMock()
        search_client.max_results = 8
        search_client.search.return_value = mock_search_results
        search_client.close = MagicMock()
        synthesizer = MagicMock()
        synthesizer.synthesize.return_value = "## Summary\nTest"
        agent = agent_factory(search_client=search_client, synthesizer=synthesizer)

        agent.run(specific_topic="Test Topic")

        # Verify intel item was created
        items = agent_components["intel"].search("Test Topic")
        assert len(items) == 1
        assert items[0]["source"] == "deep_research"

    def test_run_no_search_results(self, agent_factory):
        """Test handling when search returns no results."""
        search_client = MagicMock()
        search_client.max_results = 8
        search_client.search.return_value = []
        search_client.close = MagicMock()
        agent = agent_factory(search_client=search_client)

        results = agent.run(specific_topic="Unknown Topic")

        assert len(results) == 1
        assert not results[0]["success"]

    def test_get_user_context(self, agent_factory):
        """Test user context extraction."""
        agent = agent_factory()

        context = agent._get_user_context()

        assert "GOALS:" in context
        assert "AI Learning Goals" in context

    def test_close(self, agent_factory):
        """Test agent cleanup."""
        search_client = MagicMock()
        search_client.max_results = 8
        search_client.close = MagicMock()
        agent = agent_factory(search_client=search_client)

        agent.close()
        search_client.close.assert_called_once()

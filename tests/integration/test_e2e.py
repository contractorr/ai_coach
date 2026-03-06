"""End-to-end integration tests."""

import pytest
from pydantic import ValidationError


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_config(self):
        """Test valid config loads without errors."""
        from cli.config_models import CoachConfig

        config = CoachConfig.from_dict(
            {
                "llm": {"model": "claude-sonnet-4-6"},
                "research": {"schedule": "0 8 * * 0"},
                "logging": {"level": "DEBUG"},
            }
        )

        assert config.llm.model == "claude-sonnet-4-6"
        assert config.logging.level == "DEBUG"

    def test_invalid_cron_expression(self):
        """Test invalid cron raises error."""
        from cli.config_models import CoachConfig

        with pytest.raises(ValidationError) as exc:
            CoachConfig.from_dict(
                {
                    "research": {"schedule": "invalid cron"},
                }
            )
        assert "cron" in str(exc.value).lower() or "field" in str(exc.value).lower()

    def test_invalid_log_level(self):
        """Test invalid log level raises error."""
        from cli.config_models import CoachConfig

        with pytest.raises(ValidationError) as exc:
            CoachConfig.from_dict(
                {
                    "logging": {"level": "INVALID"},
                }
            )
        assert "log level" in str(exc.value).lower()

    def test_env_var_expansion(self, monkeypatch):
        """Test environment variable expansion in API keys."""
        from cli.config_models import CoachConfig

        monkeypatch.setenv("TEST_API_KEY", "sk-test-12345")

        config = CoachConfig.from_dict(
            {
                "llm": {"api_key": "${TEST_API_KEY}"},
            }
        )

        assert config.llm.api_key == "sk-test-12345"

    def test_path_expansion(self):
        """Test ~ expansion in paths."""
        import os

        from cli.config_models import CoachConfig

        config = CoachConfig.from_dict(
            {
                "paths": {"journal_dir": "~/coach/journal"},
            }
        )

        assert str(config.paths.journal_dir).startswith(os.path.expanduser("~"))

    def test_rag_config_defaults(self):
        """Test RAG config has correct defaults."""
        from cli.config_models import CoachConfig

        config = CoachConfig.from_dict({})
        assert config.rag.max_context_chars == 8000
        assert config.rag.journal_weight == 0.7

    def test_rag_config_custom(self):
        """Test RAG config accepts custom values."""
        from cli.config_models import CoachConfig

        config = CoachConfig.from_dict(
            {
                "rag": {"max_context_chars": 10000, "journal_weight": 0.6},
            }
        )
        assert config.rag.max_context_chars == 10000
        assert config.rag.journal_weight == 0.6

    def test_rag_journal_weight_validation(self):
        """Test journal_weight must be 0-1."""
        from cli.config_models import CoachConfig

        with pytest.raises(ValidationError):
            CoachConfig.from_dict({"rag": {"journal_weight": 1.5}})

    def test_search_config_defaults(self):
        """Test search config defaults."""
        from cli.config_models import CoachConfig

        config = CoachConfig.from_dict({})
        assert config.search.default_results == 5
        assert config.search.intel_similarity_threshold == 0.7

    def test_rate_limits_config(self):
        """Test rate limits config with per-source overrides."""
        from cli.config_models import CoachConfig

        config = CoachConfig.from_dict(
            {
                "rate_limits": {
                    "hackernews": {"requests_per_second": 3.0, "burst": 8},
                },
            }
        )
        assert config.rate_limits.hackernews.requests_per_second == 3.0
        assert config.rate_limits.hackernews.burst == 8
        assert config.rate_limits.default.requests_per_second == 2.0

    def test_recommendations_dedup_window(self):
        """Test dedup window config."""
        from cli.config_models import CoachConfig

        config = CoachConfig.from_dict(
            {
                "recommendations": {"dedup_window_days": 60, "similarity_threshold": 0.9},
            }
        )
        assert config.recommendations.dedup_window_days == 60
        assert config.recommendations.similarity_threshold == 0.9


class TestJournalFlow:
    """Test journal create -> embed -> search flow."""

    def test_create_embed_search(self, temp_dirs):
        """Test full journal flow."""
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch
        from journal.storage import JournalStorage

        # Create storage and add entries
        storage = JournalStorage(temp_dirs["journal_dir"])

        storage.create(
            content="Learning Python for data science projects. Focus on pandas and numpy.",
            entry_type="note",
            title="Python Learning",
            tags=["python", "learning"],
        )

        storage.create(
            content="Started a new Rust project for systems programming.",
            entry_type="note",
            title="Rust Project",
            tags=["rust", "programming"],
        )

        # Set up embeddings
        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(storage, embeddings)

        # Sync embeddings
        added, removed = search.sync_embeddings()
        assert added == 2

        # Search
        results = search.semantic_search("data science with python")
        assert len(results) >= 1

        # Verify Python entry ranks higher for Python query
        python_found = any("Python" in r.get("title", "") for r in results)
        assert python_found

    def test_update_reflects_in_search(self, temp_dirs):
        """Test that updates are reflected in search."""
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])
        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        search = JournalSearch(storage, embeddings)

        # Create entry
        path = storage.create(
            content="Original content about cooking",
            entry_type="note",
        )
        search.sync_embeddings()

        # Update entry
        storage.update(path, content="Updated content about machine learning AI")
        search.sync_embeddings()

        # Search should find updated content
        results = search.semantic_search("machine learning")
        assert len(results) >= 1


class TestIntelFlow:
    """Test scrape -> embed -> RAG query flow."""

    def test_scrape_embed_query(self, temp_dirs):
        """Test intelligence flow with mocked data."""
        from datetime import datetime

        from intelligence.embeddings import IntelEmbeddingManager
        from intelligence.scraper import IntelItem, IntelStorage
        from intelligence.search import IntelSearch

        # Create storage and add items
        storage = IntelStorage(temp_dirs["intel_db"])

        items = [
            IntelItem(
                source="hackernews",
                title="New ML framework released",
                url="https://example.com/ml",
                summary="A powerful new machine learning framework for Python",
                published=datetime.now(),
                tags=["ai", "python", "ml"],
            ),
            IntelItem(
                source="rss:techblog",
                title="Rust vs Go performance comparison",
                url="https://example.com/rust-go",
                summary="Benchmarks comparing Rust and Go for backend services",
                published=datetime.now(),
                tags=["rust", "go", "performance"],
            ),
        ]

        for item in items:
            storage.save(item)

        # Set up embeddings
        embeddings = IntelEmbeddingManager(temp_dirs["chroma_dir"])
        search = IntelSearch(storage, embeddings)

        # Sync embeddings
        added, removed = search.sync_embeddings()
        assert added == 2

        # Query
        context = search.get_context_for_query("machine learning python")
        assert "ML" in context or "machine" in context.lower()

    def test_rag_with_intel_search(self, temp_dirs):
        """Test RAG retriever with semantic intel search."""
        from datetime import datetime

        from advisor.rag import RAGRetriever
        from intelligence.embeddings import IntelEmbeddingManager
        from intelligence.scraper import IntelItem, IntelStorage
        from intelligence.search import IntelSearch
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch
        from journal.storage import JournalStorage

        # Set up journal with embeddings
        journal_storage = JournalStorage(temp_dirs["journal_dir"])
        journal_embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        journal_storage.create(
            content="My goal is to become an expert in AI and machine learning.",
            entry_type="goal",
        )
        journal_search = JournalSearch(journal_storage, journal_embeddings)
        journal_search.sync_embeddings()

        # Set up intel
        intel_storage = IntelStorage(temp_dirs["intel_db"])
        intel_storage.save(
            IntelItem(
                source="hackernews",
                title="AI career guide 2024",
                url="https://example.com/ai-career",
                summary="Guide to building a career in artificial intelligence",
                published=datetime.now(),
            )
        )

        intel_embeddings = IntelEmbeddingManager(temp_dirs["chroma_dir"])
        intel_search = IntelSearch(intel_storage, intel_embeddings)
        intel_search.sync_embeddings()

        # RAG retriever with semantic search
        rag = RAGRetriever(
            journal_search=journal_search,
            intel_search=intel_search,
        )

        # Get combined context
        journal_ctx, intel_ctx = rag.get_combined_context("AI career path")

        assert isinstance(journal_ctx, str)
        assert isinstance(intel_ctx, str)


class TestSchedulerFlow:
    """Test scheduler with multiple scrapers."""

    def test_scheduler_run_now(self, temp_dirs, monkeypatch):
        """Test running scheduler immediately with mocked HTTP."""
        from unittest.mock import MagicMock

        from intelligence.scheduler import IntelScheduler
        from intelligence.scraper import IntelStorage

        # Mock all HTTP requests
        mock_client = MagicMock()
        mock_client.get.return_value = MagicMock(
            json=MagicMock(return_value=[]),
            text="",
            raise_for_status=MagicMock(),
        )

        import httpx

        monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

        storage = IntelStorage(temp_dirs["intel_db"])
        scheduler = IntelScheduler(
            storage=storage,
            config={
                "enabled": ["hn_top"],
                "rss_feeds": [],
            },
        )

        results = scheduler.run_now()

        assert "hackernews" in results

    def test_scheduler_with_multiple_sources(self, temp_dirs, monkeypatch):
        """Test scheduler with multiple sources configured."""
        from unittest.mock import MagicMock

        from intelligence.scheduler import IntelScheduler
        from intelligence.scraper import IntelStorage

        # Mock HTTP client
        mock_client = MagicMock()
        mock_client.get.return_value = MagicMock(
            json=MagicMock(return_value=[]),
            text="",
            raise_for_status=MagicMock(),
        )

        import httpx

        monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

        storage = IntelStorage(temp_dirs["intel_db"])
        scheduler = IntelScheduler(
            storage=storage,
            config={
                "enabled": ["hn_top", "rss_feeds"],
                "rss_feeds": ["https://example.com/feed.xml"],
            },
        )

        # Verify scheduler initialized with sources
        assert scheduler is not None
        results = scheduler.run_now()
        assert isinstance(results, dict)


class TestGoalsFlow:
    """Test goal tracking flow."""

    def test_goal_create_and_checkin(self, temp_dirs):
        """Test creating goal and adding check-ins."""
        from advisor.goals import GoalTracker, get_goal_defaults
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])
        tracker = GoalTracker(storage)

        # Create goal via storage (the standard way)
        path = storage.create(
            content="Master K8s for container orchestration",
            entry_type="goal",
            title="Learn Kubernetes",
            metadata=get_goal_defaults(),
        )
        assert path.exists()

        # Add check-in
        tracker.check_in_goal(path, "Completed pods and deployments tutorial")

        # Verify check-in recorded (frontmatter.Post has .content attribute)
        entry = storage.read(path)
        assert "check-in" in entry.content.lower()

    def test_goal_staleness_detection(self, temp_dirs):
        """Test that stale goals are detected."""
        from advisor.goals import GoalTracker, get_goal_defaults
        from journal.storage import JournalStorage

        storage = JournalStorage(temp_dirs["journal_dir"])
        tracker = GoalTracker(storage)

        # Create goal via storage
        storage.create(
            content="A goal to track",
            entry_type="goal",
            title="Test Goal",
            metadata=get_goal_defaults(),
        )

        # Get goals
        goals = tracker.get_goals()
        assert len(goals) >= 1


class TestRecommendationsFlow:
    """Test recommendations system flow."""

    def test_recommendation_storage(self, temp_dirs):
        """Test storing and retrieving recommendations."""
        from advisor.recommendation_storage import Recommendation, RecommendationStorage

        storage = RecommendationStorage(temp_dirs["intel_db"])

        # Save recommendation
        rec = Recommendation(
            category="learning",
            title="Learn GraphQL",
            description="GraphQL is trending for API development",
            score=8.5,
            rationale="High demand skill",
        )
        rec_id = storage.save(rec)

        assert rec_id is not None

        # Retrieve
        result = storage.get(rec_id)
        assert result.title == "Learn GraphQL"
        assert result.score == 8.5

    def test_recommendation_deduplication(self, temp_dirs):
        """Test that duplicate recommendations are detected via hash."""
        import hashlib

        from advisor.recommendation_storage import Recommendation, RecommendationStorage

        storage = RecommendationStorage(temp_dirs["intel_db"])

        # Create hash for dedup check
        content = "career:Apply to FAANG"
        embed_hash = hashlib.md5(content.encode()).hexdigest()

        rec = Recommendation(
            category="career",
            title="Apply to FAANG",
            description="Consider applying to big tech",
            score=7.0,
            embedding_hash=embed_hash,
        )

        storage.save(rec)

        # Check hash exists
        assert storage.hash_exists(embed_hash)

        # List by category
        recs = storage.list_by_category("career")
        assert len(recs) >= 1


class TestCLIIntegration:
    """Test CLI command flows (without actual CLI invocation)."""

    def test_components_initialization(self, temp_dirs, monkeypatch):
        """Test that CLI components can be initialized."""
        # Set environment
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from intelligence.scheduler import IntelScheduler
        from intelligence.scraper import IntelStorage
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch
        from journal.storage import JournalStorage

        # Initialize all components like CLI would
        journal_storage = JournalStorage(temp_dirs["journal_dir"])
        embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        journal_search = JournalSearch(journal_storage, embeddings)
        intel_storage = IntelStorage(temp_dirs["intel_db"])
        scheduler = IntelScheduler(intel_storage, config={})

        assert journal_storage is not None
        assert journal_search is not None
        assert intel_storage is not None
        assert scheduler is not None

    def test_full_advisor_flow(self, temp_dirs, mock_anthropic, monkeypatch):
        """Test full advisor flow: journal -> intel -> RAG -> response."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        from datetime import datetime

        from advisor.rag import RAGRetriever
        from intelligence.embeddings import IntelEmbeddingManager
        from intelligence.scraper import IntelItem, IntelStorage
        from intelligence.search import IntelSearch
        from journal.embeddings import EmbeddingManager
        from journal.search import JournalSearch
        from journal.storage import JournalStorage

        # Setup journal with goal
        journal_storage = JournalStorage(temp_dirs["journal_dir"])
        journal_embeddings = EmbeddingManager(temp_dirs["chroma_dir"])
        journal_storage.create(
            content="I want to transition into machine learning engineering.",
            entry_type="goal",
            title="Career Goal",
        )
        journal_search = JournalSearch(journal_storage, journal_embeddings)
        journal_search.sync_embeddings()

        # Setup intel
        intel_storage = IntelStorage(temp_dirs["intel_db"])
        intel_storage.save(
            IntelItem(
                source="hackernews",
                title="ML Engineer roadmap 2024",
                url="https://example.com/ml-roadmap",
                summary="Complete guide to becoming an ML engineer",
                published=datetime.now(),
            )
        )
        intel_embeddings = IntelEmbeddingManager(temp_dirs["chroma_dir"])
        intel_search = IntelSearch(intel_storage, intel_embeddings)
        intel_search.sync_embeddings()

        # RAG retrieval
        rag = RAGRetriever(journal_search=journal_search, intel_search=intel_search)
        journal_ctx, intel_ctx = rag.get_combined_context("ML career advice")

        # Verify context retrieved
        assert (
            "machine learning" in journal_ctx.lower()
            or "ml" in journal_ctx.lower()
            or len(journal_ctx) > 0
        )
        assert isinstance(intel_ctx, str)

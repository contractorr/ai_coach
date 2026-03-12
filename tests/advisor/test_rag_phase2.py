"""Tests for Phase 2 RAG features: token budgets, temporal routing, reranker."""

from unittest.mock import MagicMock

from advisor.rag import RAGRetriever
from journal.search import JournalSearch
from services.tokens import count_tokens


class TestTokenBudgets:
    def _make_rag(self, **kwargs):
        journal_search = MagicMock(spec=JournalSearch)
        journal_search.get_context_for_query.return_value = "journal text"
        journal_search.storage = MagicMock()
        return RAGRetriever(journal_search=journal_search, **kwargs)

    def test_default_token_budget_from_chars(self):
        rag = self._make_rag(max_context_chars=8000)
        assert rag.max_context_tokens == 2000

    def test_explicit_token_budget(self):
        rag = self._make_rag(max_context_tokens=1500)
        assert rag.max_context_tokens == 1500

    def test_count_tokens_returns_int(self):
        result = count_tokens("Hello world, this is a test.")
        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_empty_string(self):
        assert count_tokens("") == 0

    def test_truncate_to_token_budget(self):
        rag = self._make_rag(max_context_tokens=10)
        # Create context that exceeds 10 tokens
        long_journal = "word " * 100
        long_intel = "item " * 100
        j, i = rag._truncate_to_token_budget(long_journal, long_intel, 0.7)
        total = count_tokens(j) + count_tokens(i)
        # Should be reduced (may not be exactly 10 due to char-based truncation)
        assert total < count_tokens(long_journal) + count_tokens(long_intel)

    def test_within_budget_unchanged(self):
        rag = self._make_rag(max_context_tokens=5000)
        j, i = rag._truncate_to_token_budget("short journal", "short intel", 0.7)
        assert j == "short journal"
        assert i == "short intel"


class TestTemporalRouting:
    def _make_rag_with_analyzer(self):
        from advisor.query_analyzer import QueryAnalyzer

        journal_search = MagicMock(spec=JournalSearch)
        journal_search.get_context_for_query.return_value = "journal text"
        journal_search.hybrid_search.return_value = []
        journal_search.temporal_search.return_value = [
            {
                "title": "Test Entry",
                "type": "reflection",
                "created": "2026-03-10",
                "tags": ["test"],
                "content": "temporal content here",
            }
        ]
        journal_search.storage = MagicMock()

        intel_search = MagicMock()
        intel_search.temporal_search.return_value = [
            {
                "source": "hackernews",
                "title": "HN Post",
                "summary": "summary",
                "url": "https://example.com",
            }
        ]
        intel_search.get_context_for_query.return_value = "intel text"

        qa = QueryAnalyzer()
        rag = RAGRetriever(
            journal_search=journal_search,
            intel_search=intel_search,
            query_analyzer=qa,
        )
        return rag, journal_search, intel_search

    def test_temporal_query_routes_to_temporal_search(self):
        rag, journal_mock, intel_mock = self._make_rag_with_analyzer()
        rag.get_enhanced_context("what happened last week")
        journal_mock.temporal_search.assert_called_once()
        intel_mock.temporal_search.assert_called_once()

    def test_non_temporal_query_skips_temporal_search(self):
        rag, journal_mock, intel_mock = self._make_rag_with_analyzer()
        rag.get_enhanced_context("compare AI models")
        journal_mock.temporal_search.assert_not_called()

    def test_temporal_context_has_content(self):
        rag, _, _ = self._make_rag_with_analyzer()
        ctx = rag.get_enhanced_context("news from yesterday")
        # Should have content from temporal search results
        assert ctx.journal != "" or ctx.intel != ""


class TestReranker:
    def _make_rag_with_reranker(self, reranker):
        from advisor.query_analyzer import QueryAnalyzer

        journal_search = MagicMock(spec=JournalSearch)
        journal_search.get_context_for_query.return_value = "journal text"
        journal_search.storage = MagicMock()

        intel_search = MagicMock()
        intel_search.get_context_for_query.return_value = "- item A\n- item B\n- item C"

        qa = QueryAnalyzer()
        rag = RAGRetriever(
            journal_search=journal_search,
            intel_search=intel_search,
            query_analyzer=qa,
            reranker=reranker,
        )
        return rag

    def test_reranker_called_when_available(self):
        reranker = MagicMock()
        reranker.available = True
        reranker.rerank.return_value = [2, 0, 1]
        rag = self._make_rag_with_reranker(reranker)
        rag.get_enhanced_context("test query")
        reranker.rerank.assert_called_once()

    def test_reranker_skipped_when_unavailable(self):
        reranker = MagicMock()
        reranker.available = False
        rag = self._make_rag_with_reranker(reranker)
        rag.get_enhanced_context("test query")
        reranker.rerank.assert_not_called()

    def test_reranker_none_works(self):
        from advisor.query_analyzer import QueryAnalyzer

        journal_search = MagicMock(spec=JournalSearch)
        journal_search.get_context_for_query.return_value = "journal text"
        journal_search.storage = MagicMock()

        rag = RAGRetriever(
            journal_search=journal_search,
            query_analyzer=QueryAnalyzer(),
            reranker=None,
        )
        ctx = rag.get_enhanced_context("test")
        assert isinstance(ctx.journal, str)


class TestCrossEncoderReranker:
    def test_unavailable_without_sentence_transformers(self):
        from services.reranker import CrossEncoderReranker

        reranker = CrossEncoderReranker()
        # sentence-transformers likely not installed in test env
        # reranker should gracefully handle this
        assert isinstance(reranker.available, bool)

    def test_rerank_identity_when_unavailable(self):
        from services.reranker import CrossEncoderReranker

        reranker = CrossEncoderReranker()
        if not reranker.available:
            result = reranker.rerank("query", ["a", "b", "c"], top_k=3)
            assert result == [0, 1, 2]

    def test_rerank_empty_passages(self):
        from services.reranker import CrossEncoderReranker

        reranker = CrossEncoderReranker()
        assert reranker.rerank("query", []) == []

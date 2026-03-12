"""Tests for QueryAnalyzer temporal detection + mode selection."""

from unittest.mock import MagicMock

from advisor.query_analyzer import QueryAnalyzer, RetrievalMode


class TestTemporalDetection:
    def test_temporal_query_sets_filter(self):
        qa = QueryAnalyzer()
        result = qa.analyze("what happened last week in AI")
        assert result.temporal_filter is not None
        assert "last week" in result.temporal_filter.original_expr

    def test_temporal_stripped_from_complexity_check(self):
        """Temporal expression should be stripped before complexity scoring."""
        qa = QueryAnalyzer()
        result = qa.analyze("recent news")
        assert result.temporal_filter is not None
        assert result.cleaned_query == "news"

    def test_no_temporal_in_normal_query(self):
        qa = QueryAnalyzer()
        result = qa.analyze("compare OpenAI and Anthropic")
        assert result.temporal_filter is None

    def test_temporal_orthogonal_to_mode(self):
        """Temporal filter can coexist with DECOMPOSED mode."""
        qa = QueryAnalyzer()
        result = qa.analyze("compare trends last 3 months versus current")
        # "compare" → complexity ≥ 2 → DECOMPOSED, "last 3 months" → temporal
        assert result.temporal_filter is not None
        assert result.mode == RetrievalMode.DECOMPOSED

    def test_simple_temporal_query(self):
        qa = QueryAnalyzer()
        result = qa.analyze("journal entries from yesterday")
        assert result.temporal_filter is not None
        assert result.mode == RetrievalMode.SIMPLE

    def test_temporal_with_entity(self):
        entity_store = MagicMock()
        entity_store.search_entities.return_value = [{"name": "OpenAI", "id": 1}]
        qa = QueryAnalyzer(entity_store=entity_store)
        result = qa.analyze("OpenAI news since January")
        assert result.temporal_filter is not None
        assert result.mode == RetrievalMode.ENTITY

    def test_cleaned_query_populated(self):
        qa = QueryAnalyzer()
        result = qa.analyze("AI trends last 2 weeks")
        assert result.cleaned_query == "AI trends"

    def test_cleaned_query_equals_original_when_no_temporal(self):
        qa = QueryAnalyzer()
        result = qa.analyze("latest AI models")
        assert result.cleaned_query == "latest AI models"


class TestModeSelection:
    def test_simple_query(self):
        qa = QueryAnalyzer()
        result = qa.analyze("what is RAG")
        assert result.mode == RetrievalMode.SIMPLE

    def test_complex_query_decomposed(self):
        qa = QueryAnalyzer()
        result = qa.analyze("compare the hiring trends at AI labs versus their product launches")
        assert result.mode == RetrievalMode.DECOMPOSED

    def test_entity_match(self):
        entity_store = MagicMock()
        entity_store.search_entities.return_value = [{"name": "Google", "id": 1}]
        qa = QueryAnalyzer(entity_store=entity_store)
        result = qa.analyze("Google news")
        assert result.mode == RetrievalMode.ENTITY

    def test_no_entity_store_never_entity_mode(self):
        qa = QueryAnalyzer()
        result = qa.analyze("Google DeepMind updates")
        assert result.mode != RetrievalMode.ENTITY
        assert result.mode != RetrievalMode.COMBINED

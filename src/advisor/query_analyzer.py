"""Query analysis for selecting retrieval modes."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

import structlog

from intelligence.entity_store import EntityStore
from llm.base import LLMProvider
from services.temporal import TemporalFilter, parse_temporal_expr, strip_temporal

logger = structlog.get_logger()

COMPLEXITY_TERMS = ("compare", "versus", "vs", "difference between", "relate to")
CONJUNCTION_TERMS = (" and ", " as well as ", " but also ")


class RetrievalMode(Enum):
    SIMPLE = "simple"
    DECOMPOSED = "decomposed"
    ENTITY = "entity"
    COMBINED = "combined"


@dataclass
class QueryAnalysis:
    mode: RetrievalMode
    matched_entities: list[dict]
    complexity_score: int
    temporal_filter: TemporalFilter | None = field(default=None)
    cleaned_query: str = ""


class QueryAnalyzer:
    """Choose the retrieval mode for a query."""

    def __init__(self, llm: LLMProvider | None = None, entity_store: EntityStore | None = None):
        self.llm = llm
        self.entity_store = entity_store

    def analyze(self, query: str) -> QueryAnalysis:
        # Detect temporal intent first
        temporal_filter = parse_temporal_expr(query)
        search_query = strip_temporal(query, temporal_filter) if temporal_filter else query

        matched_entities = []
        if self.entity_store:
            try:
                matched_entities = self.entity_store.search_entities(search_query, limit=5)
            except Exception as exc:
                logger.warning("query_analysis_entity_lookup_failed", error=str(exc))

        score = self._complexity_score(search_query)
        is_complex = score >= 2
        if score == 1 and self.llm is not None:
            is_complex = self._llm_says_complex(search_query)

        has_entities = bool(matched_entities)
        if is_complex and has_entities:
            mode = RetrievalMode.COMBINED
        elif is_complex:
            mode = RetrievalMode.DECOMPOSED
        elif has_entities:
            mode = RetrievalMode.ENTITY
        else:
            mode = RetrievalMode.SIMPLE

        return QueryAnalysis(
            mode=mode,
            matched_entities=matched_entities,
            complexity_score=score,
            temporal_filter=temporal_filter,
            cleaned_query=search_query,
        )

    def _complexity_score(self, query: str) -> int:
        lower = query.lower()
        score = 0
        if any(term in lower for term in COMPLEXITY_TERMS):
            score += 2
        if any(term in lower for term in CONJUNCTION_TERMS):
            score += 1
        # Match capitalized words that are not sentence-initial
        cap_words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", query)
        # Exclude the first word (sentence-initial capitalization)
        first_word = query.strip().split()[0] if query.strip() else ""
        named = [w for w in cap_words if w != first_word]
        if len(named) >= 2:
            score += 1
        if len(query.split()) > 20:
            score += 1
        return score

    def _llm_says_complex(self, query: str) -> bool:
        try:
            response = self.llm.generate(
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Is this query complex enough to benefit from being split into sub-questions? "
                            "Reply YES or NO.\n\nQuery: " + query
                        ),
                    }
                ],
                system="You classify retrieval complexity. Answer YES or NO only.",
                max_tokens=10,
            )
            return response.strip().upper().startswith("YES")
        except Exception:
            return False

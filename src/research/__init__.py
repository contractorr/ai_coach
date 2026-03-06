"""Deep research module for topic discovery and web research."""

from .agent import DeepResearchAgent
from .dossiers import ResearchDossierStore
from .synthesis import ResearchSynthesizer
from .topics import TopicSelector
from .web_search import WebSearchClient

__all__ = [
    "TopicSelector",
    "WebSearchClient",
    "ResearchSynthesizer",
    "ResearchDossierStore",
    "DeepResearchAgent",
]

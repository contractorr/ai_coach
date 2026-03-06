"""Tests for persistent research dossiers."""

from unittest.mock import MagicMock, patch

from intelligence.scraper import IntelStorage
from journal.storage import JournalStorage
from research.dossiers import ResearchDossierStore
from research.web_search import SearchResult


def test_dossier_store_create_and_append_update(temp_dirs):
    storage = JournalStorage(temp_dirs["journal_dir"])
    dossiers = ResearchDossierStore(storage)

    dossier = dossiers.create_dossier(
        topic="OpenAI platform strategy",
        scope="Track major platform and pricing changes.",
        core_questions=["What changed this week?"],
        tracked_subtopics=["pricing", "models"],
    )
    assert dossier["topic"] == "OpenAI platform strategy"
    assert dossier["update_count"] == 0

    update = dossiers.append_update(
        dossier["dossier_id"],
        content="## What Changed\n- Pricing changed\n",
        metadata={
            "change_summary": "Pricing changed",
            "confidence": "High",
            "recommended_actions": ["Review budget"],
            "source_urls": ["https://example.com/pricing"],
            "source_titles": ["Pricing update"],
            "sources_count": 1,
            "run_source": "manual",
        },
    )

    refreshed = dossiers.get_dossier(dossier["dossier_id"])
    assert update["change_summary"] == "Pricing changed"
    assert refreshed is not None
    assert refreshed["update_count"] >= 1
    assert refreshed["latest_change_summary"] == "Pricing changed"
    assert refreshed["updates"][0]["source_urls"] == ["https://example.com/pricing"]


def test_agent_updates_existing_dossier(temp_dirs):
    storage = JournalStorage(temp_dirs["journal_dir"])
    intel = IntelStorage(temp_dirs["intel_db"])
    embeddings = MagicMock()

    with patch("research.agent.ResearchSynthesizer") as synth_cls, patch("research.agent.WebSearchClient") as search_cls:
        synth = MagicMock()
        synth.synthesize_dossier_update.return_value = """## What Changed
- Model pricing shifted toward higher-volume discounts.

## Why It Matters
Lower marginal cost may change recommendation economics.

## Evidence
- Vendor announcement cites updated discounting.

## Confidence
High - official announcement.

## Recommended Actions
- Revisit pricing assumptions.

## Open Questions
- Will this apply to all tiers?

## Sources
- Pricing update: https://example.com/pricing
"""
        synth_cls.return_value = synth

        search = MagicMock()
        search.search.return_value = [
            SearchResult(
                title="Pricing update",
                url="https://example.com/pricing",
                content="Volume discounts expanded for API customers.",
            )
        ]
        search_cls.return_value = search

        from research.agent import DeepResearchAgent

        agent = DeepResearchAgent(
            journal_storage=storage,
            intel_storage=intel,
            embeddings=embeddings,
            config={"research": {"max_topics_per_week": 2}},
        )

    dossier = agent.create_dossier(topic="OpenAI pricing")
    result = agent.run(dossier_id=dossier["dossier_id"])
    refreshed = agent.get_dossier(dossier["dossier_id"])

    assert result[0]["success"] is True
    assert result[0]["dossier_id"] == dossier["dossier_id"]
    assert refreshed is not None
    assert refreshed["latest_change_summary"].startswith("Model pricing shifted")
    embeddings.add_entry.assert_called()

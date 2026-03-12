from unittest.mock import Mock

from advisor.entity_retriever import EntityRetriever
from memory.models import FactCategory, FactSource, StewardFact


def _mock_entity_store():
    entity_store = Mock()
    entity_store.get_relationships.return_value = []
    entity_store.get_entity_items.return_value = []
    return entity_store


def test_entity_retriever_escapes_xml_like_attributes():
    entity_store = Mock()
    entity_store.get_relationships.return_value = [
        {
            "source_id": 1,
            "target_name": 'Widget "Co" <Beta>',
            "type": "COMPETES&WITH",
            "evidence": 'Quote "here" & <there>',
        }
    ]
    entity_store.get_entity_items.return_value = [
        {
            "source": "rss&feed",
            "title": 'Launch "update"',
            "summary": "Summary with <xml> & quotes",
        }
    ]
    retriever = EntityRetriever(entity_store)

    rendered = retriever.retrieve(
        [{"id": 1, "name": 'Acme "Corp" <AI>', "type": "Company&Lab", "item_count": 3}],
        "Acme",
    )

    assert "name='Acme \"Corp\" &lt;AI&gt;'" in rendered
    assert 'type="Company&amp;Lab"' in rendered
    assert "target='Widget \"Co\" &lt;Beta&gt;'" in rendered
    assert "evidence='Quote \"here\" &amp; &lt;there&gt;'" in rendered
    assert 'source="rss&amp;feed"' in rendered
    assert 'summary="Summary with &lt;xml&gt; &amp; quotes"' in rendered


def test_memory_facts_appear_when_fact_store_set():
    entity_store = _mock_entity_store()
    fact = StewardFact(
        id="f1",
        text="User is learning Rust",
        category=FactCategory.SKILL,
        source_type=FactSource.JOURNAL,
        source_id="e1",
        confidence=0.85,
    )
    fact_store = Mock()
    fact_store.get_facts_for_entity.return_value = [fact]

    retriever = EntityRetriever(entity_store, fact_store=fact_store)
    rendered = retriever.retrieve(
        [{"id": 1, "name": "Rust", "type": "Technology", "item_count": 5}],
        "Rust",
    )

    assert "<memory_facts>" in rendered
    assert "User is learning Rust" in rendered
    assert 'category="skill"' in rendered


def test_no_memory_facts_without_fact_store():
    entity_store = _mock_entity_store()
    retriever = EntityRetriever(entity_store)

    rendered = retriever.retrieve(
        [{"id": 1, "name": "Rust", "type": "Technology", "item_count": 5}],
        "Rust",
    )

    assert "<memory_facts>" not in rendered


def test_no_memory_facts_block_when_no_match():
    entity_store = _mock_entity_store()
    fact_store = Mock()
    fact_store.get_facts_for_entity.return_value = []

    retriever = EntityRetriever(entity_store, fact_store=fact_store)
    rendered = retriever.retrieve(
        [{"id": 1, "name": "Go", "type": "Technology", "item_count": 3}],
        "Go",
    )

    assert "<memory_facts>" not in rendered


def test_budget_overflow_still_works_with_fact_store():
    entity_store = _mock_entity_store()
    fact_store = Mock()
    fact_store.get_facts_for_entity.return_value = []

    retriever = EntityRetriever(entity_store, fact_store=fact_store, max_chars=200)

    entities = [
        {"id": i, "name": f"Entity{i}", "type": "Company", "item_count": 10 - i} for i in range(10)
    ]
    rendered = retriever.retrieve(entities, "query")

    # Should not crash — budget cap truncates gracefully
    assert len(rendered) <= 400  # some slack for closing tags

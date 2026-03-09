from advisor.assumptions import AssumptionStore, refresh_active_assumptions


def test_refresh_active_assumptions_updates_status_and_deduplicates_evidence(tmp_path):
    store = AssumptionStore(tmp_path / "assumptions.db")
    assumption_id = store.create(
        {
            "statement": "Acme will grow hiring this year",
            "status": "active",
            "source_type": "journal",
            "source_id": "journal/test.md",
            "linked_entities": ["Acme"],
        }
    )
    signals = [
        {
            "kind": "hiring",
            "title": "Acme expands hiring in London",
            "summary": "Acme plans to grow engineering hiring this quarter.",
            "url": "https://example.com/acme-hiring",
        }
    ]

    refreshed = refresh_active_assumptions(store, signals)

    assert refreshed[0]["id"] == assumption_id
    assert refreshed[0]["status"] == "confirmed"
    assert len(refreshed[0]["evidence"]) == 1
    assert refreshed[0]["evidence"][0]["source_ref"] == "https://example.com/acme-hiring"

    refreshed_again = refresh_active_assumptions(store, signals)

    assert refreshed_again[0]["status"] == "confirmed"
    assert len(refreshed_again[0]["evidence"]) == 1

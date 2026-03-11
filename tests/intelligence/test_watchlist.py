"""Tests for watchlist persistence and intel annotation."""

from intelligence.watchlist import (
    IntelFollowUpStore,
    WatchlistStore,
    annotate_items,
    find_evidence_for_text,
    list_all_watchlist_items,
    sort_ranked_items,
)


def test_watchlist_store_upserts_by_label(tmp_path):
    store = WatchlistStore(tmp_path / "watchlist.json")

    first = store.save_item({"label": "OpenAI", "priority": "high"})
    second = store.save_item({"label": " openai ", "priority": "medium", "why": "updated"})

    assert first["id"] == second["id"]
    items = store.list_items()
    assert len(items) == 1
    assert items[0]["why"] == "updated"


def test_watchlist_store_preserves_pipeline_metadata(tmp_path):
    store = WatchlistStore(tmp_path / "watchlist.json")

    item = store.save_item(
        {
            "label": "OpenAI",
            "kind": "company",
            "aliases": ["Open AI"],
            "domain": "openai.com",
            "github_org": "openai",
            "ticker": " msft ",
            "topics": ["AI Act"],
            "geographies": ["EU", "UK"],
            "linked_dossier_ids": ["dos_123"],
        }
    )

    assert item["domain"] == "openai.com"
    assert item["github_org"] == "openai"
    assert item["ticker"] == "MSFT"
    assert item["topics"] == ["AI Act"]
    assert item["geographies"] == ["EU", "UK"]
    assert item["linked_dossier_ids"] == ["dos_123"]


def test_annotate_items_and_evidence(tmp_path):
    store = WatchlistStore(tmp_path / "watchlist.json")
    item = store.save_item({"label": "Anthropic", "priority": "high", "why": "Relevant to role"})

    items = [
        {
            "title": "Anthropic unveils Claude update",
            "summary": "The Anthropic team shipped a new release.",
            "url": "https://example.com/anthropic",
            "source": "rss",
            "scraped_at": "2026-03-06T09:00:00",
            "tags": [],
        },
        {
            "title": "General infra news",
            "summary": "Nothing specific",
            "url": "https://example.com/generic",
            "source": "rss",
            "scraped_at": "2026-03-06T10:00:00",
            "tags": [],
        },
    ]

    annotate_items(items, [item])
    ranked = sort_ranked_items(items)

    assert ranked[0]["title"] == "Anthropic unveils Claude update"
    assert ranked[0]["why_this_matters"] == "Relevant to role"

    evidence = find_evidence_for_text("Anthropic strategy", ranked)
    assert evidence == ["Anthropic: Anthropic unveils Claude update"]


def test_follow_up_store_removes_empty_unsaved_entry(tmp_path):
    store = IntelFollowUpStore(tmp_path / "followups.json")
    store.upsert(url="https://example.com/a", title="A", saved=True, note="keep")
    assert len(store.list_items()) == 1

    store.upsert(url="https://example.com/a", title="A", saved=False, note="")
    assert store.list_items() == []


def test_watchlist_store_ignores_corrupted_json(tmp_path):
    path = tmp_path / "watchlist.json"
    path.write_text("{not-json", encoding="utf-8")

    store = WatchlistStore(path)

    assert store.list_items() == []


def test_follow_up_store_ignores_corrupted_json(tmp_path):
    path = tmp_path / "followups.json"
    path.write_text("{not-json", encoding="utf-8")

    store = IntelFollowUpStore(path)

    assert store.list_items() == []


def test_list_all_watchlist_items_skips_corrupted_default_store(tmp_path, monkeypatch):
    coach_home = tmp_path / "coach"
    coach_home.mkdir()
    (coach_home / "watchlist.json").write_text("{not-json", encoding="utf-8")

    monkeypatch.setattr(
        "storage_paths.get_coach_home",
        lambda candidate=None: coach_home,
    )

    assert list_all_watchlist_items(coach_home) == []

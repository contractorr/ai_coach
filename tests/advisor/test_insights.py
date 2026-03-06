"""Tests for InsightStore — save, dedup, TTL, get_active."""

from datetime import datetime, timedelta

import pytest

from advisor.insights import DEFAULT_TTL_DAYS, Insight, InsightStore, InsightType


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "intel.db"
    return InsightStore(db)


def _make_insight(
    type=InsightType.GOAL_STALE,
    severity=5,
    title="Test insight",
    detail="Detail",
    **kwargs,
):
    return Insight(type=type, severity=severity, title=title, detail=detail, **kwargs)


class TestInsightStore:
    def test_save_and_retrieve(self, store):
        i = _make_insight()
        assert store.save(i) is True
        active = store.get_active()
        assert len(active) == 1
        assert active[0]["title"] == "Test insight"
        assert active[0]["type"] == "goal_stale"

    def test_dedup_by_hash(self, store):
        i1 = _make_insight(title="Same title")
        i2 = _make_insight(title="Same title")
        assert store.save(i1) is True
        assert store.save(i2) is False
        assert len(store.get_active()) == 1

    def test_different_titles_not_deduped(self, store):
        i1 = _make_insight(title="A")
        i2 = _make_insight(title="B")
        store.save(i1)
        store.save(i2)
        assert len(store.get_active()) == 2

    def test_expired_not_returned(self, store):
        expired = _make_insight(
            title="Old",
            expires_at=datetime.now() - timedelta(days=1),
        )
        store.save(expired)
        assert len(store.get_active()) == 0

    def test_expired_allows_reinsert(self, store):
        """Once expired, same hash can be saved again."""
        expired = _make_insight(
            title="Recycled",
            expires_at=datetime.now() - timedelta(days=1),
        )
        store.save(expired)
        fresh = _make_insight(title="Recycled")
        assert store.save(fresh) is True

    def test_filter_by_type(self, store):
        store.save(_make_insight(type=InsightType.GOAL_STALE, title="A"))
        store.save(_make_insight(type=InsightType.INTEL_MATCH, title="B"))
        result = store.get_active(insight_type="goal_stale")
        assert len(result) == 1
        assert result[0]["type"] == "goal_stale"

    def test_filter_by_min_severity(self, store):
        store.save(_make_insight(severity=3, title="Low"))
        store.save(_make_insight(severity=8, title="High"))
        result = store.get_active(min_severity=5)
        assert len(result) == 1
        assert result[0]["title"] == "High"

    def test_limit(self, store):
        for i in range(5):
            store.save(_make_insight(title=f"Insight {i}"))
        assert len(store.get_active(limit=3)) == 3

    def test_default_ttl(self):
        i = _make_insight()
        expected = i.created_at + timedelta(days=DEFAULT_TTL_DAYS)
        assert abs((i.expires_at - expected).total_seconds()) < 1

    def test_evidence_and_actions_roundtrip(self, store):
        i = _make_insight(
            evidence=["e1", "e2"],
            suggested_actions=["a1"],
        )
        store.save(i)
        row = store.get_active()[0]
        assert row["evidence"] == ["e1", "e2"]
        assert row["suggested_actions"] == ["a1"]

    def test_source_url_persisted(self, store):
        i = _make_insight(source_url="https://example.com")
        store.save(i)
        row = store.get_active()[0]
        assert row["source_url"] == "https://example.com"

    def test_insight_hash_auto_computed(self):
        i = _make_insight(type=InsightType.INTEL_MATCH, title="Test")
        assert len(i.insight_hash) == 16

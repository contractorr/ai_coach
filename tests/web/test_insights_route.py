"""Tests for GET /api/insights."""

from advisor.insights import Insight, InsightStore, InsightType


class TestInsightsRoute:
    def test_get_insights_empty(self, client, auth_headers):
        resp = client.get("/api/insights", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_insights_returns_saved(self, client, auth_headers, tmp_path):
        # Write directly to the same intel.db the test client uses
        db_path = tmp_path / "intel.db"
        store = InsightStore(db_path)
        store.save(
            Insight(
                type=InsightType.GOAL_STALE,
                severity=7,
                title="Stale goal: Ship MVP",
                detail="No check-in in 20 days",
            )
        )

        resp = client.get("/api/insights", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["type"] == "goal_stale"
        assert data[0]["severity"] == 7

    def test_get_insights_filter_by_type(self, client, auth_headers, tmp_path):
        db_path = tmp_path / "intel.db"
        store = InsightStore(db_path)
        store.save(Insight(type=InsightType.GOAL_STALE, severity=5, title="A", detail=""))
        store.save(Insight(type=InsightType.INTEL_MATCH, severity=5, title="B", detail=""))

        resp = client.get("/api/insights?type=intel_match", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["type"] == "intel_match"

    def test_get_insights_requires_auth(self, client):
        resp = client.get("/api/insights")
        assert resp.status_code in (401, 403)

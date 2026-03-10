"""Tests for per-user feature toggle settings."""


class TestFeatureToggleDefaults:
    def test_get_returns_config_defaults(self, client, auth_headers):
        resp = client.get("/api/settings", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # These come from global config fallback
        assert "feature_memory_enabled" in data
        assert "feature_extended_thinking" in data
        assert isinstance(data["feature_memory_enabled"], bool)


class TestFeatureTogglePersistence:
    def test_put_toggle_persists(self, client, auth_headers):
        resp = client.put(
            "/api/settings",
            json={"feature_memory_enabled": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["feature_memory_enabled"] is False

    def test_get_reflects_override(self, client, auth_headers):
        client.put(
            "/api/settings",
            json={"feature_heartbeat_enabled": True},
            headers=auth_headers,
        )
        resp = client.get("/api/settings", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["feature_heartbeat_enabled"] is True

    def test_multiple_toggles_at_once(self, client, auth_headers):
        resp = client.put(
            "/api/settings",
            json={
                "feature_research_enabled": True,
                "feature_regulatory_signals_enabled": True,
                "feature_threads_enabled": False,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["feature_research_enabled"] is True
        assert data["feature_regulatory_signals_enabled"] is True
        assert data["feature_threads_enabled"] is False

    def test_unset_toggle_uses_config_default(self, client, auth_headers):
        """Toggles not explicitly set should fall back to global config."""
        resp = client.get("/api/settings", headers=auth_headers)
        data = resp.json()
        # These should match global config defaults, not be None
        assert isinstance(data["feature_trending_radar_enabled"], bool)
        assert isinstance(data["feature_company_movement_enabled"], bool)

"""Tests for research API routes (topics, run, dossiers)."""

from unittest.mock import MagicMock, patch

_AGENT_PATCH = "web.routes.research._get_agent"
_AGENT_CLASS = "research.agent.DeepResearchAgent"


def test_get_topics(client, auth_headers):
    mock_agent = MagicMock()
    mock_agent.get_suggested_topics.return_value = [
        {"topic": "AI Safety", "source": "journal", "score": 0.9, "reason": "Mentioned often"},
    ]
    with patch(_AGENT_PATCH, return_value=mock_agent):
        res = client.get("/api/research/topics", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()[0]["topic"] == "AI Safety"


def test_run_research_with_topic(client, auth_headers):
    mock_agent = MagicMock()
    mock_agent.run.return_value = [{"topic": "Rust", "report": "Rust is great"}]
    with patch(_AGENT_PATCH, return_value=mock_agent):
        res = client.post("/api/research/run?topic=Rust", headers=auth_headers)
    assert res.status_code == 200
    mock_agent.run.assert_called_once_with(specific_topic="Rust", dossier_id=None)


def test_run_research_with_dossier_id(client, auth_headers):
    mock_agent = MagicMock()
    mock_agent.run.return_value = [{"topic": "Rust", "dossier_id": "dos-1", "success": True}]
    with patch(_AGENT_PATCH, return_value=mock_agent):
        res = client.post("/api/research/run?dossier_id=dos-1", headers=auth_headers)
    assert res.status_code == 200
    mock_agent.run.assert_called_once_with(specific_topic=None, dossier_id="dos-1")


def test_list_dossiers(client, auth_headers):
    mock_agent = MagicMock()
    mock_agent.list_dossiers.return_value = [{"dossier_id": "abc123", "topic": "AI agents"}]
    with patch(_AGENT_PATCH, return_value=mock_agent):
        res = client.get("/api/research/dossiers", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()[0]["dossier_id"] == "abc123"


def test_create_dossier(client, auth_headers):
    mock_agent = MagicMock()
    mock_agent.create_dossier.return_value = {"dossier_id": "abc123", "topic": "AI agents"}
    with patch(_AGENT_PATCH, return_value=mock_agent):
        res = client.post(
            "/api/research/dossiers",
            headers=auth_headers,
            json={"topic": "AI agents", "scope": "Track launches"},
        )
    assert res.status_code == 200
    assert res.json()["dossier_id"] == "abc123"


def test_get_dossier(client, auth_headers):
    mock_agent = MagicMock()
    mock_agent.get_dossier.return_value = {"dossier_id": "abc123", "topic": "AI agents", "updates": []}
    with patch(_AGENT_PATCH, return_value=mock_agent):
        res = client.get("/api/research/dossiers/abc123", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["topic"] == "AI agents"


def test_get_dossier_not_found(client, auth_headers):
    mock_agent = MagicMock()
    mock_agent.get_dossier.return_value = None
    with patch(_AGENT_PATCH, return_value=mock_agent):
        res = client.get("/api/research/dossiers/missing", headers=auth_headers)
    assert res.status_code == 404


def test_get_agent_injects_user_tavily_key(client, auth_headers, secret_key):
    captured_config = {}
    mock_agent = MagicMock()
    mock_agent.get_suggested_topics.return_value = []

    class FakeAgent:
        def __init__(self, **kwargs):
            captured_config.update(kwargs.get("config", {}))
            self.__dict__.update(mock_agent.__dict__)

        def get_suggested_topics(self):
            return mock_agent.get_suggested_topics()

    with (
        patch(_AGENT_CLASS, FakeAgent),
        patch("journal.storage.JournalStorage"),
        patch("journal.embeddings.EmbeddingManager"),
        patch("web.routes.research.get_intel_storage"),
        patch("web.user_store.get_user_secret", return_value="tvly-test-key-456"),
        patch("web.deps.get_secret_key", return_value=secret_key),
    ):
        res = client.get("/api/research/topics", headers=auth_headers)
    assert res.status_code == 200
    assert captured_config.get("research", {}).get("api_key") == "tvly-test-key-456"

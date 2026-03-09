"""Tests for new capability scrapers — METR, EpochAI, AIIndex, ARCEvals, FrontierEvalsGitHub."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from intelligence.sources.ai_capabilities import (
    AIIndexScraper,
    ARCEvalsScraper,
    EpochAIScraper,
    FrontierEvalsGitHubScraper,
    METRScraper,
)


@pytest.fixture(scope="module")
def storage():
    return MagicMock(name="intel_storage")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _mock_http_response(text: str, status_code: int = 200):
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


# ---------------------------------------------------------------------------
# METRScraper
# ---------------------------------------------------------------------------


class TestMETRScraper:
    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_valid_extraction(self, mock_extract, storage):
        mock_extract.return_value = [
            {
                "task_category": "coding",
                "current_success_rate": "70%",
                "projected_horizon_months": 6,
                "eval_date": "2025-01-15",
            }
        ]
        scraper = METRScraper(storage)
        scraper.client = AsyncMock()
        resp = _mock_http_response("<html><body>METR research data</body></html>")
        scraper.client.get = AsyncMock(return_value=resp)

        items = await scraper.scrape()
        assert len(items) >= 1
        assert items[0].source == "metr_evals"
        assert "coding" in items[0].title

    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_unreachable_returns_empty(self, mock_extract, storage):
        scraper = METRScraper(storage)
        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(side_effect=httpx.ConnectError("unreachable"))

        items = await scraper.scrape()
        assert items == []

    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_llm_returns_invalid_skipped(self, mock_extract, storage):
        """LLM returns items missing required fields — should be skipped."""
        mock_extract.return_value = [{"some_random_field": "value"}]
        scraper = METRScraper(storage)
        scraper.client = AsyncMock()
        resp = _mock_http_response("<html>data</html>")
        scraper.client.get = AsyncMock(return_value=resp)

        items = await scraper.scrape()
        assert items == []


# ---------------------------------------------------------------------------
# EpochAIScraper
# ---------------------------------------------------------------------------


class TestEpochAIScraper:
    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_valid_extraction(self, mock_extract, storage):
        mock_extract.return_value = [
            {
                "model_name": "GPT-5",
                "training_compute_flops": "1e26",
                "capability_notes": "Major reasoning jump",
                "publication_date": "2025-06-01",
            }
        ]
        scraper = EpochAIScraper(storage)
        scraper.client = AsyncMock()
        resp = _mock_http_response("<html>Epoch data</html>")
        scraper.client.get = AsyncMock(return_value=resp)

        items = await scraper.scrape()
        assert len(items) >= 1
        assert "GPT-5" in items[0].title

    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_unreachable_returns_empty(self, mock_extract, storage):
        scraper = EpochAIScraper(storage)
        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(side_effect=httpx.ConnectError("fail"))

        items = await scraper.scrape()
        assert items == []


# ---------------------------------------------------------------------------
# AIIndexScraper
# ---------------------------------------------------------------------------


class TestAIIndexScraper:
    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_valid_extraction(self, mock_extract, storage):
        mock_extract.return_value = [
            {
                "metric_name": "ImageNet accuracy",
                "current_value": "95%",
                "year_over_year_change": "+2%",
                "report_year": 2025,
            }
        ]
        scraper = AIIndexScraper(storage)
        scraper.client = AsyncMock()
        resp = _mock_http_response("<html>AI Index</html>")
        scraper.client.get = AsyncMock(return_value=resp)

        items = await scraper.scrape()
        assert len(items) >= 1
        assert "ImageNet" in items[0].title

    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_unreachable_returns_empty(self, mock_extract, storage):
        scraper = AIIndexScraper(storage)
        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(side_effect=httpx.ConnectError("fail"))

        items = await scraper.scrape()
        assert items == []


# ---------------------------------------------------------------------------
# ARCEvalsScraper
# ---------------------------------------------------------------------------


class TestARCEvalsScraper:
    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_valid_extraction(self, mock_extract, storage):
        mock_extract.return_value = [
            {
                "model_name": "Claude Opus 4",
                "task_category": "biosecurity",
                "score": "0.85",
                "eval_date": "2025-03-01",
            }
        ]
        scraper = ARCEvalsScraper(storage)
        scraper.client = AsyncMock()
        resp = _mock_http_response("<html>ARC evals</html>")
        scraper.client.get = AsyncMock(return_value=resp)

        items = await scraper.scrape()
        assert len(items) >= 1
        assert "Claude Opus 4" in items[0].title

    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_unreachable_returns_empty(self, mock_extract, storage):
        scraper = ARCEvalsScraper(storage)
        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(side_effect=httpx.ConnectError("fail"))

        items = await scraper.scrape()
        assert items == []

    @patch("intelligence.sources.ai_capabilities._llm_extract_json")
    async def test_invalid_llm_output_skipped(self, mock_extract, storage):
        """Items without model_name are skipped."""
        mock_extract.return_value = [{"task_category": "test"}]
        scraper = ARCEvalsScraper(storage)
        scraper.client = AsyncMock()
        resp = _mock_http_response("<html>data</html>")
        scraper.client.get = AsyncMock(return_value=resp)

        items = await scraper.scrape()
        assert items == []


# ---------------------------------------------------------------------------
# FrontierEvalsGitHubScraper
# ---------------------------------------------------------------------------


def _make_github_issue(title, body="", created_at="2025-06-01T00:00:00Z", html_url=""):
    return {
        "title": title,
        "body": body,
        "created_at": created_at,
        "html_url": html_url or f"https://github.com/test/repo/issues/{hash(title) % 1000}",
    }


class TestFrontierEvalsGitHubScraper:
    @patch("intelligence.sources.ai_capabilities._llm_extract_single")
    async def test_filters_maintenance_issues(self, mock_extract, storage):
        """Maintenance issues (LLM returns {}) are filtered out."""
        issues = [
            _make_github_issue("Fix numpy import error", "numpy version conflict"),
            _make_github_issue("Update CI config", "fix yaml syntax"),
            _make_github_issue(
                "New benchmark for long-context retrieval",
                "This adds a new benchmark for testing 100k context window",
            ),
            _make_github_issue("Typo in README", "fix typo"),
            _make_github_issue(
                "Model fails on multi-step reasoning",
                "GPT-4 consistently fails on chained deduction tasks",
            ),
        ]

        def side_effect(text, prompt):
            if "numpy" in text or "CI config" in text or "Typo" in text or "Update" in text:
                return {}  # maintenance
            if "long-context" in text:
                return {
                    "repo_name": "test/repo",
                    "capability_tested": "long-context retrieval",
                    "evaluation_method": "benchmark suite",
                    "significance": "Tests 100k context windows",
                    "is_limitation": False,
                }
            if "multi-step reasoning" in text:
                return {
                    "repo_name": "test/repo",
                    "capability_tested": "multi-step reasoning",
                    "evaluation_method": "chained deduction test",
                    "significance": "Consistent failure mode",
                    "is_limitation": True,
                }
            return {}

        mock_extract.side_effect = side_effect

        scraper = FrontierEvalsGitHubScraper(storage)
        scraper.client = AsyncMock()

        # Mock API response for each repo
        api_response = _mock_http_response(json.dumps(issues))
        api_response.json = MagicMock(return_value=issues)
        scraper.client.get = AsyncMock(return_value=api_response)

        items = await scraper.scrape()

        # Should only have capability-relevant issues (not maintenance)
        titles = [item.title for item in items]
        assert any("long-context" in t for t in titles)
        assert any("multi-step" in t for t in titles)
        assert not any("numpy" in t for t in titles)
        assert not any("Typo" in t for t in titles)

    @patch("intelligence.sources.ai_capabilities._llm_extract_single")
    async def test_limitation_flag(self, mock_extract, storage):
        """Issues describing limitations have is_limitation=True in output."""
        issues = [
            _make_github_issue(
                "Model fails on spatial reasoning", "All tested models fail on 3D spatial tasks"
            ),
        ]
        mock_extract.return_value = {
            "repo_name": "test/repo",
            "capability_tested": "spatial reasoning",
            "evaluation_method": "3D spatial test suite",
            "significance": "Universal failure mode",
            "is_limitation": True,
        }

        scraper = FrontierEvalsGitHubScraper(storage)
        scraper.client = AsyncMock()
        api_response = _mock_http_response(json.dumps(issues))
        api_response.json = MagicMock(return_value=issues)
        scraper.client.get = AsyncMock(return_value=api_response)

        items = await scraper.scrape()
        assert len(items) >= 1
        # Check is_limitation is in the summary JSON
        summary = json.loads(items[0].summary)
        assert summary["is_limitation"] is True
        # Check limitation tag
        assert "limitation" in items[0].tags

    @patch("intelligence.sources.ai_capabilities._llm_extract_single")
    async def test_per_repo_cap_20(self, mock_extract, storage):
        """Never fetch more than 20 issues per repo."""
        # Create 25 issues
        issues = [_make_github_issue(f"Issue {i}") for i in range(25)]
        mock_extract.return_value = {
            "repo_name": "test/repo",
            "capability_tested": "test",
            "evaluation_method": "test",
            "significance": "test",
            "is_limitation": False,
        }

        scraper = FrontierEvalsGitHubScraper(storage)
        scraper.client = AsyncMock()
        api_response = _mock_http_response(json.dumps(issues))
        api_response.json = MagicMock(return_value=issues)
        scraper.client.get = AsyncMock(return_value=api_response)

        # The scraper calls _fetch_repo_issues for each of 4 repos
        # Each should process at most 20 issues
        await scraper._fetch_repo_issues("test/repo")
        assert mock_extract.call_count <= 20

    @patch("intelligence.sources.ai_capabilities._llm_extract_single")
    async def test_unreachable_repo_returns_empty(self, mock_extract, storage):
        """Unreachable repo returns empty list without raising."""
        scraper = FrontierEvalsGitHubScraper(storage)
        scraper.client = AsyncMock()
        scraper.client.get = AsyncMock(side_effect=httpx.ConnectError("unreachable"))

        items = await scraper.scrape()
        assert items == []

    @patch("intelligence.sources.ai_capabilities._llm_extract_single")
    async def test_rate_limited_repo_returns_empty(self, mock_extract, storage):
        """403 from GitHub returns empty list."""
        scraper = FrontierEvalsGitHubScraper(storage)
        scraper.client = AsyncMock()
        resp = _mock_http_response("", status_code=403)
        resp.json = MagicMock(return_value=[])
        scraper.client.get = AsyncMock(return_value=resp)

        items = await scraper._fetch_repo_issues("test/repo")
        assert items == []

"""Tests for web app startup helpers."""

from unittest.mock import patch

import pytest
from fastapi.middleware.cors import CORSMiddleware

from web import app as web_app


def test_start_intel_scheduler_can_be_disabled(monkeypatch):
    monkeypatch.setenv("DISABLE_INTEL_SCHEDULER", "true")

    with patch("intelligence.scheduler.IntelScheduler") as scheduler_cls:
        result = web_app._start_intel_scheduler()

    assert result is None
    scheduler_cls.assert_not_called()


def test_start_intel_scheduler_returns_none_on_failure(monkeypatch):
    monkeypatch.delenv("DISABLE_INTEL_SCHEDULER", raising=False)

    with patch("intelligence.scheduler.IntelScheduler", side_effect=RuntimeError("boom")):
        result = web_app._start_intel_scheduler()

    assert result is None


def test_start_intel_scheduler_uses_web_scheduler_path(monkeypatch):
    monkeypatch.delenv("DISABLE_INTEL_SCHEDULER", raising=False)

    with patch("intelligence.scheduler.IntelScheduler") as scheduler_cls:
        result = web_app._start_intel_scheduler()

    mock_scheduler = scheduler_cls.return_value
    assert result is mock_scheduler
    mock_scheduler.start_web.assert_called_once()


def test_verify_secret_key_requires_env(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY required"):
        web_app._verify_secret_key()


def test_create_app_mounts_projects_route():
    app = web_app.create_app()

    paths = {route.path for route in app.routes}
    assert "/api/projects/issues" in paths
    assert "/api/health" in paths


def test_create_app_uses_frontend_origin_from_env(monkeypatch):
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://frontend.example.com")

    app = web_app.create_app()

    cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
    assert cors.kwargs["allow_origins"] == ["https://frontend.example.com"]

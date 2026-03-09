"""Tests for security fixes (T1.1-T1.5)."""

import pytest

from cli.logging_config import _redact_sensitive
from intelligence.scheduler import _parse_cron
from intelligence.scraper import IntelItem, IntelStorage, validate_url
from journal.storage import JournalStorage, _sanitize_slug, _sanitize_tag


class TestPathTraversal:
    """T1.1: Path traversal in journal storage."""

    def test_sanitize_slug_removes_path_separators(self):
        assert "/" not in _sanitize_slug("../../etc/passwd")
        assert "\\" not in _sanitize_slug("..\\..\\windows")

    def test_sanitize_slug_only_allows_safe_chars(self):
        slug = _sanitize_slug("Hello World! @#$%")
        assert slug == "hello-world-"

    def test_sanitize_slug_truncates(self):
        long = "a" * 100
        assert len(_sanitize_slug(long)) == 50

    def test_path_traversal_blocked(self, tmp_path):
        storage = JournalStorage(tmp_path / "journal")
        with pytest.raises(ValueError, match="Path escapes"):
            # Force a path traversal by calling _validate_path directly
            storage._validate_path(tmp_path / "journal" / ".." / "outside" / "evil.md")

    def test_normal_path_allowed(self, tmp_path):
        storage = JournalStorage(tmp_path / "journal")
        result = storage._validate_path(tmp_path / "journal" / "safe.md")
        assert "safe.md" in str(result)


class TestInputSanitization:
    """T1.2: Input sanitization for journal content."""

    def test_invalid_entry_type_rejected(self, tmp_path):
        storage = JournalStorage(tmp_path / "journal")
        with pytest.raises(ValueError, match="Invalid entry_type"):
            storage.create(content="test", entry_type="EVIL_TYPE")

    def test_valid_entry_types(self, tmp_path):
        storage = JournalStorage(tmp_path / "journal")
        for et in ("daily", "goal", "reflection", "research"):
            path = storage.create(content="test", entry_type=et)
            assert path.exists()

    def test_content_length_limit(self, tmp_path):
        storage = JournalStorage(tmp_path / "journal")
        with pytest.raises(ValueError, match="max length"):
            storage.create(content="x" * 200_000, entry_type="daily")

    def test_tag_sanitization(self):
        assert _sanitize_tag("normal-tag") == "normal-tag"
        assert len(_sanitize_tag("a" * 100)) == 50
        # Special chars stripped
        tag = _sanitize_tag("tag<script>alert</script>")
        assert "<" not in tag


class TestPIIRedaction:
    """T1.4: PII in debug logs."""

    def test_redacts_anthropic_key(self):
        event = {"event": "key=sk-ant-api03-abcdefghijklmnop-qrstuvwx"}
        result = _redact_sensitive(None, None, event)
        # New redaction uses _mask_token: preserves first 6 + last 4 for long tokens
        assert "abcdefghijklmnop" not in result["event"]

    def test_redacts_bearer_token(self):
        event = {"event": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9abcdef"}
        result = _redact_sensitive(None, None, event)
        # Bearer token masked — full middle portion removed
        assert "OiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result["event"]

    def test_redacts_email(self):
        event = {"event": "User email is test@example.com"}
        result = _redact_sensitive(None, None, event)
        assert "test@example.com" not in result["event"]

    def test_preserves_non_sensitive(self):
        event = {"event": "Normal log message", "count": 42}
        result = _redact_sensitive(None, None, event)
        assert result["event"] == "Normal log message"
        assert result["count"] == 42


class TestURLValidation:
    """T1.5: URL validation for scraped content."""

    def test_valid_http(self):
        assert validate_url("https://example.com/article")
        assert validate_url("http://news.ycombinator.com/item?id=123")

    def test_rejects_non_http(self):
        assert not validate_url("ftp://evil.com/file")
        assert not validate_url("javascript:alert(1)")
        assert not validate_url("file:///etc/passwd")

    def test_rejects_empty(self):
        assert not validate_url("")
        assert not validate_url(None)

    def test_rejects_no_domain(self):
        assert not validate_url("http://")
        assert not validate_url("https://localhost")

    def test_allows_internal_research_scheme(self):
        assert validate_url("research://topic/20240101")

    def test_url_validation_in_save(self, tmp_path):
        storage = IntelStorage(tmp_path / "test.db")
        item = IntelItem(
            source="test",
            title="Bad URL",
            url="javascript:alert(1)",
            summary="test",
        )
        assert not storage.save(item)


class TestCronParsing:
    """T2.1: Cron parsing helper."""

    def test_full_expression(self):
        _parse_cron("30 8 * * 1")
        # Should not raise

    def test_partial_expression_uses_defaults(self):
        _parse_cron("30")
        # Should use defaults for missing fields

    def test_custom_defaults(self):
        _parse_cron("0", defaults={"hour": "21", "day_of_week": "0"})
        # Should not raise

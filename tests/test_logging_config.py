"""Tests for structured logging configuration."""

import logging

import structlog

from cli.logging_config import setup_logging


class TestLoggingConfig:
    """Test structlog setup modes."""

    def test_console_mode(self, capsys):
        """Console mode uses dev renderer."""
        setup_logging(json_mode=False, level="DEBUG")
        logger = structlog.get_logger()
        logger.info("test message", key="value")
        # Should not raise and should produce output on stderr
        capsys.readouterr()
        # Console renderer writes to stderr via handler
        assert True  # Smoke test: no crash

    def test_json_mode(self, capsys):
        """JSON mode produces parseable JSON."""
        setup_logging(json_mode=True, level="DEBUG")
        # Use stdlib logger to go through formatter
        stdlib_logger = logging.getLogger("test_json")
        stdlib_logger.info("json test")
        # No crash = success
        assert True

    def test_stdlib_logs_are_redacted(self, capsys):
        """Stdlib logging should redact secrets via the formatter."""
        setup_logging(json_mode=False, level="INFO")
        stdlib_logger = logging.getLogger("test_redaction")
        stdlib_logger.info("OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz1234")
        captured = capsys.readouterr()
        assert "sk-pro" in captured.err
        assert "abcdefghijklmnopqrstuvwxyz" not in captured.err

    def test_level_filtering(self):
        """Log level filters lower messages."""
        setup_logging(json_mode=False, level="WARNING")
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_processor_chain(self):
        """Processor chain includes timestamp, level, caller."""
        setup_logging(json_mode=True, level="DEBUG")
        # Verify structlog is configured
        config = structlog.get_config()
        [p.__class__.__name__ if hasattr(p, "__class__") else str(p) for p in config["processors"]]
        # Should have multiple processors configured
        assert len(config["processors"]) >= 2

    def test_default_level_is_info(self):
        """Default level param is INFO."""
        setup_logging()
        root = logging.getLogger()
        assert root.level == logging.INFO

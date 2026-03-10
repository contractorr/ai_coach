"""Structured logging configuration using structlog."""

import logging
import re
import sys

import structlog

from services.redact import RedactingFormatter, redact_sensitive_text

_MASKED_SECRET_RE = re.compile(r"(?:[A-Za-z0-9._-]{2,})\.\.\.(?:[A-Za-z0-9._-]{3,})")
_MASKED_AUTH_RE = re.compile(
    r"(\bAuthorization\s*:\s*(?:Bearer|Token|Basic)\s+)(?:[A-Za-z0-9._-]{2,}\.\.\.[A-Za-z0-9._-]{3,})",
    re.IGNORECASE,
)


def _redact_sensitive(_, __, event_dict: dict) -> dict:
    """Structlog processor to redact API keys/tokens from log output."""
    for key, value in event_dict.items():
        if isinstance(value, str):
            redacted = redact_sensitive_text(value)
            if redacted != value:
                redacted = _MASKED_AUTH_RE.sub(r"\1[REDACTED]", redacted)
                redacted = _MASKED_SECRET_RE.sub("[REDACTED]", redacted)
            event_dict[key] = redacted
    return event_dict


def setup_logging(json_mode: bool = False, level: str = "INFO") -> None:
    """Configure structlog with appropriate renderer.

    Args:
        json_mode: Use JSON renderer (for daemon/machine consumption).
                   False = console renderer (Rich-compatible, for CLI).
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        _redact_sensitive,
    ]

    if json_mode:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog formatter
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(RedactingFormatter(formatter))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

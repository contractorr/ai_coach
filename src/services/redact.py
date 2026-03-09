"""Secret redaction utilities shared across logging surfaces."""

from __future__ import annotations

import logging
import re

_PREFIX_PATTERNS = [
    r"sk-ant-[A-Za-z0-9_-]{10,}",
    r"sk-proj-[A-Za-z0-9_-]{10,}",
    r"sk-or-v1-[A-Za-z0-9_-]{10,}",
    r"sk-[A-Za-z0-9_-]{10,}",
    r"ghp_[A-Za-z0-9]{10,}",
    r"gho_[A-Za-z0-9]{10,}",
    r"ghu_[A-Za-z0-9]{10,}",
    r"ghs_[A-Za-z0-9]{10,}",
    r"ghr_[A-Za-z0-9]{10,}",
    r"github_pat_[A-Za-z0-9_]{10,}",
    r"xoxb-[A-Za-z0-9-]{10,}",
    r"xoxa-[A-Za-z0-9-]{10,}",
    r"xoxp-[A-Za-z0-9-]{10,}",
    r"xoxr-[A-Za-z0-9-]{10,}",
    r"xoxs-[A-Za-z0-9-]{10,}",
    r"xapp-[A-Za-z0-9-]{10,}",
    r"AIza[A-Za-z0-9_-]{30,}",
    r"AKIA[A-Z0-9]{16}",
    r"ASIA[A-Z0-9]{16}",
    r"SG\.[A-Za-z0-9._-]{10,}",
    r"hf_[A-Za-z0-9]{10,}",
    r"sk_live_[A-Za-z0-9]{10,}",
    r"sk_test_[A-Za-z0-9]{10,}",
    r"rk_live_[A-Za-z0-9]{10,}",
    r"rk_test_[A-Za-z0-9]{10,}",
    r"pk_live_[A-Za-z0-9]{10,}",
    r"pk_test_[A-Za-z0-9]{10,}",
    r"sq0atp-[A-Za-z0-9_-]{10,}",
    r"sq0csp-[A-Za-z0-9_-]{10,}",
    r"sq0idp-[A-Za-z0-9_-]{10,}",
    r"pat-[A-Za-z0-9_-]{10,}",
    r"glpat-[A-Za-z0-9_-]{10,}",
    r"npm_[A-Za-z0-9]{10,}",
    r"ya29\.[A-Za-z0-9._-]{10,}",
]

_SECRET_PREFIX_RE = re.compile(
    r"(?<![A-Za-z0-9])(?P<token>" + "|".join(_PREFIX_PATTERNS) + r")(?![A-Za-z0-9])"
)
_ENV_ASSIGNMENT_RE = re.compile(
    r"(?P<prefix>\b[A-Z0-9_]*(?:API_?KEY|TOKEN|SECRET|PASSWORD|CREDENTIALS?|AUTH|PRIVATE_KEY)\b"
    r"\s*=\s*)(?P<quote>['\"]?)(?P<value>[^\s'\"`]+)(?P=quote)",
    re.IGNORECASE,
)
_JSON_SECRET_RE = re.compile(
    r"(?P<prefix>[\"'](?:api[_-]?key|token|secret|password|credential(?:s)?|auth(?:orization)?|"
    r"private_key)[\"']\s*:\s*[\"'])(?P<value>.*?)(?P<suffix>[\"'])",
    re.IGNORECASE | re.DOTALL,
)
_AUTH_HEADER_RE = re.compile(
    r"(?P<prefix>\bAuthorization\s*:\s*(?:Bearer|Token|Basic)\s+)(?P<value>[A-Za-z0-9._~+/=-]{6,})",
    re.IGNORECASE,
)
_DB_URL_RE = re.compile(
    r"(?P<prefix>\b(?:postgres(?:ql)?|mysql(?:\+\w+)?|mongodb(?:\+\w+)?|redis|amqp(?:s)?|mssql)"
    r"://[^/\s:@]+:)(?P<password>[^@\s/]+)(?P<suffix>@[^\s]+)",
    re.IGNORECASE,
)
_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN(?: [^-]+)? PRIVATE KEY-----.*?-----END(?: [^-]+)? PRIVATE KEY-----",
    re.DOTALL,
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _mask_token(token: str) -> str:
    """Mask a secret token while preserving a small visible prefix/suffix."""
    if len(token) < 18:
        return "***"
    return f"{token[:6]}...{token[-4:]}"


def _replace_env_assignment(match: re.Match[str]) -> str:
    quote = match.group("quote") or ""
    return f"{match.group('prefix')}{quote}{_mask_token(match.group('value'))}{quote}"


def _replace_json_secret(match: re.Match[str]) -> str:
    return f"{match.group('prefix')}{_mask_token(match.group('value'))}{match.group('suffix')}"


def _replace_auth_header(match: re.Match[str]) -> str:
    return f"{match.group('prefix')}{_mask_token(match.group('value'))}"


def _replace_db_url(match: re.Match[str]) -> str:
    return f"{match.group('prefix')}***{match.group('suffix')}"


def redact_sensitive_text(text: str | None) -> str | None:
    """Redact common secret shapes from a string."""
    if text is None or text == "":
        return text

    try:
        redacted = _PRIVATE_KEY_RE.sub("[REDACTED PRIVATE KEY]", text)
        redacted = _DB_URL_RE.sub(_replace_db_url, redacted)
        redacted = _AUTH_HEADER_RE.sub(_replace_auth_header, redacted)
        redacted = _ENV_ASSIGNMENT_RE.sub(_replace_env_assignment, redacted)
        redacted = _JSON_SECRET_RE.sub(_replace_json_secret, redacted)
        redacted = _SECRET_PREFIX_RE.sub(
            lambda match: _mask_token(match.group("token")),
            redacted,
        )
        redacted = _EMAIL_RE.sub("REDACTED@email", redacted)
        return redacted
    except re.error:
        return text


class RedactingFormatter(logging.Formatter):
    """Wrap another formatter and redact the rendered text."""

    def __init__(self, wrapped: logging.Formatter | None = None):
        super().__init__()
        self._wrapped = wrapped or logging.Formatter()

    def format(self, record: logging.LogRecord) -> str:
        return redact_sensitive_text(self._wrapped.format(record)) or ""


__all__ = ["RedactingFormatter", "redact_sensitive_text"]

"""Tests for secret redaction helpers."""

from services.redact import redact_sensitive_text


def test_prefix_pattern_redaction_masks_long_tokens():
    text = "token=sk-ant-api03-abcdefghijklmnopqrstuvwxyz123456"
    redacted = redact_sensitive_text(text)
    assert "sk-ant...3456" in redacted
    assert "abcdefghijklmnopqrstuvwxyz" not in redacted


def test_env_assignment_redaction():
    text = 'OPENAI_API_KEY="sk-proj-abcdefghijklmnopqrstuvwxyz1234"'
    redacted = redact_sensitive_text(text)
    assert redacted == 'OPENAI_API_KEY="sk-pro...1234"'


def test_json_field_redaction():
    text = '{"apiKey": "github_pat_abcdefghijklmnopqrstuvwxyz_123456"}'
    redacted = redact_sensitive_text(text)
    assert 'github...3456' in redacted
    assert "abcdefghijklmnopqrstuvwxyz" not in redacted


def test_authorization_header_redaction():
    text = "Authorization: Bearer ya29.abcdefghijklmnopqrstuvwxyz123456"
    redacted = redact_sensitive_text(text)
    assert redacted == "Authorization: Bearer ya29.a...3456"


def test_db_connection_string_redaction():
    text = "postgres://alice:supersecret@db.internal:5432/app"
    redacted = redact_sensitive_text(text)
    assert redacted == "postgres://alice:***@db.internal:5432/app"


def test_private_key_block_redaction():
    text = """-----BEGIN PRIVATE KEY-----
abc123
-----END PRIVATE KEY-----"""
    redacted = redact_sensitive_text(text)
    assert redacted == "[REDACTED PRIVATE KEY]"


def test_short_token_masks_fully():
    text = "Authorization: Bearer sk-short"
    redacted = redact_sensitive_text(text)
    assert redacted == "Authorization: Bearer ***"

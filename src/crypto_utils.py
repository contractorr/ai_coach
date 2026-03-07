"""Fernet encryption helpers.

Stateless encrypt/decrypt for per-user secrets (user_store.py).
Legacy file-based functions kept for backward compat / migration.
"""

import json
from pathlib import Path
from typing import Any

import structlog
from cryptography.fernet import Fernet, InvalidToken

logger = structlog.get_logger()


def _get_fernet(secret_key: str) -> Fernet:
    """Create Fernet instance from SECRET_KEY (must be 32-byte url-safe base64)."""
    return Fernet(secret_key.encode() if isinstance(secret_key, str) else secret_key)


# --- Stateless value-level encrypt/decrypt (used by user_store) ---


def encrypt_value(fernet_key: str, plaintext: str) -> str:
    """Encrypt a single string value, return base64 token."""
    f = _get_fernet(fernet_key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(fernet_key: str, token: str, key_name: str = "") -> str | None:
    """Decrypt a single token. Returns None on failure."""
    try:
        f = _get_fernet(fernet_key)
        return f.decrypt(token.encode()).decode()
    except InvalidToken:
        logger.warning("crypto.decrypt_failed", key=key_name, reason="invalid_token")
        return None
    except Exception as e:
        logger.warning("crypto.decrypt_failed", key=key_name, reason=str(e))
        return None


# --- Legacy file-based secrets (kept for CLI / migration) ---


def _secrets_path() -> Path:
    return Path.home() / "coach" / "secrets.enc"


def load_secrets(secret_key: str) -> dict[str, Any]:
    """Load and decrypt secrets file. Returns empty dict if missing/invalid."""
    path = _secrets_path()
    if not path.exists():
        return {}
    try:
        f = _get_fernet(secret_key)
        decrypted = f.decrypt(path.read_bytes())
        return json.loads(decrypted)
    except (InvalidToken, json.JSONDecodeError, Exception):
        return {}


def save_secrets(secret_key: str, data: dict[str, Any]) -> None:
    """Encrypt and save secrets dict."""
    path = _secrets_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    f = _get_fernet(secret_key)
    encrypted = f.encrypt(json.dumps(data).encode())
    path.write_bytes(encrypted)


def get_secret(secret_key: str, key: str) -> str | None:
    """Get a single secret by key."""
    return load_secrets(secret_key).get(key)


def set_secret(secret_key: str, key: str, value: str) -> None:
    """Set a single secret."""
    data = load_secrets(secret_key)
    data[key] = value
    save_secrets(secret_key, data)


def delete_secret(secret_key: str, key: str) -> None:
    """Delete a single secret."""
    data = load_secrets(secret_key)
    data.pop(key, None)
    save_secrets(secret_key, data)

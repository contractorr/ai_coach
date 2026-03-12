"""Token counting utility using tiktoken."""

from __future__ import annotations

_encoder = None


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken cl100k_base. Falls back to len//4 on import error."""
    global _encoder
    if _encoder is None:
        try:
            import tiktoken

            _encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            return len(text) // 4
    try:
        return len(_encoder.encode(text))
    except Exception:
        return len(text) // 4

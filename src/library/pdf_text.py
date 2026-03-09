"""PDF text extraction helpers for Library uploads."""

from __future__ import annotations

import re
from io import BytesIO


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _extract_with_pypdf(payload: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""

    try:
        reader = PdfReader(BytesIO(payload))
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
        return _normalize_text("\n".join(parts))
    except Exception:
        return ""


def _extract_literal_pdf_strings(payload: bytes) -> str:
    try:
        raw = payload.decode("latin1", errors="ignore")
    except Exception:
        return ""

    parts: list[str] = []
    for match in re.finditer(r"\(([^()]*)\)\s*Tj", raw):
        value = match.group(1)
        if value.strip():
            parts.append(value)

    for match in re.finditer(r"\[(.*?)\]\s*TJ", raw, flags=re.DOTALL):
        segment = " ".join(re.findall(r"\(([^()]*)\)", match.group(1)))
        if segment.strip():
            parts.append(segment)

    return _normalize_text(" ".join(parts))


def extract_text_from_pdf_bytes(payload: bytes) -> str:
    """Extract human-readable text from a PDF payload.

    Prefers `pypdf` when available and falls back to a light literal-string scan
    that works for simple text PDFs used in tests.
    """

    text = _extract_with_pypdf(payload)
    if text:
        return text
    return _extract_literal_pdf_strings(payload)

"""Token budget utilities for context truncation."""

from __future__ import annotations

from services.tokens import count_tokens


def tokens_to_chars(tokens: int) -> int:
    """Convert a token budget to an approximate char budget (4 chars/token)."""
    return tokens * 4


def truncate_lines_to_tokens(text: str, token_budget: int) -> str:
    """Truncate text at line boundaries to fit within a token budget."""
    if count_tokens(text) <= token_budget:
        return text
    lines = text.split("\n")
    kept: list[str] = []
    for line in lines:
        candidate = "\n".join([*kept, line]) if kept else line
        if count_tokens(candidate) > token_budget:
            break
        kept.append(line)
    return "\n".join(kept) if kept else ""


def truncate_to_token_budget(
    journal_ctx: str, intel_ctx: str, weight: float, max_tokens: int
) -> tuple[str, str]:
    """Ensure combined context fits within max_tokens."""
    total_tokens = count_tokens(journal_ctx) + count_tokens(intel_ctx)
    if total_tokens <= max_tokens:
        return journal_ctx, intel_ctx

    journal_budget = int(max_tokens * weight)
    intel_budget = max_tokens - journal_budget

    journal_ctx = truncate_lines_to_tokens(journal_ctx, journal_budget)
    intel_ctx = truncate_lines_to_tokens(intel_ctx, intel_budget)
    return journal_ctx, intel_ctx

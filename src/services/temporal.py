"""Temporal expression parsing for search queries — regex-based, zero LLM calls."""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class TemporalFilter:
    """Parsed temporal constraint from a query."""

    start: datetime | None
    end: datetime | None
    original_expr: str  # matched expression to strip from query


# --- Relative period patterns ---

_PERIOD_UNITS = {
    "day": 1,
    "days": 1,
    "week": 7,
    "weeks": 7,
    "month": 30,
    "months": 30,
    "year": 365,
    "years": 365,
}

_PATTERNS: list[tuple[re.Pattern, str]] = []


def _register(pattern: str, tag: str) -> None:
    _PATTERNS.append((re.compile(pattern, re.IGNORECASE), tag))


# "last N days/weeks/months/years" or "past N ..."
_register(r"\b(?:last|past)\s+(\d+)\s+(days?|weeks?|months?|years?)\b", "last_n")
# "last week" / "last month" / "last year" (no number)
_register(r"\b(?:last)\s+(week|month|year)\b", "last_unit")
# "this week" / "this month" / "this year"
_register(r"\b(?:this)\s+(week|month|year)\b", "this_unit")
# "yesterday"
_register(r"\byesterday\b", "yesterday")
# "today"
_register(r"\btoday\b", "today")
# "recently" / "recent"
_register(r"\brecent(?:ly)?\b", "recent")
# "since <month>" e.g. "since January", "since march"
_register(
    r"\bsince\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    "since_month",
)
# "in <year>" e.g. "in 2025"
_register(r"\bin\s+(20\d{2})\b", "in_year")
# "after <date>" e.g. "after 2025-01-15" or "after Jan 15"
_register(r"\bafter\s+(\d{4}-\d{2}-\d{2})\b", "after_date")
# "before <date>"
_register(r"\bbefore\s+(\d{4}-\d{2}-\d{2})\b", "before_date")


_MONTH_NAMES = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}


def parse_temporal_expr(query: str, now: datetime | None = None) -> TemporalFilter | None:
    """Parse temporal expressions from a query string.

    Returns TemporalFilter if a temporal signal is found, else None.
    Uses first match only.
    """
    now = now or datetime.now()

    for pattern, tag in _PATTERNS:
        m = pattern.search(query)
        if not m:
            continue

        expr = m.group(0)

        if tag == "last_n":
            n = int(m.group(1))
            unit = m.group(2).lower()
            days = n * _PERIOD_UNITS.get(unit, 1)
            return TemporalFilter(start=now - timedelta(days=days), end=None, original_expr=expr)

        if tag == "last_unit":
            unit = m.group(1).lower()
            days = _PERIOD_UNITS.get(unit, 7)
            return TemporalFilter(start=now - timedelta(days=days), end=None, original_expr=expr)

        if tag == "this_unit":
            unit = m.group(1).lower()
            if unit == "week":
                start = now - timedelta(days=now.weekday())
                start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            elif unit == "month":
                start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:  # year
                start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return TemporalFilter(start=start, end=None, original_expr=expr)

        if tag == "yesterday":
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return TemporalFilter(start=start, end=end, original_expr=expr)

        if tag == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return TemporalFilter(start=start, end=None, original_expr=expr)

        if tag == "recent":
            return TemporalFilter(start=now - timedelta(days=7), end=None, original_expr=expr)

        if tag == "since_month":
            month_name = m.group(1).lower()
            month_num = _MONTH_NAMES.get(month_name, 1)
            year = now.year if month_num <= now.month else now.year - 1
            start = datetime(year, month_num, 1)
            return TemporalFilter(start=start, end=None, original_expr=expr)

        if tag == "in_year":
            year = int(m.group(1))
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31, 23, 59, 59)
            return TemporalFilter(start=start, end=end, original_expr=expr)

        if tag == "after_date":
            date = datetime.fromisoformat(m.group(1))
            return TemporalFilter(start=date, end=None, original_expr=expr)

        if tag == "before_date":
            date = datetime.fromisoformat(m.group(1))
            return TemporalFilter(start=None, end=date, original_expr=expr)

    return None


def strip_temporal(query: str, temporal_filter: TemporalFilter) -> str:
    """Remove the matched temporal expression from the query."""
    cleaned = query.replace(temporal_filter.original_expr, "")
    return re.sub(r"\s{2,}", " ", cleaned).strip()

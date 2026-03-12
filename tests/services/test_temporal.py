"""Tests for temporal expression parsing."""

from datetime import datetime

from services.temporal import TemporalFilter, parse_temporal_expr, strip_temporal

NOW = datetime(2026, 3, 12, 14, 30, 0)


class TestParseTemporalExpr:
    def test_last_n_days(self):
        f = parse_temporal_expr("what happened last 3 days", now=NOW)
        assert f is not None
        assert f.start == datetime(2026, 3, 9, 14, 30, 0)
        assert f.end is None
        assert f.original_expr == "last 3 days"

    def test_last_n_weeks(self):
        f = parse_temporal_expr("trends last 2 weeks", now=NOW)
        assert f is not None
        assert f.start == datetime(2026, 2, 26, 14, 30, 0)

    def test_past_n_months(self):
        f = parse_temporal_expr("news from past 6 months", now=NOW)
        assert f is not None
        # 6 * 30 = 180 days
        assert (NOW - f.start).days == 180

    def test_last_week(self):
        f = parse_temporal_expr("what did I write last week", now=NOW)
        assert f is not None
        assert (NOW - f.start).days == 7

    def test_last_month(self):
        f = parse_temporal_expr("entries from last month", now=NOW)
        assert f is not None
        assert (NOW - f.start).days == 30

    def test_this_week(self):
        f = parse_temporal_expr("journal entries this week", now=NOW)
        assert f is not None
        # March 12 2026 is a Thursday → Monday is March 9
        assert f.start == datetime(2026, 3, 9, 0, 0, 0)

    def test_this_month(self):
        f = parse_temporal_expr("intel this month", now=NOW)
        assert f is not None
        assert f.start == datetime(2026, 3, 1, 0, 0, 0)

    def test_this_year(self):
        f = parse_temporal_expr("all activity this year", now=NOW)
        assert f is not None
        assert f.start == datetime(2026, 1, 1, 0, 0, 0)

    def test_yesterday(self):
        f = parse_temporal_expr("what happened yesterday", now=NOW)
        assert f is not None
        assert f.start == datetime(2026, 3, 11, 0, 0, 0)
        assert f.end.day == 11  # type: ignore[union-attr]

    def test_today(self):
        f = parse_temporal_expr("news from today", now=NOW)
        assert f is not None
        assert f.start == datetime(2026, 3, 12, 0, 0, 0)
        assert f.end is None

    def test_recently(self):
        f = parse_temporal_expr("any recent updates on Rust", now=NOW)
        assert f is not None
        assert (NOW - f.start).days == 7
        assert f.original_expr == "recent"

    def test_recently_adverb(self):
        f = parse_temporal_expr("what was discussed recently", now=NOW)
        assert f is not None
        assert f.original_expr == "recently"

    def test_since_month_current_year(self):
        f = parse_temporal_expr("intel since January", now=NOW)
        assert f is not None
        assert f.start == datetime(2026, 1, 1)

    def test_since_month_previous_year(self):
        # If query says "since October" but now is March, that's October of last year
        f = parse_temporal_expr("since October", now=NOW)
        assert f is not None
        assert f.start == datetime(2025, 10, 1)

    def test_in_year(self):
        f = parse_temporal_expr("AI papers in 2025", now=NOW)
        assert f is not None
        assert f.start == datetime(2025, 1, 1)
        assert f.end == datetime(2025, 12, 31, 23, 59, 59)

    def test_after_date(self):
        f = parse_temporal_expr("items after 2026-01-15", now=NOW)
        assert f is not None
        assert f.start == datetime(2026, 1, 15)
        assert f.end is None

    def test_before_date(self):
        f = parse_temporal_expr("entries before 2025-12-01", now=NOW)
        assert f is not None
        assert f.start is None
        assert f.end == datetime(2025, 12, 1)

    def test_no_temporal_expression(self):
        assert parse_temporal_expr("compare OpenAI and Anthropic", now=NOW) is None

    def test_no_temporal_in_simple_query(self):
        assert parse_temporal_expr("latest AI news", now=NOW) is None

    def test_case_insensitive(self):
        f = parse_temporal_expr("Since JANUARY", now=NOW)
        assert f is not None


class TestStripTemporal:
    def test_strip_removes_expression(self):
        f = TemporalFilter(start=NOW, end=None, original_expr="last 3 days")
        result = strip_temporal("what happened last 3 days in AI", f)
        assert result == "what happened in AI"

    def test_strip_trims_whitespace(self):
        f = TemporalFilter(start=NOW, end=None, original_expr="recently")
        result = strip_temporal("recently discussed topics", f)
        assert result == "discussed topics"

    def test_strip_handles_trailing_expr(self):
        f = TemporalFilter(start=NOW, end=None, original_expr="last week")
        result = strip_temporal("journal entries from last week", f)
        assert result == "journal entries from"

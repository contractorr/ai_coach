"""Tests for DailyBriefBuilder."""

from advisor.daily_brief import (
    DailyBriefBuilder,
    _score_intel_match,
    _score_recommendation,
    _score_stale_goal,
)


def _goal(title: str, days: int = 10) -> dict:
    return {"title": title, "days_since_check": days, "status": "active", "path": f"g/{title}.md"}


def _rec(title: str, desc: str = "desc") -> dict:
    return {"title": title, "description": desc}


def _intel_match(title: str = "Intel", urgency: str = "high", score: float = 0.2) -> dict:
    return {"title": title, "summary": "summary", "urgency": urgency, "score": score}


class TestDailyBriefBuilder:
    def setup_method(self):
        self.builder = DailyBriefBuilder()

    def test_empty_with_goals_gives_nudge(self):
        brief = self.builder.build(
            stale_goals=[],
            recommendations=[],
            all_goals=[_goal("Ship MVP")],
            weekly_hours=5,
        )
        assert len(brief.items) == 1
        assert brief.items[0].kind == "nudge"
        assert "Ship MVP" in brief.items[0].action

    def test_empty_no_goals_gives_reflection(self):
        brief = self.builder.build(
            stale_goals=[],
            recommendations=[],
            all_goals=[],
            weekly_hours=5,
        )
        assert len(brief.items) == 1
        assert brief.items[0].kind == "nudge"
        assert "reflect" in brief.items[0].action.lower()

    def test_stale_goals_ranked_high(self):
        """Very stale goals should outrank recommendations."""
        brief = self.builder.build(
            stale_goals=[_goal("Goal A", days=20)],
            recommendations=[_rec("Rec 1")],
            all_goals=[],
            weekly_hours=5,
        )
        assert brief.items[0].kind == "stale_goal"
        assert brief.items[0].priority == 1

    def test_high_urgency_intel_beats_recommendation(self):
        """High-urgency intel with high score should outrank a recommendation."""
        brief = self.builder.build(
            stale_goals=[],
            recommendations=[_rec("Rec 1")],
            all_goals=[],
            weekly_hours=10,
            intel_matches=[_intel_match("Breaking Intel", urgency="high", score=0.3)],
        )
        kinds = [i.kind for i in brief.items]
        assert kinds.index("intel_match") < kinds.index("recommendation")

    def test_budget_calculation(self):
        brief = self.builder.build(
            stale_goals=[],
            recommendations=[],
            all_goals=[_goal("X")],
            weekly_hours=7,
        )
        assert brief.budget_minutes == 60  # 7*60/7

    def test_max_items_low_budget(self):
        """<30 min budget caps at 2 items."""
        brief = self.builder.build(
            stale_goals=[_goal("A"), _goal("B"), _goal("C")],
            recommendations=[],
            all_goals=[],
            weekly_hours=3,  # ~26 min/day
        )
        assert len(brief.items) <= 2

    def test_max_items_medium_budget(self):
        """30-60 min budget caps at 3 items."""
        brief = self.builder.build(
            stale_goals=[_goal("A"), _goal("B"), _goal("C"), _goal("D")],
            recommendations=[],
            all_goals=[],
            weekly_hours=5,  # ~43 min/day
        )
        assert len(brief.items) <= 3

    def test_max_items_high_budget(self):
        """60+ min budget caps at 5 items."""
        brief = self.builder.build(
            stale_goals=[_goal("A"), _goal("B"), _goal("C")],
            recommendations=[_rec("R1"), _rec("R2")],
            all_goals=[],
            weekly_hours=14,  # 120 min/day
        )
        assert len(brief.items) <= 5

    def test_budget_stops_filling(self):
        """Stop adding items when budget exhausted."""
        brief = self.builder.build(
            stale_goals=[_goal("A")],  # 10 min
            recommendations=[_rec("R")],  # 15 min → 25 total
            all_goals=[],
            weekly_hours=5,  # ~43 min budget
        )
        assert brief.used_minutes <= brief.budget_minutes + 15  # at most one overshoot

    def test_generated_at_is_iso(self):
        brief = self.builder.build(
            stale_goals=[],
            recommendations=[],
            all_goals=[],
            weekly_hours=5,
        )
        assert "T" in brief.generated_at

    def test_used_minutes_accurate(self):
        brief = self.builder.build(
            stale_goals=[_goal("A"), _goal("B")],
            recommendations=[],
            all_goals=[],
            weekly_hours=5,
        )
        expected = sum(i.time_minutes for i in brief.items)
        assert brief.used_minutes == expected

    def test_recs_as_objects(self):
        """Recommendations can be passed as objects with .title/.description attrs."""

        class FakeRec:
            def __init__(self, t, d):
                self.title = t
                self.description = d

        brief = self.builder.build(
            stale_goals=[],
            recommendations=[FakeRec("Try X", "details")],
            all_goals=[],
            weekly_hours=5,
        )
        assert brief.items[0].kind == "recommendation"
        assert brief.items[0].title == "Try X"

    def test_medium_intel_included(self):
        """Medium-urgency intel matches should be included as candidates."""
        brief = self.builder.build(
            stale_goals=[],
            recommendations=[],
            all_goals=[],
            weekly_hours=5,
            intel_matches=[_intel_match("Medium item", urgency="medium")],
        )
        assert brief.items[0].kind == "intel_match"

    def test_low_intel_excluded(self):
        """Low-urgency intel matches should not appear."""
        brief = self.builder.build(
            stale_goals=[],
            recommendations=[],
            all_goals=[_goal("X")],
            weekly_hours=5,
            intel_matches=[_intel_match("Low item", urgency="low")],
        )
        assert brief.items[0].kind == "nudge"


# --- Score function unit tests (Phase 3) ---


class TestScoreFunctions:
    def test_stale_goal_increases_with_staleness(self):
        low = _score_stale_goal({"days_since_check": 3})
        high = _score_stale_goal({"days_since_check": 25})
        assert high > low

    def test_stale_goal_saturates_at_30(self):
        s30 = _score_stale_goal({"days_since_check": 30})
        s60 = _score_stale_goal({"days_since_check": 60})
        assert s30 == s60  # both saturate at 1.0

    def test_intel_high_beats_medium(self):
        high = _score_intel_match({"urgency": "high", "score": 0.2})
        medium = _score_intel_match({"urgency": "medium", "score": 0.2})
        assert high > medium

    def test_recommendation_first_beats_later(self):
        first = _score_recommendation(0)
        third = _score_recommendation(2)
        assert first > third

    def test_very_stale_goal_beats_high_intel(self):
        """A 30-day stale goal should outrank even high-urgency intel."""
        goal_score = _score_stale_goal({"days_since_check": 30})
        intel_score = _score_intel_match({"urgency": "high", "score": 0.3})
        assert goal_score > intel_score

    def test_high_intel_beats_recommendation(self):
        intel_score = _score_intel_match({"urgency": "high", "score": 0.2})
        rec_score = _score_recommendation(0)
        assert intel_score > rec_score

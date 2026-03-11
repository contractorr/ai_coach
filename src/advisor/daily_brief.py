"""Daily brief builder — zero-LLM, time-budgeted action plan with score-based ranking."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DailyBriefItem:
    kind: str  # "stale_goal" | "recommendation" | "nudge" | "intel_match"
    title: str
    description: str
    time_minutes: int
    action: str  # chat pre-fill
    priority: int  # 1-based, assigned during fill
    _rank_score: float = 0.0  # internal sorting score, not exposed in API


@dataclass
class DailyBrief:
    items: list[DailyBriefItem] = field(default_factory=list)
    budget_minutes: int = 0
    used_minutes: int = 0
    generated_at: str = ""


# Fixed time estimates per kind
_TIME = {
    "stale_goal": 10,
    "recommendation": 15,
    "nudge": 5,
    "intel_match": 5,
}

# Base urgency scores per kind — higher = more urgent by default
_BASE_URGENCY = {
    "stale_goal": 0.7,
    "intel_match": 0.5,
    "recommendation": 0.4,
    "nudge": 0.1,
}

# Intel urgency tier multipliers
_INTEL_URGENCY_MULT = {"high": 1.5, "medium": 1.0, "low": 0.6}


def _max_items(budget: int) -> int:
    if budget < 30:
        return 2
    if budget <= 60:
        return 3
    return 5


def _score_stale_goal(g: dict) -> float:
    """Score a stale goal: more stale = higher urgency."""
    days = g.get("days_since_check", 7)
    # Normalize days to [0, 1] — 30+ days saturates at 1.0
    recency_factor = min(1.0, days / 30)
    return _BASE_URGENCY["stale_goal"] + 0.3 * recency_factor


def _score_intel_match(m: dict) -> float:
    """Score an intel match using its urgency tier and match score."""
    urgency = m.get("urgency", "medium")
    mult = _INTEL_URGENCY_MULT.get(urgency, 1.0)
    match_score = m.get("score", 0.1)
    return _BASE_URGENCY["intel_match"] * mult + 0.2 * min(1.0, match_score / 0.3)


def _score_recommendation(idx: int) -> float:
    """Score a recommendation — recs are pre-sorted, penalize later ones."""
    return _BASE_URGENCY["recommendation"] * (1.0 - 0.1 * min(idx, 5))


class DailyBriefBuilder:
    """Build a time-budgeted daily brief from pre-gathered data (no I/O).

    Candidates are scored by urgency × recency and sorted globally,
    then filled within the user's time budget.
    """

    def build(
        self,
        *,
        stale_goals: list[dict],
        recommendations: list,
        all_goals: list[dict],
        weekly_hours: int = 5,
        intel_matches: list[dict] | None = None,
    ) -> DailyBrief:
        budget = round(weekly_hours * 60 / 7)
        if budget <= 0:
            return DailyBrief(
                items=[],
                budget_minutes=0,
                used_minutes=0,
                generated_at=datetime.now(timezone.utc).isoformat(),
            )
        cap = _max_items(budget)

        _matches = intel_matches or []

        # Build all candidates with rank scores
        candidates: list[DailyBriefItem] = []

        for g in stale_goals:
            candidates.append(
                DailyBriefItem(
                    kind="stale_goal",
                    title=g.get("title", ""),
                    description=f"Last check-in {g.get('days_since_check', '?')} days ago",
                    time_minutes=_TIME["stale_goal"],
                    action=f"What concrete steps can I take this week to advance my goal: {g.get('title', '')}? Suggest specific events, projects, or resources.",
                    priority=0,
                    _rank_score=_score_stale_goal(g),
                )
            )

        for m in _matches:
            urgency = m.get("urgency", "low")
            if urgency not in ("high", "medium"):
                continue
            candidates.append(
                DailyBriefItem(
                    kind="intel_match",
                    title=m.get("title", ""),
                    description=m.get("summary", "")[:200],
                    time_minutes=_TIME["intel_match"],
                    action=f"Tell me about this and how it relates to my goal: {m.get('title', '')}",
                    priority=0,
                    _rank_score=_score_intel_match(m),
                )
            )

        for idx, r in enumerate(recommendations):
            title = r.title if hasattr(r, "title") else r.get("title", "")
            desc = r.description if hasattr(r, "description") else r.get("description", "")
            candidates.append(
                DailyBriefItem(
                    kind="recommendation",
                    title=title,
                    description=desc[:200] if desc else "",
                    time_minutes=_TIME["recommendation"],
                    action=f"Tell me more about: {title}",
                    priority=0,
                    _rank_score=_score_recommendation(idx),
                )
            )

        # Sort all candidates by rank score descending
        candidates.sort(key=lambda c: c._rank_score, reverse=True)

        # Fill within budget
        items: list[DailyBriefItem] = []
        used = 0
        for c in candidates:
            if len(items) >= cap:
                break
            if used + c.time_minutes > budget and items:
                break
            # Always include first item even if over budget
            used += c.time_minutes
            c.priority = len(items) + 1
            items.append(c)

        # Ambient fallback when no candidates
        if not items:
            if all_goals:
                g = all_goals[0]
                title = g.get("title", "")
                items.append(
                    DailyBriefItem(
                        kind="nudge",
                        title=title,
                        description="Quick check-in to keep momentum",
                        time_minutes=_TIME["nudge"],
                        action=f"What concrete steps can I take this week to advance my goal: {title}? Suggest specific events, projects, or resources.",
                        priority=1,
                    )
                )
                used = _TIME["nudge"]
            else:
                items.append(
                    DailyBriefItem(
                        kind="nudge",
                        title="Reflect",
                        description="Take a moment to journal or set a goal",
                        time_minutes=_TIME["nudge"],
                        action="Help me reflect on what I should focus on",
                        priority=1,
                    )
                )
                used = _TIME["nudge"]

        return DailyBrief(
            items=items,
            budget_minutes=budget,
            used_minutes=used,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

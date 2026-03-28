"""Profile-aware curriculum recommendation helpers."""

from __future__ import annotations

import re
from profile.storage import UserProfile
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "their",
    "to",
    "with",
}
_TOKEN_EXPANSIONS = {
    "ai": {"ai", "artificial", "intelligence", "automation", "copilot", "llm", "machine"},
    "algorithms": {"algorithms", "software", "engineering", "technical"},
    "business": {"business", "commercial", "operator", "operations", "strategy"},
    "construction": {"construction", "infrastructure", "built", "environment"},
    "cybersecurity": {"cybersecurity", "security", "risk", "controls"},
    "decision": {"decision", "judgment", "forecasting", "uncertainty"},
    "economics": {"economics", "market", "pricing", "incentives", "competition"},
    "energy": {"energy", "utilities", "power", "grid", "climate"},
    "financialservices": {"financial", "finance", "fintech", "banking", "capital"},
    "geopolitics": {"geopolitics", "policy", "public", "global", "regulation"},
    "government": {"government", "public", "policy", "regulation", "institution"},
    "healthcare": {"healthcare", "health", "clinical", "medical", "biotech"},
    "hr": {"hr", "people", "talent", "workforce", "recruiting"},
    "industry": {"industry", "sector", "domain", "vertical"},
    "insurance": {"insurance", "risk", "actuarial", "claims"},
    "investing": {"investing", "investor", "portfolio", "capital", "allocation"},
    "legal": {"legal", "law", "regulation", "compliance", "contracts"},
    "mba": {"mba", "management", "leadership", "operator", "strategy"},
    "operators": {"operators", "operator", "operations", "manager", "execution"},
    "private": {"private", "markets", "equity", "investing", "capital"},
    "realestate": {"realestate", "real", "estate", "property", "housing"},
    "supplychain": {"supplychain", "supply", "chain", "logistics", "operations"},
}
_CATEGORY_LABELS = {
    "business": "business",
    "humanities": "humanities",
    "industry": "industry",
    "professional": "professional",
    "science": "science",
    "social_science": "social science",
    "technology": "technology",
}
_TRACK_LABELS = {
    "business_economics": "business economics",
    "foundations": "foundations",
    "human_sciences": "human sciences",
    "industry": "industry",
    "natural_sciences": "natural sciences",
    "technology": "technology",
}


def _tokenize(*values: str) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        if not value:
            continue
        lowered = value.lower().replace("/", " ").replace("-", " ").replace("_", " ")
        for token in _TOKEN_RE.findall(lowered):
            if len(token) <= 1 or token in _STOP_WORDS:
                continue
            tokens.add(token)
            tokens.update(_TOKEN_EXPANSIONS.get(token, set()))
    return tokens


def _collect_profile_terms(profile: UserProfile | None) -> dict[str, Any]:
    if profile is None:
        return {
            "all": set(),
            "goal": set(),
            "industry": set(),
            "weekly_hours": 0,
            "role": "",
            "industry_labels": [],
        }

    goal_text = " ".join(
        filter(
            None,
            [
                profile.goals_short_term,
                profile.goals_long_term,
                profile.aspirations,
                " ".join(profile.active_projects),
            ],
        )
    )
    role_text = " ".join(filter(None, [profile.current_role, profile.aspirations]))
    industry_text = " ".join(profile.industries_watching)
    all_terms = _tokenize(
        role_text,
        goal_text,
        industry_text,
        " ".join(profile.interests),
        " ".join(profile.technologies_watching),
        " ".join(profile.languages_frameworks),
    )
    return {
        "all": all_terms,
        "goal": _tokenize(goal_text),
        "industry": _tokenize(industry_text),
        "weekly_hours": int(
            profile.constraints.get("time_per_week", profile.weekly_hours_available) or 0
        ),
        "role": profile.current_role,
        "industry_labels": list(profile.industries_watching),
    }


def _program_terms(program: dict) -> set[str]:
    return _tokenize(
        program.get("title", ""),
        program.get("audience", ""),
        program.get("description", ""),
        " ".join(program.get("outcomes", [])),
        " ".join(program.get("guide_ids", [])),
        " ".join(program.get("applied_module_ids", [])),
    )


def _guide_terms(guide: dict, programs: list[dict]) -> set[str]:
    return _tokenize(
        guide.get("title", ""),
        guide.get("id", ""),
        guide.get("track", ""),
        _TRACK_LABELS.get(guide.get("track", ""), ""),
        guide.get("category", ""),
        _CATEGORY_LABELS.get(guide.get("category", ""), ""),
        " ".join(program.get("title", "") for program in programs),
    )


def _time_fit(guide: dict, weekly_hours: int) -> tuple[int, str | None]:
    total_minutes = int(guide.get("total_reading_time_minutes") or 0)
    if weekly_hours <= 0:
        return 0, None
    if weekly_hours <= 4:
        if total_minutes and total_minutes <= weekly_hours * 70:
            return 10, f"Fits a lighter {weekly_hours}h/week learning budget."
        return -4, f"Better tackled in smaller sessions at {weekly_hours}h/week."
    if weekly_hours >= 8:
        if total_minutes >= 180:
            return 6, f"Has enough depth for a {weekly_hours}h/week push."
        return 2, f"Should move quickly with {weekly_hours}h/week available."
    return 4, f"Reasonable scope for roughly {weekly_hours}h/week."


def summarize_program_match(program: dict, overlap: set[str], profile_terms: dict[str, Any]) -> str:
    overlap_terms = sorted(term for term in overlap if len(term) > 2)[:3]
    if overlap_terms:
        return "Matches your goals around " + ", ".join(overlap_terms) + "."
    if profile_terms["industry"]:
        return "Links general capability building to applied sector work."
    return "Supports one of the curated mid-career learning paths."


def score_guide_candidate(
    guide: dict,
    programs: list[dict],
    profile: UserProfile | None,
    *,
    stage: str,
) -> dict[str, Any]:
    """Score a guide candidate and explain the strongest matching signals."""
    profile_terms = _collect_profile_terms(profile)
    guide_term_set = _guide_terms(guide, programs)
    score = 0
    signals: list[dict[str, str]] = []
    matched_programs: list[dict[str, Any]] = []

    if stage == "continue":
        score += 120
        signals.append(
            {
                "kind": "progress",
                "label": "Active momentum",
                "detail": "You already started this guide, so the shortest path is to keep moving.",
            }
        )
    elif stage == "enrolled":
        score += 95
        signals.append(
            {
                "kind": "progress",
                "label": "Already enrolled",
                "detail": "Continuing an enrolled guide avoids context switching and preserves momentum.",
            }
        )
    elif stage == "ready":
        score += 48
        signals.append(
            {
                "kind": "readiness",
                "label": "Prerequisites complete",
                "detail": "This guide is unlocked and ready to start now.",
            }
        )
    elif stage == "entry":
        score += 24
        signals.append(
            {
                "kind": "readiness",
                "label": "Entry point",
                "detail": "No prerequisites are required, so you can start here immediately.",
            }
        )

    if profile_terms["all"]:
        guide_overlap = profile_terms["all"] & guide_term_set
        if guide_overlap:
            overlap_terms = sorted(term for term in guide_overlap if len(term) > 2)[:3]
            score += min(len(guide_overlap), 4) * 4
            signals.append(
                {
                    "kind": "context",
                    "label": "Goal alignment",
                    "detail": "Connects to your current focus on " + ", ".join(overlap_terms) + ".",
                }
            )

    for program in programs:
        overlap = profile_terms["all"] & _program_terms(program)
        if not overlap:
            continue
        program_score = 10 + min(len(overlap), 4) * 3
        score += program_score
        matched_programs.append(
            {
                **program,
                "match_reason": summarize_program_match(program, overlap, profile_terms),
                "match_score": program_score,
            }
        )

    if profile_terms["industry"]:
        applied_text = " ".join(
            module.replace("industry-", "").replace("-", " ")
            for program in programs
            for module in program.get("applied_module_ids", [])
        )
        industry_overlap = profile_terms["industry"] & _tokenize(applied_text, guide.get("id", ""))
        if industry_overlap:
            score += 12
            industry_terms = sorted(industry_overlap)[:2]
            signals.append(
                {
                    "kind": "industry",
                    "label": "Industry fit",
                    "detail": "Maps cleanly to your sector context in "
                    + ", ".join(industry_terms)
                    + ".",
                }
            )

    time_bonus, time_detail = _time_fit(guide, profile_terms["weekly_hours"])
    if time_detail:
        score += time_bonus
        signals.append({"kind": "time", "label": "Time fit", "detail": time_detail})

    matched_programs.sort(key=lambda item: item["match_score"], reverse=True)
    return {
        "score": score,
        "signals": signals[:4],
        "matched_programs": [
            {key: value for key, value in item.items() if key != "match_score"}
            for item in matched_programs[:2]
        ],
    }


def build_applied_assessments(
    guide: dict,
    programs: list[dict],
    profile: UserProfile | None,
    *,
    chapter_title: str | None = None,
) -> list[dict[str, Any]]:
    """Return a pilot assessment plan for the guide."""
    profile_terms = _collect_profile_terms(profile)
    role = profile_terms["role"] or "your role"
    industry = ", ".join(profile_terms["industry_labels"][:2]) or "your operating context"
    primary_program = programs[0]["title"] if programs else guide.get("title", "this guide")
    focus_title = chapter_title or guide.get("title", "this guide")

    return [
        {
            "type": "teach_back",
            "stage": "chapter_completion",
            "title": "Teach-back note",
            "summary": f"Translate {focus_title} into plain-language guidance for a teammate.",
            "deliverable": "6-10 bullet note or a 3-minute voice memo.",
            "prompt": f"Explain the key idea from {focus_title} to someone in {role}. Include one decision it should change this week.",
            "evaluation_focus": [
                "Accurate use of the chapter concept",
                "Clear translation into workplace language",
                "Concrete action or implication",
            ],
        },
        {
            "type": "decision_brief",
            "stage": "review",
            "title": "Decision brief",
            "summary": f"Use one framework from {guide.get('title', 'the guide')} to support a real decision.",
            "deliverable": "One-page brief with recommendation, trade-offs, and assumptions.",
            "prompt": f"Write a short brief for a decision in {industry}. State the choice, the recommendation, the key uncertainties, and what would change your view.",
            "evaluation_focus": [
                "Explicit assumptions and trade-offs",
                "Use of course frameworks instead of opinion only",
                "Recommendation tied to evidence",
            ],
        },
        {
            "type": "scenario_analysis",
            "stage": "scenario_practice",
            "title": "Scenario analysis",
            "summary": "Pressure-test the guide against two plausible operating scenarios.",
            "deliverable": "Two-scenario comparison with leading indicators and response triggers.",
            "prompt": f"Model a base case and a stressed case for {primary_program}. Show what you would watch, what would break, and how you would respond.",
            "evaluation_focus": [
                "Plausible scenarios rooted in real constraints",
                "Useful leading indicators",
                "Specific response options for each branch",
            ],
        },
        {
            "type": "case_memo",
            "stage": "capstone",
            "title": "Case memo",
            "summary": "Synthesize the guide into a workplace-grade recommendation artifact.",
            "deliverable": "1-2 page memo with recommendation, rationale, and execution risks.",
            "prompt": f"Write a case memo for a realistic decision in {industry}. Use ideas from {guide.get('title', 'the guide')} and end with a concrete recommendation, execution plan, and failure modes to watch.",
            "evaluation_focus": [
                "Strong synthesis across chapters",
                "Decision quality under uncertainty",
                "Operational realism and next-step clarity",
            ],
        },
    ]

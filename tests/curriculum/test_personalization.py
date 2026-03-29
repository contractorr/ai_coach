from profile.storage import UserProfile

from curriculum.personalization import build_applied_assessments, score_guide_candidate


def test_score_guide_candidate_matches_program_and_time_budget():
    guide = {
        "id": "28-accounting",
        "title": "Accounting",
        "category": "business",
        "track": "business_economics",
        "total_reading_time_minutes": 120,
    }
    program = {
        "id": "business-acumen",
        "title": "Business Acumen",
        "audience": "Operators and functional leads who need sharper commercial judgment.",
        "description": "Read a P&L, understand incentives, and connect daily decisions to business performance.",
        "outcomes": [
            "Interpret core financial statements and operating metrics.",
            "Reason about pricing, market structure, and growth trade-offs.",
        ],
        "guide_ids": ["28-accounting"],
        "applied_module_ids": ["industry-financialservices"],
        "color": "#2563eb",
    }
    profile = UserProfile(
        current_role="Operations manager",
        goals_short_term="Build stronger business acumen and read a P&L with confidence.",
        weekly_hours_available=3,
    )

    result = score_guide_candidate(guide, [program], profile, stage="entry")

    assert result["score"] > 24
    assert any(signal["kind"] == "context" for signal in result["signals"])
    assert any(signal["kind"] == "time" for signal in result["signals"])
    assert result["matched_programs"][0]["id"] == "business-acumen"


def test_build_applied_assessments_returns_full_pilot_plan():
    guide = {
        "id": "37-ai-ml-fundamentals-guide",
        "title": "AI/ML Fundamentals",
        "category": "technology",
        "track": "technology",
    }
    program = {
        "id": "ai-for-operators",
        "title": "AI for Operators",
        "audience": "Mid-career managers deploying AI into workflows, products, and teams.",
        "description": "Build enough technical judgment to scope AI use cases and drive adoption.",
        "outcomes": [],
        "guide_ids": ["37-ai-ml-fundamentals-guide"],
        "applied_module_ids": ["industry-healthcare"],
        "color": "#7c3aed",
    }
    profile = UserProfile(
        current_role="Healthcare operations lead",
        industries_watching=["healthcare"],
        weekly_hours_available=4,
    )

    assessments = build_applied_assessments(
        guide,
        [program],
        profile,
        chapter_title="Model limits and deployment risk",
    )

    assert [assessment["stage"] for assessment in assessments] == [
        "chapter_completion",
        "review",
        "scenario_practice",
        "capstone",
    ]
    assert {assessment["type"] for assessment in assessments} == {
        "teach_back",
        "decision_brief",
        "scenario_analysis",
        "case_memo",
    }
    assert "healthcare" in assessments[1]["prompt"].lower()


def test_score_guide_candidate_uses_learning_performance_signals():
    guide = {
        "id": "37-ai-ml-fundamentals-guide",
        "title": "AI/ML Fundamentals",
        "category": "technology",
        "track": "technology",
        "total_reading_time_minutes": 150,
    }
    profile = UserProfile(
        current_role="Operations lead",
        goals_short_term="Use AI with better judgment in operational workflows.",
        weekly_hours_available=4,
    )

    result = score_guide_candidate(
        guide,
        [],
        profile,
        stage="enrolled",
        learning_signals={
            "reviewed_review_count": 4,
            "weak_review_count": 2,
            "revision_backlog_count": 1,
            "assessment_grade_count": 1,
            "average_assessment_grade": 2.0,
        },
    )

    assert result["score"] > 120
    assert any(signal["kind"] == "performance" for signal in result["signals"])
    assert any(signal["kind"] == "assessment" for signal in result["signals"])

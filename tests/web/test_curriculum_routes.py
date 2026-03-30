"""Tests for curriculum routes: tree, ready, next (DAG-aware), placement."""

from datetime import datetime, timedelta
from pathlib import Path
from profile.storage import ProfileStorage, UserProfile
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from curriculum.models import BloomLevel, ReviewGradeResult, ReviewItem, ReviewItemType
from curriculum.store import CurriculumStore
from curriculum.user_content import write_guide_metadata
from journal.storage import JournalStorage
from web.deps import get_user_paths


def _curriculum_store(user_id: str = "user-123") -> CurriculumStore:
    return CurriculumStore(Path(get_user_paths(user_id)["data_dir"]) / "curriculum.db")


def _write_user_guide_content(
    user_id: str,
    guide_id: str,
    title: str,
    *,
    kind: str = "standalone",
    base_guide_id: str | None = None,
) -> None:
    guide_dir = Path(get_user_paths(user_id)["curriculum_dir"]) / guide_id
    guide_dir.mkdir(parents=True, exist_ok=True)
    write_guide_metadata(
        guide_dir,
        {
            "title": title,
            "origin": "user",
            "kind": kind,
            "owner_user_id": user_id,
            "base_guide_id": base_guide_id,
            "category": "professional",
            "difficulty": "intermediate",
            "created_at": datetime.utcnow().isoformat(),
        },
    )
    (guide_dir / "01-introduction.mdx").write_text(
        """---
title: Introduction
summary: Start here.
objectives:
  - Understand the central idea.
checkpoints:
  - Explain the core takeaway.
content_format: markdown
schema_version: 1
---
# Introduction

This is a generated learning chapter with enough structure to scan and study.

## Core Idea

The guide introduces the topic in a practical way.

## Why It Matters

This section explains why the material matters to the learner.

## Checkpoint

- Explain the core takeaway.
""",
        encoding="utf-8",
    )


class _StubGuideGenerationService:
    def __init__(self, user_id: str):
        self.user_id = user_id

    async def generate_guide(self, *, topic: str, **_: object) -> dict:
        guide_id = "user-custom-topic-abc123"
        _write_user_guide_content(self.user_id, guide_id, f"{topic} Guide")
        return {"guide_id": guide_id, "title": f"{topic} Guide", "kind": "standalone"}

    async def extend_guide(self, *, source_guide: dict, prompt: str, **_: object) -> dict:
        guide_id = "ext-custom-extension-def456"
        _write_user_guide_content(
            self.user_id,
            guide_id,
            f"{source_guide['title']} Extension",
            kind="extension",
            base_guide_id=source_guide["id"],
        )
        return {
            "guide_id": guide_id,
            "title": f"{source_guide['title']} Extension",
            "kind": "extension",
            "base_guide_id": source_guide["id"],
            "prompt": prompt,
        }


def test_tree_endpoint(client, auth_headers):
    """GET /api/curriculum/tree returns tracks, nodes, edges."""
    # Sync catalog first
    client.post("/api/curriculum/sync", headers=auth_headers)

    resp = client.get("/api/curriculum/tree", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "tracks" in data
    assert "programs" in data
    assert "nodes" in data
    assert "edges" in data
    assert isinstance(data["programs"], list)
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)
    assert "human_sciences" in data["tracks"]
    assert data["tracks"]["human_sciences"]["id"] == "human_sciences"
    assert data["tracks"]["human_sciences"]["title"] == "Human Sciences"

    node_ids = {node["id"] for node in data["nodes"]}
    assert "05-game-theory-strategic-interaction-guide" not in node_ids
    assert "32-engineering-guide" not in node_ids
    assert "34-game-theory-strategic-interaction-guide" in node_ids
    assert "35-engineering-guide" in node_ids
    assert any(program["id"] == "business-acumen" for program in data["programs"])

    # If nodes exist, check structure
    if data["nodes"]:
        node = data["nodes"][0]
        assert "id" in node
        assert "position" in node
        assert "status" in node
        assert "is_entry_point" in node


def test_ready_endpoint(client, auth_headers):
    """GET /api/curriculum/ready returns list (possibly empty)."""
    client.post("/api/curriculum/sync", headers=auth_headers)
    resp = client.get("/api/curriculum/ready", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_guides_hides_superseded_guides_and_exposes_programs(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)
    guides = client.get("/api/curriculum/guides", headers=auth_headers).json()
    guide_ids = {guide["id"] for guide in guides}

    assert "05-game-theory-strategic-interaction-guide" not in guide_ids
    assert "32-engineering-guide" not in guide_ids

    philosophy = next(guide for guide in guides if guide["id"] == "01-philosophy-guide")
    assert philosophy["canonical_guide_id"] is None
    assert philosophy["summary"]
    assert any(program["id"] == "decision-quality" for program in philosophy["learning_programs"])


def test_get_guide_resolves_superseded_alias_to_canonical_guide(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    resp = client.get(
        "/api/curriculum/guides/32-engineering-guide",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["id"] == "35-engineering-guide"
    assert payload["chapter_count"] >= 1


def test_get_chapter_resolves_superseded_alias_to_canonical_chapter(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    resp = client.get(
        "/api/curriculum/guides/32-engineering-guide/chapters/01-introduction",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["guide_id"] == "35-engineering-guide"
    assert payload["id"] == "35-engineering-guide/01-introduction"


def test_generate_user_guide_creates_separate_user_owned_guide(client, auth_headers):
    with patch(
        "web.routes.curriculum._build_guide_generation_service",
        return_value=_StubGuideGenerationService("user-123"),
    ):
        resp = client.post(
            "/api/curriculum/guides/generate",
            headers=auth_headers,
            json={
                "topic": "Custom Topic",
                "depth": "practitioner",
                "audience": "Product manager",
                "time_budget": "3 hours per week",
                "instruction": "Focus on implementation trade-offs.",
            },
        )

    assert resp.status_code == 201
    payload = resp.json()
    assert payload["id"] == "user-custom-topic-abc123"
    assert payload["origin"] == "user"
    assert payload["kind"] == "standalone"
    assert payload["enrolled"] is False
    assert payload["base_guide_id"] is None

    user_guides = client.get("/api/curriculum/guides?origin=user", headers=auth_headers).json()
    assert any(guide["id"] == "user-custom-topic-abc123" for guide in user_guides)


def test_extend_guide_creates_linked_extension(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    with patch(
        "web.routes.curriculum._build_guide_generation_service",
        return_value=_StubGuideGenerationService("user-123"),
    ):
        resp = client.post(
            "/api/curriculum/guides/28-accounting/extend",
            headers=auth_headers,
            json={"prompt": "Add startup finance operator scenarios."},
        )

    assert resp.status_code == 201
    payload = resp.json()
    assert payload["origin"] == "user"
    assert payload["kind"] == "extension"
    assert payload["base_guide_id"] == "28-accounting"

    base_guide = client.get("/api/curriculum/guides/28-accounting", headers=auth_headers).json()
    assert any(
        extension["id"] == "ext-custom-extension-def456"
        for extension in base_guide["linked_extensions"]
    )


def test_archive_and_restore_user_guide_preserves_progress(client, auth_headers):
    with patch(
        "web.routes.curriculum._build_guide_generation_service",
        return_value=_StubGuideGenerationService("user-123"),
    ):
        create_resp = client.post(
            "/api/curriculum/guides/generate",
            headers=auth_headers,
            json={
                "topic": "Custom Topic",
                "depth": "practitioner",
                "audience": "Product manager",
                "time_budget": "3 hours per week",
            },
        )

    guide_id = create_resp.json()["id"]
    enroll_resp = client.post(
        f"/api/curriculum/guides/{guide_id}/enroll?create_goal=false",
        headers=auth_headers,
    )
    assert enroll_resp.status_code == 201

    guide_detail = client.get(f"/api/curriculum/guides/{guide_id}", headers=auth_headers).json()
    chapter_id = guide_detail["chapters"][0]["id"]
    client.post(
        "/api/curriculum/progress",
        headers=auth_headers,
        json={
            "chapter_id": chapter_id,
            "guide_id": guide_id,
            "status": "completed",
        },
    )

    archive_resp = client.delete(f"/api/curriculum/guides/{guide_id}", headers=auth_headers)
    assert archive_resp.status_code == 200
    assert archive_resp.json()["archived"] is True

    guides = client.get("/api/curriculum/guides?origin=user", headers=auth_headers).json()
    assert all(guide["id"] != guide_id for guide in guides)

    archived = client.get("/api/curriculum/guides/archived", headers=auth_headers).json()
    assert any(guide["id"] == guide_id for guide in archived)

    hidden_resp = client.get(f"/api/curriculum/guides/{guide_id}", headers=auth_headers)
    assert hidden_resp.status_code == 404

    restore_resp = client.post(f"/api/curriculum/guides/{guide_id}/restore", headers=auth_headers)
    assert restore_resp.status_code == 200
    assert restore_resp.json()["restored"] is True

    restored = client.get(f"/api/curriculum/guides/{guide_id}", headers=auth_headers).json()
    assert restored["enrolled"] is True
    assert restored["chapters"][0]["status"] == "completed"


def test_archive_rejects_builtin_guide(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    resp = client.delete("/api/curriculum/guides/28-accounting", headers=auth_headers)

    assert resp.status_code == 403


def test_build_question_generator_wires_resolved_llm_providers():
    from web.routes import curriculum as curriculum_routes

    full_llm = object()
    cheap_llm = object()
    config = SimpleNamespace(
        llm=SimpleNamespace(provider="claude", model="claude-sonnet-4-20250514")
    )

    with (
        patch.object(
            curriculum_routes,
            "resolve_llm_credentials_for_user",
            return_value=("openai", "test-key", "shared"),
        ),
        patch.object(curriculum_routes, "get_config", return_value=config),
        patch.object(curriculum_routes, "create_llm_provider", return_value=full_llm) as full_mock,
        patch.object(
            curriculum_routes,
            "create_cheap_provider",
            return_value=cheap_llm,
        ) as cheap_mock,
    ):
        generator = curriculum_routes._build_question_generator("user-123")

    assert generator.llm is full_llm
    assert generator.cheap_llm is cheap_llm
    full_mock.assert_called_once_with(
        provider="openai",
        api_key="test-key",
        model=curriculum_routes.SHARED_LLM_MODEL,
    )
    cheap_mock.assert_called_once_with(provider="openai", api_key="test-key")


def test_progress_write_canonicalizes_alias_chapter_ids(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    resp = client.post(
        "/api/curriculum/progress",
        headers=auth_headers,
        json={
            "chapter_id": "32-engineering-guide/01-introduction",
            "guide_id": "32-engineering-guide",
            "status": "in_progress",
        },
    )

    assert resp.status_code == 200
    store = _curriculum_store()
    progress = store.get_chapter_progress("user-123", "35-engineering-guide/01-introduction")
    assert progress is not None
    assert progress["guide_id"] == "35-engineering-guide"
    assert store.get_chapter_progress("user-123", "32-engineering-guide/01-introduction") is None


def test_next_returns_entry_point_when_no_enrollment(client, auth_headers):
    """GET /api/curriculum/next suggests entry-point guide when nothing enrolled."""
    client.post("/api/curriculum/sync", headers=auth_headers)
    resp = client.get("/api/curriculum/next", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Should return either an entry point or fallback
    assert "reason" in data
    assert "guide_id" in data


def test_stats_auto_syncs_catalog_when_empty(client, auth_headers):
    store = _curriculum_store()
    assert store.list_guides() == []

    resp = client.get("/api/curriculum/stats", headers=auth_headers)

    assert resp.status_code == 200
    assert store.list_guides()


def test_next_auto_syncs_catalog_when_empty(client, auth_headers):
    store = _curriculum_store()
    assert store.list_guides() == []

    resp = client.get("/api/curriculum/next", headers=auth_headers)

    assert resp.status_code == 200
    assert store.list_guides()
    data = resp.json()
    assert "reason" in data
    assert "recommendation_type" in data


def test_today_auto_syncs_catalog_when_empty(client, auth_headers):
    store = _curriculum_store()
    assert store.list_guides() == []

    resp = client.get("/api/curriculum/today", headers=auth_headers)

    assert resp.status_code == 200
    assert store.list_guides()
    data = resp.json()
    assert data["headline"] == "Today in Learn"
    assert "tasks" in data
    assert "focus_programs" in data


def test_next_continues_enrolled_guide(client, auth_headers):
    """GET /api/curriculum/next continues enrolled guide."""
    client.post("/api/curriculum/sync", headers=auth_headers)

    # Get a guide and enroll
    guides_resp = client.get("/api/curriculum/guides", headers=auth_headers)
    guides = guides_resp.json()
    if not guides:
        return  # no content to test

    guide_id = guides[0]["id"]
    client.post(
        f"/api/curriculum/guides/{guide_id}/enroll?create_goal=false",
        headers=auth_headers,
    )

    # Mark a chapter as in_progress to create last-read
    guide_detail = client.get(f"/api/curriculum/guides/{guide_id}", headers=auth_headers).json()
    chapters = guide_detail.get("chapters", [])
    if chapters:
        client.post(
            "/api/curriculum/progress",
            headers=auth_headers,
            json={
                "chapter_id": chapters[0]["id"],
                "guide_id": guide_id,
                "status": "in_progress",
            },
        )

    resp = client.get("/api/curriculum/next", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["guide_id"] == guide_id
    assert "chapter" in data
    assert "signals" in data
    assert "applied_assessments" in data


def test_next_personalizes_entry_point_with_profile(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    profile_path = get_user_paths("user-123")["profile_path"]
    ProfileStorage(profile_path).save(
        UserProfile(
            current_role="Operations manager",
            goals_short_term="Build business acumen and learn to read a P&L.",
            weekly_hours_available=3,
        )
    )

    resp = client.get("/api/curriculum/next", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["guide_id"] == "28-accounting"
    assert data["recommendation_type"] == "entry"
    assert any(program["id"] == "business-acumen" for program in data["matched_programs"])
    assert any(signal["kind"] in {"context", "time"} for signal in data["signals"])


def test_next_surfaces_weak_review_signal_for_enrolled_guide(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    store = _curriculum_store()
    guide_id = "28-accounting"
    store.enroll("user-123", guide_id)
    guide = store.get_guide(guide_id, user_id="user-123")
    chapter = guide["chapters"][0]
    store.add_review_items(
        [
            ReviewItem(
                id="weak-review-next",
                user_id="user-123",
                chapter_id=chapter["id"],
                guide_id=guide_id,
                question="Why does gross margin matter?",
                expected_answer="It shows how much value remains after direct costs.",
                bloom_level=BloomLevel.UNDERSTAND,
                item_type=ReviewItemType.QUIZ,
                next_review=datetime.utcnow() - timedelta(days=1),
            )
        ]
    )
    store.grade_review("weak-review-next", 2)

    resp = client.get("/api/curriculum/next", headers=auth_headers)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["guide_id"] == guide_id
    assert any(signal["kind"] == "performance" for signal in payload["signals"])


def test_next_prioritizes_revision_backlog_in_enrolled_guides(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    store = _curriculum_store()
    store.enroll("user-123", "28-accounting")
    store.enroll("user-123", "37-ai-ml-fundamentals-guide")

    launched = client.post(
        "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/launch",
        headers=auth_headers,
    ).json()
    storage = JournalStorage(get_user_paths("user-123")["journal_dir"])
    storage.update(
        launched["entry_path"],
        content=(
            "# Decision brief\n\n"
            "Use a broad AI rollout soon. It could help with efficiency, but the case is still thin "
            "and the draft needs better trade-offs, clearer assumptions, stronger metrics, and a more "
            "specific recommendation about scope, risk, and review checkpoints."
        ),
    )

    with patch(
        "web.routes.curriculum.QuestionGenerator.grade_applied_assessment",
        new=AsyncMock(
            return_value=ReviewGradeResult(
                grade=2,
                feedback="Needs sharper trade-offs and clearer operating constraints.",
                correct_points=["The draft names a real decision"],
                missing_points=["Concrete trade-offs", "Success metrics"],
            )
        ),
    ):
        submit_resp = client.post(
            "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/submit",
            headers=auth_headers,
        )

    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "active"

    resp = client.get("/api/curriculum/next", headers=auth_headers)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["guide_id"] == "37-ai-ml-fundamentals-guide"
    assert any(signal["kind"] == "assessment" for signal in payload["signals"])


def test_today_returns_queue_and_program_focus(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    profile_path = get_user_paths("user-123")["profile_path"]
    ProfileStorage(profile_path).save(
        UserProfile(
            current_role="Operations manager",
            goals_short_term="Build business acumen and get sharper at applied decision-making.",
            weekly_hours_available=4,
        )
    )

    store = _curriculum_store()
    guide_id = "28-accounting"
    store.enroll("user-123", guide_id)

    guide = store.get_guide(guide_id, user_id="user-123")
    chapter = guide["chapters"][0]
    store.update_progress(
        "user-123",
        chapter["id"],
        guide_id,
        status="in_progress",
        reading_time_seconds=300,
    )
    store.add_review_items(
        [
            ReviewItem(
                id="review-due-1",
                user_id="user-123",
                chapter_id=chapter["id"],
                guide_id=guide_id,
                question="What does a P&L show?",
                expected_answer="Revenue, expenses, and profit.",
                bloom_level=BloomLevel.UNDERSTAND,
                item_type=ReviewItemType.QUIZ,
                next_review=datetime.utcnow() - timedelta(days=1),
            )
        ]
    )

    resp = client.get("/api/curriculum/today", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["headline"] == "Today in Learn"
    assert data["recommended_action"]["guide_id"] == guide_id
    assert len(data["tasks"]) >= 3
    assert data["tasks"][0]["task_type"] in {"continue_chapter", "due_reviews"}
    assert any(task["task_type"] == "due_reviews" for task in data["tasks"])
    assert any(task["task_type"] == "applied_practice" for task in data["tasks"])
    assert any(program["status"] == "active" for program in data["focus_programs"])


def test_today_orders_program_focus_by_revision_pressure(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    store = _curriculum_store()
    store.enroll("user-123", "28-accounting")
    store.enroll("user-123", "37-ai-ml-fundamentals-guide")

    accounting = store.get_guide("28-accounting", user_id="user-123")
    accounting_chapter = accounting["chapters"][0]
    store.add_review_items(
        [
            ReviewItem(
                id="program-weak-review",
                user_id="user-123",
                chapter_id=accounting_chapter["id"],
                guide_id="28-accounting",
                question="Why does working capital matter?",
                expected_answer="It shows short-term operating flexibility.",
                bloom_level=BloomLevel.UNDERSTAND,
                item_type=ReviewItemType.QUIZ,
                next_review=datetime.utcnow() - timedelta(days=1),
            )
        ]
    )
    store.grade_review("program-weak-review", 2)

    launched = client.post(
        "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/launch",
        headers=auth_headers,
    ).json()
    JournalStorage(get_user_paths("user-123")["journal_dir"]).update(
        launched["entry_path"],
        metadata={
            "assessment_status": "active",
            "assessment_feedback": {
                "grade": 2,
                "feedback": "Revise the trade-offs and scope.",
                "correct_points": ["Clear decision"],
                "missing_points": ["Sharper trade-offs"],
            },
        },
    )

    resp = client.get("/api/curriculum/today", headers=auth_headers)

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["focus_programs"][0]["id"] == "ai-for-operators"
    assert payload["focus_programs"][0]["revision_backlog_count"] == 1
    assert payload["focus_programs"][0]["average_assessment_grade"] == 2.0

    business_program = next(
        program for program in payload["focus_programs"] if program["id"] == "business-acumen"
    )
    assert business_program["weak_review_count"] >= 1
    assert business_program["revision_backlog_count"] == 0


def test_get_guide_exposes_applied_assessment_plan(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    profile_path = get_user_paths("user-123")["profile_path"]
    ProfileStorage(profile_path).save(
        UserProfile(
            current_role="Healthcare operator",
            industries_watching=["healthcare"],
            weekly_hours_available=4,
        )
    )

    guide = client.get("/api/curriculum/guides/37-ai-ml-fundamentals-guide", headers=auth_headers)
    assert guide.status_code == 200
    payload = guide.json()
    assert len(payload["applied_assessments"]) == 4
    assert {assessment["stage"] for assessment in payload["applied_assessments"]} == {
        "chapter_completion",
        "review",
        "scenario_practice",
        "capstone",
    }


def test_launch_assessment_creates_draft_and_goal(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    resp = client.post(
        "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/launch",
        headers=auth_headers,
    )

    assert resp.status_code == 201
    payload = resp.json()
    assert payload["created"] is True

    storage = JournalStorage(get_user_paths("user-123")["journal_dir"])
    entry = storage.read(payload["entry_path"])
    goal = storage.read(payload["goal_path"])

    assert entry["curriculum_assessment_type"] == "decision_brief"
    assert entry["assessment_status"] == "draft"
    assert entry["linked_goal_path"] == payload["goal_path"]
    assert goal["curriculum_assessment_type"] == "decision_brief"
    assert goal["goal_type"] == "learning"


def test_get_guide_exposes_existing_assessment_draft_metadata(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)
    client.post(
        "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/launch",
        headers=auth_headers,
    )

    guide = client.get("/api/curriculum/guides/37-ai-ml-fundamentals-guide", headers=auth_headers)
    assert guide.status_code == 200
    payload = guide.json()
    decision_brief = next(
        assessment
        for assessment in payload["applied_assessments"]
        if assessment["type"] == "decision_brief"
    )
    assert decision_brief["draft_entry_path"]
    assert decision_brief["draft_goal_path"]
    assert decision_brief["draft_status"] == "draft"


def test_launch_assessment_reuses_existing_draft(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    first = client.post(
        "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/launch",
        headers=auth_headers,
    ).json()
    second = client.post(
        "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/launch",
        headers=auth_headers,
    ).json()

    assert first["entry_path"] == second["entry_path"]
    assert first["goal_path"] == second["goal_path"]
    assert second["created"] is False


def test_get_guide_finds_assessment_draft_beyond_latest_hundred_entries(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    launched = client.post(
        "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/launch",
        headers=auth_headers,
    ).json()

    storage = JournalStorage(get_user_paths("user-123")["journal_dir"])
    for index in range(120):
        storage.create(
            content=f"Noise entry {index}",
            entry_type="note",
            title=f"zzzz filler entry {index:03d}",
        )

    guide = client.get("/api/curriculum/guides/37-ai-ml-fundamentals-guide", headers=auth_headers)

    assert guide.status_code == 200
    payload = guide.json()
    decision_brief = next(
        assessment
        for assessment in payload["applied_assessments"]
        if assessment["type"] == "decision_brief"
    )
    assert decision_brief["draft_entry_path"] == launched["entry_path"]


def test_submit_assessment_grades_draft_and_updates_goal(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    launched = client.post(
        "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/launch",
        headers=auth_headers,
    ).json()

    storage = JournalStorage(get_user_paths("user-123")["journal_dir"])
    storage.update(
        launched["entry_path"],
        content=(
            "# Decision brief\n\n"
            "Recommend piloting a narrow internal AI assistant for support triage because it "
            "improves response quality, reduces repetitive work, and preserves a human review "
            "step for edge cases. The trade-offs are implementation effort, hallucination risk, "
            "and the need for clear escalation paths, metrics, and rollback criteria."
        ),
    )

    with patch(
        "web.routes.curriculum.QuestionGenerator.grade_applied_assessment",
        new=AsyncMock(
            return_value=ReviewGradeResult(
                grade=4,
                feedback="Strong framing with clear trade-offs.",
                correct_points=["Clear framing", "Good trade-off analysis"],
                missing_points=["Define explicit success metrics"],
            )
        ),
    ):
        resp = client.post(
            "/api/curriculum/guides/37-ai-ml-fundamentals-guide/assessments/decision_brief/submit",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "submitted"
    assert payload["grade"] == 4
    assert payload["feedback"] == "Strong framing with clear trade-offs."

    entry = storage.read(launched["entry_path"])
    goal = storage.read(launched["goal_path"])
    assert entry["assessment_status"] == "submitted"
    assert entry["assessment_feedback"]["grade"] == 4
    assert goal["status"] == "completed"
    assert all(milestone.get("completed") for milestone in goal["milestones"])


def test_retry_reviews_endpoint_returns_recent_weak_items(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)
    store = _curriculum_store()
    guide_id = "28-accounting"
    guide = store.get_guide(guide_id, user_id="user-123")
    chapter = guide["chapters"][0]

    store.add_review_items(
        [
            ReviewItem(
                id="retry-item-1",
                user_id="user-123",
                chapter_id=chapter["id"],
                guide_id=guide_id,
                question="What does working capital show?",
                expected_answer="It shows short-term operating liquidity.",
                bloom_level=BloomLevel.UNDERSTAND,
                item_type=ReviewItemType.QUIZ,
                next_review=datetime.utcnow() - timedelta(days=1),
            )
        ]
    )
    store.grade_review("retry-item-1", 2)

    resp = client.get("/api/curriculum/review/retry", headers=auth_headers)

    assert resp.status_code == 200
    payload = resp.json()
    assert [item["id"] for item in payload] == ["retry-item-1"]


def test_review_grade_uses_teachback_grader_for_teachback_items(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    store = _curriculum_store()
    chapter = store.get_guide("01-philosophy-guide", user_id="user-123")["chapters"][0]
    store.add_review_items(
        [
            ReviewItem(
                id="teachback-review",
                user_id="user-123",
                chapter_id=chapter["id"],
                guide_id=chapter["guide_id"],
                question="Explain opportunity cost as if teaching someone with no background",
                expected_answer="Opportunity cost is the value of the next-best alternative you give up.",
                bloom_level=BloomLevel.CREATE,
                item_type=ReviewItemType.TEACHBACK,
                next_review=datetime.utcnow() - timedelta(days=1),
            )
        ]
    )

    fake_generator = SimpleNamespace(
        grade_teachback=AsyncMock(
            return_value=ReviewGradeResult(
                grade=4,
                feedback="Clear explanation with a usable everyday example.",
                correct_points=["Defines the trade-off"],
                missing_points=["Sharpen the example"],
            )
        ),
        grade_answer=AsyncMock(),
    )

    with patch("web.routes.curriculum._build_question_generator", return_value=fake_generator):
        resp = client.post(
            "/api/curriculum/review/teachback-review/grade",
            headers=auth_headers,
            json={"answer": "It is what you give up when you choose one option over another."},
        )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["grade"] == 4
    assert payload["feedback"] == "Clear explanation with a usable everyday example."
    fake_generator.grade_teachback.assert_awaited_once()
    fake_generator.grade_answer.assert_not_called()


def test_quiz_generation_replaces_stale_cached_questions(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    store = _curriculum_store()
    chapter = store.get_guide("01-philosophy-guide", user_id="user-123")["chapters"][0]
    store.add_review_items(
        [
            ReviewItem(
                id="stale-quiz",
                user_id="user-123",
                chapter_id=chapter["id"],
                guide_id=chapter["guide_id"],
                question="Old quiz question",
                expected_answer="Old answer",
                bloom_level=BloomLevel.REMEMBER,
                item_type=ReviewItemType.QUIZ,
                content_hash="stale-hash",
                next_review=datetime.utcnow(),
            )
        ]
    )

    fresh_item = ReviewItem(
        id="fresh-quiz",
        user_id="user-123",
        chapter_id=chapter["id"],
        guide_id=chapter["guide_id"],
        question="Fresh quiz question",
        expected_answer="Fresh answer",
        bloom_level=BloomLevel.UNDERSTAND,
        item_type=ReviewItemType.QUIZ,
        content_hash=chapter["content_hash"],
        next_review=datetime.utcnow(),
    )
    fake_generator = SimpleNamespace(generate_questions=AsyncMock(return_value=[fresh_item]))

    with patch("web.routes.curriculum._build_question_generator", return_value=fake_generator):
        resp = client.post(
            f"/api/curriculum/quiz/{chapter['id']}/generate",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["cached"] is False
    assert [item["id"] for item in payload["questions"]] == ["fresh-quiz"]
    assert store.get_review_item("stale-quiz") is None
    assert store.get_review_item("fresh-quiz") is not None


def test_pre_reading_generation_reuses_current_quiz_without_duplication(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)

    store = _curriculum_store()
    chapter = store.get_guide("01-philosophy-guide", user_id="user-123")["chapters"][0]
    store.add_review_items(
        [
            ReviewItem(
                id="current-quiz",
                user_id="user-123",
                chapter_id=chapter["id"],
                guide_id=chapter["guide_id"],
                question="Current quiz question",
                expected_answer="Current answer",
                bloom_level=BloomLevel.REMEMBER,
                item_type=ReviewItemType.QUIZ,
                content_hash=chapter["content_hash"],
                next_review=datetime.utcnow(),
            )
        ]
    )

    generated_items = [
        ReviewItem(
            id="duplicate-quiz",
            user_id="user-123",
            chapter_id=chapter["id"],
            guide_id=chapter["guide_id"],
            question="Duplicate quiz question",
            expected_answer="Duplicate answer",
            bloom_level=BloomLevel.REMEMBER,
            item_type=ReviewItemType.QUIZ,
            content_hash=chapter["content_hash"],
            next_review=datetime.utcnow(),
        ),
        ReviewItem(
            id="fresh-pre-reading",
            user_id="user-123",
            chapter_id=chapter["id"],
            guide_id=chapter["guide_id"],
            question="Fresh pre-reading question",
            expected_answer="",
            bloom_level=BloomLevel.REMEMBER,
            item_type=ReviewItemType.PRE_READING,
            content_hash=chapter["content_hash"],
            next_review=None,
        ),
    ]
    fake_generator = SimpleNamespace(generate_questions=AsyncMock(return_value=generated_items))

    with patch("web.routes.curriculum._build_question_generator", return_value=fake_generator):
        resp = client.get(
            f"/api/curriculum/chapters/{chapter['id']}/pre-reading",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    payload = resp.json()
    assert [item["id"] for item in payload["questions"]] == ["fresh-pre-reading"]
    chapter_items = store.get_review_items_for_chapter("user-123", chapter["id"])
    quiz_ids = [item["id"] for item in chapter_items if item["item_type"] == "quiz"]
    assert quiz_ids == ["current-quiz"]
    assert store.get_review_item("duplicate-quiz") is None
    assert store.get_review_item("fresh-pre-reading") is not None


def test_today_merges_retry_items_into_review_task(client, auth_headers):
    client.post("/api/curriculum/sync", headers=auth_headers)
    store = _curriculum_store()
    guide_id = "28-accounting"
    guide = store.get_guide(guide_id, user_id="user-123")
    chapter = guide["chapters"][0]

    store.enroll("user-123", guide_id)
    store.add_review_items(
        [
            ReviewItem(
                id="retry-item-today",
                user_id="user-123",
                chapter_id=chapter["id"],
                guide_id=guide_id,
                question="Why do margins matter?",
                expected_answer="They show unit economics and operating leverage.",
                bloom_level=BloomLevel.UNDERSTAND,
                item_type=ReviewItemType.QUIZ,
                next_review=datetime.utcnow() - timedelta(days=1),
            )
        ]
    )
    store.grade_review("retry-item-today", 1)

    resp = client.get("/api/curriculum/today", headers=auth_headers)

    assert resp.status_code == 200
    payload = resp.json()
    review_task = next(task for task in payload["tasks"] if task["task_type"] == "due_reviews")
    assert review_task["review_count"] == 1
    assert review_task["cta_label"] == "Start review"


def test_placement_generate_disabled(client, auth_headers):
    """POST placement/generate returns 400 when placement disabled."""
    client.post("/api/curriculum/sync", headers=auth_headers)
    guides = client.get("/api/curriculum/guides", headers=auth_headers).json()
    if not guides:
        return

    with patch("web.routes.curriculum.get_config") as mock_config:
        cfg = mock_config.return_value
        cfg.curriculum.placement_enabled = False
        cfg.curriculum.teachback_enabled = True
        cfg.curriculum.pre_reading_enabled = True
        cfg.curriculum.cross_guide_connections = True
        cfg.memory.enabled = False
        resp = client.post(
            f"/api/curriculum/guides/{guides[0]['id']}/placement/generate",
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "disabled" in resp.json()["detail"].lower()


def test_placement_submit_expired(client, auth_headers):
    """POST placement/submit returns 410 when no cached session."""
    client.post("/api/curriculum/sync", headers=auth_headers)
    guides = client.get("/api/curriculum/guides", headers=auth_headers).json()
    if not guides:
        return

    resp = client.post(
        f"/api/curriculum/guides/{guides[0]['id']}/placement/submit",
        headers=auth_headers,
        json={"answers": {"q1": "answer"}},
    )
    assert resp.status_code == 410


def test_placement_generate_and_submit(client, auth_headers):
    """Full placement flow: generate → submit → verify result structure."""
    client.post("/api/curriculum/sync", headers=auth_headers)
    guides = client.get("/api/curriculum/guides", headers=auth_headers).json()
    if not guides:
        return

    guide_id = guides[0]["id"]

    # Mock the question generator to return predictable questions
    mock_questions = [
        {
            "id": "pq1",
            "question": "Test placement Q1",
            "expected_answer": "Answer 1",
            "bloom_level": "apply",
            "chapter_id": "ch1",
        },
        {
            "id": "pq2",
            "question": "Test placement Q2",
            "expected_answer": "Answer 2",
            "bloom_level": "analyze",
            "chapter_id": "ch1",
        },
    ]

    fake_generator = SimpleNamespace(
        generate_placement_questions=AsyncMock(return_value=mock_questions),
        grade_answer=AsyncMock(
            return_value=type(
                "R",
                (),
                {"grade": 4, "feedback": "Good", "correct_points": [], "missing_points": []},
            )()
        ),
    )

    with patch("web.routes.curriculum._build_question_generator", return_value=fake_generator):
        # Generate
        resp = client.post(
            f"/api/curriculum/guides/{guide_id}/placement/generate",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "questions" in data
        assert len(data["questions"]) > 0
        # Client should NOT see expected_answer
        for q in data["questions"]:
            assert "expected_answer" not in q

        # Submit
        answers = {q["id"]: "my answer" for q in data["questions"]}
        resp = client.post(
            f"/api/curriculum/guides/{guide_id}/placement/submit",
            headers=auth_headers,
            json={"answers": answers},
        )
        assert resp.status_code == 200
        result = resp.json()
        assert "results" in result
        assert "average_grade" in result
        assert "passed" in result
        assert "threshold" in result

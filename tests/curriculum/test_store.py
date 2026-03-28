"""Tests for curriculum SQLite store."""

import uuid
from datetime import datetime

import pytest

from curriculum.models import (
    BloomLevel,
    Chapter,
    DifficultyLevel,
    Guide,
    GuideCategory,
    ReviewItem,
    ReviewItemType,
)
from curriculum.store import CurriculumStore


@pytest.fixture
def store(tmp_path):
    return CurriculumStore(tmp_path / "curriculum.db")


@pytest.fixture
def sample_guide():
    return Guide(
        id="01-philosophy-guide",
        title="Philosophy",
        category=GuideCategory.HUMANITIES,
        difficulty=DifficultyLevel.INTRODUCTORY,
        source_dir="/content/01-philosophy-guide",
        chapter_count=3,
        total_word_count=5000,
        total_reading_time_minutes=20,
        has_glossary=True,
        prerequisites=[],
    )


@pytest.fixture
def sample_chapters():
    return [
        Chapter(
            id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            title="Introduction to Philosophy",
            filename="01-introduction.md",
            order=0,
            word_count=2000,
            reading_time_minutes=8,
            content_hash="abc123",
        ),
        Chapter(
            id="01-philosophy-guide/02-logic",
            guide_id="01-philosophy-guide",
            title="Logic and Reasoning",
            filename="02-logic.md",
            order=1,
            word_count=2500,
            reading_time_minutes=10,
            content_hash="def456",
        ),
        Chapter(
            id="01-philosophy-guide/03-glossary",
            guide_id="01-philosophy-guide",
            title="Glossary",
            filename="03-glossary.md",
            order=2,
            word_count=500,
            reading_time_minutes=2,
            is_glossary=True,
            content_hash="ghi789",
        ),
    ]


def test_sync_catalog(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    guides = store.list_guides()
    assert len(guides) == 1
    assert guides[0]["id"] == "01-philosophy-guide"


def test_get_guide_with_chapters(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    guide = store.get_guide("01-philosophy-guide")
    assert guide is not None
    assert len(guide["chapters"]) == 3


def test_enrollment(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"

    assert not store.is_enrolled(user_id, "01-philosophy-guide")
    store.enroll(user_id, "01-philosophy-guide")
    assert store.is_enrolled(user_id, "01-philosophy-guide")

    enrollments = store.get_enrollments(user_id)
    assert len(enrollments) == 1


def test_progress_tracking(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"

    # Start reading
    result = store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        status="in_progress",
    )
    assert result["status"] == "in_progress"
    assert result["started_at"] is not None

    # Complete
    result = store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        status="completed",
    )
    assert result["status"] == "completed"
    assert result["completed_at"] is not None


def test_reading_time_accumulates(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"

    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        status="in_progress",
        reading_time_seconds=30,
    )
    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        reading_time_seconds=45,
    )
    progress = store.get_chapter_progress(user_id, "01-philosophy-guide/01-introduction")
    assert progress["reading_time_seconds"] == 75


def test_guide_auto_complete(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    store.enroll(user_id, "01-philosophy-guide")

    # Complete non-glossary chapters
    for ch_id in ["01-philosophy-guide/01-introduction", "01-philosophy-guide/02-logic"]:
        store.update_progress(
            user_id=user_id,
            chapter_id=ch_id,
            guide_id="01-philosophy-guide",
            status="completed",
        )

    # Guide should be auto-completed (glossary not required)
    enrollments = store.get_enrollments(user_id)
    assert enrollments[0]["completed_at"] is not None


def test_review_items(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    now = datetime.utcnow()

    items = [
        ReviewItem(
            id=uuid.uuid4().hex[:16],
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="What is philosophy?",
            expected_answer="The study of fundamental questions about existence, knowledge, values.",
            bloom_level=BloomLevel.REMEMBER,
            next_review=now,
            created_at=now,
            content_hash="abc123",
        ),
    ]
    store.add_review_items(items)

    due = store.get_due_reviews(user_id)
    assert len(due) == 1
    assert due[0]["question"] == "What is philosophy?"


def test_grade_review_updates_schedule(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    now = datetime.utcnow()
    item_id = uuid.uuid4().hex[:16]

    items = [
        ReviewItem(
            id=item_id,
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="Test question",
            expected_answer="Test answer",
            bloom_level=BloomLevel.REMEMBER,
            next_review=now,
            created_at=now,
            content_hash="abc123",
        ),
    ]
    store.add_review_items(items)

    updated = store.grade_review(item_id, 5)
    assert updated is not None
    assert updated["repetitions"] == 1
    assert updated["interval_days"] == 1


def test_stats(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    store.enroll(user_id, "01-philosophy-guide")

    stats = store.get_stats(user_id)
    assert stats.guides_enrolled == 1
    assert stats.total_chapters == 3
    assert stats.chapters_completed == 0


def test_next_chapter(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"

    # First chapter should be next
    nxt = store.get_next_chapter(user_id, "01-philosophy-guide")
    assert nxt is not None
    assert nxt["id"] == "01-philosophy-guide/01-introduction"

    # Complete first, next should be second
    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        status="completed",
    )
    nxt = store.get_next_chapter(user_id, "01-philosophy-guide")
    assert nxt["id"] == "01-philosophy-guide/02-logic"


def test_list_guides_with_progress(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    store.enroll(user_id, "01-philosophy-guide")
    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        status="completed",
    )

    guides = store.list_guides(user_id=user_id)
    assert guides[0]["enrolled"]
    assert guides[0]["chapters_completed"] == 1
    assert guides[0]["progress_pct"] > 0


def test_count_due_reviews(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"

    assert store.count_due_reviews(user_id) == 0

    items = [
        ReviewItem(
            id=uuid.uuid4().hex[:16],
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="Q1",
            expected_answer="A1",
            bloom_level=BloomLevel.REMEMBER,
            next_review=datetime.utcnow(),
            created_at=datetime.utcnow(),
            content_hash="abc",
        ),
    ]
    store.add_review_items(items)
    assert store.count_due_reviews(user_id) == 1


def test_get_chapter_metadata(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    ch = store.get_chapter("01-philosophy-guide/01-introduction")
    assert ch is not None
    assert ch["title"] == "Introduction to Philosophy"
    assert ch["word_count"] == 2000


def test_reconcile_guide_aliases_merges_user_data_and_removes_alias_catalog_rows(store):
    alias_guide = Guide(
        id="32-engineering-guide",
        title="Engineering Legacy",
        category=GuideCategory.TECHNOLOGY,
        difficulty=DifficultyLevel.INTERMEDIATE,
        source_dir="/content/32-engineering-guide",
        chapter_count=1,
        total_word_count=1200,
        total_reading_time_minutes=5,
        has_glossary=False,
        prerequisites=[],
    )
    canonical_guide = Guide(
        id="35-engineering-guide",
        title="Engineering",
        category=GuideCategory.TECHNOLOGY,
        difficulty=DifficultyLevel.INTERMEDIATE,
        source_dir="/content/35-engineering-guide",
        chapter_count=1,
        total_word_count=2200,
        total_reading_time_minutes=9,
        has_glossary=False,
        prerequisites=[],
    )
    alias_chapter = Chapter(
        id="32-engineering-guide/01-introduction",
        guide_id="32-engineering-guide",
        title="Legacy intro",
        filename="01-introduction.md",
        order=0,
        word_count=1200,
        reading_time_minutes=5,
        content_hash="legacy123",
    )
    canonical_chapter = Chapter(
        id="35-engineering-guide/01-introduction",
        guide_id="35-engineering-guide",
        title="Canonical intro",
        filename="01-introduction.md",
        order=0,
        word_count=2200,
        reading_time_minutes=9,
        content_hash="canon123",
    )
    store.sync_catalog([alias_guide, canonical_guide], [alias_chapter, canonical_chapter])

    user_id = "test-user"
    store.enroll(user_id, "35-engineering-guide")
    store.enroll(user_id, "32-engineering-guide", linked_goal_id="goal-legacy")
    store.update_progress(
        user_id=user_id,
        chapter_id="35-engineering-guide/01-introduction",
        guide_id="35-engineering-guide",
        status="in_progress",
        reading_time_seconds=30,
    )
    store.update_progress(
        user_id=user_id,
        chapter_id="32-engineering-guide/01-introduction",
        guide_id="32-engineering-guide",
        status="completed",
        reading_time_seconds=45,
    )
    store.add_review_items(
        [
            ReviewItem(
                id="review-legacy",
                user_id=user_id,
                chapter_id="32-engineering-guide/01-introduction",
                guide_id="32-engineering-guide",
                question="Legacy question",
                expected_answer="Legacy answer",
                bloom_level=BloomLevel.REMEMBER,
                item_type=ReviewItemType.QUIZ,
                next_review=datetime.utcnow(),
                created_at=datetime.utcnow(),
                content_hash="legacy123",
            )
        ]
    )

    stats = store.reconcile_guide_aliases(
        {"32-engineering-guide": "35-engineering-guide"}
    )

    assert stats["aliases_processed"] == 1
    assert stats["enrollments_merged"] == 1
    assert stats["progress_rows_migrated"] == 1
    assert stats["review_items_migrated"] == 1
    assert store.get_guide("32-engineering-guide") is None
    assert store.get_chapter("32-engineering-guide/01-introduction") is None

    enrollments = store.get_enrollments(user_id)
    assert len(enrollments) == 1
    assert enrollments[0]["guide_id"] == "35-engineering-guide"
    assert enrollments[0]["linked_goal_id"] == "goal-legacy"

    progress = store.get_chapter_progress(user_id, "35-engineering-guide/01-introduction")
    assert progress is not None
    assert progress["guide_id"] == "35-engineering-guide"
    assert progress["status"] == "completed"
    assert progress["reading_time_seconds"] == 75
    assert (
        store.get_chapter_progress(user_id, "32-engineering-guide/01-introduction") is None
    )

    review_item = store.get_review_item("review-legacy")
    assert review_item is not None
    assert review_item["guide_id"] == "35-engineering-guide"
    assert review_item["chapter_id"] == "35-engineering-guide/01-introduction"


def test_schema_v4_chapter_metadata_columns(store, sample_guide, sample_chapters):
    sample_chapters[0].summary = "An introduction to philosophical inquiry."
    sample_chapters[0].objectives = ["Understand the core branches of philosophy."]
    sample_chapters[0].checkpoints = ["Explain what philosophy studies."]
    sample_chapters[0].content_references = ["curriculum:01-philosophy-guide/02-logic"]
    sample_chapters[0].content_format = "mdx"
    sample_chapters[0].schema_version = 1

    store.sync_catalog([sample_guide], sample_chapters)

    chapter = store.get_chapter("01-philosophy-guide/01-introduction")
    assert chapter["summary"] == "An introduction to philosophical inquiry."
    assert chapter["objectives"] == ["Understand the core branches of philosophy."]
    assert chapter["checkpoints"] == ["Explain what philosophy studies."]
    assert chapter["content_references"] == ["curriculum:01-philosophy-guide/02-logic"]
    assert chapter["content_format"] == "mdx"
    assert chapter["schema_version"] == 1


def test_schema_v2_item_type_column(store, sample_guide, sample_chapters):
    """Schema v2 migration adds item_type column."""
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    now = datetime.utcnow()

    # Default item_type is quiz
    items = [
        ReviewItem(
            id="quiz-1",
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="What is X?",
            expected_answer="X is Y",
            bloom_level=BloomLevel.REMEMBER,
            next_review=now,
            created_at=now,
        ),
    ]
    store.add_review_items(items)
    item = store.get_review_item("quiz-1")
    assert item["item_type"] == "quiz"


def test_add_teachback_item(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    now = datetime.utcnow()

    items = [
        ReviewItem(
            id="tb-1",
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="Explain logic as if teaching someone with no background",
            expected_answer="Logic is the study of reasoning",
            bloom_level=BloomLevel.CREATE,
            item_type=ReviewItemType.TEACHBACK,
            next_review=now,
            created_at=now,
        ),
    ]
    store.add_review_items(items)

    tb = store.get_teachback_for_chapter(user_id, "01-philosophy-guide/01-introduction")
    assert tb is not None
    assert tb["item_type"] == "teachback"
    assert tb["bloom_level"] == "create"


def test_pre_reading_items(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    now = datetime.utcnow()

    items = [
        ReviewItem(
            id="pr-1",
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="What questions does philosophy try to answer?",
            expected_answer="",
            bloom_level=BloomLevel.REMEMBER,
            item_type=ReviewItemType.PRE_READING,
            next_review=None,
            created_at=now,
        ),
        ReviewItem(
            id="pr-2",
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="Why is philosophy still relevant?",
            expected_answer="",
            bloom_level=BloomLevel.REMEMBER,
            item_type=ReviewItemType.PRE_READING,
            next_review=None,
            created_at=now,
        ),
    ]
    store.add_review_items(items)

    prs = store.get_pre_reading_questions(user_id, "01-philosophy-guide/01-introduction")
    assert len(prs) == 2
    assert all(p["item_type"] == "pre_reading" for p in prs)


def test_pre_reading_excluded_from_due_reviews(store, sample_guide, sample_chapters):
    """Pre-reading items never appear in due reviews."""
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    now = datetime.utcnow()

    items = [
        ReviewItem(
            id="quiz-due",
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="Quiz Q",
            expected_answer="A",
            bloom_level=BloomLevel.REMEMBER,
            item_type=ReviewItemType.QUIZ,
            next_review=now,
            created_at=now,
        ),
        ReviewItem(
            id="tb-due",
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="Teach-back Q",
            expected_answer="A",
            bloom_level=BloomLevel.CREATE,
            item_type=ReviewItemType.TEACHBACK,
            next_review=now,
            created_at=now,
        ),
        ReviewItem(
            id="pr-not-due",
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="Pre-reading Q",
            expected_answer="",
            bloom_level=BloomLevel.REMEMBER,
            item_type=ReviewItemType.PRE_READING,
            next_review=now,
            created_at=now,
        ),
    ]
    store.add_review_items(items)

    due = store.get_due_reviews(user_id)
    due_ids = [d["id"] for d in due]
    assert "quiz-due" in due_ids
    assert "tb-due" in due_ids
    assert "pr-not-due" not in due_ids


# --- Skill tree / mastery tests ---


def test_schema_v3_track_column(store, sample_guide, sample_chapters):
    """v3 migration adds track column."""
    sample_guide.track = "foundations"
    store.sync_catalog([sample_guide], sample_chapters)
    guides = store.list_guides()
    assert guides[0]["track"] == "foundations"


def test_list_guides_includes_track_and_mastery(store, sample_guide, sample_chapters):
    sample_guide.track = "foundations"
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    guides = store.list_guides(user_id=user_id)
    assert "track" in guides[0]
    assert "mastery_score" in guides[0]


def test_mastery_score_no_reviews(store, sample_guide, sample_chapters):
    """Mastery = completion_pct * 0.4 when no reviews."""
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    store.enroll(user_id, "01-philosophy-guide")

    # Complete 1 of 3 chapters
    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        status="completed",
    )

    guides = store.list_guides(user_id=user_id)
    g = guides[0]
    # completion_pct = 1/3 * 100 = 33.33, mastery = 33.33 * 0.4 = 13.3
    assert 13.0 <= g["mastery_score"] <= 14.0


def test_mastery_score_with_reviews(store, sample_guide, sample_chapters):
    """Blended mastery from completion + review EF."""
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"

    # Complete all non-glossary chapters
    for ch_id in ["01-philosophy-guide/01-introduction", "01-philosophy-guide/02-logic"]:
        store.update_progress(
            user_id=user_id,
            chapter_id=ch_id,
            guide_id="01-philosophy-guide",
            status="completed",
        )

    # Add review with good EF (2.5 default, graded well)
    now = datetime.utcnow()
    items = [
        ReviewItem(
            id="mastery-q1",
            user_id=user_id,
            chapter_id="01-philosophy-guide/01-introduction",
            guide_id="01-philosophy-guide",
            question="Q1",
            expected_answer="A1",
            bloom_level=BloomLevel.REMEMBER,
            next_review=now,
            created_at=now,
        ),
    ]
    store.add_review_items(items)
    store.grade_review("mastery-q1", 5)

    guides = store.list_guides(user_id=user_id)
    g = guides[0]
    assert g["mastery_score"] > 0


def test_mastery_score_no_progress(store, sample_guide, sample_chapters):
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"
    guides = store.list_guides(user_id=user_id)
    assert guides[0]["mastery_score"] == 0.0


def test_list_tracks(store, sample_chapters):
    """Track aggregation works."""
    guide1 = Guide(
        id="01-philosophy-guide",
        title="Philosophy",
        category=GuideCategory.HUMANITIES,
        difficulty=DifficultyLevel.INTRODUCTORY,
        chapter_count=3,
        prerequisites=[],
        track="foundations",
    )
    guide2 = Guide(
        id="02-economics-guide",
        title="Economics",
        category=GuideCategory.BUSINESS,
        difficulty=DifficultyLevel.INTERMEDIATE,
        chapter_count=1,
        prerequisites=[],
        track="business_economics",
    )
    econ_chapter = Chapter(
        id="02-economics-guide/01-introduction",
        guide_id="02-economics-guide",
        title="Intro Econ",
        filename="01-introduction.md",
        order=0,
        word_count=1000,
    )
    store.sync_catalog([guide1, guide2], sample_chapters + [econ_chapter])

    track_meta = {
        "foundations": {"title": "Foundations", "description": "Core", "color": "#6366f1"},
        "business_economics": {"title": "Business", "description": "Biz", "color": "#3b82f6"},
    }
    tracks = store.list_tracks("test-user", track_meta)
    assert len(tracks) == 2

    foundations = next(t for t in tracks if t["id"] == "foundations")
    assert foundations["guide_count"] == 1
    assert "01-philosophy-guide" in foundations["guide_ids"]


def test_list_tracks_uncategorized(store, sample_guide, sample_chapters):
    """Guides without track grouped into _uncategorized."""
    store.sync_catalog([sample_guide], sample_chapters)  # sample_guide has track=""
    tracks = store.list_tracks("test-user", {})
    uncategorized = next((t for t in tracks if t["id"] == "_uncategorized"), None)
    assert uncategorized is not None
    assert uncategorized["guide_count"] == 1


def test_list_tracks_excludes_superseded_guides(store, sample_chapters):
    guide1 = Guide(
        id="01-philosophy-guide",
        title="Philosophy",
        category=GuideCategory.HUMANITIES,
        difficulty=DifficultyLevel.INTRODUCTORY,
        chapter_count=3,
        prerequisites=[],
        track="foundations",
    )
    guide2 = Guide(
        id="02-legacy-guide",
        title="Legacy",
        category=GuideCategory.HUMANITIES,
        difficulty=DifficultyLevel.INTRODUCTORY,
        chapter_count=1,
        prerequisites=[],
        track="foundations",
    )
    legacy_chapter = Chapter(
        id="02-legacy-guide/01-introduction",
        guide_id="02-legacy-guide",
        title="Legacy Intro",
        filename="01-introduction.md",
        order=0,
        word_count=500,
    )
    store.sync_catalog([guide1, guide2], sample_chapters + [legacy_chapter])

    tracks = store.list_tracks(
        "test-user",
        {"foundations": {"title": "Foundations", "description": "Core", "color": "#6366f1"}},
        excluded_guide_ids={"02-legacy-guide"},
    )

    foundations = next(t for t in tracks if t["id"] == "foundations")
    assert foundations["guide_count"] == 1
    assert foundations["guide_ids"] == ["01-philosophy-guide"]


# --- get_tree_data tests ---


def test_get_tree_data_basic(store, sample_guide, sample_chapters):
    """Returns all guides with expected fields."""
    store.sync_catalog([sample_guide], sample_chapters)
    data = store.get_tree_data("test-user")
    assert len(data) == 1
    node = data[0]
    assert node["id"] == "01-philosophy-guide"
    assert node["title"] == "Philosophy"
    assert "status" in node
    assert "mastery_score" in node
    assert "prerequisites" in node
    assert node["status"] == "not_started"


def test_get_tree_data_with_progress(store, sample_guide, sample_chapters):
    """Status transitions: enrolled → in_progress → completed."""
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"

    # Not enrolled → not_started
    data = store.get_tree_data(user_id)
    assert data[0]["status"] == "not_started"

    # Enroll → enrolled
    store.enroll(user_id, "01-philosophy-guide")
    data = store.get_tree_data(user_id)
    assert data[0]["status"] == "enrolled"
    assert data[0]["enrolled"]

    # Complete one chapter → in_progress
    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        status="completed",
    )
    data = store.get_tree_data(user_id)
    assert data[0]["status"] == "in_progress"
    assert data[0]["chapters_completed"] == 1

    # Complete all non-glossary → completed
    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/02-logic",
        guide_id="01-philosophy-guide",
        status="completed",
    )
    data = store.get_tree_data(user_id)
    assert data[0]["status"] == "completed"


def test_get_tree_data_mastery(store, sample_guide, sample_chapters):
    """Mastery computed per node."""
    store.sync_catalog([sample_guide], sample_chapters)
    user_id = "test-user"

    # No progress → 0
    data = store.get_tree_data(user_id)
    assert data[0]["mastery_score"] == 0.0

    # Partial progress → mastery > 0
    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        status="completed",
    )
    data = store.get_tree_data(user_id)
    assert data[0]["mastery_score"] > 0


def test_get_tree_data_excludes_superseded_guides(store, sample_guide, sample_chapters):
    legacy_guide = Guide(
        id="02-legacy-guide",
        title="Legacy",
        category=GuideCategory.HUMANITIES,
        difficulty=DifficultyLevel.INTRODUCTORY,
        chapter_count=1,
        prerequisites=[],
    )
    legacy_chapter = Chapter(
        id="02-legacy-guide/01-introduction",
        guide_id="02-legacy-guide",
        title="Legacy Intro",
        filename="01-introduction.md",
        order=0,
        word_count=500,
    )
    store.sync_catalog([sample_guide, legacy_guide], sample_chapters + [legacy_chapter])

    data = store.get_tree_data("test-user", excluded_guide_ids={"02-legacy-guide"})
    assert [node["id"] for node in data] == ["01-philosophy-guide"]


def test_get_ready_guides_excludes_superseded_guides(store, sample_guide, sample_chapters):
    ready_guide = Guide(
        id="02-legacy-guide",
        title="Legacy",
        category=GuideCategory.HUMANITIES,
        difficulty=DifficultyLevel.INTERMEDIATE,
        chapter_count=1,
        prerequisites=["01-philosophy-guide"],
    )
    ready_chapter = Chapter(
        id="02-legacy-guide/01-introduction",
        guide_id="02-legacy-guide",
        title="Legacy Intro",
        filename="01-introduction.md",
        order=0,
        word_count=500,
    )
    store.sync_catalog([sample_guide, ready_guide], sample_chapters + [ready_chapter])
    user_id = "test-user"
    store.enroll(user_id, "01-philosophy-guide")
    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/01-introduction",
        guide_id="01-philosophy-guide",
        status="completed",
    )
    store.update_progress(
        user_id=user_id,
        chapter_id="01-philosophy-guide/02-logic",
        guide_id="01-philosophy-guide",
        status="completed",
    )

    ready = store.get_ready_guides(user_id, excluded_guide_ids={"02-legacy-guide"})
    assert ready == []

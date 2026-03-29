"""Tests for SupplementaryRetriever."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from advisor.retrievers.supplementary import SupplementaryRetriever
from curriculum.models import BloomLevel, Chapter, Guide, GuideCategory, ReviewItem, ReviewItemType
from curriculum.store import CurriculumStore
from journal.storage import JournalStorage
from web.deps import get_user_paths


class TestGetDocumentContext:
    def test_no_library_index(self):
        sr = SupplementaryRetriever()
        assert sr.get_document_context("q") == ""

    def test_with_attachment_ids(self):
        lib = MagicMock()
        lib.get_item_text.return_value = {
            "report_id": "r1",
            "title": "Doc",
            "extracted_text": "content here",
            "file_name": "doc.pdf",
            "source_kind": "document",
        }
        sr = SupplementaryRetriever(library_index=lib)
        result = sr.get_document_context("q", attachment_ids=["r1"])
        assert "Doc" in result
        assert "content here" in result

    def test_no_results_returns_empty(self):
        lib = MagicMock()
        lib.get_item_text.return_value = None
        lib.hybrid_search.return_value = []
        sr = SupplementaryRetriever(library_index=lib)
        assert sr.get_document_context("q") == ""


class TestGetRepoContext:
    def test_no_user_id(self):
        sr = SupplementaryRetriever()
        assert sr.get_repo_context("q") == ""

    def test_no_intel_db(self):
        sr = SupplementaryRetriever(user_id="u1")
        assert sr.get_repo_context("q") == ""


class TestGetCurriculumContext:
    def test_no_user_id(self):
        sr = SupplementaryRetriever()
        assert sr.get_curriculum_context("q") == ""

    def test_no_intel_db(self):
        sr = SupplementaryRetriever(user_id="u1")
        assert sr.get_curriculum_context("q") == ""

    def test_includes_learning_pressure_and_assessment_signals(self, tmp_path, monkeypatch):
        monkeypatch.setenv("COACH_HOME", str(tmp_path))
        user_id = "u1"
        paths = get_user_paths(user_id)
        store = CurriculumStore(paths["data_dir"] / "curriculum.db")
        guide_id = "decision-guide"
        chapter_id = f"{guide_id}/01-foundations"

        store.upsert_guide(
            Guide(
                id=guide_id,
                title="Decision Foundations",
                category=GuideCategory.BUSINESS,
                chapter_count=1,
                track="business_economics",
            )
        )
        store.upsert_chapter(
            Chapter(
                id=chapter_id,
                guide_id=guide_id,
                title="Foundations",
                filename="01-foundations.md",
                order=1,
                content_hash="hash-1",
            )
        )
        store.enroll(user_id, guide_id)
        store.update_progress(
            user_id,
            chapter_id,
            guide_id,
            status="in_progress",
            reading_time_seconds=180,
        )
        store.add_review_items(
            [
                ReviewItem(
                    id="weak-review",
                    user_id=user_id,
                    chapter_id=chapter_id,
                    guide_id=guide_id,
                    question="Why does framing matter?",
                    expected_answer="It defines the decision before solutioning.",
                    bloom_level=BloomLevel.UNDERSTAND,
                    item_type=ReviewItemType.QUIZ,
                    next_review=datetime.utcnow() - timedelta(days=1),
                )
            ]
        )
        store.grade_review("weak-review", 2)

        storage = JournalStorage(paths["journal_dir"])
        storage.create(
            content="# Decision brief\n\nDraft needs revision.",
            entry_type="reflection",
            title="Decision brief draft",
            metadata={
                "curriculum_guide_id": guide_id,
                "curriculum_assessment_type": "decision_brief",
                "assessment_status": "active",
                "assessment_feedback": {"grade": 2, "feedback": "Revise and tighten the case."},
            },
        )

        intel_db = paths["intel_db"]
        intel_db.touch()
        sr = SupplementaryRetriever(user_id=user_id, intel_db_path=intel_db)

        result = sr.get_curriculum_context("help me study")

        assert "<curriculum_progress>" in result
        assert 'learning_pressure due_reviews="0" retry_reviews="1"' in result
        assert 'weak_reviews="1"' in result
        assert 'active_revisions="1"' in result
        assert f'guide id="{guide_id}"' in result
        assert 'progress="0/1"' in result
        assert 'weak_reviews="1"' in result
        assert 'revision_backlog="1"' in result
        assert 'avg_assessment_grade="2.0"' in result

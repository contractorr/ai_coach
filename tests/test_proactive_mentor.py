"""Tests for proactive mentor upgrade — profile, events, learning, projects, nudges."""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# === Phase 1: Profile ===


class TestProfileStorage:
    def test_save_and_load(self, tmp_path):
        from profile.storage import ProfileStorage, Skill, UserProfile

        ps = ProfileStorage(tmp_path / "profile.yaml")
        profile = UserProfile(
            skills=[Skill(name="Python", proficiency=4), Skill(name="SQL", proficiency=3)],
            interests=["machine learning", "distributed systems"],
            career_stage="senior",
            current_role="Backend Engineer",
            aspirations="Move into ML engineering",
            location="San Francisco, CA",
            languages_frameworks=["python", "go", "pytorch"],
            learning_style="hands-on",
            weekly_hours_available=8,
        )
        ps.save(profile)

        loaded = ps.load()
        assert loaded is not None
        assert loaded.current_role == "Backend Engineer"
        assert len(loaded.skills) == 2
        assert loaded.skills[0].name == "Python"
        assert loaded.career_stage == "senior"
        assert loaded.location == "San Francisco, CA"
        assert loaded.updated_at is not None

    def test_load_nonexistent(self, tmp_path):
        from profile.storage import ProfileStorage

        ps = ProfileStorage(tmp_path / "nope.yaml")
        assert ps.load() is None
        assert ps.exists() is False

    def test_update_field(self, tmp_path):
        from profile.storage import ProfileStorage, UserProfile

        ps = ProfileStorage(tmp_path / "profile.yaml")
        ps.save(UserProfile(current_role="Junior Dev"))

        updated = ps.update_field("current_role", "Senior Dev")
        assert updated.current_role == "Senior Dev"

        # Verify persisted
        loaded = ps.load()
        assert loaded.current_role == "Senior Dev"

    def test_update_unknown_field(self, tmp_path):
        from profile.storage import ProfileStorage, UserProfile

        ps = ProfileStorage(tmp_path / "profile.yaml")
        ps.save(UserProfile())
        with pytest.raises(ValueError, match="Unknown"):
            ps.update_field("nonexistent", "value")

    def test_is_stale(self, tmp_path):
        from profile.storage import ProfileStorage, UserProfile

        ProfileStorage(tmp_path / "profile.yaml")
        profile = UserProfile()
        profile.updated_at = (datetime.now() - timedelta(days=100)).isoformat()
        assert profile.is_stale(days=90) is True
        assert profile.is_stale(days=120) is False

    def test_summary(self):
        from profile.storage import Skill, UserProfile

        p = UserProfile(
            current_role="ML Engineer",
            career_stage="senior",
            skills=[Skill(name="Python", proficiency=5)],
            interests=["AI"],
            location="NYC",
        )
        s = p.summary()
        assert "ML Engineer" in s
        assert "Python" in s
        assert "NYC" in s

    def test_get_or_empty(self, tmp_path):
        from profile.storage import ProfileStorage

        ps = ProfileStorage(tmp_path / "profile.yaml")
        p = ps.get_or_empty()
        assert p.current_role == ""


class TestProfileInterview:
    def test_extract_profile_json(self):
        from profile.interview import _extract_profile_json

        text = """Here's your profile:
```json
{"done": true, "profile": {
  "current_role": "Engineer",
  "career_stage": "mid",
  "skills": [{"name": "Python", "proficiency": 4}],
  "interests": ["AI"],
  "languages_frameworks": ["python"],
  "aspirations": "Lead a team",
  "location": "NYC",
  "learning_style": "hands-on",
  "weekly_hours_available": 5
}}
```"""
        result = _extract_profile_json(text)
        assert result is not None
        assert result["current_role"] == "Engineer"
        assert result["career_stage"] == "mid"

    def test_extract_no_json(self):
        from profile.interview import _extract_profile_json

        assert _extract_profile_json("Just a normal response") is None

    def test_build_profile(self):
        from profile.interview import _build_profile

        data = {
            "current_role": "Dev",
            "career_stage": "senior",
            "skills": [{"name": "Go", "proficiency": 3}],
            "interests": ["systems"],
            "languages_frameworks": ["go", "rust"],
            "aspirations": "Architect",
            "location": "London",
            "learning_style": "reading",
            "weekly_hours_available": 10,
        }
        p = _build_profile(data)
        assert p.current_role == "Dev"
        assert p.career_stage == "senior"
        assert len(p.skills) == 1
        assert p.learning_style == "reading"
        assert p.weekly_hours_available == 10

    def test_build_profile_invalid_values(self):
        from profile.interview import _build_profile

        data = {
            "career_stage": "wizard",
            "learning_style": "telepathy",
            "weekly_hours_available": "lots",
            "skills": [{"name": "X", "proficiency": 99}],
        }
        p = _build_profile(data)
        assert p.career_stage == "mid"  # fallback
        assert p.learning_style == "mixed"  # fallback
        assert p.weekly_hours_available == 5  # fallback
        assert p.skills[0].proficiency == 5  # clamped


class TestCareerStageEnum:
    def test_career_stages(self):
        from shared_types import CareerStage

        assert CareerStage.JUNIOR == "junior"
        assert CareerStage.EXEC == "exec"


# === Phase 2: Events ===


class TestEventScoring:
    def test_score_basic(self):
        from advisor.events import score_event

        event = {
            "tags": "event,python",
            "content": json.dumps(
                {"event_date": (datetime.now() + timedelta(days=20)).isoformat()}
            ),
        }
        score = score_event(event)
        assert 0 <= score <= 10

    def test_score_with_profile(self):
        from profile.storage import UserProfile

        from advisor.events import score_event

        profile = UserProfile(
            interests=["python", "ai"],
            languages_frameworks=["python", "pytorch"],
            location="San Francisco",
        )
        event = {
            "tags": ["event", "python"],
            "content": json.dumps(
                {
                    "topic": "python",
                    "event_date": (datetime.now() + timedelta(days=15)).isoformat(),
                    "location": "San Francisco, CA",
                }
            ),
        }
        score = score_event(event, profile)
        # Should be higher due to interest + location match
        assert score > 7.0

    def test_score_past_event(self):
        from advisor.events import score_event

        event = {
            "tags": "event",
            "content": json.dumps({"event_date": (datetime.now() - timedelta(days=5)).isoformat()}),
        }
        score = score_event(event)
        assert score < 5.0  # penalized

    def test_score_urgent_cfp(self):
        from advisor.events import score_event

        event = {
            "tags": "event,cfp-open",
            "content": json.dumps(
                {
                    "cfp_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
                    "event_date": (datetime.now() + timedelta(days=60)).isoformat(),
                }
            ),
        }
        score = score_event(event)
        assert score >= 7.0  # urgent CFP boost

    def test_score_accepts_timezone_aware_deadlines(self):
        from advisor.events import score_event

        event = {
            "tags": "event,cfp-open",
            "content": json.dumps(
                {
                    "cfp_deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                    "event_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                }
            ),
        }
        score = score_event(event)
        assert score >= 7.0

    def test_score_accepts_z_suffix_event_dates(self):
        from advisor.events import score_event

        z_timestamp = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat().replace(
            "+00:00", "Z"
        )
        event = {
            "tags": "event",
            "content": json.dumps({"event_date": z_timestamp}),
        }
        score = score_event(event)
        assert 0 <= score <= 10

    def test_get_upcoming_events(self, tmp_path):
        from advisor.events import get_upcoming_events
        from intelligence.scraper import IntelItem, IntelStorage

        storage = IntelStorage(tmp_path / "intel.db")
        # Save event items
        for i in range(3):
            storage.save(
                IntelItem(
                    source="events",
                    title=f"Event {i}",
                    url=f"https://event{i}.example.com",
                    summary="Test event",
                    content=json.dumps(
                        {"event_date": (datetime.now() + timedelta(days=10 + i)).isoformat()}
                    ),
                    tags=["event"],
                )
            )

        events = get_upcoming_events(storage, days=30, limit=10)
        assert len(events) == 3
        assert all("_score" in e for e in events)


class TestEventScraper:
    def test_source_name(self, tmp_path):
        from intelligence.scraper import IntelStorage
        from intelligence.sources.events import EventScraper

        storage = IntelStorage(tmp_path / "intel.db")
        scraper = EventScraper(storage)
        assert scraper.source_name == "events"

    def test_parse_confs_tech_event(self, tmp_path):
        from intelligence.scraper import IntelStorage
        from intelligence.sources.events import EventScraper

        storage = IntelStorage(tmp_path / "intel.db")
        scraper = EventScraper(storage)
        event = {
            "name": "PyCon US",
            "url": "https://pycon.org",
            "city": "Pittsburgh",
            "country": "USA",
            "startDate": "2026-04-15",
            "endDate": "2026-04-20",
            "cfpUrl": "https://pycon.org/cfp",
            "cfpEndDate": "2026-01-15",
            "online": False,
        }
        item = scraper._parse_confs_tech_event(event, "python")
        assert item is not None
        assert item.title == "PyCon US"
        assert "python" in item.tags
        assert "event" in item.tags

    def test_location_filter(self, tmp_path):
        from intelligence.scraper import IntelStorage
        from intelligence.sources.events import EventScraper

        storage = IntelStorage(tmp_path / "intel.db")
        scraper = EventScraper(storage, location_filter="USA")
        event_usa = {
            "name": "PyCon",
            "url": "https://pycon.org",
            "city": "Pittsburgh",
            "country": "USA",
            "startDate": "2026-04-15",
        }
        event_uk = {
            "name": "PyConUK",
            "url": "https://pyconuk.org",
            "city": "London",
            "country": "UK",
            "startDate": "2026-04-15",
        }
        assert scraper._parse_confs_tech_event(event_usa, "python") is not None
        assert scraper._parse_confs_tech_event(event_uk, "python") is None


class TestSkillGapViaAsk:
    def test_skill_gap_advice_type(self):
        """skill_gap advice type uses profile + journal context."""
        mock_rag = MagicMock()
        mock_rag.get_profile_context.return_value = "Role: Backend Dev"
        mock_rag.get_journal_context.return_value = "Want to learn ML"
        mock_rag.cache = None

        mock_client = MagicMock()
        resp = MagicMock()
        resp.content = [MagicMock(text="## Skill Gap Analysis\n- Python: 4/5")]
        mock_client.messages.create.return_value = resp

        from advisor.engine import AdvisorEngine

        engine = AdvisorEngine(rag=mock_rag, provider="claude", client=mock_client)
        result = engine.ask("What are my skill gaps?", advice_type="skill_gap")
        assert "Skill Gap" in result


# === Phase 4: Projects ===


class TestGitHubIssuesScraper:
    def test_source_name(self, tmp_path):
        from intelligence.scraper import IntelStorage
        from intelligence.sources.github_issues import GitHubIssuesScraper

        storage = IntelStorage(tmp_path / "intel.db")
        scraper = GitHubIssuesScraper(storage, languages=["python"])
        assert scraper.source_name == "github_issues"


class TestProjectMatching:
    def test_get_matching_issues_no_profile(self, tmp_path):
        from advisor.projects import get_matching_issues
        from intelligence.scraper import IntelItem, IntelStorage

        storage = IntelStorage(tmp_path / "intel.db")
        storage.save(
            IntelItem(
                source="github_issues",
                title="Fix typing issue",
                url="https://github.com/test/repo/issues/1",
                summary="Repo: test/repo | Labels: good-first-issue | Language: python",
                tags=["github-issue", "good-first-issue", "python"],
            )
        )

        issues = get_matching_issues(storage, days=7)
        assert len(issues) == 1

    def test_get_matching_issues_with_profile(self, tmp_path):
        from profile.storage import Skill, UserProfile

        from advisor.projects import get_matching_issues
        from intelligence.scraper import IntelItem, IntelStorage

        storage = IntelStorage(tmp_path / "intel.db")
        storage.save(
            IntelItem(
                source="github_issues",
                title="Add Python type hints",
                url="https://github.com/test/repo/issues/1",
                summary="Repo: test/repo | Language: python",
                tags=["github-issue", "python"],
            )
        )
        storage.save(
            IntelItem(
                source="github_issues",
                title="Fix Ruby gem",
                url="https://github.com/test/repo2/issues/1",
                summary="Repo: test/repo2 | Language: ruby",
                tags=["github-issue", "ruby"],
            )
        )

        profile = UserProfile(
            skills=[Skill(name="Python", proficiency=4)],
            languages_frameworks=["python"],
        )
        issues = get_matching_issues(storage, profile=profile, days=7)
        # Python issue should be ranked higher
        assert issues[0]["title"] == "Add Python type hints"


# === Phase 5: Nudges ===


class TestNudges:
    def test_no_profile_nudge(self, tmp_path):
        from profile.storage import ProfileStorage

        from advisor.nudges import NudgeEngine

        ps = ProfileStorage(tmp_path / "noprofile.yaml")
        engine = NudgeEngine(profile_storage=ps)
        nudges = engine.get_nudges()
        assert any("profile" in n.lower() for n in nudges)

    def test_stale_profile_nudge(self, tmp_path):
        from profile.storage import ProfileStorage, UserProfile

        from advisor.nudges import NudgeEngine

        ps = ProfileStorage(tmp_path / "profile.yaml")
        p = UserProfile()
        p.updated_at = (datetime.now() - timedelta(days=100)).isoformat()
        # Write with plain types to avoid YAML tag issues
        data = p.model_dump()
        data["career_stage"] = str(data["career_stage"])
        ps.path.parent.mkdir(parents=True, exist_ok=True)
        with open(ps.path, "w") as f:
            yaml.dump(data, f)

        engine = NudgeEngine(profile_storage=ps)
        nudges = engine.get_nudges()
        assert any(">90" in n or "profile" in n.lower() for n in nudges)

    def test_journal_streak(self, tmp_path):
        from advisor.nudges import NudgeEngine

        mock_storage = MagicMock()
        mock_storage.list_entries.return_value = []
        engine = NudgeEngine(journal_storage=mock_storage)
        nudges = engine.get_nudges()
        assert any("journal" in n.lower() for n in nudges)

    def test_max_nudges_limit(self, tmp_path):
        from profile.storage import ProfileStorage

        from advisor.nudges import NudgeEngine

        ps = ProfileStorage(tmp_path / "noprofile.yaml")
        mock_storage = MagicMock()
        mock_storage.list_entries.return_value = []
        engine = NudgeEngine(journal_storage=mock_storage, profile_storage=ps)
        nudges = engine.get_nudges(max_nudges=1)
        assert len(nudges) <= 1


# === RAG Profile Context ===


class TestRAGProfileContext:
    def test_get_profile_context(self, tmp_path):
        from profile.storage import ProfileStorage, Skill, UserProfile

        from advisor.rag import RAGRetriever

        profile_path = tmp_path / "profile.yaml"
        ps = ProfileStorage(profile_path)
        ps.save(
            UserProfile(
                current_role="ML Engineer",
                skills=[Skill(name="Python", proficiency=5)],
            )
        )

        mock_search = MagicMock()
        rag = RAGRetriever(mock_search, profile_path=str(profile_path))
        ctx = rag.get_profile_context()
        assert "ML Engineer" in ctx
        assert "Python" in ctx

    def test_get_profile_context_missing(self, tmp_path):
        mock_search = MagicMock()
        from advisor.rag import RAGRetriever

        rag = RAGRetriever(mock_search, profile_path=str(tmp_path / "nope.yaml"))
        ctx = rag.get_profile_context()
        assert ctx == ""


# === Shared Types ===


class TestSharedTypes:
    def test_new_intel_sources(self):
        from shared_types import IntelSource

        assert IntelSource.EVENTS == "events"
        assert IntelSource.CONFS_TECH == "confs_tech"
        assert IntelSource.GITHUB_ISSUES == "github_issues"

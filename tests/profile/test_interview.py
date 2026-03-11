"""Tests for profile interview — extraction, building, interactive flow."""

from profile.interview import ProfileInterviewer, _build_profile, _extract_profile_json
from profile.storage import ProfileStorage, UserProfile

# ── _extract_profile_json ──


class TestExtractProfileJson:
    def test_json_block_extracted(self):
        text = 'Some text\n```json\n{"done": true, "profile": {"current_role": "Dev"}}\n```\nMore.'
        result = _extract_profile_json(text)
        assert result == {"current_role": "Dev"}

    def test_bare_json_extracted(self):
        text = 'Alright, here it is: {"done": true, "profile": {"current_role": "PM"}} end'
        result = _extract_profile_json(text)
        assert result == {"current_role": "PM"}

    def test_invalid_json_returns_none(self):
        text = "```json\n{broken json\n```"
        assert _extract_profile_json(text) is None

    def test_missing_profile_key_returns_none(self):
        text = '```json\n{"done": true, "data": {}}\n```'
        assert _extract_profile_json(text) is None

    def test_no_json_returns_none(self):
        text = "Just a regular conversation about career goals."
        assert _extract_profile_json(text) is None

    def test_done_false_returns_none(self):
        text = '```json\n{"done": false, "profile": {"current_role": "Dev"}}\n```'
        assert _extract_profile_json(text) is None


# ── _build_profile ──


class TestBuildProfile:
    def test_valid_data(self):
        data = {
            "current_role": "Senior Dev",
            "career_stage": "senior",
            "skills": [{"name": "Python", "proficiency": 5}],
            "learning_style": "hands-on",
            "weekly_hours_available": 10,
            "interests": ["ML", "infra"],
            "languages_frameworks": ["FastAPI"],
        }
        p = _build_profile(data)
        assert p.current_role == "Senior Dev"
        assert p.career_stage == "senior"
        assert p.skills[0].proficiency == 5
        assert p.learning_style == "hands-on"
        assert p.weekly_hours_available == 10

    def test_invalid_career_stage_defaults_mid(self):
        p = _build_profile({"career_stage": "guru"})
        assert p.career_stage == "mid"

    def test_invalid_learning_style_defaults_mixed(self):
        p = _build_profile({"learning_style": "auditory"})
        assert p.learning_style == "mixed"

    def test_hours_clamped_low(self):
        p = _build_profile({"weekly_hours_available": -5})
        assert p.weekly_hours_available == 1

    def test_hours_clamped_high(self):
        p = _build_profile({"weekly_hours_available": 100})
        assert p.weekly_hours_available == 40

    def test_hours_non_numeric_defaults(self):
        p = _build_profile({"weekly_hours_available": "lots"})
        assert p.weekly_hours_available == 5

    def test_skills_missing_name_skipped(self):
        p = _build_profile({"skills": [{"proficiency": 3}, {"name": "Go", "proficiency": 4}]})
        assert len(p.skills) == 1
        assert p.skills[0].name == "Go"

    def test_proficiency_clamped(self):
        p = _build_profile({"skills": [{"name": "X", "proficiency": 10}]})
        assert p.skills[0].proficiency == 5

    def test_proficiency_clamped_low(self):
        p = _build_profile({"skills": [{"name": "X", "proficiency": -1}]})
        assert p.skills[0].proficiency == 1

    def test_invalid_proficiency_defaults_midpoint(self):
        p = _build_profile({"skills": [{"name": "X", "proficiency": "high"}]})
        assert p.skills[0].proficiency == 3

    def test_comma_separated_list_fields_normalized(self):
        p = _build_profile({"industries_watching": "fintech, healthtech, edtech"})
        assert p.industries_watching == ["fintech", "healthtech", "edtech"]

    def test_interests_string_normalized(self):
        p = _build_profile({"interests": "ML, infra"})
        assert p.interests == ["ML", "infra"]

    def test_languages_frameworks_string_normalized(self):
        p = _build_profile({"languages_frameworks": "Python, FastAPI"})
        assert p.languages_frameworks == ["Python", "FastAPI"]

    def test_non_dict_constraints_empty(self):
        p = _build_profile({"constraints": "none"})
        assert p.constraints == {}


# ── ProfileInterviewer ──


class TestProfileInterviewer:
    def _make_storage(self, tmp_path):
        return ProfileStorage(tmp_path / "profile.yaml")

    def test_normal_flow_json_on_turn_3(self, tmp_path):
        """LLM returns profile JSON on third user turn."""
        storage = self._make_storage(tmp_path)
        responses = [
            "What's your current role?",  # opening
            "What skills do you use daily?",  # turn 1
            "What are your career goals?",  # turn 2
            '```json\n{"done": true, "profile": {"current_role": "Dev", "career_stage": "mid", "skills": [{"name": "Python", "proficiency": 4}]}}\n```',  # turn 3
        ]
        call_count = 0

        def fake_llm(*args, **kwargs):
            nonlocal call_count
            resp = responses[call_count]
            call_count += 1
            return resp

        inputs = iter(["I'm a dev", "Python mostly", "Want to lead"])
        interviewer = ProfileInterviewer(fake_llm, storage)
        profile = interviewer.run_interactive(
            input_fn=lambda _: next(inputs),
            output_fn=lambda _: None,
        )
        assert profile.current_role == "Dev"
        assert storage.exists()

    def test_force_extraction_fallback(self, tmp_path):
        """10 turns without JSON → force prompt succeeds."""
        storage = self._make_storage(tmp_path)
        call_count = 0

        def fake_llm(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # First 11 calls (opening + 10 turns) = no JSON
            if call_count <= 11:
                return "Tell me more about your work."
            # 12th call = force extraction
            return '```json\n{"done": true, "profile": {"current_role": "Forced"}}\n```'

        inputs = iter(["answer"] * 10)
        interviewer = ProfileInterviewer(fake_llm, storage)
        profile = interviewer.run_interactive(
            input_fn=lambda _: next(inputs),
            output_fn=lambda _: None,
        )
        assert profile.current_role == "Forced"

    def test_absolute_fallback_empty_profile(self, tmp_path):
        """Extraction always fails → empty profile saved."""
        storage = self._make_storage(tmp_path)

        def fake_llm(*args, **kwargs):
            return "I don't know how to produce JSON."

        inputs = iter(["answer"] * 10)
        interviewer = ProfileInterviewer(fake_llm, storage)
        profile = interviewer.run_interactive(
            input_fn=lambda _: next(inputs),
            output_fn=lambda _: None,
        )
        assert isinstance(profile, UserProfile)
        assert profile.current_role == ""
        assert storage.exists()

    def test_needs_refresh_no_profile(self, tmp_path):
        storage = self._make_storage(tmp_path)
        interviewer = ProfileInterviewer(lambda *a, **k: "", storage)
        assert interviewer.needs_refresh()

    def test_needs_refresh_stale_profile(self, tmp_path):
        from datetime import datetime, timedelta

        import yaml

        storage = self._make_storage(tmp_path)
        p = UserProfile()
        storage.save(p)
        # Re-set updated_at to old date (save overwrites it)
        data = yaml.safe_load(storage.path.read_text())
        data["updated_at"] = (datetime.now() - timedelta(days=91)).isoformat()
        storage.path.write_text(yaml.dump(data))

        interviewer = ProfileInterviewer(lambda *a, **k: "", storage)
        assert interviewer.needs_refresh()

    def test_needs_refresh_fresh_profile(self, tmp_path):
        storage = self._make_storage(tmp_path)
        storage.save(UserProfile())  # updated_at = now
        interviewer = ProfileInterviewer(lambda *a, **k: "", storage)
        assert not interviewer.needs_refresh()

"""Tests for shared profile service helpers."""

from profile.storage import ProfileStorage, UserProfile

from services.profile import (
    get_profile_payload,
    normalize_profile_value,
    update_profile_fields,
)


def test_normalize_profile_value_handles_career_stage_skills_and_lists():
    career_stage = normalize_profile_value("career_stage", "senior")
    skills = normalize_profile_value("skills", [{"name": "Python", "proficiency": 5}])
    interests = normalize_profile_value("interests", "AI, Systems,  ")

    assert str(career_stage) == "senior"
    assert skills[0].name == "Python"
    assert skills[0].proficiency == 5
    assert interests == ["AI", "Systems"]


def test_get_profile_payload_serializes_profile(tmp_path):
    storage = ProfileStorage(tmp_path / "profile.yaml")
    storage.save(UserProfile(career_stage="senior", location="London"))

    payload = get_profile_payload(storage)

    assert payload["exists"] is True
    assert payload["profile"]["career_stage"] == "senior"
    assert payload["profile"]["location"] == "London"
    assert "summary" in payload["profile"]
    assert "is_stale" in payload["profile"]


def test_update_profile_fields_saves_and_returns_updated_fields(tmp_path):
    storage = ProfileStorage(tmp_path / "profile.yaml")
    captured = []

    profile, updated_fields = update_profile_fields(
        storage,
        {
            "career_stage": "senior",
            "skills": [{"name": "Python", "proficiency": 5}],
            "interests": "AI, APIs",
        },
        embed_callback=lambda profile: captured.append(profile.summary()),
    )

    assert updated_fields == ["career_stage", "skills", "interests"]
    assert str(profile.career_stage) == "senior"
    assert profile.skills[0].name == "Python"
    assert profile.interests == ["AI", "APIs"]
    assert captured


def test_update_profile_fields_rejects_empty_or_unknown_updates(tmp_path):
    storage = ProfileStorage(tmp_path / "profile.yaml")

    try:
        update_profile_fields(storage, {})
    except ValueError as exc:
        assert str(exc) == "No fields to update"
    else:
        raise AssertionError("Expected ValueError for empty updates")

    try:
        update_profile_fields(storage, {"unknown_field": "x"})
    except ValueError as exc:
        assert str(exc) == "Unknown field: unknown_field"
    else:
        raise AssertionError("Expected ValueError for unknown field")

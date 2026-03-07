"""Shared project discovery and idea-context helpers for delivery surfaces."""

from typing import Any

DEFAULT_PROJECTS_QUERY = "frustration problem idea project build wish"
DEFAULT_PROJECTS_QUERY_GENERATE = "frustration problem idea project build wish annoying"
DEFAULT_SUMMARY_LIMIT = 300


def _normalize_tags(tags: Any) -> list[str]:
    """Normalize issue tags into a list of strings."""
    if isinstance(tags, str):
        return [tag.strip() for tag in tags.split(",") if tag.strip()]
    if isinstance(tags, list):
        return [str(tag).strip() for tag in tags if str(tag).strip()]
    return []


def serialize_project_issue(
    issue: dict[str, Any],
    *,
    summary_limit: int | None = None,
    include_scraped_at: bool = False,
) -> dict[str, Any]:
    """Serialize a GitHub issue match into surface-friendly primitives."""
    summary = issue.get("summary", "") or ""
    if summary_limit is not None:
        summary = summary[:summary_limit]

    payload = {
        "title": issue.get("title", ""),
        "url": issue.get("url", ""),
        "summary": summary,
        "tags": _normalize_tags(issue.get("tags", [])),
        "source": issue.get("source", ""),
        "match_score": issue.get("_match_score", issue.get("match_score", 0)),
    }
    if include_scraped_at:
        payload["scraped_at"] = issue.get("scraped_at", "")
    return payload


def load_profile_summary(profile_storage) -> str:
    """Load a profile summary, returning an empty string on failure."""
    if profile_storage is None:
        return ""

    try:
        profile = profile_storage.load()
    except Exception:
        return ""

    if not profile:
        return ""
    return profile.summary()


def discover_matching_project_issues(
    intel_storage,
    *,
    profile=None,
    limit: int = 20,
    days: int = 14,
    summary_limit: int | None = None,
    include_scraped_at: bool = False,
) -> dict[str, Any]:
    """Find and serialize matching GitHub issues for a user's profile."""
    from advisor.projects import get_matching_issues

    issues = get_matching_issues(intel_storage, profile=profile, limit=limit, days=days)
    serialized = [
        serialize_project_issue(issue, summary_limit=summary_limit, include_scraped_at=include_scraped_at)
        for issue in issues
    ]
    return {"issues": serialized, "count": len(serialized)}


def list_project_issues(
    intel_storage,
    *,
    days: int = 14,
    limit: int = 50,
    summary_limit: int = DEFAULT_SUMMARY_LIMIT,
    include_scraped_at: bool = False,
) -> dict[str, Any]:
    """List tracked GitHub issues from intel storage."""
    items = intel_storage.get_recent(days=days, limit=limit)
    issues = [item for item in items if item.get("source") == "github_issues"]
    serialized = [
        serialize_project_issue(issue, summary_limit=summary_limit, include_scraped_at=include_scraped_at)
        for issue in issues
    ]
    return {"issues": serialized, "count": len(serialized)}


def build_project_ideas_context(
    *,
    profile_storage=None,
    journal_search=None,
    query: str = DEFAULT_PROJECTS_QUERY,
    max_entries: int = 10,
    max_chars: int = 5000,
) -> dict[str, Any]:
    """Build shared context payload for side-project idea generation."""
    journal_context = ""
    if journal_search is not None:
        journal_context = journal_search.get_context_for_query(
            query,
            max_entries=max_entries,
            max_chars=max_chars,
        )

    return {
        "profile": load_profile_summary(profile_storage),
        "journal_context": journal_context,
        "instruction": "Generate side-project ideas based on the user's pain points, interests, and skills from journal entries.",
    }


def generate_project_ideas(rag, llm_caller) -> str:
    """Generate side-project ideas using the shared advisor project generator."""
    from advisor.projects import ProjectIdeaGenerator

    generator = ProjectIdeaGenerator(rag, llm_caller)
    return generator.generate_ideas()

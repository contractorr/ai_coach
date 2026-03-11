"""Event recommendation logic — score and rank events by profile match."""

import json
from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()


def parse_event_metadata(content: str) -> dict:
    """Parse event metadata from content JSON."""
    try:
        return json.loads(content) if content else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _parse_event_datetime(raw_value: str) -> datetime:
    dt = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def score_event(event: dict, profile=None) -> float:
    """Score an event based on profile match and urgency.

    Returns score 0-10.
    """
    score = 5.0  # base score
    metadata = parse_event_metadata(event.get("content", ""))

    # Interest match from profile
    if profile:
        event_tags = set(
            event.get("tags", "").split(",")
            if isinstance(event.get("tags"), str)
            else event.get("tags", [])
        )
        event_topic = metadata.get("topic", "")
        profile_interests = set(i.lower() for i in profile.interests)
        profile_tech = set(t.lower() for t in profile.languages_frameworks)

        # Topic match
        if event_topic.lower() in profile_interests or event_topic.lower() in profile_tech:
            score += 2.0
        # Tag overlap
        overlap = event_tags & (profile_interests | profile_tech)
        score += min(1.5, len(overlap) * 0.5)

        # Location proximity
        if profile.location and metadata.get("location"):
            profile_loc = profile.location.lower()
            event_loc = metadata.get("location", "").lower()
            if profile_loc in event_loc or event_loc in profile_loc:
                score += 1.0
        # Online events get small bonus (accessible to everyone)
        if metadata.get("online"):
            score += 0.5

    # Deadline urgency — CFP closing soon gets boost
    cfp_deadline = metadata.get("cfp_deadline", "")
    if cfp_deadline:
        try:
            deadline = _parse_event_datetime(cfp_deadline)
            days_until = (deadline - datetime.now()).days
            if 0 < days_until <= 14:
                score += 2.0  # urgent
            elif 14 < days_until <= 30:
                score += 1.0
        except ValueError:
            pass

    # Event date proximity — prefer nearer events
    event_date = metadata.get("event_date", "")
    if event_date:
        try:
            edate = _parse_event_datetime(event_date)
            days_until = (edate - datetime.now()).days
            if days_until < 0:
                score -= 3.0  # past event
            elif days_until <= 30:
                score += 1.0
            elif days_until <= 90:
                score += 0.5
        except ValueError:
            pass

    return min(10.0, max(0.0, score))


def get_upcoming_events(
    intel_storage,
    profile=None,
    days: int = 90,
    limit: int = 20,
    min_score: float = 4.0,
) -> list[dict]:
    """Get upcoming events sorted by score and deadline.

    Args:
        intel_storage: IntelStorage instance
        profile: Optional UserProfile for personalized scoring
        days: Lookback/forward window
        limit: Max results
        min_score: Minimum score threshold
    """
    # Get event items from storage
    items = intel_storage.get_recent(days=days, limit=100)
    events = [i for i in items if i.get("source") in ("events", "confs_tech")]

    # Score and filter
    scored = []
    for event in events:
        s = score_event(event, profile)
        if s >= min_score:
            event["_score"] = s
            event["_metadata"] = parse_event_metadata(event.get("content", ""))
            scored.append(event)

    # Sort by score desc, then by event date
    scored.sort(key=lambda e: (-e["_score"], e.get("_metadata", {}).get("event_date", "z")))
    return scored[:limit]

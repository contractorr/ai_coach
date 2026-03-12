"""Data models for the distilled memory system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FactCategory(str, Enum):
    PREFERENCE = "preference"
    SKILL = "skill"
    CONSTRAINT = "constraint"
    PATTERN = "pattern"
    CONTEXT = "context"
    GOAL_CONTEXT = "goal_context"
    OBSERVATION = "observation"


class FactSource(str, Enum):
    JOURNAL = "journal"
    FEEDBACK = "feedback"
    PROFILE = "profile"
    GOAL = "goal"
    DOCUMENT = "document"
    ASSUMPTION = "assumption"
    CONSOLIDATION = "consolidation"


@dataclass
class StewardFact:
    id: str
    text: str
    category: FactCategory
    source_type: FactSource
    source_id: str
    confidence: float = 0.8
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    superseded_by: str | None = None


@dataclass
class FactUpdate:
    """Result of conflict resolution for a candidate fact."""

    action: str  # ADD | UPDATE | DELETE | NOOP
    candidate: str
    existing_id: str | None = None
    reasoning: str = ""

"""Profile storage — Pydantic model + YAML CRUD at ~/coach/profile.yaml."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
import yaml
from pydantic import BaseModel, Field, ValidationError

from shared_types import CareerStage

logger = structlog.get_logger()


class IntelPreferences(BaseModel):
    """Per-user intelligence feed preferences."""

    excluded_sources: list[str] = Field(default_factory=list)
    excluded_keywords: list[str] = Field(default_factory=list)
    min_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    preferred_sources: list[str] = Field(default_factory=list)


class Skill(BaseModel):
    name: str
    proficiency: int = Field(ge=1, le=5, description="1=beginner, 5=expert")


class UserProfile(BaseModel):
    skills: list[Skill] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    career_stage: CareerStage = CareerStage.MID
    current_role: str = ""
    aspirations: str = ""
    location: str = ""
    languages_frameworks: list[str] = Field(default_factory=list)
    learning_style: str = "mixed"  # visual/reading/hands-on/mixed
    weekly_hours_available: int = 5
    goals_short_term: str = ""  # 6-month horizon
    goals_long_term: str = ""  # 3-year horizon
    industries_watching: list[str] = Field(default_factory=list)
    technologies_watching: list[str] = Field(default_factory=list)
    constraints: dict = Field(default_factory=dict)  # time_per_week, geography, budget_sensitivity
    fears_risks: list[str] = Field(default_factory=list)
    active_projects: list[str] = Field(default_factory=list)
    github_username: Optional[str] = None
    intel_preferences: IntelPreferences = Field(default_factory=IntelPreferences)
    updated_at: Optional[str] = None

    def is_stale(self, days: int = 90) -> bool:
        if not self.updated_at:
            return True
        try:
            updated = datetime.fromisoformat(self.updated_at)
        except (TypeError, ValueError):
            logger.warning("profile.invalid_updated_at", updated_at=self.updated_at)
            return True

        now = datetime.now(updated.tzinfo) if updated.tzinfo else datetime.now()
        return (now - updated).days > days

    def summary(self) -> str:
        """One-paragraph profile summary for LLM context."""
        parts = []
        if self.current_role:
            parts.append(f"Role: {self.current_role} ({self.career_stage})")
        if self.skills:
            top = sorted(self.skills, key=lambda s: s.proficiency, reverse=True)[:5]
            parts.append("Skills: " + ", ".join(f"{s.name}({s.proficiency})" for s in top))
        if self.languages_frameworks:
            parts.append("Tech: " + ", ".join(self.languages_frameworks[:8]))
        if self.interests:
            parts.append("Interests: " + ", ".join(self.interests[:6]))
        if self.aspirations:
            parts.append(f"Aspirations: {self.aspirations[:200]}")
        if self.goals_short_term:
            parts.append(f"6-month goals: {self.goals_short_term[:200]}")
        if self.goals_long_term:
            parts.append(f"3-year goals: {self.goals_long_term[:200]}")
        if self.industries_watching:
            parts.append("Industries: " + ", ".join(self.industries_watching[:6]))
        if self.technologies_watching:
            parts.append("Watching: " + ", ".join(self.technologies_watching[:6]))
        if self.active_projects:
            parts.append("Projects: " + ", ".join(self.active_projects[:5]))
        if self.fears_risks:
            parts.append("Risks: " + ", ".join(self.fears_risks[:4]))
        if self.location:
            parts.append(f"Location: {self.location}")
        if self.constraints:
            c = self.constraints
            constraint_parts = []
            if c.get("time_per_week"):
                constraint_parts.append(f"{c['time_per_week']}h/week")
            if c.get("geography"):
                constraint_parts.append(c["geography"])
            if c.get("budget_sensitivity"):
                constraint_parts.append(f"budget: {c['budget_sensitivity']}")
            if constraint_parts:
                parts.append("Constraints: " + ", ".join(constraint_parts))
        elif self.weekly_hours_available:
            parts.append(f"Available: {self.weekly_hours_available}h/week")
        parts.append(f"Learning style: {self.learning_style}")
        return " | ".join(parts)

    def structured_summary(self) -> str:
        """Multi-section profile summary optimized for LLM recommendation context.

        Produces clearly labeled sections so the LLM can reference specific
        aspects of the user's situation when generating recommendations.
        """
        sections = []

        # Identity
        identity_parts = []
        if self.current_role:
            identity_parts.append(f"Current role: {self.current_role}")
        identity_parts.append(f"Career stage: {self.career_stage}")
        if self.location:
            identity_parts.append(f"Location: {self.location}")
        if identity_parts:
            sections.append("[IDENTITY]\n" + "\n".join(identity_parts))

        # Goals — full text, not truncated
        goals_parts = []
        if self.goals_short_term:
            goals_parts.append(f"6-month goals: {self.goals_short_term}")
        if self.goals_long_term:
            goals_parts.append(f"3-year vision: {self.goals_long_term}")
        if self.aspirations:
            goals_parts.append(f"Career aspirations: {self.aspirations}")
        if goals_parts:
            sections.append("[GOALS & ASPIRATIONS]\n" + "\n".join(goals_parts))

        # Skills — all skills with proficiency, not just top 5
        if self.skills:
            by_level = {}
            for s in sorted(self.skills, key=lambda s: s.proficiency, reverse=True):
                by_level.setdefault(s.proficiency, []).append(s.name)
            skill_lines = []
            for level in sorted(by_level.keys(), reverse=True):
                label = {
                    5: "Expert",
                    4: "Advanced",
                    3: "Intermediate",
                    2: "Beginner",
                    1: "Novice",
                }.get(level, str(level))
                skill_lines.append(f"  {label} ({level}/5): {', '.join(by_level[level])}")
            sections.append("[SKILLS]\n" + "\n".join(skill_lines))

        # Tech stack
        if self.languages_frameworks:
            sections.append("[TECH STACK]\n" + ", ".join(self.languages_frameworks))

        # Interests & watching
        watch_parts = []
        if self.interests:
            watch_parts.append(f"Professional interests: {', '.join(self.interests)}")
        if self.industries_watching:
            watch_parts.append(f"Industries watching: {', '.join(self.industries_watching)}")
        if self.technologies_watching:
            watch_parts.append(f"Technologies watching: {', '.join(self.technologies_watching)}")
        if watch_parts:
            sections.append("[INTERESTS & WATCHING]\n" + "\n".join(watch_parts))

        # Active projects
        if self.active_projects:
            sections.append(
                "[ACTIVE PROJECTS]\n" + "\n".join(f"- {p}" for p in self.active_projects)
            )

        # Constraints
        constraint_parts = []
        hrs = self.constraints.get("time_per_week", self.weekly_hours_available)
        if hrs:
            constraint_parts.append(f"Available time: {hrs} hours/week")
        if self.constraints.get("geography"):
            constraint_parts.append(f"Geography: {self.constraints['geography']}")
        if self.constraints.get("budget_sensitivity"):
            constraint_parts.append(f"Budget sensitivity: {self.constraints['budget_sensitivity']}")
        constraint_parts.append(f"Learning style: {self.learning_style}")
        sections.append("[CONSTRAINTS]\n" + "\n".join(constraint_parts))

        # Fears & concerns
        if self.fears_risks:
            sections.append("[CONCERNS & RISKS]\n" + "\n".join(f"- {f}" for f in self.fears_risks))

        return "\n\n".join(sections)


class ProfileStorage:
    """YAML-backed profile storage."""

    def __init__(self, path: str | Path = "~/coach/profile.yaml"):
        self.path = Path(path).expanduser()

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> Optional[UserProfile]:
        if not self.path.exists():
            return None
        try:
            with open(self.path) as f:
                data = yaml.safe_load(f)
        except (OSError, yaml.YAMLError) as exc:
            logger.warning("profile.load_failed", path=str(self.path), error=str(exc))
            return None
        if not data:
            return None
        if not isinstance(data, dict):
            logger.warning(
                "profile.invalid_data", path=str(self.path), data_type=type(data).__name__
            )
            return None
        try:
            return UserProfile(**data)
        except (TypeError, ValidationError) as exc:
            logger.warning("profile.invalid_schema", path=str(self.path), error=str(exc))
            return None

    def save(self, profile: UserProfile) -> Path:
        profile.updated_at = datetime.now().isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Convert to plain dict with string values (avoid YAML Python-object tags)
        data = profile.model_dump()
        data["career_stage"] = str(data["career_stage"])
        data["skills"] = [
            {"name": s["name"], "proficiency": int(s["proficiency"])} for s in data["skills"]
        ]
        with open(self.path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return self.path

    def update_field(self, field: str, value) -> UserProfile:
        """Update a single field on the profile."""
        profile = self.load() or UserProfile()
        if not hasattr(profile, field):
            raise ValueError(f"Unknown profile field: {field}")
        setattr(profile, field, value)
        self.save(profile)
        return profile

    def get_or_empty(self) -> UserProfile:
        return self.load() or UserProfile()

"""Shared enums and types for stewardme."""

from enum import StrEnum


class GoalStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class RecommendationStatus(StrEnum):
    SUGGESTED = "suggested"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class ActionItemStatus(StrEnum):
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class CareerStage(StrEnum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXEC = "exec"


class IntelSource(StrEnum):
    HACKERNEWS = "hackernews"
    REDDIT = "reddit"
    RSS = "rss"
    GITHUB_TRENDING = "github_trending"
    ARXIV = "arxiv"
    EVENTS = "events"
    CONFS_TECH = "confs_tech"
    GITHUB_ISSUES = "github_issues"
    PRODUCTHUNT = "producthunt"
    YC_JOBS = "yc_jobs"
    GOOGLE_PATENTS = "google_patents"
    AI_CAPABILITIES = "ai_capabilities"
    METR_EVALS = "metr_evals"
    EPOCH_AI = "epoch_ai"
    AI_INDEX = "ai_index"
    ARC_EVALS = "arc_evals"
    FRONTIER_EVALS_GITHUB = "frontier_evals_github"
    INDEED_HIRING_LAB = "indeed_hiring_lab"
    GOOGLE_TRENDS = "google_trends"
    CRUNCHBASE = "crunchbase"
    X_LIST = "x_list"


class EntryType(StrEnum):
    DAILY = "daily"
    PROJECT = "project"
    GOAL = "goal"
    REFLECTION = "reflection"
    INSIGHT = "insight"
    NOTE = "note"
    QUICK = "quick"
    RESEARCH = "research"
    ACTION_BRIEF = "action_brief"

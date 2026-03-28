"""Pydantic models and enums for the curriculum system."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class GuideCategory(str, Enum):
    SCIENCE = "science"
    HUMANITIES = "humanities"
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    INDUSTRY = "industry"
    SOCIAL_SCIENCE = "social_science"
    PROFESSIONAL = "professional"


class DifficultyLevel(str, Enum):
    INTRODUCTORY = "introductory"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ReviewItemType(str, Enum):
    QUIZ = "quiz"
    TEACHBACK = "teachback"
    PRE_READING = "pre_reading"


class BloomLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class ChapterStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# --- Guide + Chapter data models ---


class Chapter(BaseModel):
    id: str  # guide_id/chapter_filename_stem
    guide_id: str
    title: str
    filename: str
    order: int
    summary: str = ""
    objectives: list[str] = Field(default_factory=list)
    checkpoints: list[str] = Field(default_factory=list)
    content_references: list[str] = Field(default_factory=list)
    content_format: str = "markdown"
    schema_version: int = 0
    word_count: int = 0
    reading_time_minutes: int = 0
    has_diagrams: bool = False
    has_tables: bool = False
    has_formulas: bool = False
    is_glossary: bool = False
    content_hash: str = ""


class Guide(BaseModel):
    id: str  # directory name
    title: str
    category: GuideCategory = GuideCategory.HUMANITIES
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    source_dir: str = ""  # relative path within content dir
    chapter_count: int = 0
    total_word_count: int = 0
    total_reading_time_minutes: int = 0
    has_glossary: bool = False
    prerequisites: list[str] = Field(default_factory=list)  # guide IDs
    track: str = ""


class Track(BaseModel):
    id: str
    title: str
    description: str = ""
    color: str = "#6b7280"
    guide_count: int = 0
    guides_completed: int = 0
    average_mastery: float = 0.0
    completion_pct: float = 0.0
    guide_ids: list[str] = Field(default_factory=list)


class LearningProgram(BaseModel):
    id: str
    title: str
    audience: str = ""
    description: str = ""
    color: str = "#6b7280"
    outcomes: list[str] = Field(default_factory=list)
    guide_ids: list[str] = Field(default_factory=list)
    applied_module_ids: list[str] = Field(default_factory=list)


# --- User progress models ---


class UserChapterProgress(BaseModel):
    user_id: str = ""
    chapter_id: str = ""
    guide_id: str = ""
    status: ChapterStatus = ChapterStatus.NOT_STARTED
    reading_time_seconds: int = 0
    scroll_position: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime | None = None


class UserGuideEnrollment(BaseModel):
    user_id: str = ""
    guide_id: str = ""
    enrolled_at: datetime | None = None
    completed_at: datetime | None = None
    linked_goal_id: str | None = None


# --- Review / quiz models ---


class ReviewItem(BaseModel):
    id: str = ""
    user_id: str = ""
    chapter_id: str = ""
    guide_id: str = ""
    question: str = ""
    expected_answer: str = ""
    bloom_level: BloomLevel = BloomLevel.REMEMBER
    item_type: ReviewItemType = ReviewItemType.QUIZ
    easiness_factor: float = 2.5
    interval_days: int = 1
    repetitions: int = 0
    next_review: datetime | None = None
    last_reviewed: datetime | None = None
    content_hash: str = ""
    created_at: datetime | None = None


class ReviewGradeResult(BaseModel):
    grade: int = 0  # 0-5
    feedback: str = ""
    correct_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)


class QuizQuestion(BaseModel):
    id: str = ""
    chapter_id: str = ""
    question: str = ""
    bloom_level: BloomLevel = BloomLevel.REMEMBER
    expected_answer: str = ""


# --- Stats ---


class LearningStats(BaseModel):
    guides_enrolled: int = 0
    guides_completed: int = 0
    chapters_completed: int = 0
    total_chapters: int = 0
    total_reading_time_seconds: int = 0
    reviews_completed: int = 0
    average_grade: float = 0.0
    current_streak_days: int = 0
    reviews_due: int = 0
    mastery_by_category: dict[str, float] = Field(default_factory=dict)
    mastery_by_track: dict[str, float] = Field(default_factory=dict)
    daily_activity: dict[str, int] = Field(default_factory=dict)  # date -> count


# --- API request/response models ---


class ProgressUpdate(BaseModel):
    chapter_id: str
    guide_id: str
    status: ChapterStatus | None = None
    reading_time_seconds: int | None = None
    scroll_position: float | None = None


class ReviewGradeRequest(BaseModel):
    answer: str
    self_grade: int | None = None  # 0-5 override


class QuizSubmission(BaseModel):
    answers: dict[str, str]  # question_id -> answer text


# --- Skill tree DAG models ---


class SkillTreeNode(BaseModel):
    id: str
    title: str
    track: str
    category: str
    difficulty: str
    chapter_count: int = 0
    prerequisites: list[str] = Field(default_factory=list)
    is_entry_point: bool = False
    # User progress
    status: str = "not_started"  # not_started | enrolled | in_progress | completed
    enrolled: bool = False
    progress_pct: float = 0.0
    mastery_score: float = 0.0
    chapters_completed: int = 0
    chapters_total: int = 0
    # Layout hints
    position: dict = Field(default_factory=dict)  # {x, y, depth}


class SkillTreeEdge(BaseModel):
    source: str  # prerequisite guide_id
    target: str  # dependent guide_id


class SkillTreeResponse(BaseModel):
    tracks: dict[str, dict]  # track_id -> {title, description, color}
    programs: list[LearningProgram] = Field(default_factory=list)
    nodes: list[SkillTreeNode]
    edges: list[SkillTreeEdge]

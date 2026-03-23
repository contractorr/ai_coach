"""Pydantic models and enums for the curriculum system."""

from datetime import datetime
from enum import Enum
from typing import Optional

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


# --- User progress models ---


class UserChapterProgress(BaseModel):
    user_id: str = ""
    chapter_id: str = ""
    guide_id: str = ""
    status: ChapterStatus = ChapterStatus.NOT_STARTED
    reading_time_seconds: int = 0
    scroll_position: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserGuideEnrollment(BaseModel):
    user_id: str = ""
    guide_id: str = ""
    enrolled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    linked_goal_id: Optional[str] = None


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
    next_review: Optional[datetime] = None
    last_reviewed: Optional[datetime] = None
    content_hash: str = ""
    created_at: Optional[datetime] = None


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
    daily_activity: dict[str, int] = Field(default_factory=dict)  # date -> count


# --- API request/response models ---


class ProgressUpdate(BaseModel):
    chapter_id: str
    guide_id: str
    status: Optional[ChapterStatus] = None
    reading_time_seconds: Optional[int] = None
    scroll_position: Optional[float] = None


class ReviewGradeRequest(BaseModel):
    answer: str
    self_grade: Optional[int] = None  # 0-5 override


class QuizSubmission(BaseModel):
    answers: dict[str, str]  # question_id -> answer text

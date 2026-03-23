export type GuideCategory =
  | "science"
  | "humanities"
  | "business"
  | "technology"
  | "industry"
  | "social_science"
  | "professional";

export type DifficultyLevel = "introductory" | "intermediate" | "advanced";

export type BloomLevel =
  | "remember"
  | "understand"
  | "apply"
  | "analyze"
  | "evaluate"
  | "create";

export type ChapterStatus = "not_started" | "in_progress" | "completed";

export type ReviewItemType = "quiz" | "teachback" | "pre_reading";

export interface Guide {
  id: string;
  title: string;
  category: GuideCategory;
  difficulty: DifficultyLevel;
  source_dir: string;
  chapter_count: number;
  total_word_count: number;
  total_reading_time_minutes: number;
  has_glossary: boolean;
  prerequisites: string[];
  // Progress (present when user_id provided)
  enrolled?: boolean;
  enrollment_completed_at?: string | null;
  chapters_total?: number;
  chapters_completed?: number;
  progress_pct?: number;
}

export interface Chapter {
  id: string;
  guide_id: string;
  title: string;
  filename: string;
  order: number;
  word_count: number;
  reading_time_minutes: number;
  has_diagrams: boolean;
  has_tables: boolean;
  has_formulas: boolean;
  is_glossary: boolean;
  content_hash: string;
  // Progress
  status?: ChapterStatus;
  reading_time_seconds?: number;
}

export interface GuideDetail extends Guide {
  chapters: Chapter[];
}

export interface ChapterDetail extends Chapter {
  content: string;
  progress: UserChapterProgress | null;
  prev_chapter: string | null;
  next_chapter: string | null;
}

export interface UserChapterProgress {
  user_id: string;
  chapter_id: string;
  guide_id: string;
  status: ChapterStatus;
  reading_time_seconds: number;
  scroll_position: number;
  started_at: string | null;
  completed_at: string | null;
  updated_at: string | null;
}

export interface ReviewItem {
  id: string;
  user_id: string;
  chapter_id: string;
  guide_id: string;
  question: string;
  expected_answer: string;
  bloom_level: BloomLevel;
  item_type?: ReviewItemType;
  easiness_factor: number;
  interval_days: number;
  repetitions: number;
  next_review: string | null;
  last_reviewed: string | null;
  content_hash: string;
  created_at: string | null;
}

export interface ReviewGradeResult {
  grade: number;
  feedback: string;
  correct_points: string[];
  missing_points: string[];
}

export interface QuizQuestion {
  id: string;
  chapter_id: string;
  question: string;
  bloom_level: BloomLevel;
  expected_answer: string;
}

export interface LearningStats {
  guides_enrolled: number;
  guides_completed: number;
  chapters_completed: number;
  total_chapters: number;
  total_reading_time_seconds: number;
  reviews_completed: number;
  average_grade: number;
  current_streak_days: number;
  reviews_due: number;
  mastery_by_category: Record<string, number>;
  daily_activity: Record<string, number>;
}

export interface NextRecommendation {
  guide_id: string | null;
  guide_title?: string;
  chapter: Chapter | null;
  reason: string;
}

export interface RelatedChapter {
  chapter_id: string;
  guide_id: string;
  title: string;
  guide_title: string;
  distance: number;
}

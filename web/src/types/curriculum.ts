export type GuideCategory =
  | "science"
  | "humanities"
  | "business"
  | "technology"
  | "industry"
  | "social_science"
  | "professional";

export type DifficultyLevel = "introductory" | "intermediate" | "advanced";
export type GuideOrigin = "builtin" | "user";
export type GuideKind = "core" | "standalone" | "extension";
export type GuideDepth = "survey" | "practitioner" | "deep_dive";

export type BloomLevel =
  | "remember"
  | "understand"
  | "apply"
  | "analyze"
  | "evaluate"
  | "create";

export type ChapterStatus = "not_started" | "in_progress" | "completed";

export type ReviewItemType = "quiz" | "prediction" | "teachback" | "pre_reading";

export interface CausalLens {
  drivers: string[];
  mechanism: string;
  effects: string[];
  second_order_effects: string[];
}

export interface MisconceptionCard {
  misconception: string;
  why_it_seems_true?: string;
  correction: string;
  counterexample?: string;
}

export interface GuideSynthesis {
  what_this_explains: string;
  where_it_applies: string[];
  where_it_breaks: string;
}

export interface Guide {
  id: string;
  title: string;
  summary: string;
  category: GuideCategory;
  difficulty: DifficultyLevel;
  source_dir: string;
  origin: GuideOrigin;
  kind: GuideKind;
  owner_user_id?: string;
  base_guide_id?: string | null;
  chapter_count: number;
  total_word_count: number;
  total_reading_time_minutes: number;
  has_glossary: boolean;
  prerequisites: string[];
  deletable?: boolean;
  archived_at?: string | null;
  archive_path?: string;
  track?: string;
  // Progress (present when user_id provided)
  enrolled?: boolean;
  enrollment_completed_at?: string | null;
  chapters_total?: number;
  chapters_completed?: number;
  progress_pct?: number;
  mastery_score?: number;
  canonical_guide_id?: string | null;
  learning_programs?: LearningProgram[];
  applied_assessments?: AppliedAssessment[];
  linked_extensions?: Guide[];
  guide_synthesis?: GuideSynthesis;
}

export interface Chapter {
  id: string;
  guide_id: string;
  title: string;
  filename: string;
  order: number;
  summary?: string;
  objectives?: string[];
  checkpoints?: string[];
  content_references?: string[];
  content_format?: string;
  schema_version?: number;
  word_count: number;
  reading_time_minutes: number;
  has_diagrams: boolean;
  has_tables: boolean;
  has_formulas: boolean;
  is_glossary: boolean;
  content_hash: string;
  causal_lens?: CausalLens | null;
  misconception_card?: MisconceptionCard | null;
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

export type CurriculumVisualBlockType =
  | "diagram"
  | "process-flow"
  | "framework"
  | "comparison-table"
  | "chart"
  | "timeline"
  | "map";

export interface CurriculumVisualNode {
  id: string;
  title: string;
  detail?: string;
  column?: number;
  row?: number;
  tone?: "default" | "accent" | "muted";
}

export interface CurriculumVisualEdge {
  from: string;
  to: string;
  label?: string;
}

export interface CurriculumDiagramBlock {
  type: "diagram";
  title?: string;
  note?: string;
  nodes: CurriculumVisualNode[];
  edges?: CurriculumVisualEdge[];
}

export interface CurriculumProcessStep {
  id: string;
  title: string;
  detail?: string;
  emphasis?: string;
}

export interface CurriculumProcessFlowBlock {
  type: "process-flow";
  title?: string;
  note?: string;
  steps: CurriculumProcessStep[];
}

export interface CurriculumFrameworkPillar {
  title: string;
  detail?: string;
  bullets?: string[];
}

export interface CurriculumFrameworkBlock {
  type: "framework";
  title?: string;
  note?: string;
  pillars: CurriculumFrameworkPillar[];
}

export interface CurriculumComparisonColumn {
  key: string;
  label: string;
}

export interface CurriculumComparisonTableBlock {
  type: "comparison-table";
  title?: string;
  note?: string;
  columns: CurriculumComparisonColumn[];
  rows: Array<Record<string, string | number>>;
}

export interface CurriculumChartBlock {
  type: "chart";
  title?: string;
  note?: string;
  chartType: "line" | "bar" | "scatter";
  xLabel: string;
  yLabel?: string;
  series?: string[];
  data: Array<Record<string, string | number>>;
}

export interface CurriculumTimelineEntry {
  id: string;
  period: string;
  title: string;
  detail?: string;
  emphasis?: string;
}

export interface CurriculumTimelineBlock {
  type: "timeline";
  title?: string;
  note?: string;
  entries: CurriculumTimelineEntry[];
}

export interface CurriculumMapBlock {
  type: "map";
  title?: string;
  note?: string;
  mapId: string;
  initialCountry?: string;
}

export type CurriculumVisualBlock =
  | CurriculumDiagramBlock
  | CurriculumProcessFlowBlock
  | CurriculumFrameworkBlock
  | CurriculumComparisonTableBlock
  | CurriculumChartBlock
  | CurriculumTimelineBlock
  | CurriculumMapBlock;

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

export interface ReviewSubmissionResult {
  grade: number;
  feedback?: string;
  correct_points?: string[];
  missing_points?: string[];
}

export interface AssessmentFeedbackResult extends ReviewGradeResult {
  graded_at?: string | null;
}

export interface QuizResult {
  question_id: string;
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
  mastery_by_track?: Record<string, number>;
  daily_activity: Record<string, number>;
}

export type RecommendationType = "continue" | "enrolled" | "ready" | "entry" | "fallback";

export interface RecommendationSignal {
  kind: "progress" | "readiness" | "context" | "industry" | "time" | "performance" | "assessment";
  label: string;
  detail: string;
}

export type AppliedAssessmentType =
  | "teach_back"
  | "decision_brief"
  | "scenario_analysis"
  | "case_memo";

export type AppliedAssessmentStage =
  | "chapter_completion"
  | "review"
  | "scenario_practice"
  | "capstone";

export interface AppliedAssessment {
  type: AppliedAssessmentType;
  stage: AppliedAssessmentStage;
  title: string;
  summary: string;
  deliverable: string;
  prompt: string;
  evaluation_focus: string[];
  draft_entry_path?: string | null;
  draft_entry_title?: string | null;
  draft_goal_path?: string | null;
  draft_goal_title?: string | null;
  draft_status?: "draft" | "active" | "submitted" | null;
  draft_feedback?: AssessmentFeedbackResult | null;
}

export interface NextRecommendation {
  guide_id: string | null;
  guide_title?: string;
  chapter: Chapter | null;
  reason: string;
  action?: "enroll";
  recommendation_type?: RecommendationType;
  signals?: RecommendationSignal[];
  matched_programs?: Array<LearningProgram & { match_reason?: string }>;
  applied_assessments?: AppliedAssessment[];
}

export type LearningTodayTaskType =
  | "continue_chapter"
  | "due_reviews"
  | "retry_reviews"
  | "start_guide"
  | "applied_practice";

export interface LearningTodayTask {
  id: string;
  task_type: LearningTodayTaskType;
  title: string;
  detail: string;
  cta_label: string;
  priority: number;
  estimate_minutes: number;
  guide_id?: string | null;
  guide_title?: string | null;
  chapter_id?: string | null;
  chapter_title?: string | null;
  entry_path?: string | null;
  recommendation_type?: RecommendationType;
  review_count?: number;
  retry_count?: number;
  signals?: RecommendationSignal[];
  matched_programs?: Array<LearningProgram & { match_reason?: string }>;
  assessment?: AppliedAssessment | null;
}

export interface AppliedAssessmentLaunchResult {
  guide_id: string;
  assessment_type: AppliedAssessmentType;
  entry_path: string;
  entry_title: string;
  goal_path: string | null;
  goal_title: string | null;
  created: boolean;
}

export interface AppliedAssessmentSubmissionResult extends AssessmentFeedbackResult {
  guide_id: string;
  assessment_type: AppliedAssessmentType;
  entry_path: string;
  goal_path: string | null;
  status: "active" | "submitted";
}

export type LearningProgramFocusStatus = "active" | "recommended" | "available";

export interface LearningProgramFocus extends LearningProgram {
  status: LearningProgramFocusStatus;
  total_guide_count: number;
  enrolled_guide_count: number;
  completed_guide_count: number;
  in_progress_guide_count: number;
  ready_guide_count: number;
  weak_review_count?: number;
  revision_backlog_count?: number;
  submitted_assessment_count?: number;
  average_assessment_grade?: number | null;
  progress_pct: number;
}

export interface LearningToday {
  headline: string;
  summary: string;
  recommended_action: NextRecommendation | null;
  tasks: LearningTodayTask[];
  focus_programs: LearningProgramFocus[];
  reviews_due: number;
}

export interface ReadyGuide {
  id: string;
  title: string;
  track: string;
  category: GuideCategory;
  difficulty: DifficultyLevel;
  chapter_count: number;
  prerequisites: string[];
}

export interface PlacementQuestion {
  id: string;
  chapter_id: string;
  question: string;
  bloom_level: BloomLevel;
}

export interface PlacementResult {
  results: {
    question_id: string;
    grade: number;
    feedback: string;
    correct_points: string[];
    missing_points: string[];
  }[];
  average_grade: number;
  passed: boolean;
  threshold: number;
  completion: { guide_id: string; chapters_marked: number; completed_at: string } | null;
}

export interface Track {
  id: string;
  title: string;
  description: string;
  color: string;
  guide_count: number;
  guides_completed: number;
  average_mastery: number;
  completion_pct: number;
  guide_ids: string[];
}

export interface LearningProgram {
  id: string;
  title: string;
  audience: string;
  description: string;
  color: string;
  outcomes: string[];
  guide_ids: string[];
  applied_module_ids: string[];
}

export interface RelatedChapter {
  chapter_id: string;
  guide_id: string;
  title: string;
  guide_title: string;
  distance: number;
}

// --- Skill tree DAG types ---

export type GuideStatus = "not_started" | "enrolled" | "in_progress" | "completed";

export interface SkillTreeNode {
  id: string;
  title: string;
  track: string;
  category: GuideCategory;
  difficulty: DifficultyLevel;
  chapter_count: number;
  prerequisites: string[];
  is_entry_point: boolean;
  status: GuideStatus;
  enrolled: boolean;
  progress_pct: number;
  mastery_score: number;
  chapters_completed: number;
  chapters_total: number;
  position: { x: number; y: number; depth: number };
}

export interface SkillTreeEdge {
  source: string;
  target: string;
}

export interface SkillTreeResponse {
  tracks: Record<string, Track>;
  programs: LearningProgram[];
  nodes: SkillTreeNode[];
  edges: SkillTreeEdge[];
}

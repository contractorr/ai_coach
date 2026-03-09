export interface ReasoningTrace {
  source_signal: string;
  profile_match: string;
  confidence: number;
  caveats: string;
}

export interface CriticData {
  confidence: string; // "High" | "Medium" | "Low"
  confidence_rationale: string;
  critic_challenge: string;
  missing_context: string;
  alternative?: string | null;
  intel_contradictions?: string | null;
}

export interface BriefingRecommendation {
  id: string;
  category: string;
  title: string;
  description: string;
  score: number;
  status: string;
  reasoning_trace?: ReasoningTrace | null;
  critic?: CriticData | null;
  watchlist_evidence?: string[];
  action_item?: RecommendationActionItem | null;
  user_rating?: number | null;
  feedback_comment?: string | null;
  feedback_at?: string | null;
  why_now?: Array<{ code: string; label: string; severity: string; detail?: Record<string, unknown> }>;
  harvested_outcome?: {
    state: string;
    confidence: number;
    source_summary: string;
    user_overridden: boolean;
    evidence?: Array<Record<string, unknown>>;
  } | null;
}

export interface RecommendationActionItem {
  objective: string;
  next_step: string;
  effort: "small" | "medium" | "large";
  due_window: "today" | "this_week" | "later";
  blockers: string[];
  success_criteria: string;
  status: "accepted" | "deferred" | "blocked" | "completed" | "abandoned";
  review_notes?: string | null;
  goal_path?: string | null;
  goal_title?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrackedRecommendationAction {
  recommendation_id: string;
  recommendation_title: string;
  category: string;
  score: number;
  recommendation_status: string;
  created_at: string;
  action_item: RecommendationActionItem;
}

export interface WeeklyPlanResponse {
  items: TrackedRecommendationAction[];
  capacity_points: number;
  used_points: number;
  remaining_points: number;
  generated_at: string;
}

export interface BriefingGoal {
  path: string;
  title: string;
  status: string;
  days_since_check: number;
}

export interface DailyBriefItem {
  kind: "stale_goal" | "recommendation" | "nudge" | "intel_match";
  title: string;
  description: string;
  time_minutes: number;
  action: string;
  priority: number;
}

export interface DailyBrief {
  items: DailyBriefItem[];
  budget_minutes: number;
  used_minutes: number;
  generated_at: string;
}

export interface GoalIntelMatch {
  id: number;
  goal_path: string;
  goal_title: string;
  url: string;
  title: string;
  summary: string;
  score: number;
  urgency: "high" | "medium" | "low";
  match_reasons: string[];
  created_at: string;
  llm_evaluated: boolean;
}

export interface BriefingResponse {
  recommendations: BriefingRecommendation[];
  stale_goals: BriefingGoal[];
  goals: BriefingGoal[];
  has_data: boolean;
  adaptation_count: number;
  daily_brief?: DailyBrief | null;
  goal_intel_matches: GoalIntelMatch[];
}

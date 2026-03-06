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

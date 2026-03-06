"""Pydantic request/response schemas for the web API."""

from typing import Optional

from pydantic import BaseModel, Field

# --- Settings ---


class SettingsUpdate(BaseModel):
    """Update user settings / API keys."""

    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    github_token: Optional[str] = None
    eventbrite_token: Optional[str] = None


class SettingsResponse(BaseModel):
    """Settings with bool mask for secrets (never raw keys)."""

    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key_set: bool = False
    llm_api_key_hint: Optional[str] = None
    using_shared_key: bool = False
    has_own_key: bool = False
    tavily_api_key_set: bool = False
    tavily_api_key_hint: Optional[str] = None
    github_token_set: bool = False
    github_token_hint: Optional[str] = None
    eventbrite_token_set: bool = False


# --- Journal ---


class QuickCapture(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class JournalCreate(BaseModel):
    content: str = Field(..., max_length=100_000)
    entry_type: str = "daily"
    title: Optional[str] = None
    tags: Optional[list[str]] = None


class JournalUpdate(BaseModel):
    content: Optional[str] = Field(None, max_length=100_000)
    metadata: Optional[dict] = None


class JournalEntry(BaseModel):
    path: str
    title: str
    type: str
    created: Optional[str] = None
    tags: list[str] = []
    preview: str = ""
    content: Optional[str] = None


# --- Advisor ---


class AdvisorAsk(BaseModel):
    question: str = Field(..., max_length=5000)
    advice_type: str = "general"
    conversation_id: str | None = None


class AdvisorResponse(BaseModel):
    answer: str
    advice_type: str
    conversation_id: str


class ConversationMessage(BaseModel):
    role: str
    content: str
    created_at: str


class ConversationListItem(BaseModel):
    id: str
    title: str
    updated_at: str
    message_count: int


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[ConversationMessage]


# --- Goals ---


class GoalCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: str = Field("", max_length=10_000)
    tags: Optional[list[str]] = None


class GoalCheckIn(BaseModel):
    notes: Optional[str] = Field(None, max_length=5000)


class GoalStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(active|paused|completed|abandoned)$")


class MilestoneAdd(BaseModel):
    title: str = Field(..., max_length=200)


class MilestoneComplete(BaseModel):
    milestone_index: int


# --- Intel ---


class IntelItem(BaseModel):
    source: str
    title: str
    url: str
    summary: str
    published: Optional[str] = None
    tags: list[str] = []


# --- Research ---


class ResearchRun(BaseModel):
    topic: Optional[str] = None


class ResearchTopic(BaseModel):
    topic: str
    source: str
    score: float
    reason: str


# --- Onboarding ---


class ProfileStatus(BaseModel):
    has_profile: bool = False
    is_stale: bool = False
    has_api_key: bool = False
    has_own_key: bool = False
    using_shared_key: bool = False


class OnboardingChat(BaseModel):
    message: str = Field(..., max_length=5000)


class OnboardingResponse(BaseModel):
    message: str
    done: bool = False
    goals_created: int = 0
    turn: int = 0
    estimated_total: int = 8


class FeedCategoryItem(BaseModel):
    id: str
    label: str
    icon: str
    feed_count: int
    preselected: bool = False


class OnboardingFeedsRequest(BaseModel):
    selected_category_ids: list[str]


class OnboardingFeedsResponse(BaseModel):
    feeds_added: int
    categories: list[str]


# --- Greeting ---


class GreetingResponse(BaseModel):
    text: str
    cached: bool = False
    stale: bool = False


# --- Briefing ---


class InsightResponse(BaseModel):
    id: int = 0
    type: str = ""
    severity: int = 0
    title: str = ""
    detail: str = ""
    suggested_actions: list[str] = []
    evidence: list[str] = []
    source_url: str = ""
    created_at: str = ""
    expires_at: Optional[str] = None
    insight_hash: str = ""


class ReasoningTrace(BaseModel):
    source_signal: str = ""
    profile_match: str = ""
    confidence: float = 0.5
    caveats: str = ""


class CriticData(BaseModel):
    """Adversarial critic output for a recommendation."""

    confidence: str = "Medium"  # High / Medium / Low
    confidence_rationale: str = ""
    critic_challenge: str = ""
    missing_context: str = ""
    alternative: Optional[str] = None
    intel_contradictions: Optional[str] = None


class BriefingRecommendation(BaseModel):
    id: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    score: float = 0.0
    status: str = ""
    reasoning_trace: Optional[ReasoningTrace] = None
    critic: Optional[CriticData] = None


class BriefingGoal(BaseModel):
    path: str = ""
    title: str = ""
    status: str = ""
    days_since_check: int = 0


class DailyBriefItem(BaseModel):
    kind: str = ""
    title: str = ""
    description: str = ""
    time_minutes: int = 0
    action: str = ""
    priority: int = 0


class DailyBrief(BaseModel):
    items: list[DailyBriefItem] = []
    budget_minutes: int = 0
    used_minutes: int = 0
    generated_at: str = ""


class SuggestionItem(BaseModel):
    """Unified suggestion — either from daily brief or recommendations."""

    source: str = ""  # "brief" | "recommendation"
    kind: str = ""  # "stale_goal" | "recommendation" | "nudge" | "intel_match"
    title: str = ""
    description: str = ""
    action: str = ""
    priority: int = 0
    score: float = 0.0


class GoalIntelMatch(BaseModel):
    id: int = 0
    goal_path: str = ""
    goal_title: str = ""
    url: str = ""
    title: str = ""
    summary: str = ""
    score: float = 0.0
    urgency: str = ""
    match_reasons: list[str] = []
    created_at: str = ""
    llm_evaluated: bool = False


class BriefingResponse(BaseModel):
    recommendations: list[BriefingRecommendation] = []
    stale_goals: list[BriefingGoal] = []
    goals: list[BriefingGoal] = []
    has_data: bool = False
    adaptation_count: int = 0
    daily_brief: Optional[DailyBrief] = None
    goal_intel_matches: list[GoalIntelMatch] = []


# --- Trends ---


class TopicTrend(BaseModel):
    topic: str
    direction: str  # emerging/declining/stable
    growth_rate: float
    counts: list[int]
    windows: list[str]
    total_entries: int
    representative_titles: list[str]


# --- Projects ---


class MatchingIssue(BaseModel):
    title: str
    url: str
    summary: str
    tags: list[str]
    source: str
    match_score: int = 0


# --- Memory ---


class MemoryFact(BaseModel):
    id: str = ""
    text: str = ""
    category: str = ""
    source_type: str = ""
    source_id: str = ""
    confidence: float = 0.0
    created_at: str = ""
    updated_at: str = ""


class MemoryStats(BaseModel):
    total_active: int = 0
    total_superseded: int = 0
    by_category: dict = {}


# --- Threads ---


class ThreadSummary(BaseModel):
    id: str = ""
    label: str = ""
    entry_count: int = 0
    first_date: str = ""
    last_date: str = ""
    status: str = "active"


class ThreadEntryItem(BaseModel):
    entry_id: str = ""
    entry_date: str = ""
    similarity: float = 0.0


class ThreadDetail(BaseModel):
    id: str = ""
    label: str = ""
    entry_count: int = 0
    entries: list[ThreadEntryItem] = []


# --- Engagement ---


class EngagementEvent(BaseModel):
    event_type: str = Field(
        ...,
        pattern=r"^(opened|saved|dismissed|acted_on|feedback_useful|feedback_irrelevant)$",
    )
    target_type: str = Field(..., max_length=50)
    target_id: str = Field(..., max_length=200)
    metadata: Optional[dict] = None


class EngagementStats(BaseModel):
    by_target: dict = {}
    by_event: dict = {}
    total: int = 0


# --- User ---


class UserMe(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class UserMeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)


# --- Profile ---


class ProfileResponse(BaseModel):
    current_role: str = ""
    career_stage: str = ""
    skills: list[dict] = []
    interests: list[str] = []
    aspirations: str = ""
    location: str = ""
    languages_frameworks: list[str] = []
    learning_style: str = "mixed"
    weekly_hours_available: int = 5
    goals_short_term: str = ""
    goals_long_term: str = ""
    industries_watching: list[str] = []
    technologies_watching: list[str] = []
    constraints: dict = {}
    fears_risks: list[str] = []
    active_projects: list[str] = []
    updated_at: Optional[str] = None
    summary: str = ""
    is_stale: bool = False


class ProfileUpdate(BaseModel):
    current_role: Optional[str] = None
    career_stage: Optional[str] = None
    skills: Optional[list[dict]] = None
    interests: Optional[list[str]] = None
    aspirations: Optional[str] = None
    location: Optional[str] = None
    languages_frameworks: Optional[list[str]] = None
    learning_style: Optional[str] = None
    weekly_hours_available: Optional[int] = None
    goals_short_term: Optional[str] = None
    goals_long_term: Optional[str] = None
    industries_watching: Optional[list[str]] = None
    technologies_watching: Optional[list[str]] = None
    constraints: Optional[dict] = None
    fears_risks: Optional[list[str]] = None
    active_projects: Optional[list[str]] = None

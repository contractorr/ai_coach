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
    attachment_ids: list[str] = Field(default_factory=list)


class AdvisorResponse(BaseModel):
    answer: str
    advice_type: str
    conversation_id: str


class ConversationAttachment(BaseModel):
    library_item_id: str
    file_name: str | None = None
    mime_type: str | None = None


class ConversationMessage(BaseModel):
    role: str
    content: str
    created_at: str
    attachments: list[ConversationAttachment] = Field(default_factory=list)


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
    return_brief: Optional[dict] = None


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
    watchlist_evidence: list[str] = []


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
    watchlist_evidence: list[str] = []
    action_item: Optional["RecommendationActionItem"] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_comment: Optional[str] = None
    feedback_at: Optional[str] = None
    why_now: list[dict] = []
    harvested_outcome: Optional[dict] = None


class RecommendationActionItem(BaseModel):
    objective: str = ""
    next_step: str = ""
    effort: str = Field("medium", pattern=r"^(small|medium|large)$")
    due_window: str = Field("this_week", pattern=r"^(today|this_week|later)$")
    blockers: list[str] = Field(default_factory=list)
    success_criteria: str = ""
    status: str = Field("accepted", pattern=r"^(accepted|deferred|blocked|completed|abandoned)$")
    review_notes: Optional[str] = None
    goal_path: Optional[str] = None
    goal_title: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class RecommendationActionCreate(BaseModel):
    goal_path: Optional[str] = None
    objective: Optional[str] = Field(None, max_length=200)
    next_step: Optional[str] = Field(None, max_length=500)
    effort: Optional[str] = Field(None, pattern=r"^(small|medium|large)$")
    due_window: Optional[str] = Field(None, pattern=r"^(today|this_week|later)$")
    blockers: Optional[list[str]] = None
    success_criteria: Optional[str] = Field(None, max_length=500)


class RecommendationActionUpdate(BaseModel):
    status: Optional[str] = Field(
        None, pattern=r"^(accepted|deferred|blocked|completed|abandoned)$"
    )
    effort: Optional[str] = Field(None, pattern=r"^(small|medium|large)$")
    due_window: Optional[str] = Field(None, pattern=r"^(today|this_week|later)$")
    blockers: Optional[list[str]] = None
    review_notes: Optional[str] = Field(None, max_length=5000)
    next_step: Optional[str] = Field(None, max_length=500)
    success_criteria: Optional[str] = Field(None, max_length=500)
    goal_path: Optional[str] = None


class RecommendationFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class TrackedRecommendationAction(BaseModel):
    recommendation_id: str = ""
    recommendation_title: str = ""
    category: str = ""
    score: float = 0.0
    recommendation_status: str = ""
    created_at: str = ""
    action_item: RecommendationActionItem


class WeeklyPlanResponse(BaseModel):
    items: list[TrackedRecommendationAction] = Field(default_factory=list)
    capacity_points: int = 0
    used_points: int = 0
    remaining_points: int = 0
    generated_at: str = ""


class WatchlistItem(BaseModel):
    id: str = ""
    label: str = ""
    kind: str = "theme"
    aliases: list[str] = []
    why: str = ""
    priority: str = "medium"
    tags: list[str] = []
    goal: str = ""
    time_horizon: str = "quarter"
    source_preferences: list[str] = []
    created_at: str = ""
    updated_at: str = ""


class IntelFollowUp(BaseModel):
    url: str = ""
    title: str = ""
    saved: bool = False
    note: str = ""
    watchlist_ids: list[str] = []
    created_at: str = ""
    updated_at: str = ""


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
    why_now: Optional[list[dict]] = None
    payload: Optional[dict] = None


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


class ThreadInboxSummary(ThreadSummary):
    inbox_state: str = "active"
    linked_goal_path: Optional[str] = None
    linked_dossier_id: Optional[str] = None
    last_action: str = ""
    recent_snippets: list[str] = []


class ThreadEntryItem(BaseModel):
    entry_id: str = ""
    entry_date: str = ""
    similarity: float = 0.0


class ThreadDetail(BaseModel):
    id: str = ""
    label: str = ""
    entry_count: int = 0
    entries: list[ThreadEntryItem] = []


class ThreadInboxDetail(ThreadDetail):
    first_date: str = ""
    last_date: str = ""
    status: str = "active"
    inbox_state: str = "active"
    linked_goal_path: Optional[str] = None
    linked_dossier_id: Optional[str] = None
    last_action: str = ""
    recent_snippets: list[str] = []
    available_actions: dict = {}


class ThreadInboxStateUpdate(BaseModel):
    inbox_state: str = Field(
        ..., pattern=r"^(active|dismissed|goal_created|research_started|dossier_started|dormant)$"
    )
    linked_goal_path: Optional[str] = None
    linked_dossier_id: Optional[str] = None
    last_action: str = ""


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


# --- Library ---


class LibraryReportCreate(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=10000)
    report_type: str = Field(
        "custom", pattern=r"^(crash_course|overview|memo|plan|custom|document)$"
    )
    title: Optional[str] = Field(None, max_length=200)
    collection: Optional[str] = Field(None, max_length=100)


class LibraryReportUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=100_000)
    collection: Optional[str] = Field(None, max_length=100)


class LibraryReportListItem(BaseModel):
    id: str
    title: str
    report_type: str
    status: str
    collection: Optional[str] = None
    prompt: str = ""
    source_kind: str = "generated"
    created: str = ""
    updated: str = ""
    last_generated_at: str = ""
    preview: str = ""
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    has_attachment: bool = False
    extraction_status: Optional[str] = None
    has_extracted_text: bool = False
    origin_surface: str = "library"
    visibility_state: str = "saved"
    index_status: Optional[str] = None
    extracted_chars: int = 0


class LibraryReportResponse(LibraryReportListItem):
    content: str = ""


class ChatAttachmentResponse(BaseModel):
    attachment_id: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    index_status: str = "ready"
    visibility_state: str = "hidden"
    extracted_chars: int = 0
    warning: Optional[str] = None


class ExtractionReceiptEnvelope(BaseModel):
    status: str = "pending"
    receipt: Optional[dict] = None


class DossierEscalationResponse(BaseModel):
    escalation_id: str = ""
    topic_key: str = ""
    topic_label: str = ""
    score: float = 0.0
    state: str = "active"
    evidence: dict = {}
    payload: dict = {}
    created_at: str = ""
    updated_at: str = ""
    snoozed_until: Optional[str] = None
    dismissed_at: Optional[str] = None
    accepted_dossier_id: Optional[str] = None


class DossierEscalationSnoozeRequest(BaseModel):
    until: Optional[str] = None


class RecommendationOutcomeOverrideRequest(BaseModel):
    state: str = Field(..., pattern=r"^(positive|negative|unresolved|conflicted)$")
    note: str = Field("", max_length=2000)


class RecommendationOutcomeResponse(BaseModel):
    state: str = "unresolved"
    confidence: float = 0.0
    source_summary: str = ""
    user_overridden: bool = False
    evidence: list[dict] = []


class CompanyMovementResponse(BaseModel):
    id: int = 0
    company_key: str = ""
    company_label: str = ""
    movement_type: str = ""
    title: str = ""
    summary: str = ""
    significance: float = 0.0
    source_url: str = ""
    source_family: str = ""
    observed_at: str = ""
    metadata: dict = {}


class HiringSignalResponse(BaseModel):
    id: int = 0
    entity_key: str = ""
    entity_label: str = ""
    signal_type: str = ""
    title: str = ""
    summary: str = ""
    strength: float = 0.0
    source_url: str = ""
    observed_at: str = ""
    metadata: dict = {}


class RegulatoryAlertResponse(BaseModel):
    id: int = 0
    target_key: str = ""
    title: str = ""
    summary: str = ""
    source_family: str = ""
    change_type: str = ""
    urgency: str = ""
    relevance: float = 0.0
    effective_date: Optional[str] = None
    source_url: str = ""
    observed_at: str = ""
    metadata: dict = {}


class AssumptionCreate(BaseModel):
    statement: str = Field(..., min_length=3, max_length=500)
    status: str = Field(
        "active", pattern=r"^(suggested|active|confirmed|invalidated|resolved|archived)$"
    )
    source_type: str = "manual"
    source_id: str = "manual"
    extraction_confidence: Optional[float] = None
    linked_goal_path: Optional[str] = None
    linked_dossier_id: Optional[str] = None
    linked_entities: list[str] = []


class AssumptionUpdate(BaseModel):
    status: Optional[str] = Field(
        None, pattern=r"^(suggested|active|confirmed|invalidated|resolved|archived)$"
    )
    latest_evidence_summary: Optional[str] = Field(None, max_length=500)


class AssumptionResponse(BaseModel):
    id: str = ""
    statement: str = ""
    status: str = "active"
    source_type: str = "manual"
    source_id: str = ""
    extraction_confidence: Optional[float] = None
    linked_goal_path: Optional[str] = None
    linked_dossier_id: Optional[str] = None
    linked_entities: list[str] = []
    latest_evidence_summary: str = ""
    last_evaluated_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    evidence: list[dict] = []

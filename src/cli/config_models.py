"""Pydantic configuration models for AI Coach."""

import os
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

VALID_LLM_PROVIDERS = {"auto", "claude", "openai", "gemini"}


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = "auto"
    model: Optional[str] = None  # None = use provider default
    api_key: Optional[str] = None
    extended_thinking: bool = True
    max_tokens: int = 16000
    cheap_max_tokens: int = 4000

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in VALID_LLM_PROVIDERS:
            raise ValueError(f"Invalid LLM provider: {v}. Must be one of {VALID_LLM_PROVIDERS}")
        return v


class PathsConfig(BaseModel):
    """File paths configuration."""

    journal_dir: Path = Path("~/coach/journal")
    chroma_dir: Path = Path("~/coach/chroma")
    intel_db: Path = Path("~/coach/intel.db")
    log_file: Path = Path("~/coach/coach.log")

    @model_validator(mode="after")
    def expand_paths(self):
        """Expand ~ in all paths."""
        self.journal_dir = self.journal_dir.expanduser()
        self.chroma_dir = self.chroma_dir.expanduser()
        self.intel_db = self.intel_db.expanduser()
        self.log_file = self.log_file.expanduser()
        return self


class SourcesConfig(BaseModel):
    """Intelligence sources configuration."""

    custom_blogs: list[str] = Field(default_factory=list)
    rss_feeds: list[str] = Field(default_factory=lambda: ["https://news.ycombinator.com/rss"])
    enabled: list[str] = Field(default_factory=lambda: ["hn_top", "rss_feeds"])
    github_trending: dict = Field(default_factory=dict)
    indeed_hiring_lab: dict = Field(default_factory=dict)
    google_trends: dict = Field(default_factory=dict)
    crunchbase: dict = Field(default_factory=dict)


def validate_cron(expr: str) -> str:
    """Validate cron expression format (5 fields)."""
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"Cron must have 5 fields, got {len(parts)}: {expr}")
    patterns = [
        r"^(\*|[0-9]|[1-5][0-9])(/[0-9]+)?$",  # minute
        r"^(\*|[0-9]|1[0-9]|2[0-3])(/[0-9]+)?$",  # hour
        r"^(\*|[1-9]|[12][0-9]|3[01])(/[0-9]+)?$",  # day
        r"^(\*|[1-9]|1[0-2])(/[0-9]+)?$",  # month
        r"^(\*|[0-6])(/[0-9]+)?$",  # weekday
    ]
    for i, (part, pattern) in enumerate(zip(parts, patterns)):
        if not re.match(pattern, part) and part != "*":
            # Allow common patterns like */5, 1-5, etc
            if not re.match(r"^[\d\-,\*/]+$", part):
                raise ValueError(f"Invalid cron field {i}: {part}")
    return expr


class ResearchConfig(BaseModel):
    """Deep research configuration."""

    enabled: bool = False
    max_topics: int = 3
    tavily_api_key: Optional[str] = None
    schedule: str = "0 21 * * 0"

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: str) -> str:
        return validate_cron(v)


class ScoringConfig(BaseModel):
    """Recommendation scoring configuration."""

    min_threshold: float = 6.0
    max_per_category: int = 3


class RAGConfig(BaseModel):
    """RAG retrieval configuration."""

    max_context_chars: int = 8000
    journal_weight: float = 0.7
    structured_profile: bool = False
    inject_memory: bool = False
    inject_recurring_thoughts: bool = False
    xml_delimiters: bool = False

    @field_validator("journal_weight")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"journal_weight must be 0-1, got {v}")
        return v


class SearchConfig(BaseModel):
    """Search defaults."""

    default_results: int = 5
    intel_similarity_threshold: float = 0.7


class RateLimitSourceConfig(BaseModel):
    """Per-source rate limit."""

    requests_per_second: float = 2.0
    burst: int = 5


class RateLimitsConfig(BaseModel):
    """Rate limits for external APIs."""

    default: RateLimitSourceConfig = Field(default_factory=RateLimitSourceConfig)
    tavily: RateLimitSourceConfig = Field(
        default_factory=lambda: RateLimitSourceConfig(requests_per_second=1.0, burst=1)
    )
    hackernews: RateLimitSourceConfig = Field(
        default_factory=lambda: RateLimitSourceConfig(requests_per_second=5.0, burst=10)
    )
    reddit: RateLimitSourceConfig = Field(
        default_factory=lambda: RateLimitSourceConfig(requests_per_second=1.0, burst=2)
    )


class DeliveryConfig(BaseModel):
    """Recommendation delivery configuration."""

    methods: list[str] = Field(default_factory=lambda: ["journal"])
    schedule: str = "0 8 * * 0"

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: str) -> str:
        return validate_cron(v)


class RecommendationsConfig(BaseModel):
    """Recommendations system configuration."""

    enabled: bool = False
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    delivery: DeliveryConfig = Field(default_factory=DeliveryConfig)
    similarity_threshold: float = 0.85
    dedup_window_days: int = 30


class RetryConfig(BaseModel):
    """Retry/backoff configuration."""

    max_attempts: int = 3
    min_wait: float = 2.0
    max_wait: float = 10.0
    llm_max_wait: float = 30.0


class LimitsConfig(BaseModel):
    """Resource limits configuration."""

    hn_max_stories: int = 30
    rss_max_entries: int = 20
    github_max_repos: int = 25
    journal_max_entries: int = 5
    journal_max_chars: int = 6000
    intel_max_items: int = 5
    intel_max_chars: int = 3000
    total_context_chars: int = 8000
    summary_truncate: int = 500
    preview_truncate: int = 200
    llm_max_tokens: int = 2000


VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    file_level: str = "DEBUG"

    @field_validator("level", "file_level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in VALID_LOG_LEVELS:
            raise ValueError(f"Invalid log level: {v}. Must be one of {VALID_LOG_LEVELS}")
        return v_upper


class HeartbeatWeightsConfig(BaseModel):
    """Weights for heartbeat composite scoring."""

    keyword_overlap: float = 0.35
    recency: float = 0.35
    source_affinity: float = 0.3


class HeartbeatConfig(BaseModel):
    """Heartbeat proactive intel-to-goal matching."""

    enabled: bool = False
    interval_minutes: int = 30
    heuristic_threshold: float = 0.3
    llm_budget_per_cycle: int = 5
    notification_cooldown_hours: int = 4
    lookback_hours: int = 2
    preferred_sources: list[str] = Field(default_factory=list)
    weights: HeartbeatWeightsConfig = Field(default_factory=HeartbeatWeightsConfig)


class MemoryConfig(BaseModel):
    """Distilled memory configuration."""

    enabled: bool = True
    model_override: Optional[str] = None
    max_facts_per_entry: int = 5
    similarity_threshold: float = 0.7
    auto_noop_threshold: float = 0.95
    max_context_facts: int = 25
    high_confidence_threshold: float = 0.9
    backfill_batch_size: int = 10


class ThreadsConfig(BaseModel):
    """Journal recurrence detection configuration."""

    enabled: bool = True
    similarity_threshold: float = 0.78
    min_entries_for_thread: int = 2
    candidate_count: int = 10


class TrendingRadarConfig(BaseModel):
    """Cross-source topic convergence configuration."""

    enabled: bool = True
    min_sources: int = 2
    days: int = 7
    max_topics: int = 15
    interval_hours: int = 6


class CompanyMovementConfig(BaseModel):
    """Company-movement pipeline configuration."""

    enabled: bool = False
    min_significance: float = 0.45
    run_cron: str = "0 */6 * * *"
    lookback_days: int = 14

    @field_validator("run_cron")
    @classmethod
    def validate_schedule(cls, v: str) -> str:
        return validate_cron(v)


class HiringPipelineConfig(BaseModel):
    """Hiring-activity pipeline configuration."""

    enabled: bool = False
    spike_multiplier: float = 2.0
    min_post_count: int = 5
    min_family_count: int = 3
    min_geo_count: int = 3
    run_cron: str = "0 */12 * * *"
    lookback_days: int = 14

    @field_validator("run_cron")
    @classmethod
    def validate_schedule(cls, v: str) -> str:
        return validate_cron(v)


class RegulatoryPipelineConfig(BaseModel):
    """Regulatory-change pipeline configuration."""

    enabled: bool = False
    min_relevance: float = 0.5
    run_cron: str = "0 */12 * * *"
    lookback_days: int = 30

    @field_validator("run_cron")
    @classmethod
    def validate_schedule(cls, v: str) -> str:
        return validate_cron(v)


class CoachConfig(BaseModel):
    """Main configuration model."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    recommendations: RecommendationsConfig = Field(default_factory=RecommendationsConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    rate_limits: RateLimitsConfig = Field(default_factory=RateLimitsConfig)
    heartbeat: HeartbeatConfig = Field(default_factory=HeartbeatConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    threads: ThreadsConfig = Field(default_factory=ThreadsConfig)
    trending_radar: TrendingRadarConfig = Field(default_factory=TrendingRadarConfig)
    company_movement: CompanyMovementConfig = Field(default_factory=CompanyMovementConfig)
    hiring: HiringPipelineConfig = Field(default_factory=HiringPipelineConfig)
    regulatory: RegulatoryPipelineConfig = Field(default_factory=RegulatoryPipelineConfig)

    @model_validator(mode="after")
    def expand_env_vars(self):
        """Expand ${VAR} patterns in API keys."""
        if self.llm.api_key:
            key = self.llm.api_key
            if key.startswith("${") and key.endswith("}"):
                env_var = key[2:-1]
                self.llm.api_key = os.getenv(env_var, "")
        if self.research.tavily_api_key:
            key = self.research.tavily_api_key
            if key.startswith("${") and key.endswith("}"):
                env_var = key[2:-1]
                self.research.tavily_api_key = os.getenv(env_var, "")
        cb_key = self.sources.crunchbase.get("api_key", "")
        if isinstance(cb_key, str) and cb_key.startswith("${") and cb_key.endswith("}"):
            self.sources.crunchbase["api_key"] = os.getenv(cb_key[2:-1], "")
        return self

    @classmethod
    def from_dict(cls, data: dict) -> "CoachConfig":
        """Create config from dict, migrating old format if needed."""
        # Handle old paths format (strings instead of Path objects)
        if "paths" in data:
            for key in ["journal_dir", "chroma_dir", "intel_db", "log_file"]:
                if key in data["paths"] and isinstance(data["paths"][key], str):
                    data["paths"][key] = Path(data["paths"][key])

        # Handle old limits format (flat dict at root)
        if "limits" in data and isinstance(data["limits"], dict):
            # Merge with defaults
            pass

        return cls.model_validate(data)

    def to_dict(self) -> dict:
        """Convert to dict for backwards compatibility."""
        return self.model_dump(mode="python")

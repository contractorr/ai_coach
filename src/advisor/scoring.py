"""Scoring utilities for recommendations."""

import hashlib
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import structlog

from db import wal_connect

if TYPE_CHECKING:
    from .recommendation_storage import RecommendationStorage

logger = structlog.get_logger()

# Minimum engagement events before applying boosts
MIN_EVENTS_FOR_BOOST = 10
# Max score adjustment from engagement
MAX_BOOST = 1.5
# User rating (1-5) boost thresholds
MIN_RATINGS_FOR_BOOST = 2
MAX_RATING_BOOST = 1.0
MIN_EXECUTION_EVENTS_FOR_BOOST = 2
MAX_EXECUTION_BOOST = 1.0


class RecommendationScorer:
    """Score and deduplicate recommendations."""

    def __init__(
        self,
        min_threshold: float = 6.0,
        users_db_path: Optional[Path] = None,
        user_id: Optional[str] = None,
        intel_db_path: Optional[Path] = None,
        rec_storage: Optional["RecommendationStorage"] = None,
        **_kwargs,
    ):
        self.min_threshold = min_threshold
        self._users_db_path = users_db_path
        self._user_id = user_id
        self._intel_db_path = intel_db_path
        self._rec_storage = rec_storage
        self._category_boosts: Optional[dict[str, float]] = None
        self._rating_boosts: Optional[dict[str, float]] = None
        self._execution_boosts: Optional[dict[str, float]] = None

    def passes_threshold(self, score: float) -> bool:
        """Check if score meets minimum threshold."""
        return score >= self.min_threshold

    def content_hash(self, title: str, description: str) -> str:
        """Generate hash for deduplication."""
        content = f"{title.lower().strip()}|{description.lower().strip()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def engagement_boost(self, category: str) -> float:
        """Per-category score adjustment from engagement feedback.

        Computes useful_ratio per category from last 30d of feedback events.
        Returns boost in [-MAX_BOOST, +MAX_BOOST]. Positive = users liked this
        category, negative = users found it irrelevant.
        """
        if self._category_boosts is not None:
            return self._category_boosts.get(category, 0.0)

        self._category_boosts = {}
        if not self._users_db_path or not self._user_id:
            return 0.0

        try:
            with wal_connect(self._users_db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT
                        json_extract(metadata_json, '$.category') as category,
                        event_type,
                        COUNT(*) as cnt
                    FROM engagement_events
                    WHERE user_id = ?
                      AND target_type = 'recommendation'
                      AND event_type IN ('feedback_useful', 'feedback_irrelevant')
                      AND created_at >= datetime('now', '-30 days')
                    GROUP BY category, event_type
                    """,
                    (self._user_id,),
                ).fetchall()

            # Aggregate per category
            cat_counts: dict[str, dict[str, int]] = {}
            for r in rows:
                cat = r["category"] or "unknown"
                cat_counts.setdefault(cat, {"useful": 0, "irrelevant": 0})
                if r["event_type"] == "feedback_useful":
                    cat_counts[cat]["useful"] += r["cnt"]
                else:
                    cat_counts[cat]["irrelevant"] += r["cnt"]

            for cat, counts in cat_counts.items():
                total = counts["useful"] + counts["irrelevant"]
                if total < MIN_EVENTS_FOR_BOOST:
                    continue
                # ratio 0-1, 0.5 = neutral
                ratio = counts["useful"] / total
                # map [0,1] -> [-MAX_BOOST, +MAX_BOOST]
                self._category_boosts[cat] = MAX_BOOST * (2 * ratio - 1)

            logger.debug(
                "engagement.category_boosts",
                user_id=self._user_id,
                boosts=self._category_boosts,
            )
        except Exception as e:
            logger.debug("engagement.boost_error", error=str(e))

        return self._category_boosts.get(category, 0.0)

    def rating_boost(self, category: str) -> float:
        """Per-category score adjustment from explicit user ratings (1-5).

        Reads user_rating from recommendation markdown frontmatter via storage.
        Maps avg rating [1,5] → boost in [-MAX_RATING_BOOST, +MAX_RATING_BOOST].
        Rating 3 is neutral; <3 penalizes, >3 rewards.
        """
        if self._rating_boosts is not None:
            return self._rating_boosts.get(category, 0.0)

        self._rating_boosts = {}
        if not self._rec_storage:
            return 0.0

        try:
            stats = self._rec_storage.get_feedback_stats()
            for cat, cat_stats in stats.get("by_category", {}).items():
                if cat_stats["count"] < MIN_RATINGS_FOR_BOOST:
                    continue
                avg = cat_stats["avg_rating"]
                # map [1,5] → [-1,1] then scale by MAX_RATING_BOOST
                self._rating_boosts[cat] = MAX_RATING_BOOST * (avg - 3.0) / 2.0

            logger.debug("rating.category_boosts", boosts=self._rating_boosts)
        except Exception as e:
            logger.debug("rating.boost_error", error=str(e))

        return self._rating_boosts.get(category, 0.0)

    def execution_boost(self, category: str) -> float:
        """Per-category score adjustment from tracked execution outcomes."""
        if self._execution_boosts is not None:
            return self._execution_boosts.get(category, 0.0)

        self._execution_boosts = {}
        if not self._rec_storage:
            return 0.0

        try:
            stats = self._rec_storage.get_execution_stats()
            for cat, cat_stats in stats.get("by_category", {}).items():
                if cat_stats.get("count", 0) < MIN_EXECUTION_EVENTS_FOR_BOOST:
                    continue
                avg = float(cat_stats.get("avg_outcome", 0.0))
                avg = max(-1.0, min(1.0, avg))
                self._execution_boosts[cat] = MAX_EXECUTION_BOOST * avg

            logger.debug("execution.category_boosts", boosts=self._execution_boosts)
        except Exception as e:
            logger.debug("execution.boost_error", error=str(e))

        return self._execution_boosts.get(category, 0.0)

    def adjust_score(self, score: float, category: str) -> float:
        """Apply engagement + rating boosts to a raw LLM score, clamped [0, 10]."""
        boost = (
            self.engagement_boost(category)
            + self.rating_boost(category)
            + self.execution_boost(category)
        )
        return max(0.0, min(10.0, score + boost))

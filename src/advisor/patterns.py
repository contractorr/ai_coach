"""Higher-level pattern recognition — synthesizes signals into coaching insights."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import structlog

logger = structlog.get_logger()


@dataclass
class Pattern:
    type: str  # blind_spot, blocker_cycle
    confidence: float  # 0-1
    summary: str
    evidence: list[str] = field(default_factory=list)
    coaching_prompt: str = ""


class PatternDetector:
    """Detects high-level behavioral patterns from journal + goals data."""

    def __init__(
        self, journal_storage, embeddings=None, config: Optional[dict] = None, insight_store=None
    ):
        self.storage = journal_storage
        self.embeddings = embeddings
        self.config = config or {}
        self.insight_store = insight_store

    def detect_all(self, lookback_days: int = 30) -> list[Pattern]:
        """Run all pattern detectors and return findings."""
        patterns = []
        detectors = [
            self._detect_blind_spots,
            self._detect_blocker_cycle,
        ]
        for detector in detectors:
            try:
                result = detector(lookback_days)
                if result:
                    patterns.append(result)
            except Exception as e:
                logger.warning("pattern_detector_error", detector=detector.__name__, error=str(e))
        # Persist to InsightStore if available
        if self.insight_store:
            for p in patterns:
                self._persist_as_insight(p)

        return sorted(patterns, key=lambda p: p.confidence, reverse=True)

    def _persist_as_insight(self, pattern: Pattern):
        """Convert Pattern → Insight and save to InsightStore."""
        from advisor.insights import Insight, InsightType

        type_map = {
            "blind_spot": InsightType.PATTERN_BLIND_SPOT,
            "blocker_cycle": InsightType.PATTERN_BLOCKER_CYCLE,
        }
        insight_type = type_map.get(pattern.type)
        if not insight_type:
            return
        try:
            insight = Insight(
                type=insight_type,
                severity=round(pattern.confidence * 10),
                title=pattern.summary,
                detail=pattern.coaching_prompt,
                evidence=pattern.evidence,
            )
            self.insight_store.save(insight)
        except Exception as e:
            logger.debug("pattern_to_insight_error", error=str(e))

    def _detect_blind_spots(self, lookback_days: int) -> Optional[Pattern]:
        """Active goals with zero related journal entries (low embedding similarity)."""
        if not self.embeddings:
            return None

        try:
            from advisor.goals import GoalTracker

            tracker = GoalTracker(self.storage)
            goals = tracker.get_goals(include_inactive=False)
        except Exception:
            return None

        if not goals:
            return None

        blind_spots = []
        for goal in goals:
            if goal["status"] != "active":
                continue
            goal_text = f"{goal['title']} {goal.get('content', '')}"
            try:
                results = self.embeddings.query(goal_text, n_results=3)
                if not results:
                    blind_spots.append(goal["title"])
                    continue

                # Check if any result is recent and relevant
                cutoff = (datetime.now() - timedelta(days=lookback_days)).isoformat()
                recent_relevant = [
                    r
                    for r in results
                    if r.get("metadata", {}).get("created", "") >= cutoff
                    and r.get("distance", 1.0) < 0.7  # similarity > 0.3
                ]
                if not recent_relevant:
                    blind_spots.append(goal["title"])
            except Exception:
                continue

        if not blind_spots:
            return None

        return Pattern(
            type="blind_spot",
            confidence=min(1.0, 0.4 + len(blind_spots) * 0.2),
            summary=f"{len(blind_spots)} active goal(s) with no recent journal mentions",
            evidence=[f"Unmentioned: {g}" for g in blind_spots],
            coaching_prompt=f"You haven't written about {', '.join(blind_spots[:3])} recently. "
            "Are these goals still relevant? If so, what's one step you could take this week?",
        )

    def _detect_blocker_cycle(self, lookback_days: int) -> Optional[Pattern]:
        """Same negative keywords across 3+ entries in 14 days."""
        try:
            import re

            from journal.sentiment import analyze_sentiment

            entries = self.storage.list_entries(limit=50)
        except Exception:
            return None

        cutoff = (datetime.now() - timedelta(days=min(lookback_days, 14))).isoformat()

        _BLOCKER_KEYWORDS = {
            "stuck",
            "blocked",
            "struggling",
            "frustrated",
            "confused",
            "overwhelmed",
            "procrastinating",
            "impossible",
        }

        keyword_entries: dict[str, list[str]] = {}
        for entry in entries:
            if entry.get("created", "") < cutoff:
                continue
            try:
                post = self.storage.read(entry["path"])
                sentiment = analyze_sentiment(post.content)
                if sentiment["score"] >= 0:
                    continue
                words = set(re.findall(r"\b[a-z]+\b", post.content.lower()))
                for w in words & _BLOCKER_KEYWORDS:
                    keyword_entries.setdefault(w, []).append(
                        entry.get("title", entry.get("created", "")[:10])
                    )
            except Exception:
                continue

        # Find most recurring blocker
        worst = None
        worst_count = 0
        for kw, entries_list in keyword_entries.items():
            if len(entries_list) >= 3 and len(entries_list) > worst_count:
                worst = kw
                worst_count = len(entries_list)

        if not worst:
            return None

        return Pattern(
            type="blocker_cycle",
            confidence=min(1.0, 0.4 + worst_count * 0.15),
            summary=f"Recurring blocker: '{worst}' in {worst_count} entries",
            evidence=keyword_entries[worst][:5],
            coaching_prompt=f"I notice '{worst}' keeps coming up in your journal. "
            "This might be a systemic issue worth addressing directly. "
            "What would it take to break through this? Could you try a completely different approach?",
        )

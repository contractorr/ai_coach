"""Topic selection for deep research."""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

import structlog

from journal import JournalStorage

logger = structlog.get_logger()


class TopicSelector:
    """Selects research topics from goals, journal themes, and detected trends."""

    def __init__(
        self,
        storage: JournalStorage,
        journal_search=None,
        max_topics: int = 2,
        theme_window_days: int = 30,
        min_mentions: int = 3,
        skip_researched_days: int = 60,
    ):
        self.storage = storage
        self.journal_search = journal_search
        self.max_topics = max_topics
        self.theme_window_days = theme_window_days
        self.min_mentions = min_mentions
        self.skip_researched_days = skip_researched_days

    def get_topics(self, researched_topics: Optional[list[str]] = None) -> list[dict]:
        """Get ranked list of topics to research.

        Args:
            researched_topics: Topics already researched (to skip)

        Returns:
            List of {topic, source, score, reason}
        """
        researched = set(t.lower() for t in (researched_topics or []))
        candidates = []

        # 1. Explicit research requests from goals
        goal_topics = self._extract_goal_topics()
        for topic in goal_topics:
            if topic["topic"].lower() not in researched:
                candidates.append(topic)

        # 2. Emerging trends from journal embeddings
        trend_topics = self._extract_trend_topics()
        for topic in trend_topics:
            if topic["topic"].lower() not in researched:
                if not any(c["topic"].lower() == topic["topic"].lower() for c in candidates):
                    candidates.append(topic)

        # 3. Clustered themes from journal
        theme_topics = self._cluster_journal_themes()
        for topic in theme_topics:
            if topic["topic"].lower() not in researched:
                if not any(c["topic"].lower() == topic["topic"].lower() for c in candidates):
                    candidates.append(topic)

        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)

        return candidates[: self.max_topics]

    def _extract_trend_topics(self) -> list[dict]:
        """Extract emerging topics from TrendDetector."""
        if not self.journal_search:
            return []
        try:
            from journal.trends import TrendDetector

            detector = TrendDetector(self.journal_search)
            emerging = detector.get_emerging_topics(threshold=0.2, days=60)
            topics = []
            for trend in emerging[:5]:
                topics.append(
                    {
                        "topic": trend["topic"].title(),
                        "source": "trend",
                        "score": min(9, 5 + trend["growth_rate"] * 10),
                        "reason": f"Emerging trend (growth={trend['growth_rate']:+.0%})",
                    }
                )
            return topics
        except Exception:
            return []

    def _extract_goal_topics(self) -> list[dict]:
        """Extract explicit research requests from goals."""
        topics = []
        goals = self.storage.list_entries(entry_type="goal", limit=20)

        for entry in goals:
            post = self._safe_read_entry(entry)
            if post is None:
                continue
            content = post.content.lower()

            # Look for research-related phrases
            patterns = [
                r"research\s+(?:about\s+)?([^,.!\n]+)",
                r"learn\s+(?:more\s+)?about\s+([^,.!\n]+)",
                r"understand\s+([^,.!\n]+)",
                r"explore\s+([^,.!\n]+)",
                r"deep\s+dive\s+(?:into\s+)?([^,.!\n]+)",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    topic = match.strip()
                    if len(topic) > 3 and len(topic) < 100:
                        topics.append(
                            {
                                "topic": topic.title(),
                                "source": "goal",
                                "score": 10,  # High priority for explicit requests
                                "reason": f"Explicit goal: {entry['title'][:40]}",
                            }
                        )

        return topics

    def _cluster_journal_themes(self) -> list[dict]:
        """Identify recurring themes from recent journal entries."""
        cutoff = datetime.now() - timedelta(days=self.theme_window_days)
        entries = self.storage.list_entries(limit=100)

        # Collect words from recent entries
        word_counter = Counter()
        stopwords = self._get_stopwords()

        for entry in entries:
            created = entry.get("created")
            if created:
                try:
                    entry_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if entry_date.replace(tzinfo=None) < cutoff:
                        continue
                except (ValueError, TypeError):
                    continue

            post = self._safe_read_entry(entry)
            if post is None:
                continue
            words = self._extract_keywords(post.content, stopwords)
            word_counter.update(words)

            # Also count tags
            for tag in entry.get("tags", []):
                if tag.lower() not in stopwords:
                    word_counter[tag.lower()] += 2  # Weight tags higher

        # Filter to themes with minimum mentions
        themes = []
        for word, count in word_counter.most_common(20):
            if count >= self.min_mentions:
                themes.append(
                    {
                        "topic": word.title(),
                        "source": "theme",
                        "score": min(count, 10),  # Cap at 10
                        "reason": f"Mentioned {count} times in last {self.theme_window_days} days",
                    }
                )

        return themes

    def _extract_keywords(self, text: str, stopwords: set) -> list[str]:
        """Extract meaningful keywords from text."""
        # Simple word extraction (could be enhanced with NLP)
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        return [w for w in words if w not in stopwords]

    def _get_stopwords(self) -> set:
        """Common words to filter out."""
        return {
            "that",
            "this",
            "with",
            "from",
            "have",
            "been",
            "were",
            "will",
            "would",
            "could",
            "should",
            "about",
            "which",
            "their",
            "there",
            "what",
            "when",
            "where",
            "than",
            "then",
            "they",
            "them",
            "some",
            "more",
            "also",
            "just",
            "only",
            "very",
            "much",
            "such",
            "like",
            "into",
            "over",
            "after",
            "before",
            "being",
            "through",
            "each",
            "work",
            "working",
            "worked",
            "want",
            "need",
            "think",
            "know",
            "make",
            "made",
            "take",
            "took",
            "come",
            "came",
            "going",
            "doing",
            "done",
            "time",
            "today",
            "week",
            "month",
            "year",
            "daily",
            "journal",
            "entry",
            "note",
            "notes",
            "goal",
            "goals",
            "project",
        }

    def get_recent_research_topics(self) -> list[str]:
        """Get topics researched within skip window."""
        cutoff = datetime.now() - timedelta(days=self.skip_researched_days)
        entries = self.storage.list_entries(entry_type="research", limit=50)

        topics = []
        for entry in entries:
            created = entry.get("created")
            if created:
                try:
                    entry_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if entry_date.replace(tzinfo=None) >= cutoff:
                        # Extract topic from metadata or title
                        post = self._safe_read_entry(entry)
                        if post is None:
                            continue
                        topic = post.get("topic") or entry["title"].replace("Research: ", "")
                        topics.append(topic)
                except (ValueError, TypeError):
                    continue

        return topics

    def _safe_read_entry(self, entry: dict):
        try:
            return self.storage.read(entry["path"])
        except (OSError, ValueError) as exc:
            logger.warning(
                "topic_selector_entry_read_failed",
                path=str(entry.get("path")),
                title=entry.get("title"),
                error=str(exc),
            )
            return None

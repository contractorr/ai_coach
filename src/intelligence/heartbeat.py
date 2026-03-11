"""Heartbeat — proactive intel-to-goal matching with composite scoring + notifications."""

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import structlog

from db import wal_connect

from .goal_intel_match import _STOPWORDS

logger = structlog.get_logger()


# --- Dataclasses ---


@dataclass
class ScoredItem:
    """Intel item scored against a goal."""

    intel_item: dict
    keyword_score: float = 0.0
    recency_score: float = 0.0
    source_affinity_score: float = 0.0
    composite_score: float = 0.0
    matched_goal_path: str = ""
    matched_goal_title: str = ""


@dataclass
class ActionBrief:
    """Notification generated from a scored intel item."""

    intel_item_id: int = 0
    intel_url: str = ""
    intel_title: str = ""
    intel_summary: str = ""
    relevance: float = 0.0
    urgency: str = "low"
    suggested_action: str = ""
    reasoning: str = ""
    related_goal_id: str | None = None
    notification_hash: str = ""

    def compute_hash(self) -> str:
        raw = f"{self.intel_url}|{self.related_goal_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# --- HeartbeatFilter ---


class HeartbeatFilter:
    """Score intel items against goals using keyword overlap + recency + source affinity."""

    def __init__(
        self,
        goals: list[dict],
        threshold: float = 0.3,
        weights: dict | None = None,
        preferred_sources: list[str] | None = None,
    ):
        self.goals = goals
        self.threshold = threshold
        self.weights = weights or {
            "keyword_overlap": 0.35,
            "recency": 0.35,
            "source_affinity": 0.3,
        }
        self.preferred_sources = set(preferred_sources or [])
        # Pre-extract keywords per goal
        self._goal_keywords: dict[str, list[str]] = {}
        for g in goals:
            path = str(g.get("path", ""))
            self._goal_keywords[path] = self._extract_keywords(g)

    @staticmethod
    def _extract_keywords(goal: dict) -> list[str]:
        """Extract keywords from goal title and tags (same logic as GoalIntelMatcher)."""
        parts: list[str] = []
        title = goal.get("title", "")
        if title:
            parts.append(title)
        tags = goal.get("tags", [])
        if tags:
            parts.extend(tags)
        text = " ".join(parts).lower()
        tokens = set(re.findall(r"[a-z][a-z0-9\-]+", text))
        filtered = [t for t in tokens if t not in _STOPWORDS and len(t) > 2]
        filtered.sort(key=len, reverse=True)
        return filtered[:30]

    def score_item_against_goal(self, item: dict, goal: dict) -> ScoredItem:
        """Compute composite score for one item against one goal."""
        path = str(goal.get("path", ""))
        keywords = self._goal_keywords.get(path, [])

        # Keyword score
        item_text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        matching = sum(1 for kw in keywords if kw in item_text)
        keyword_score = matching / max(len(keywords), 1)

        # Recency score
        recency_score = 0.5  # default if no timestamp
        scraped_at = item.get("scraped_at")
        if scraped_at:
            try:
                if isinstance(scraped_at, str):
                    scraped_dt = datetime.fromisoformat(scraped_at)
                else:
                    scraped_dt = scraped_at
                hours_since = (datetime.now() - scraped_dt).total_seconds() / 3600
                recency_score = max(0.0, 1.0 - hours_since / 48.0)
            except (ValueError, TypeError):
                pass

        # Source affinity score
        source = item.get("source", "")
        source_affinity_score = 1.0 if source in self.preferred_sources else 0.5

        # Composite
        w = self.weights
        composite = (
            w.get("keyword_overlap", 0.35) * keyword_score
            + w.get("recency", 0.35) * recency_score
            + w.get("source_affinity", 0.3) * source_affinity_score
        )

        return ScoredItem(
            intel_item=item,
            keyword_score=keyword_score,
            recency_score=recency_score,
            source_affinity_score=source_affinity_score,
            composite_score=composite,
            matched_goal_path=path,
            matched_goal_title=goal.get("title", ""),
        )

    def filter(self, items: list[dict]) -> list[ScoredItem]:
        """Score each item against each goal, keep best goal match per URL, filter by threshold."""
        if not self.goals or not items:
            return []

        # Best score per URL
        best_per_url: dict[str, ScoredItem] = {}

        for item in items:
            url = item.get("url", "")
            for goal in self.goals:
                scored = self.score_item_against_goal(item, goal)
                if scored.composite_score < self.threshold:
                    continue
                existing = best_per_url.get(url)
                if existing is None or scored.composite_score > existing.composite_score:
                    best_per_url[url] = scored

        result = list(best_per_url.values())
        result.sort(key=lambda s: s.composite_score, reverse=True)
        return result


# --- HeartbeatEvaluator ---


_SYSTEM_PROMPT = (
    "You evaluate whether news items are relevant to user goals. "
    "Be strict — keyword matches often produce false positives. "
    "For each item, judge relevance, urgency, and suggest an action."
)


class HeartbeatEvaluator:
    """Optional LLM refinement of scored items, with heuristic fallback."""

    def __init__(self, provider=None, budget: int = 5):
        self._provider = provider
        self.budget = budget

    def _get_provider(self):
        if self._provider:
            return self._provider
        from llm.factory import create_cheap_provider

        return create_cheap_provider()

    def _heuristic_brief(self, scored: ScoredItem) -> ActionBrief:
        """Create ActionBrief from heuristic scoring only."""
        cs = scored.composite_score
        if cs > 0.7:
            urgency = "high"
        elif cs > 0.5:
            urgency = "medium"
        else:
            urgency = "low"

        brief = ActionBrief(
            intel_item_id=scored.intel_item.get("id", 0),
            intel_url=scored.intel_item.get("url", ""),
            intel_title=scored.intel_item.get("title", ""),
            intel_summary=(scored.intel_item.get("summary") or "")[:300],
            relevance=scored.composite_score,
            urgency=urgency,
            suggested_action="Review this item",
            reasoning=f"Matched goal '{scored.matched_goal_title}' (score={cs:.2f})",
            related_goal_id=scored.matched_goal_path or None,
        )
        brief.notification_hash = brief.compute_hash()
        return brief

    def _build_prompt(self, scored_items: list[ScoredItem]) -> str:
        lines: list[str] = []
        for idx, s in enumerate(scored_items):
            goal_title = s.matched_goal_title
            title = s.intel_item.get("title", "")
            summary = (s.intel_item.get("summary") or "")[:200]
            lines.append(
                f'{idx + 1}. GOAL: "{goal_title}" | [Title] "{title}" | [Summary] "{summary}"'
            )
        lines.append("")
        lines.append("For each item respond EXACTLY:")
        for idx in range(len(scored_items)):
            lines.append(f"ITEM_{idx + 1}_RELEVANT: yes|no")
            lines.append(f"ITEM_{idx + 1}_URGENCY: high|medium|low|drop")
            lines.append(f"ITEM_{idx + 1}_ACTION: <one sentence suggested action>")
            lines.append(f"ITEM_{idx + 1}_REASON: <one sentence reasoning>")
        lines.append('"drop" means false positive — remove entirely.')
        return "\n".join(lines)

    def _parse_response(self, text: str, scored_items: list[ScoredItem]) -> list[ActionBrief]:
        results: dict[int, dict] = {}
        for line in text.strip().splitlines():
            line = line.strip()
            m = re.match(
                r"ITEM_(\d+)_(RELEVANT|URGENCY|ACTION|REASON):\s*(.+)",
                line,
                re.IGNORECASE,
            )
            if not m:
                continue
            idx = int(m.group(1))
            field_name = m.group(2).upper()
            value = m.group(3).strip()
            results.setdefault(idx, {})[field_name] = value

        briefs: list[ActionBrief] = []
        for i, scored in enumerate(scored_items):
            data = results.get(i + 1, {})
            relevant = data.get("RELEVANT", "yes").lower()
            urgency = data.get("URGENCY", "medium").lower()

            if relevant == "no" or urgency == "drop":
                continue

            if urgency not in ("high", "medium", "low"):
                urgency = "medium"

            brief = ActionBrief(
                intel_item_id=scored.intel_item.get("id", 0),
                intel_url=scored.intel_item.get("url", ""),
                intel_title=scored.intel_item.get("title", ""),
                intel_summary=(scored.intel_item.get("summary") or "")[:300],
                relevance=scored.composite_score,
                urgency=urgency,
                suggested_action=data.get("ACTION", "Review this item"),
                reasoning=data.get("REASON", "LLM evaluated as relevant"),
                related_goal_id=scored.matched_goal_path or None,
            )
            brief.notification_hash = brief.compute_hash()
            briefs.append(brief)

        return briefs

    def evaluate(self, scored_items: list[ScoredItem]) -> list[ActionBrief]:
        """Evaluate scored items via LLM or heuristic fallback."""
        if not scored_items:
            return []

        # No LLM: heuristic only
        if self.budget == 0:
            return [self._heuristic_brief(s) for s in scored_items]

        # Try LLM
        try:
            provider = self._get_provider()
            batch = scored_items[: self.budget]
            prompt = self._build_prompt(batch)
            response = provider.generate(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
            )
            briefs = self._parse_response(response, batch)

            # Heuristic for any remaining items beyond budget
            for s in scored_items[self.budget :]:
                briefs.append(self._heuristic_brief(s))

            return briefs
        except Exception as e:
            logger.warning("heartbeat_evaluator.llm_failed", error=str(e))
            return [self._heuristic_brief(s) for s in scored_items]


# --- ActionBriefStore ---


class ActionBriefStore:
    """SQLite persistence for heartbeat notifications and run history."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser()
        self._init_db()

    def _init_db(self):
        with wal_connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS heartbeat_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intel_item_id INTEGER NOT NULL,
                    intel_url TEXT NOT NULL,
                    intel_title TEXT NOT NULL,
                    intel_summary TEXT,
                    relevance REAL NOT NULL,
                    urgency TEXT NOT NULL,
                    suggested_action TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    related_goal_id TEXT,
                    notification_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    dismissed_at TIMESTAMP
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hbn_undismissed "
                "ON heartbeat_notifications(dismissed_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hbn_hash "
                "ON heartbeat_notifications(notification_hash)"
            )

            conn.execute("""
                CREATE TABLE IF NOT EXISTS heartbeat_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TIMESTAMP NOT NULL,
                    finished_at TIMESTAMP,
                    items_checked INTEGER DEFAULT 0,
                    items_passed INTEGER DEFAULT 0,
                    briefs_saved INTEGER DEFAULT 0,
                    llm_used INTEGER DEFAULT 0,
                    error TEXT
                )
            """)

    def log_run(self, stats: dict):
        """Record a heartbeat run."""
        with wal_connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO heartbeat_runs
                   (started_at, finished_at, items_checked, items_passed, briefs_saved, llm_used, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    stats.get("started_at", datetime.now().isoformat()),
                    stats.get("finished_at", datetime.now().isoformat()),
                    stats.get("items_checked", 0),
                    stats.get("items_passed", 0),
                    stats.get("briefs_saved", 0),
                    stats.get("llm_used", 0),
                    stats.get("error"),
                ),
            )

    def get_last_run_at(self) -> datetime | None:
        """Get timestamp of most recent heartbeat run."""
        with wal_connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT started_at FROM heartbeat_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row:
                return datetime.fromisoformat(row[0])
            return None

    def get_last_llm_run_at(self) -> datetime | None:
        """Get timestamp of most recent heartbeat run that used LLM."""
        with wal_connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT started_at FROM heartbeat_runs WHERE llm_used = 1 ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row:
                return datetime.fromisoformat(row[0])
            return None

    def get_runs(self, limit: int = 10) -> list[dict]:
        """Get recent heartbeat runs."""
        with wal_connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM heartbeat_runs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def cleanup_old(self, days: int = 30) -> int:
        """Delete notifications older than given days."""
        with wal_connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM heartbeat_notifications WHERE created_at < datetime('now', ?)",
                (f"-{days} days",),
            )
            return cursor.rowcount


# --- HeartbeatPipeline ---


class HeartbeatPipeline:
    """Orchestrates filter -> evaluate -> store cycle."""

    def __init__(
        self,
        intel_storage,
        goals: list[dict],
        db_path: str | Path,
        config: dict | None = None,
    ):
        self.intel_storage = intel_storage
        self.goals = goals
        self.db_path = Path(db_path).expanduser()
        self.config = config or {}

    def run(self) -> dict:
        """Execute one heartbeat cycle. Returns stats dict."""
        started_at = datetime.now()
        store = ActionBriefStore(self.db_path)

        threshold = self.config.get("heuristic_threshold", 0.3)
        budget = self.config.get("llm_budget_per_cycle", 5)
        lookback = self.config.get("lookback_hours", 2)

        # Weights
        weights_cfg = self.config.get("weights", {})
        weights = {
            "keyword_overlap": weights_cfg.get("keyword_overlap", 0.35),
            "recency": weights_cfg.get("recency", 0.35),
            "source_affinity": weights_cfg.get("source_affinity", 0.3),
        }
        preferred_sources = self.config.get("preferred_sources", [])

        # Determine lookback window
        last_run = store.get_last_run_at()
        since = last_run or (started_at - timedelta(hours=lookback))

        # Fetch intel
        items = self.intel_storage.get_items_since(since, limit=200)

        # Filter
        hb_filter = HeartbeatFilter(
            self.goals,
            threshold=threshold,
            weights=weights,
            preferred_sources=preferred_sources,
        )
        scored = hb_filter.filter(items)

        # Evaluate (cap at budget for LLM)
        evaluator = HeartbeatEvaluator(budget=budget)
        briefs = evaluator.evaluate(scored)

        # Save to InsightStore
        from advisor.insights import Insight, InsightStore, InsightType

        insight_store = InsightStore(self.db_path)
        saved = 0
        for b in briefs:
            urgency_severity = {"high": 8, "medium": 5, "low": 3}.get(b.urgency, 3)
            insight = Insight(
                type=InsightType.INTEL_MATCH,
                severity=urgency_severity,
                title=b.intel_title,
                detail=f"{b.reasoning}\n\n{b.intel_summary}",
                suggested_actions=[b.suggested_action] if b.suggested_action else [],
                source_url=b.intel_url,
            )
            if insight_store.save(insight):
                saved += 1

        finished_at = datetime.now()
        llm_used = 1 if budget > 0 and scored else 0

        stats = {
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "items_checked": len(items),
            "items_passed": len(scored),
            "briefs_saved": saved,
            "llm_used": llm_used,
        }
        store.log_run(stats)

        logger.info("heartbeat.complete", **stats)
        return stats

    def evaluate_pending(self, budget: int = 5) -> dict:
        """On-demand LLM evaluation of heuristic-filtered intel. Respects cooldown."""
        store = ActionBriefStore(self.db_path)
        cooldown_hours = self.config.get("notification_cooldown_hours", 4)

        last_llm = store.get_last_llm_run_at()
        if last_llm and (datetime.now() - last_llm) < timedelta(hours=cooldown_hours):
            return {"skipped": "cooldown"}

        if not self.goals:
            return {"skipped": "no_goals"}

        started_at = datetime.now()
        lookback = self.config.get("lookback_hours", 2)
        threshold = self.config.get("heuristic_threshold", 0.3)

        weights_cfg = self.config.get("weights", {})
        weights = {
            "keyword_overlap": weights_cfg.get("keyword_overlap", 0.35),
            "recency": weights_cfg.get("recency", 0.35),
            "source_affinity": weights_cfg.get("source_affinity", 0.3),
        }
        preferred_sources = self.config.get("preferred_sources", [])

        last_run = store.get_last_run_at()
        since = last_run or (started_at - timedelta(hours=lookback))

        items = self.intel_storage.get_items_since(since, limit=200)

        hb_filter = HeartbeatFilter(
            self.goals,
            threshold=threshold,
            weights=weights,
            preferred_sources=preferred_sources,
        )
        scored = hb_filter.filter(items)

        evaluator = HeartbeatEvaluator(budget=budget)
        briefs = evaluator.evaluate(scored)

        from advisor.insights import Insight, InsightStore, InsightType

        insight_store = InsightStore(self.db_path)
        saved = 0
        for b in briefs:
            urgency_severity = {"high": 8, "medium": 5, "low": 3}.get(b.urgency, 3)
            insight = Insight(
                type=InsightType.INTEL_MATCH,
                severity=urgency_severity,
                title=b.intel_title,
                detail=f"{b.reasoning}\n\n{b.intel_summary}",
                suggested_actions=[b.suggested_action] if b.suggested_action else [],
                source_url=b.intel_url,
            )
            if insight_store.upsert(insight):
                saved += 1

        finished_at = datetime.now()
        stats = {
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "items_checked": len(items),
            "items_passed": len(scored),
            "briefs_saved": saved,
            "llm_used": 1,
        }
        store.log_run(stats)

        logger.info("heartbeat.evaluate_pending.complete", **stats)
        return stats

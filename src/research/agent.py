"""Deep research agent orchestrating standalone reports and dossier updates."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog

from intelligence.scraper import IntelItem, IntelStorage
from journal import EmbeddingManager, JournalStorage

from .dossiers import ResearchDossierStore
from .synthesis import ResearchSynthesizer
from .topics import TopicSelector
from .web_search import AsyncWebSearchClient, SearchResult, WebSearchClient

logger = structlog.get_logger()

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def _extract_section(markdown: str, heading: str) -> str:
    matches = list(_SECTION_RE.finditer(markdown or ""))
    for idx, match in enumerate(matches):
        if match.group(1).strip().lower() != heading.lower():
            continue
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        return markdown[start:end].strip()
    return ""


def _bullet_lines(section: str) -> list[str]:
    lines = []
    for raw in (section or "").splitlines():
        text = raw.strip()
        if text.startswith(("- ", "* ")):
            text = text[2:].strip()
        if text:
            lines.append(text)
    return lines


def _first_line(section: str, default: str = "") -> str:
    for line in _bullet_lines(section):
        if line:
            return line
    for line in (section or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return default


class DeepResearchAgent:
    """Orchestrates topic selection, web search, and dossier-aware report generation."""

    def __init__(
        self,
        journal_storage: JournalStorage,
        intel_storage: IntelStorage,
        embeddings: EmbeddingManager,
        config: Optional[dict] = None,
        topic_selector: TopicSelector | None = None,
        search_client: WebSearchClient | None = None,
        synthesizer: ResearchSynthesizer | None = None,
        dossiers: ResearchDossierStore | None = None,
    ):
        self.journal = journal_storage
        self.intel = intel_storage
        self.embeddings = embeddings
        self.config = config or {}

        research_config = self.config.get("research", {})
        self.max_topics = int(research_config.get("max_topics_per_week", 2) or 2)

        self.topic_selector = topic_selector or self._create_topic_selector(research_config)
        self.search_client = search_client or self._create_search_client(research_config)
        llm_config = self.config.get("llm", {})
        self.synthesizer = synthesizer or self._create_synthesizer(llm_config)
        self.dossiers = dossiers or self._create_dossier_store(journal_storage)

    def _create_topic_selector(self, research_config: dict) -> TopicSelector:
        return TopicSelector(
            storage=self.journal,
            max_topics=self.max_topics,
            skip_researched_days=research_config.get("skip_if_researched_days", 60),
        )

    def _create_search_client(self, research_config: dict) -> WebSearchClient:
        return WebSearchClient(
            api_key=research_config.get("api_key"),
            provider=research_config.get("api_provider", "tavily"),
            max_results=research_config.get("sources_per_topic", 8),
        )

    def _create_synthesizer(self, llm_config: dict) -> ResearchSynthesizer:
        return ResearchSynthesizer(
            model=llm_config.get("model"),
            provider=llm_config.get("provider"),
            api_key=llm_config.get("api_key"),
        )

    def _create_dossier_store(self, journal_storage: JournalStorage) -> ResearchDossierStore:
        return ResearchDossierStore(journal_storage)

    def create_dossier(
        self,
        topic: str,
        scope: str = "",
        core_questions: Optional[list[str]] = None,
        assumptions: Optional[list[str]] = None,
        related_goals: Optional[list[str]] = None,
        tracked_subtopics: Optional[list[str]] = None,
        open_questions: Optional[list[str]] = None,
    ) -> dict:
        return self.dossiers.create_dossier(
            topic=topic,
            scope=scope,
            core_questions=core_questions,
            assumptions=assumptions,
            related_goals=related_goals,
            tracked_subtopics=tracked_subtopics,
            open_questions=open_questions,
        )

    def list_dossiers(self, include_archived: bool = False, limit: int = 50) -> list[dict]:
        return self.dossiers.list_dossiers(include_archived=include_archived, limit=limit)

    def get_dossier(self, dossier_id: str) -> dict | None:
        return self.dossiers.get_dossier(dossier_id)

    def run(
        self,
        specific_topic: Optional[str] = None,
        dossier_id: Optional[str] = None,
    ) -> list[dict]:
        """Run deep research on standalone topics or persistent dossiers."""
        if dossier_id:
            dossier = self.dossiers.get_dossier(dossier_id)
            if not dossier:
                raise ValueError(f"Unknown dossier: {dossier_id}")
            return [self._run_dossier(dossier, run_source="manual")]

        if specific_topic:
            return self._run_topics(
                [
                    {
                        "topic": specific_topic,
                        "source": "manual",
                        "score": 10,
                        "reason": "User specified",
                    }
                ]
            )

        active_dossiers = self.dossiers.get_active_dossiers(limit=self.max_topics)
        if active_dossiers:
            return [
                self._run_dossier(dossier, run_source="scheduled") for dossier in active_dossiers
            ]

        recent = self.topic_selector.get_recent_research_topics()
        return self._run_topics(self.topic_selector.get_topics(researched_topics=recent))

    def get_suggested_topics(self) -> list[dict]:
        recent = self.topic_selector.get_recent_research_topics()
        return self.topic_selector.get_topics(researched_topics=recent)

    def _run_topics(self, topics: list[dict]) -> list[dict]:
        results = []
        if not topics:
            logger.info("No topics to research")
            return results

        user_context = self._get_user_context()
        for topic_info in topics:
            topic = topic_info["topic"]
            logger.info("research_topic_started", topic=topic, source=topic_info.get("source"))
            try:
                search_results = self.search_client.search(topic)
                if not search_results:
                    results.append(
                        {
                            "topic": topic,
                            "filepath": None,
                            "success": False,
                            "error": "No search results",
                        }
                    )
                    continue

                report = self.synthesizer.synthesize(
                    topic=topic, results=search_results, user_context=user_context
                )
                filepath = self._store_journal_entry(topic, report, topic_info)
                self._store_intel_item(topic, report, search_results)
                self._add_embeddings(
                    filepath,
                    report,
                    {"type": "research", "topic": topic, "research_kind": "report"},
                )
                results.append(
                    {
                        "topic": topic,
                        "title": f"Research: {topic}",
                        "summary": report[:400],
                        "content": report,
                        "sources": [r.url for r in search_results],
                        "saved_path": filepath,
                        "filepath": filepath,
                        "success": True,
                    }
                )
            except (IOError, ValueError, KeyError) as e:
                logger.error("research_failed", topic=topic, error=str(e))
                results.append(
                    {"topic": topic, "filepath": None, "success": False, "error": str(e)}
                )
        return results

    def _run_dossier(self, dossier: dict, run_source: str) -> dict:
        topic = dossier["topic"]
        search_results = self.search_client.search(topic)
        if not search_results:
            return {
                "topic": topic,
                "title": f"Research Update: {topic}",
                "dossier_id": dossier["dossier_id"],
                "filepath": None,
                "success": False,
                "error": "No search results",
            }

        user_context = self._build_dossier_user_context(dossier)
        report = self.synthesizer.synthesize_dossier_update(
            topic=topic,
            results=search_results,
            dossier_context=dossier.get("content", ""),
            previous_change_summary=dossier.get("latest_change_summary", ""),
            user_context=user_context,
        )
        metadata = self._build_update_metadata(report, search_results, run_source)
        update = self.dossiers.append_update(dossier["dossier_id"], report, metadata)
        refreshed = self.dossiers.get_dossier(dossier["dossier_id"]) or dossier

        self._store_intel_item(
            topic,
            report,
            search_results,
            dossier_id=dossier["dossier_id"],
            summary=metadata.get("change_summary", report[:300]),
        )
        self._add_embeddings(
            update["path"],
            report,
            {
                "type": "research",
                "topic": topic,
                "research_kind": "dossier_update",
                "dossier_id": dossier["dossier_id"],
                "change_summary": metadata.get("change_summary", ""),
            },
        )
        self._add_embeddings(
            refreshed["path"],
            refreshed.get("content", ""),
            {
                "type": "research",
                "topic": topic,
                "research_kind": "dossier",
                "dossier_id": dossier["dossier_id"],
                "change_summary": refreshed.get("latest_change_summary", ""),
            },
        )

        return {
            "topic": topic,
            "title": update["title"],
            "summary": metadata.get("change_summary", report[:400]),
            "content": report,
            "sources": [r.url for r in search_results],
            "saved_path": update["path"],
            "filepath": update["path"],
            "dossier_id": dossier["dossier_id"],
            "change_summary": metadata.get("change_summary", ""),
            "success": True,
        }

    def _build_update_metadata(
        self,
        report: str,
        search_results: list[SearchResult],
        run_source: str,
    ) -> dict:
        what_changed = _extract_section(report, "What Changed")
        confidence = _first_line(_extract_section(report, "Confidence"), default="Medium")
        recommended_actions = _bullet_lines(_extract_section(report, "Recommended Actions"))
        open_questions = _bullet_lines(_extract_section(report, "Open Questions"))
        change_summary = _first_line(what_changed, default=report[:240])
        return {
            "change_summary": change_summary,
            "confidence": confidence,
            "recommended_actions": recommended_actions,
            "open_questions": open_questions,
            "citations": [r.title for r in search_results],
            "source_urls": [r.url for r in search_results],
            "source_titles": [r.title for r in search_results],
            "sources_count": len(search_results),
            "run_source": run_source,
        }

    def _get_user_context(self) -> str:
        context_parts = []
        goals = self.journal.list_entries(entry_type="goal", limit=5)
        if goals:
            context_parts.append("GOALS:")
            for goal in goals:
                context_parts.append(f"- {goal['title']}")

        recent_entries = self.journal.list_entries(limit=5)
        non_goals = [entry for entry in recent_entries if entry.get("type") != "goal"]
        if non_goals:
            context_parts.append("RECENT JOURNAL THEMES:")
            for entry in non_goals[:3]:
                preview = (entry.get("preview") or "").replace("\n", " ").strip()
                if preview:
                    context_parts.append(f"- {entry['title']}: {preview[:140]}")

        return "\n".join(context_parts) if context_parts else ""

    def _build_dossier_user_context(self, dossier: dict) -> str:
        parts = [self._get_user_context()]
        if dossier.get("scope"):
            parts.append(f"DOSSIER SCOPE: {dossier['scope']}")
        if dossier.get("core_questions"):
            parts.append(
                "CORE QUESTIONS:\n" + "\n".join(f"- {q}" for q in dossier["core_questions"])
            )
        if dossier.get("assumptions"):
            parts.append("ASSUMPTIONS:\n" + "\n".join(f"- {a}" for a in dossier["assumptions"]))
        if dossier.get("related_goals"):
            parts.append("RELATED GOALS:\n" + "\n".join(f"- {g}" for g in dossier["related_goals"]))
        if dossier.get("tracked_subtopics"):
            parts.append(
                "TRACKED SUBTOPICS:\n" + "\n".join(f"- {s}" for s in dossier["tracked_subtopics"])
            )
        return "\n\n".join(part for part in parts if part)

    def _store_journal_entry(self, topic: str, report: str, topic_info: dict) -> Path:
        return self.journal.create(
            content=report,
            entry_type="research",
            title=f"Research: {topic}",
            tags=["research", "auto", topic_info["source"]],
            metadata={
                "topic": topic,
                "research_source": topic_info["source"],
                "research_kind": "report",
            },
        )

    def _store_intel_item(
        self,
        topic: str,
        report: str,
        search_results: list[SearchResult],
        dossier_id: str | None = None,
        summary: str | None = None,
    ) -> None:
        if dossier_id:
            unique_url = (
                f"research://dossier/{dossier_id}/{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            tags = ["research", "dossier"]
            title = f"Research Update: {topic}"
        else:
            unique_url = (
                f"research://{topic.lower().replace(' ', '-')}/{datetime.now().strftime('%Y%m%d')}"
            )
            tags = ["research", "auto"]
            title = f"Research: {topic}"

        item = IntelItem(
            source="deep_research",
            title=title,
            url=unique_url,
            summary=(summary or report)[:500],
            content=report,
            published=datetime.now(),
            tags=tags,
        )
        self.intel.save(item)

    def _add_embeddings(self, filepath: Path, content: str, metadata: dict) -> None:
        self.embeddings.add_entry(str(filepath), content, metadata)

    def close(self):
        """Close underlying clients."""
        self.search_client.close()


class AsyncDeepResearchAgent(DeepResearchAgent):
    """Async version of the deep research agent."""

    def __init__(
        self,
        journal_storage: JournalStorage,
        intel_storage: IntelStorage,
        embeddings: EmbeddingManager,
        config: Optional[dict] = None,
        topic_selector: TopicSelector | None = None,
        search_client: AsyncWebSearchClient | None = None,
        synthesizer: ResearchSynthesizer | None = None,
        dossiers: ResearchDossierStore | None = None,
    ):
        super().__init__(
            journal_storage=journal_storage,
            intel_storage=intel_storage,
            embeddings=embeddings,
            config=config,
            topic_selector=topic_selector,
            search_client=search_client,
            synthesizer=synthesizer,
            dossiers=dossiers,
        )

    def _create_search_client(self, research_config: dict) -> AsyncWebSearchClient:
        return AsyncWebSearchClient(
            api_key=research_config.get("api_key"),
            provider=research_config.get("api_provider", "tavily"),
            max_results=research_config.get("sources_per_topic", 8),
        )

    async def run(
        self,
        specific_topic: Optional[str] = None,
        dossier_id: Optional[str] = None,
    ) -> list[dict]:
        if dossier_id:
            dossier = self.dossiers.get_dossier(dossier_id)
            if not dossier:
                raise ValueError(f"Unknown dossier: {dossier_id}")
            return [await self._run_dossier_async(dossier, run_source="manual")]

        if specific_topic:
            topics = [
                {
                    "topic": specific_topic,
                    "source": "manual",
                    "score": 10,
                    "reason": "User specified",
                }
            ]
        else:
            active_dossiers = self.dossiers.get_active_dossiers(limit=self.max_topics)
            if active_dossiers:
                return [
                    await self._run_dossier_async(dossier, run_source="scheduled")
                    for dossier in active_dossiers
                ]
            recent = self.topic_selector.get_recent_research_topics()
            topics = self.topic_selector.get_topics(researched_topics=recent)

        results = []
        user_context = self._get_user_context()
        for topic_info in topics:
            topic = topic_info["topic"]
            try:
                search_results = await self.search_client.search(topic)
                if not search_results:
                    results.append(
                        {
                            "topic": topic,
                            "filepath": None,
                            "success": False,
                            "error": "No search results",
                        }
                    )
                    continue
                report = self.synthesizer.synthesize(
                    topic=topic, results=search_results, user_context=user_context
                )
                filepath = self._store_journal_entry(topic, report, topic_info)
                self._store_intel_item(topic, report, search_results)
                self._add_embeddings(
                    filepath,
                    report,
                    {"type": "research", "topic": topic, "research_kind": "report"},
                )
                results.append(
                    {"topic": topic, "filepath": filepath, "saved_path": filepath, "success": True}
                )
            except (IOError, ValueError, KeyError) as e:
                logger.error("async_research_failed", topic=topic, error=str(e))
                results.append(
                    {"topic": topic, "filepath": None, "success": False, "error": str(e)}
                )
        return results

    async def _run_dossier_async(self, dossier: dict, run_source: str) -> dict:
        topic = dossier["topic"]
        search_results = await self.search_client.search(topic)
        if not search_results:
            return {
                "topic": topic,
                "dossier_id": dossier["dossier_id"],
                "filepath": None,
                "success": False,
                "error": "No search results",
            }

        report = self.synthesizer.synthesize_dossier_update(
            topic=topic,
            results=search_results,
            dossier_context=dossier.get("content", ""),
            previous_change_summary=dossier.get("latest_change_summary", ""),
            user_context=self._build_dossier_user_context(dossier),
        )
        metadata = self._build_update_metadata(report, search_results, run_source)
        update = self.dossiers.append_update(dossier["dossier_id"], report, metadata)
        refreshed = self.dossiers.get_dossier(dossier["dossier_id"]) or dossier
        self._store_intel_item(
            topic,
            report,
            search_results,
            dossier_id=dossier["dossier_id"],
            summary=metadata.get("change_summary"),
        )
        self._add_embeddings(
            update["path"],
            report,
            {
                "type": "research",
                "topic": topic,
                "research_kind": "dossier_update",
                "dossier_id": dossier["dossier_id"],
            },
        )
        self._add_embeddings(
            refreshed["path"],
            refreshed.get("content", ""),
            {
                "type": "research",
                "topic": topic,
                "research_kind": "dossier",
                "dossier_id": dossier["dossier_id"],
            },
        )
        return {
            "topic": topic,
            "title": update["title"],
            "summary": metadata.get("change_summary", ""),
            "saved_path": update["path"],
            "filepath": update["path"],
            "dossier_id": dossier["dossier_id"],
            "success": True,
        }

    async def close(self):
        await self.search_client.close()

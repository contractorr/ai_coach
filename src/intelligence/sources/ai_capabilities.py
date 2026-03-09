"""AI capabilities scrapers — METR, Epoch AI, AI Index, ARC Evals, frontier GitHub evals."""

import json
from datetime import datetime
from typing import Optional

import httpx
import structlog
from bs4 import BeautifulSoup

from intelligence.scraper import BaseScraper, IntelItem, IntelStorage
from llm.factory import create_cheap_provider
from retry_utils import http_retry
from shared_types import IntelSource

logger = structlog.get_logger().bind(source="ai_capabilities")


def _strip_html_to_text(html: str) -> str:
    """Strip HTML to plain text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def _llm_extract_json(text: str, fields_prompt: str, max_chars: int = 8000) -> list[dict]:
    """Use cheap LLM to extract structured JSON from plain text.

    Returns parsed list of dicts, or empty list on failure.
    """
    truncated = text[:max_chars]
    prompt = (
        f"{fields_prompt}\n\n"
        "Return ONLY a valid JSON array of objects. No other text.\n\n"
        f"TEXT:\n{truncated}"
    )
    try:
        provider = create_cheap_provider()
        response = provider.generate(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        # Strip markdown code fences if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned[: cleaned.rfind("```")]
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
        return []
    except Exception as e:
        logger.warning("llm_extract_json_failed", error=str(e))
        return []


def _llm_extract_single(text: str, fields_prompt: str, max_chars: int = 8000) -> dict:
    """Use cheap LLM to extract a single JSON object from text."""
    truncated = text[:max_chars]
    prompt = (
        f"{fields_prompt}\n\n"
        "Return ONLY valid JSON (a single object or empty object {{}}). No other text.\n\n"
        f"TEXT:\n{truncated}"
    )
    try:
        provider = create_cheap_provider()
        response = provider.generate(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned[: cleaned.rfind("```")]
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {}
    except Exception as e:
        logger.warning("llm_extract_single_failed", error=str(e))
        return {}


_DEFAULT_TAGS = ["ai-capabilities", "benchmarks"]


class AICapabilitiesScraper(BaseScraper):
    """Scrapes AI capability benchmarks from METR, Chatbot Arena, and HELM."""

    METR_API = "https://api.github.com/repos/METR/autonomy-evals/releases"
    CHATBOT_ARENA_URL = "https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard"
    HELM_URL = "https://crfm.stanford.edu/helm/latest/"

    def __init__(
        self,
        storage: IntelStorage,
        sources: Optional[list[str]] = None,
        max_items_per_source: int = 10,
    ):
        super().__init__(storage)
        self.enabled_sources = sources or ["metr", "chatbot_arena", "helm"]
        self.max_items = max_items_per_source

    @property
    def source_name(self) -> str:
        return IntelSource.AI_CAPABILITIES

    @http_retry(exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.RequestError))
    async def scrape(self) -> list[IntelItem]:
        """Scrape all enabled AI capability sources."""
        items: list[IntelItem] = []

        if "metr" in self.enabled_sources:
            items.extend(await self._scrape_metr())

        if "chatbot_arena" in self.enabled_sources:
            items.extend(await self._scrape_chatbot_arena())

        if "helm" in self.enabled_sources:
            items.extend(await self._scrape_helm())

        logger.info("Scraped %d AI capability items", len(items))
        return items

    async def _scrape_metr(self) -> list[IntelItem]:
        """Fetch METR autonomy eval releases from GitHub API."""
        items = []
        try:
            response = await self.client.get(
                self.METR_API,
                headers={"Accept": "application/vnd.github+json"},
            )
            response.raise_for_status()
            releases = response.json()[: self.max_items]

            for rel in releases:
                published = None
                if rel.get("published_at"):
                    try:
                        published = datetime.fromisoformat(
                            rel["published_at"].replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass

                body = (rel.get("body") or "")[:500]
                items.append(
                    IntelItem(
                        source=self.source_name,
                        title=f"METR Eval: {rel.get('name') or rel.get('tag_name', 'unknown')}",
                        url=rel.get("html_url", "https://github.com/METR/autonomy-evals"),
                        summary=body if body else f"Release {rel.get('tag_name', '')}",
                        published=published,
                        tags=_DEFAULT_TAGS + ["metr", "autonomy"],
                    )
                )
        except httpx.RequestError as e:
            logger.warning("METR scrape failed: %s", e)

        return items

    async def _scrape_chatbot_arena(self) -> list[IntelItem]:
        """Scrape Chatbot Arena leaderboard from HuggingFace."""
        items = []
        try:
            soup = await self.fetch_html(self.CHATBOT_ARENA_URL)
            if not soup:
                return items

            # Extract model rankings from the leaderboard page
            # HF spaces render dynamically; we extract whatever static content is available
            title_el = soup.find("title")
            page_title = title_el.get_text(strip=True) if title_el else "Chatbot Arena"

            # Look for table rows or model cards
            rows = soup.select("table tr, .model-row, [class*='leaderboard']")
            if rows:
                summaries = []
                for row in rows[: self.max_items]:
                    text = row.get_text(separator=" ", strip=True)[:200]
                    if text:
                        summaries.append(text)

                if summaries:
                    items.append(
                        IntelItem(
                            source=self.source_name,
                            title="Chatbot Arena Leaderboard Update",
                            url=self.CHATBOT_ARENA_URL,
                            summary="; ".join(summaries[:5]),
                            published=datetime.now(),
                            tags=_DEFAULT_TAGS + ["chatbot-arena", "rankings"],
                        )
                    )
            else:
                # Fallback: store page as single item
                text = soup.get_text(separator=" ", strip=True)[:500]
                if text:
                    items.append(
                        IntelItem(
                            source=self.source_name,
                            title=f"Chatbot Arena: {page_title}",
                            url=self.CHATBOT_ARENA_URL,
                            summary=text,
                            published=datetime.now(),
                            tags=_DEFAULT_TAGS + ["chatbot-arena", "rankings"],
                        )
                    )
        except httpx.RequestError as e:
            logger.warning("Chatbot Arena scrape failed: %s", e)

        return items

    async def _scrape_helm(self) -> list[IntelItem]:
        """Scrape HELM benchmark results from Stanford CRFM."""
        items = []
        try:
            soup = await self.fetch_html(self.HELM_URL)
            if not soup:
                return items

            # Extract benchmark results — HELM pages have structured tables
            tables = soup.select("table")
            if tables:
                for table in tables[:3]:
                    caption = table.find("caption")
                    caption_text = caption.get_text(strip=True) if caption else "HELM Benchmark"

                    rows = table.select("tr")
                    row_texts = []
                    for row in rows[:8]:
                        cells = row.find_all(["td", "th"])
                        text = " | ".join(c.get_text(strip=True) for c in cells)
                        if text:
                            row_texts.append(text)

                    if row_texts:
                        items.append(
                            IntelItem(
                                source=self.source_name,
                                title=f"HELM: {caption_text}",
                                url=self.HELM_URL,
                                summary="\n".join(row_texts[:5]),
                                published=datetime.now(),
                                tags=_DEFAULT_TAGS + ["helm", "stanford"],
                            )
                        )
            else:
                # Fallback: grab page summary
                text = soup.get_text(separator=" ", strip=True)[:500]
                if text:
                    items.append(
                        IntelItem(
                            source=self.source_name,
                            title="HELM Benchmark Results",
                            url=self.HELM_URL,
                            summary=text,
                            published=datetime.now(),
                            tags=_DEFAULT_TAGS + ["helm", "stanford"],
                        )
                    )
        except httpx.RequestError as e:
            logger.warning("HELM scrape failed: %s", e)

        return items


# ---------------------------------------------------------------------------
# New capability-grounding scrapers (LLM-based extraction)
# ---------------------------------------------------------------------------

_METR_FIELDS_PROMPT = (
    "Extract published AI evaluation benchmarks and autonomy assessments from this text. "
    "For each item, extract as JSON with fields: "
    "task_category (str), current_success_rate (str), projected_horizon_months (int or null), "
    "eval_date (str YYYY-MM-DD or null)."
)

_EPOCH_FIELDS_PROMPT = (
    "Extract notable AI model training information from this text. "
    "For each item, extract as JSON with fields: "
    "model_name (str), training_compute_flops (str or null), "
    "capability_notes (str), publication_date (str YYYY-MM-DD or null)."
)

_AI_INDEX_FIELDS_PROMPT = (
    "Extract headline AI benchmark and economic impact metrics from this text. "
    "For each item, extract as JSON with fields: "
    "metric_name (str), current_value (str), "
    "year_over_year_change (str or null), report_year (int)."
)

_ARC_EVALS_FIELDS_PROMPT = (
    "Extract frontier model evaluation results from this text. "
    "For each item, extract as JSON with fields: "
    "model_name (str), task_category (str), score (str), eval_date (str YYYY-MM-DD or null)."
)

_GITHUB_FILTER_PROMPT = (
    "Read this GitHub issue. If it is about a bug, dependency conflict, typo, CI failure, "
    "or routine software maintenance, return an empty JSON object {}. "
    "If it discusses a new evaluation benchmark, a new AI capability being tested, "
    "a dataset for frontier models, or a notable limitation or failure mode of a current model, "
    "extract it as JSON with the fields: repo_name (str), capability_tested (str), "
    "evaluation_method (str), significance (str), is_limitation (bool — true if this "
    "describes a failure or limitation rather than a new capability)."
)


class METRScraper(BaseScraper):
    """Scrape METR research and taskdev blog for benchmark/autonomy data."""

    URLS = [
        "https://metr.org/research",
        "https://taskdev.metr.org/blog",
    ]

    def __init__(self, storage: IntelStorage):
        super().__init__(storage)

    @property
    def source_name(self) -> str:
        return IntelSource.METR_EVALS

    async def scrape(self) -> list[IntelItem]:
        items: list[IntelItem] = []
        for url in self.URLS:
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                plain_text = _strip_html_to_text(response.text)
                extracted = _llm_extract_json(plain_text, _METR_FIELDS_PROMPT)
                for entry in extracted:
                    if not entry.get("task_category"):
                        continue
                    items.append(
                        IntelItem(
                            source=self.source_name,
                            title=f"METR: {entry['task_category']}",
                            url=url,
                            summary=json.dumps(entry),
                            published=datetime.now(),
                            tags=["ai-capabilities", "metr", "evals"],
                        )
                    )
            except Exception as e:
                logger.warning("metr_scraper_failed", url=url, error=str(e))
        return items


class EpochAIScraper(BaseScraper):
    """Scrape Epoch AI blog and notable models data."""

    URLS = [
        "https://epochai.org/blog",
        "https://epochai.org/data/notable-ai-models",
    ]

    def __init__(self, storage: IntelStorage):
        super().__init__(storage)

    @property
    def source_name(self) -> str:
        return IntelSource.EPOCH_AI

    async def scrape(self) -> list[IntelItem]:
        items: list[IntelItem] = []
        for url in self.URLS:
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                plain_text = _strip_html_to_text(response.text)
                extracted = _llm_extract_json(plain_text, _EPOCH_FIELDS_PROMPT)
                for entry in extracted:
                    if not entry.get("model_name") and not entry.get("capability_notes"):
                        continue
                    title = entry.get("model_name") or entry.get("capability_notes", "")[:60]
                    items.append(
                        IntelItem(
                            source=self.source_name,
                            title=f"EpochAI: {title}",
                            url=url,
                            summary=json.dumps(entry),
                            published=datetime.now(),
                            tags=["ai-capabilities", "epoch-ai", "compute"],
                        )
                    )
            except Exception as e:
                logger.warning("epoch_ai_scraper_failed", url=url, error=str(e))
        return items


class AIIndexScraper(BaseScraper):
    """Scrape Stanford AI Index report for benchmark and economic metrics."""

    URLS = [
        "https://aiindex.stanford.edu/report/",
    ]

    def __init__(self, storage: IntelStorage):
        super().__init__(storage)

    @property
    def source_name(self) -> str:
        return IntelSource.AI_INDEX

    async def scrape(self) -> list[IntelItem]:
        items: list[IntelItem] = []
        for url in self.URLS:
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                plain_text = _strip_html_to_text(response.text)
                extracted = _llm_extract_json(plain_text, _AI_INDEX_FIELDS_PROMPT)
                for entry in extracted:
                    if not entry.get("metric_name"):
                        continue
                    items.append(
                        IntelItem(
                            source=self.source_name,
                            title=f"AI Index: {entry['metric_name']}",
                            url=url,
                            summary=json.dumps(entry),
                            published=datetime.now(),
                            tags=["ai-capabilities", "ai-index", "stanford"],
                        )
                    )
            except Exception as e:
                logger.warning("ai_index_scraper_failed", url=url, error=str(e))
        return items


class ARCEvalsScraper(BaseScraper):
    """Scrape ARC Evals (Alignment Research Center) evaluation results."""

    URLS = [
        "https://evals.alignment.org",
    ]

    def __init__(self, storage: IntelStorage):
        super().__init__(storage)

    @property
    def source_name(self) -> str:
        return IntelSource.ARC_EVALS

    async def scrape(self) -> list[IntelItem]:
        items: list[IntelItem] = []
        for url in self.URLS:
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                plain_text = _strip_html_to_text(response.text)
                extracted = _llm_extract_json(plain_text, _ARC_EVALS_FIELDS_PROMPT)
                for entry in extracted:
                    if not entry.get("model_name"):
                        continue
                    items.append(
                        IntelItem(
                            source=self.source_name,
                            title=f"ARC Evals: {entry['model_name']}",
                            url=url,
                            summary=json.dumps(entry),
                            published=datetime.now(),
                            tags=["ai-capabilities", "arc-evals", "alignment"],
                        )
                    )
            except Exception as e:
                logger.warning("arc_evals_scraper_failed", url=url, error=str(e))
        return items


class FrontierEvalsGitHubScraper(BaseScraper):
    """Scrape frontier eval repos for capability-relevant issues, LLM-filtered.

    Inherits BaseScraper (not GitHubIssuesScraper) but reuses GitHub API patterns.
    Caps at 20 issues per repo. Filters out maintenance noise via LLM.
    """

    REPOS = [
        "metr/task-standard",
        "EleutherAI/lm-evaluation-harness",
        "openai/evals",
        "anthropics/evals",
    ]
    MAX_PER_REPO = 20

    def __init__(self, storage: IntelStorage, token: Optional[str] = None):
        super().__init__(storage)
        self.set_client_headers(Accept="application/vnd.github.v3+json")
        if token:
            self.set_client_headers(Authorization=f"token {token}")

    @property
    def source_name(self) -> str:
        return IntelSource.FRONTIER_EVALS_GITHUB

    async def scrape(self) -> list[IntelItem]:
        items: list[IntelItem] = []
        for repo in self.REPOS:
            try:
                repo_items = await self._fetch_repo_issues(repo)
                items.extend(repo_items)
            except Exception as e:
                logger.warning("frontier_evals_repo_failed", repo=repo, error=str(e))
        return items

    async def _fetch_repo_issues(self, repo: str) -> list[IntelItem]:
        """Fetch up to MAX_PER_REPO issues, then LLM-filter each."""
        url = f"https://api.github.com/repos/{repo}/issues"
        params = {
            "state": "open",
            "sort": "created",
            "direction": "desc",
            "per_page": self.MAX_PER_REPO,
        }
        try:
            response = await self.client.get(url, params=params)
            if response.status_code == 403:
                logger.warning("github_rate_limited", repo=repo)
                return []
            response.raise_for_status()
            issues = response.json()
        except Exception as e:
            logger.warning("frontier_evals_fetch_failed", repo=repo, error=str(e))
            return []

        items: list[IntelItem] = []
        for issue in issues[: self.MAX_PER_REPO]:
            title = issue.get("title", "")
            body = (issue.get("body") or "")[:1000]
            issue_text = f"Title: {title}\nBody: {body}"

            # LLM filter
            extracted = _llm_extract_single(issue_text, _GITHUB_FILTER_PROMPT)
            if not extracted or not extracted.get("capability_tested"):
                continue

            published = None
            if issue.get("created_at"):
                try:
                    published = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            items.append(
                IntelItem(
                    source=self.source_name,
                    title=f"[{repo}] {title[:80]}",
                    url=issue.get("html_url", ""),
                    summary=json.dumps(extracted),
                    published=published,
                    tags=[
                        "ai-capabilities",
                        "frontier-evals",
                        repo.split("/")[0],
                        *(["limitation"] if extracted.get("is_limitation") else []),
                    ],
                )
            )
        return items

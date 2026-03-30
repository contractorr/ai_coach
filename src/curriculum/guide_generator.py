"""LLM-driven generation of user-authored curriculum guides."""

from __future__ import annotations

import inspect
import json
import shutil
from datetime import datetime
from pathlib import Path

from llm.base import LLMError, LLMProvider

from .content_schema import load_curriculum_document
from .models import DifficultyLevel, GuideCategory, GuideDepth, GuideKind
from .user_content import build_user_guide_id, write_guide_metadata

_PLAN_PROMPT = """Create a structured learning guide plan.

Topic: {topic}
Depth: {depth}
Audience: {audience}
Time budget: {time_budget}
Additional instruction: {instruction}
Mode: {mode}
{base_context}

Return JSON only with this shape:
{{
  "title": "string",
  "category": "science|humanities|business|technology|industry|social_science|professional",
  "difficulty": "introductory|intermediate|advanced",
  "chapters": [
    {{
      "title": "string",
      "summary": "string",
      "objectives": ["string"],
      "checkpoints": ["string"]
    }}
  ]
}}

Requirements:
- Choose 3 to {max_chapters} chapters.
- Keep the guide coherent for the stated audience and time budget.
- For extension mode, focus on supplemental material that expands the source guide instead of repeating it.
"""

_CHAPTER_PROMPT = """Write a curriculum chapter as MDX with YAML frontmatter.

Guide title: {guide_title}
Guide topic: {topic}
Mode: {mode}
Audience: {audience}
Depth: {depth}
Time budget: {time_budget}
Additional instruction: {instruction}
{base_context}

Chapter title: {chapter_title}
Chapter summary: {chapter_summary}
Objectives:
{objectives}

Checkpoints:
{checkpoints}

Output requirements:
- Output only the chapter file content.
- Start with YAML frontmatter containing:
  title
  summary
  objectives
  checkpoints
  content_format: markdown
  schema_version: 1
- Then include a markdown body with:
  - an H1 title
  - an overview section
  - 3 to 5 content sections
  - a short "In Practice" or "Why This Matters" section when useful
  - a checkpoint section near the end
- Make the chapter detailed enough to study from directly.
"""


class GuideGenerationService:
    """Generate and validate user-authored curriculum guides."""

    def __init__(
        self,
        *,
        llm_provider: LLMProvider,
        output_root: Path,
        owner_user_id: str,
        max_chapters: int = 6,
    ):
        self.llm = llm_provider
        self.output_root = Path(output_root)
        self.owner_user_id = owner_user_id
        self.max_chapters = max(1, max_chapters)

    async def generate_guide(
        self,
        *,
        topic: str,
        depth: GuideDepth,
        audience: str,
        time_budget: str,
        instruction: str | None = None,
    ) -> dict:
        return await self._generate(
            topic=topic,
            depth=depth,
            audience=audience,
            time_budget=time_budget,
            instruction=instruction,
            mode="standalone",
            kind=GuideKind.STANDALONE,
            base_guide=None,
        )

    async def extend_guide(
        self,
        *,
        source_guide: dict,
        prompt: str,
        depth: GuideDepth | None = None,
        audience: str | None = None,
        time_budget: str | None = None,
        instruction: str | None = None,
    ) -> dict:
        extension_topic = f"{source_guide['title']}: {prompt}"
        return await self._generate(
            topic=extension_topic,
            depth=depth or GuideDepth.PRACTITIONER,
            audience=audience or "A learner who has completed or is studying the source guide",
            time_budget=time_budget or "2-4 focused sessions",
            instruction=instruction,
            mode="extension",
            kind=GuideKind.EXTENSION,
            base_guide=source_guide,
        )

    async def _generate(
        self,
        *,
        topic: str,
        depth: GuideDepth,
        audience: str,
        time_budget: str,
        instruction: str | None,
        mode: str,
        kind: GuideKind,
        base_guide: dict | None,
    ) -> dict:
        self.output_root.mkdir(parents=True, exist_ok=True)
        plan = await self._plan_guide(
            topic=topic,
            depth=depth,
            audience=audience,
            time_budget=time_budget,
            instruction=instruction,
            mode=mode,
            base_guide=base_guide,
        )

        guide_title = str(plan.get("title") or topic).strip()
        guide_id = build_user_guide_id(guide_title, kind=kind.value)
        temp_dir = self.output_root / f".tmp-{guide_id}"
        final_dir = self.output_root / guide_id

        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            write_guide_metadata(
                temp_dir,
                {
                    "title": guide_title,
                    "summary": str(plan.get("summary") or "").strip(),
                    "origin": "user",
                    "kind": kind.value,
                    "owner_user_id": self.owner_user_id,
                    "base_guide_id": base_guide["id"] if base_guide else None,
                    "category": self._coerce_category(plan.get("category")).value,
                    "difficulty": self._coerce_difficulty(plan.get("difficulty")).value,
                    "topic_prompt": topic,
                    "depth": depth.value,
                    "audience": audience,
                    "time_budget": time_budget,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )

            chapters = self._normalize_chapters(plan.get("chapters"))
            for index, chapter in enumerate(chapters, start=1):
                chapter_content = await self._write_chapter(
                    temp_dir=temp_dir,
                    chapter=chapter,
                    order=index,
                    guide_title=guide_title,
                    topic=topic,
                    depth=depth,
                    audience=audience,
                    time_budget=time_budget,
                    instruction=instruction,
                    mode=mode,
                    base_guide=base_guide,
                )
                load_curriculum_document(chapter_content)

            temp_dir.rename(final_dir)
            return {
                "guide_id": guide_id,
                "title": guide_title,
                "kind": kind.value,
                "base_guide_id": base_guide["id"] if base_guide else None,
            }
        except Exception:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    async def _plan_guide(
        self,
        *,
        topic: str,
        depth: GuideDepth,
        audience: str,
        time_budget: str,
        instruction: str | None,
        mode: str,
        base_guide: dict | None,
    ) -> dict:
        base_context = ""
        if base_guide:
            base_context = (
                f"Source guide title: {base_guide['title']}\nSource guide id: {base_guide['id']}\n"
            )
        prompt = _PLAN_PROMPT.format(
            topic=topic,
            depth=depth.value,
            audience=audience,
            time_budget=time_budget,
            instruction=instruction or "None",
            mode=mode,
            base_context=base_context,
            max_chapters=self.max_chapters,
        )
        response = await self._generate_text(prompt)
        data = self._parse_json_object(response)
        if not isinstance(data, dict):
            raise LLMError("Guide planner returned invalid JSON")
        return data

    async def _write_chapter(
        self,
        *,
        temp_dir: Path,
        chapter: dict,
        order: int,
        guide_title: str,
        topic: str,
        depth: GuideDepth,
        audience: str,
        time_budget: str,
        instruction: str | None,
        mode: str,
        base_guide: dict | None,
    ) -> Path:
        objectives = "\n".join(f"- {item}" for item in chapter["objectives"])
        checkpoints = "\n".join(f"- {item}" for item in chapter["checkpoints"])
        base_context = ""
        if base_guide:
            base_context = (
                f"Source guide title: {base_guide['title']}\n"
                f"Source guide purpose: This chapter should extend that guide with additional material.\n"
            )

        prompt = _CHAPTER_PROMPT.format(
            guide_title=guide_title,
            topic=topic,
            mode=mode,
            audience=audience,
            depth=depth.value,
            time_budget=time_budget,
            instruction=instruction or "None",
            base_context=base_context,
            chapter_title=chapter["title"],
            chapter_summary=chapter["summary"],
            objectives=objectives,
            checkpoints=checkpoints,
        )
        content = await self._generate_text(prompt)
        filename = f"{order:02d}-{self._slugify(chapter['title'])}.mdx"
        chapter_path = temp_dir / filename
        chapter_path.write_text(content.strip() + "\n", encoding="utf-8")
        return chapter_path

    async def _generate_text(self, prompt: str) -> str:
        result = self.llm.generate([{"role": "user", "content": prompt}], max_tokens=4000)
        if inspect.isawaitable(result):
            result = await result
        if not isinstance(result, str) or not result.strip():
            raise LLMError("Guide generation returned empty output")
        return result

    @staticmethod
    def _parse_json_object(text: str) -> object:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped[3:]
            if stripped.endswith("```"):
                stripped = stripped[:-3]
        stripped = stripped.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            start = min(
                [idx for idx in (stripped.find("{"), stripped.find("[")) if idx != -1],
                default=-1,
            )
            end = max(stripped.rfind("}"), stripped.rfind("]"))
            if start != -1 and end != -1 and end > start:
                return json.loads(stripped[start : end + 1])
            raise

    @staticmethod
    def _normalize_chapters(raw: object) -> list[dict]:
        if not isinstance(raw, list):
            raise LLMError("Guide planner returned no chapters")
        chapters: list[dict] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            summary = str(item.get("summary") or "").strip()
            objectives = [str(x).strip() for x in item.get("objectives", []) if str(x).strip()]
            checkpoints = [str(x).strip() for x in item.get("checkpoints", []) if str(x).strip()]
            if not title:
                continue
            chapters.append(
                {
                    "title": title,
                    "summary": summary or f"Study the core ideas in {title}.",
                    "objectives": objectives[:5] or [f"Understand the key ideas in {title}."],
                    "checkpoints": checkpoints[:5]
                    or [f"Explain the practical implications of {title}."],
                }
            )
        if not chapters:
            raise LLMError("Guide planner returned no valid chapters")
        return chapters

    @staticmethod
    def _coerce_category(raw: object) -> GuideCategory:
        if isinstance(raw, str):
            try:
                return GuideCategory(raw)
            except ValueError:
                pass
        return GuideCategory.PROFESSIONAL

    @staticmethod
    def _coerce_difficulty(raw: object) -> DifficultyLevel:
        if isinstance(raw, str):
            try:
                return DifficultyLevel(raw)
            except ValueError:
                pass
        return DifficultyLevel.INTERMEDIATE

    @staticmethod
    def _slugify(value: str) -> str:
        chars = [c.lower() if c.isalnum() else "-" for c in value]
        slug = "".join(chars).strip("-")
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug or "chapter"

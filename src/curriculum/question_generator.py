"""LLM-powered question generation and answer grading for curriculum."""

import json
import uuid
from datetime import datetime

import structlog

from .models import BloomLevel, ReviewGradeResult, ReviewItem, ReviewItemType

logger = structlog.get_logger()

_BLOOM_DESCRIPTIONS = {
    BloomLevel.REMEMBER: "factual recall — who, what, when, where, define",
    BloomLevel.UNDERSTAND: "explain concepts in own words, summarize, compare",
    BloomLevel.APPLY: "use knowledge in a new situation, solve a problem",
    BloomLevel.ANALYZE: "break down, identify patterns, distinguish cause/effect",
    BloomLevel.EVALUATE: "judge, critique, defend a position with reasoning",
    BloomLevel.CREATE: "synthesize, design, propose something new",
}

_GENERATION_PROMPT = """Generate {count} study questions for the following chapter content.

Chapter: {chapter_title}
Guide: {guide_title}

Bloom's taxonomy levels requested: {bloom_levels}

Content:
{content}

For each question, output JSON array of objects with fields:
- "question": the question text
- "expected_answer": a concise model answer (2-4 sentences)
- "bloom_level": one of {bloom_values}

{extra_instructions}

Output ONLY valid JSON array, no other text."""

_CROSS_DOMAIN_PROMPT = """Generate 1 cross-domain synthesis question connecting these two topics:

Topic A ({guide_a}): {summary_a}
Topic B ({guide_b}): {summary_b}

The question should require integrating knowledge from BOTH domains.
Bloom's level: EVALUATE or CREATE.

Output JSON object with fields: "question", "expected_answer", "bloom_level"

Output ONLY valid JSON, no other text."""

_TEACHBACK_CONCEPT_PROMPT = """Identify the single most important concept from this chapter.

Chapter: {chapter_title}
Guide: {guide_title}

Content:
{content}

Output JSON with fields:
- "concept": a concise name for the concept (3-8 words)
- "description": a brief description of the concept (2-3 sentences)

Output ONLY valid JSON, no other text."""

_TEACHBACK_GRADING_PROMPT = """Grade this teach-back explanation of a concept.

Concept: {concept}
Expected understanding: {expected_answer}
Chapter: {chapter_title} (from {guide_title})
Student explanation: {student_answer}

Evaluate on three dimensions (0-5 each):
- Accuracy: Are the facts and relationships correct?
- Completeness: Are the key aspects covered?
- Clarity: Would someone with no background understand this?

Also provide an overall grade (0-5):
0 = no relevant content
1 = mostly incorrect
2 = partially correct, major gaps
3 = correct but incomplete or unclear
4 = correct, complete, and mostly clear
5 = excellent — accurate, complete, and crystal clear

Output JSON with fields:
- "grade": integer 0-5 (overall)
- "accuracy": integer 0-5
- "completeness": integer 0-5
- "clarity": integer 0-5
- "feedback": brief constructive feedback (1-2 sentences)
- "correct_points": array of things explained well
- "missing_points": array of things missed or unclear

Output ONLY valid JSON, no other text."""

_GRADING_PROMPT = """Grade this answer to a study question.

Question: {question}
Expected answer: {expected_answer}
Bloom's level: {bloom_level} ({bloom_description})
Student answer: {student_answer}

Evaluate on a 0-5 scale:
0 = no relevant content
1 = mostly incorrect
2 = partially correct, major gaps
3 = correct but incomplete
4 = correct and well-explained
5 = excellent, shows deep understanding

Output JSON with fields:
- "grade": integer 0-5
- "feedback": brief constructive feedback (1-2 sentences)
- "correct_points": array of things the student got right
- "missing_points": array of things the student missed

Output ONLY valid JSON, no other text."""


class QuestionGenerator:
    """Generate questions and grade answers using LLM."""

    def __init__(self, llm_provider=None, cheap_llm_provider=None):
        self.llm = llm_provider
        self.cheap_llm = cheap_llm_provider or llm_provider

    async def generate_questions(
        self,
        content: str,
        chapter_title: str,
        guide_title: str,
        bloom_levels: list[BloomLevel] | None = None,
        count: int = 5,
        content_hash: str = "",
        chapter_id: str = "",
        guide_id: str = "",
        user_id: str = "",
        include_pre_reading: bool = False,
        pre_reading_count: int = 3,
    ) -> list[ReviewItem]:
        """Generate review questions for a chapter.

        When include_pre_reading=True, also generates pre-reading priming
        questions that are stored as ReviewItems with item_type=PRE_READING.
        """
        if not self.cheap_llm:
            logger.warning("curriculum.questions.no_llm")
            return []

        if bloom_levels is None:
            bloom_levels = [
                BloomLevel.REMEMBER,
                BloomLevel.REMEMBER,
                BloomLevel.REMEMBER,
                BloomLevel.UNDERSTAND,
                BloomLevel.UNDERSTAND,
            ]

        bloom_str = ", ".join(f"{bl.value} ({_BLOOM_DESCRIPTIONS[bl]})" for bl in set(bloom_levels))
        bloom_vals = ", ".join(f'"{bl.value}"' for bl in set(bloom_levels))

        # Truncate content to ~4000 words for LLM context
        words = content.split()
        if len(words) > 4000:
            content = " ".join(words[:4000]) + "\n...[truncated]"

        extra = ""
        if include_pre_reading:
            extra = (
                f'Additionally, generate {pre_reading_count} pre-reading "priming" questions that:\n'
                "- Cannot be answered without reading the chapter\n"
                "- Direct attention to the most important concepts\n"
                "- Spark curiosity\n"
                'Mark these with "pre_reading": true in the JSON output.\n'
                "Pre-reading questions do NOT need expected_answer or bloom_level fields."
            )

        prompt = _GENERATION_PROMPT.format(
            count=count,
            chapter_title=chapter_title,
            guide_title=guide_title,
            bloom_levels=bloom_str,
            bloom_values=bloom_vals,
            content=content,
            extra_instructions=extra,
        )

        try:
            response = await self.cheap_llm.generate(prompt)
            questions = self._parse_questions(response)
        except Exception:
            logger.exception("curriculum.questions.generation_failed")
            return []

        items = []
        now = datetime.utcnow()
        quiz_count = 0
        for q in questions:
            is_pre_reading = q.get("pre_reading", False)

            if is_pre_reading:
                items.append(
                    ReviewItem(
                        id=uuid.uuid4().hex[:16],
                        user_id=user_id,
                        chapter_id=chapter_id,
                        guide_id=guide_id,
                        question=q.get("question", ""),
                        expected_answer="",
                        bloom_level=BloomLevel.REMEMBER,
                        item_type=ReviewItemType.PRE_READING,
                        content_hash=content_hash,
                        next_review=None,
                        created_at=now,
                    )
                )
            else:
                if quiz_count >= count:
                    continue
                bloom = q.get("bloom_level", "remember")
                try:
                    bloom_enum = BloomLevel(bloom)
                except ValueError:
                    bloom_enum = BloomLevel.REMEMBER

                items.append(
                    ReviewItem(
                        id=uuid.uuid4().hex[:16],
                        user_id=user_id,
                        chapter_id=chapter_id,
                        guide_id=guide_id,
                        question=q.get("question", ""),
                        expected_answer=q.get("expected_answer", ""),
                        bloom_level=bloom_enum,
                        item_type=ReviewItemType.QUIZ,
                        content_hash=content_hash,
                        next_review=now,
                        created_at=now,
                    )
                )
                quiz_count += 1
        return items

    async def grade_answer(
        self,
        question: str,
        expected_answer: str,
        student_answer: str,
        bloom_level: BloomLevel,
    ) -> ReviewGradeResult:
        """Grade a student answer."""
        # REMEMBER level: keyword matching (no LLM needed)
        if bloom_level == BloomLevel.REMEMBER:
            return self._keyword_grade(expected_answer, student_answer)

        provider = self.cheap_llm
        # Use expensive LLM for higher-order questions
        if bloom_level in (BloomLevel.EVALUATE, BloomLevel.CREATE) and self.llm:
            provider = self.llm

        if not provider:
            return self._keyword_grade(expected_answer, student_answer)

        prompt = _GRADING_PROMPT.format(
            question=question,
            expected_answer=expected_answer,
            bloom_level=bloom_level.value,
            bloom_description=_BLOOM_DESCRIPTIONS[bloom_level],
            student_answer=student_answer,
        )

        try:
            response = await provider.generate(prompt)
            return self._parse_grade(response)
        except Exception:
            logger.exception("curriculum.grading.failed")
            return self._keyword_grade(expected_answer, student_answer)

    async def generate_teachback(
        self,
        content: str,
        chapter_title: str,
        guide_title: str,
        content_hash: str = "",
        chapter_id: str = "",
        guide_id: str = "",
        user_id: str = "",
    ) -> ReviewItem | None:
        """Generate a teach-back prompt for a completed chapter."""
        if not self.cheap_llm:
            logger.warning("curriculum.teachback.no_llm")
            return None

        words = content.split()
        if len(words) > 4000:
            content = " ".join(words[:4000]) + "\n...[truncated]"

        prompt = _TEACHBACK_CONCEPT_PROMPT.format(
            chapter_title=chapter_title,
            guide_title=guide_title,
            content=content,
        )

        try:
            response = await self.cheap_llm.generate(prompt)
            data = json.loads(self._strip_code_fences(response))
            concept = data.get("concept", "")
            description = data.get("description", "")
            if not concept:
                return None
        except Exception:
            logger.exception("curriculum.teachback.generation_failed")
            return None

        now = datetime.utcnow()
        return ReviewItem(
            id=uuid.uuid4().hex[:16],
            user_id=user_id,
            chapter_id=chapter_id,
            guide_id=guide_id,
            question=f"Explain {concept} as if teaching someone with no background",
            expected_answer=description,
            bloom_level=BloomLevel.CREATE,
            item_type=ReviewItemType.TEACHBACK,
            content_hash=content_hash,
            next_review=now,
            created_at=now,
        )

    async def grade_teachback(
        self,
        concept: str,
        expected_answer: str,
        student_answer: str,
        chapter_title: str,
        guide_title: str,
    ) -> ReviewGradeResult:
        """Grade a teach-back response with 3-dimension rubric."""
        provider = self.llm or self.cheap_llm
        if not provider:
            return self._keyword_grade(expected_answer, student_answer)

        prompt = _TEACHBACK_GRADING_PROMPT.format(
            concept=concept,
            expected_answer=expected_answer,
            chapter_title=chapter_title,
            guide_title=guide_title,
            student_answer=student_answer,
        )

        try:
            response = await provider.generate(prompt)
            return self._parse_grade(response)
        except Exception:
            logger.exception("curriculum.teachback.grading_failed")
            return self._keyword_grade(expected_answer, student_answer)

    def _strip_code_fences(self, text: str) -> str:
        """Strip markdown code fences from LLM response."""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _keyword_grade(self, expected: str, student: str) -> ReviewGradeResult:
        """Simple keyword overlap grading."""
        expected_words = set(expected.lower().split())
        student_words = set(student.lower().split())
        # Remove common stop words
        stop = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "in",
            "on",
            "at",
            "to",
            "of",
            "and",
            "or",
            "for",
        }
        expected_kw = expected_words - stop
        student_kw = student_words - stop

        if not expected_kw:
            return ReviewGradeResult(grade=3, feedback="Unable to evaluate automatically.")

        overlap = expected_kw & student_kw
        ratio = len(overlap) / len(expected_kw)

        if ratio >= 0.7:
            grade = 5
        elif ratio >= 0.5:
            grade = 4
        elif ratio >= 0.3:
            grade = 3
        elif ratio >= 0.15:
            grade = 2
        elif ratio > 0:
            grade = 1
        else:
            grade = 0

        missing = expected_kw - student_kw
        return ReviewGradeResult(
            grade=grade,
            feedback=f"Keyword match: {len(overlap)}/{len(expected_kw)} key terms.",
            correct_points=sorted(overlap)[:5],
            missing_points=sorted(missing)[:5],
        )

    def _parse_questions(self, response: str) -> list[dict]:
        """Parse LLM response into question dicts."""
        text = self._strip_code_fences(response)

        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "questions" in data:
                return data["questions"]
            return [data]
        except json.JSONDecodeError:
            logger.warning("curriculum.questions.parse_failed", text=text[:200])
            return []

    def _parse_grade(self, response: str) -> ReviewGradeResult:
        """Parse LLM grading response."""
        text = self._strip_code_fences(response)

        try:
            data = json.loads(text)
            return ReviewGradeResult(
                grade=max(0, min(5, int(data.get("grade", 0)))),
                feedback=data.get("feedback", ""),
                correct_points=data.get("correct_points", []),
                missing_points=data.get("missing_points", []),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning("curriculum.grading.parse_failed", text=text[:200])
            return ReviewGradeResult(grade=0, feedback="Could not parse grading response.")

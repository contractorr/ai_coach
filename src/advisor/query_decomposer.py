"""Split complex questions into searchable sub-questions."""

from __future__ import annotations

import json

from llm.base import LLMProvider


class QueryDecomposer:
    """Use a cheap model to break a query into smaller retrieval units."""

    def __init__(self, llm: LLMProvider, max_sub_questions: int = 4):
        self.llm = llm
        self.max_sub_questions = max_sub_questions

    async def decompose(self, query: str) -> list[str]:
        prompt = (
            f"Split this question into 2-{self.max_sub_questions} independent sub-questions that "
            "together cover the full scope. Each sub-question should be self-contained and searchable.\n\n"
            f"Question: {query}\n\nReturn JSON array of strings. No explanations."
        )
        try:
            response = self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                system="You decompose retrieval questions.",
                max_tokens=400,
            )
            parts = json.loads(response)
            if not isinstance(parts, list) or not parts:
                return [query]
            deduped = []
            seen = set()
            for part in parts:
                if not isinstance(part, str):
                    continue
                normalized = part.strip()
                if not normalized:
                    continue
                lowered = normalized.lower()
                if lowered in seen:
                    continue
                seen.add(lowered)
                deduped.append(normalized)
                if len(deduped) >= self.max_sub_questions:
                    break
            return deduped or [query]
        except Exception:
            return [query]

"""LLM council orchestration for high-stakes advice prompts."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable

import structlog

from llm import LLMError as BaseLLMError
from llm import create_llm_provider

from .prompts import PromptTemplates

logger = structlog.get_logger()


@dataclass
class CouncilMember:
    provider: str
    api_key: str
    model: str | None = None


@dataclass
class CouncilMemberResponse:
    provider: str
    content: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return bool(self.content) and not self.error


@dataclass
class CouncilResult:
    answer: str
    used: bool = False
    providers: list[str] = field(default_factory=list)
    failed_providers: list[str] = field(default_factory=list)
    partial: bool = False
    member_responses: list[CouncilMemberResponse] = field(default_factory=list)


def is_council_eligible(
    question: str,
    advice_type: str = "general",
) -> bool:
    """Heuristic gate for important or open-ended prompts in v1."""
    normalized = (question or "").strip().lower()
    if not normalized:
        return False

    if advice_type in {"career", "goals", "opportunities", "skill_gap"}:
        return True

    low_risk_prefixes = (
        "rewrite",
        "rephrase",
        "fix grammar",
        "summarize",
        "what is",
        "who is",
        "when is",
        "where is",
        "define",
    )
    if normalized.startswith(low_risk_prefixes):
        return False

    strategy_markers = (
        "should i",
        "help me decide",
        "best path",
        "path forward",
        "tradeoff",
        "trade-off",
        "strategy",
        "strategic",
        "roadmap",
        "prioritize",
        "career move",
        "next move",
        "important",
        "plan",
        "compare",
        "which option",
        "big decision",
    )
    return len(normalized) >= 120 or any(marker in normalized for marker in strategy_markers)


class CouncilOrchestrator:
    """Runs independent provider calls and synthesizes them into one answer."""

    def __init__(
        self,
        members: list[CouncilMember],
        lead_provider: str | None = None,
        provider_factory: Callable[..., object] = create_llm_provider,
    ):
        self.members = members
        self.lead_provider = lead_provider
        self.provider_factory = provider_factory

    def _invoke_member(
        self,
        member: CouncilMember,
        *,
        system: str,
        user_prompt: str,
        conversation_history: list[dict] | None,
        max_tokens: int,
    ) -> CouncilMemberResponse:
        try:
            provider = self.provider_factory(
                provider=member.provider,
                api_key=member.api_key,
                model=member.model,
            )
            messages = list(conversation_history or [])
            messages.append(
                {
                    "role": "user",
                    "content": PromptTemplates.build_council_member_prompt(user_prompt),
                }
            )
            content = provider.generate(
                messages=messages,
                system=PromptTemplates.build_council_member_system(system),
                max_tokens=max_tokens,
            )
            return CouncilMemberResponse(provider=member.provider, content=content)
        except Exception as exc:
            logger.warning(
                "advisor.council.member_failed",
                provider=member.provider,
                error=str(exc),
            )
            return CouncilMemberResponse(provider=member.provider, error=str(exc))

    def _select_synthesis_member(
        self,
        successful: list[CouncilMemberResponse],
    ) -> CouncilMemberResponse:
        if self.lead_provider:
            for response in successful:
                if response.provider == self.lead_provider:
                    return response
        return successful[0]

    def _fallback_answer(
        self,
        success: CouncilMemberResponse,
        failed_providers: list[str],
    ) -> str:
        note = ""
        if failed_providers:
            failed = ", ".join(failed_providers)
            note = (
                "Note: I attempted a multi-model council, but fewer voices were available "
                f"than expected ({failed}). Here's the best single-provider answer I could produce.\n\n"
            )
        return note + (success.content or "")

    def _synthesize(
        self,
        *,
        system: str,
        original_prompt: str,
        successful: list[CouncilMemberResponse],
        failed_providers: list[str],
        max_tokens: int,
    ) -> str:
        lead = self._select_synthesis_member(successful)
        lead_member = next(member for member in self.members if member.provider == lead.provider)
        synthesizer = self.provider_factory(
            provider=lead_member.provider,
            api_key=lead_member.api_key,
            model=lead_member.model,
        )
        synthesis_prompt = PromptTemplates.build_council_synthesis_prompt(
            original_prompt=original_prompt,
            member_responses=[
                {"provider": response.provider, "content": response.content or ""}
                for response in successful
            ],
            failed_providers=failed_providers,
        )
        return synthesizer.generate(
            messages=[{"role": "user", "content": synthesis_prompt}],
            system=PromptTemplates.build_council_synthesis_system(system),
            max_tokens=max_tokens,
        )

    def run(
        self,
        *,
        system: str,
        user_prompt: str,
        conversation_history: list[dict] | None = None,
        max_tokens: int = 2200,
    ) -> CouncilResult:
        if len(self.members) < 2:
            raise BaseLLMError("Council requires at least two configured providers")

        responses: list[CouncilMemberResponse] = []
        with ThreadPoolExecutor(max_workers=len(self.members)) as executor:
            future_map = {
                executor.submit(
                    self._invoke_member,
                    member,
                    system=system,
                    user_prompt=user_prompt,
                    conversation_history=conversation_history,
                    max_tokens=max_tokens,
                ): member.provider
                for member in self.members
            }
            for future in as_completed(future_map):
                responses.append(future.result())

        successful = [response for response in responses if response.ok]
        failed_providers = [response.provider for response in responses if not response.ok]

        if not successful:
            errors = ", ".join(failed_providers) or "all providers"
            raise BaseLLMError(f"Council failed across {errors}")

        if len(successful) == 1:
            return CouncilResult(
                answer=self._fallback_answer(successful[0], failed_providers),
                used=False,
                providers=[successful[0].provider],
                failed_providers=failed_providers,
                partial=bool(failed_providers),
                member_responses=responses,
            )

        answer = self._synthesize(
            system=system,
            original_prompt=user_prompt,
            successful=successful,
            failed_providers=failed_providers,
            max_tokens=max_tokens,
        )
        return CouncilResult(
            answer=answer,
            used=True,
            providers=[response.provider for response in successful],
            failed_providers=failed_providers,
            partial=bool(failed_providers),
            member_responses=responses,
        )

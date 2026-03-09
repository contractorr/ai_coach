"""Tests for council orchestration."""

from advisor.council import CouncilMember, CouncilOrchestrator


class _FakeProvider:
    def __init__(self, provider_name, calls, failing=None):
        self.provider_name = provider_name
        self.calls = calls
        self.failing = set(failing or [])

    def generate(self, messages, system=None, max_tokens=2000, use_thinking=False):
        self.calls.append((self.provider_name, messages[-1]["content"], system))
        if self.provider_name in self.failing:
            raise RuntimeError(f"{self.provider_name} boom")
        prompt = messages[-1]["content"]
        if "COUNCIL RESPONSES:" in prompt:
            return "Final synthesized answer"
        return f"Independent answer from {self.provider_name}"


def test_council_invokes_each_member_and_synthesizes():
    calls = []

    def factory(provider, api_key=None, model=None, client=None, extended_thinking=False):
        return _FakeProvider(provider, calls)

    orchestrator = CouncilOrchestrator(
        members=[
            CouncilMember(provider="claude", api_key="k1"),
            CouncilMember(provider="openai", api_key="k2"),
            CouncilMember(provider="gemini", api_key="k3"),
        ],
        lead_provider="openai",
        provider_factory=factory,
    )

    result = orchestrator.run(system="base system", user_prompt="Important strategic prompt")

    assert result.used is True
    assert result.answer == "Final synthesized answer"
    assert set(result.providers) == {"claude", "openai", "gemini"}
    assert result.failed_providers == []
    assert len(calls) == 4


def test_council_falls_back_to_single_answer_when_only_one_member_succeeds():
    calls = []

    def factory(provider, api_key=None, model=None, client=None, extended_thinking=False):
        return _FakeProvider(provider, calls, failing={"openai"})

    orchestrator = CouncilOrchestrator(
        members=[
            CouncilMember(provider="claude", api_key="k1"),
            CouncilMember(provider="openai", api_key="k2"),
        ],
        lead_provider="claude",
        provider_factory=factory,
    )

    result = orchestrator.run(system="base system", user_prompt="Help me decide what to do")

    assert result.used is False
    assert result.partial is True
    assert result.providers == ["claude"]
    assert result.failed_providers == ["openai"]
    assert "fewer voices were available" in result.answer.lower()

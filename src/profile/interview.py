"""LLM-driven adaptive profile interview."""

import json
import re

import structlog

from .storage import ProfileStorage, Skill, UserProfile

logger = structlog.get_logger()

INTERVIEW_SYSTEM = """You are a career coach conducting a quick profile interview. Ask one clear question at a time.
Your job is to gather enough info to build a professional profile.

You need to learn:
1. Current role and career stage (junior/mid/senior/lead/exec)
2. Technical skills and proficiency levels (1-5 scale)
3. Programming languages and frameworks used
4. Professional interests and passions
5. Career aspirations and goals
6. Location (city/country)
7. Preferred learning style (visual/reading/hands-on/mixed)
8. Weekly hours available for professional development

Sound like a real person — casual, direct, no corporate tone. Keep questions short.
Adapt based on previous answers. Don't repeat what they already told you.
After gathering enough info (5-7 questions), output EXACTLY this JSON block:

```json
{"done": true, "profile": {
  "current_role": "...",
  "career_stage": "junior|mid|senior|lead|exec",
  "skills": [{"name": "...", "proficiency": 1-5}, ...],
  "languages_frameworks": ["python", "react", ...],
  "interests": ["...", ...],
  "aspirations": "...",
  "location": "...",
  "learning_style": "visual|reading|hands-on|mixed",
  "weekly_hours_available": N
}}
```"""

INTERVIEW_START = """Start the profile interview. Ask your first question to understand
who this person is professionally. Keep it casual and short — one question only."""


class ProfileInterviewError(Exception):
    """Raised when the interview cannot continue safely."""


class ProfileInterviewAborted(ProfileInterviewError):
    """Raised when the user aborts the interview input stream."""


def _extract_profile_json(text: str) -> dict | None:
    """Extract profile JSON from LLM response."""
    # Try ```json block first
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if data.get("done") and "profile" in data:
                return data["profile"]
        except json.JSONDecodeError:
            pass

    # Try bare JSON
    match = re.search(r'\{"done"\s*:\s*true.*?"profile"\s*:\s*\{.*\}\s*\}', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if "profile" in data:
                return data["profile"]
        except json.JSONDecodeError:
            pass

    return None


def _build_profile(data: dict) -> UserProfile:
    """Build UserProfile from extracted JSON."""
    skills = []
    for s in data.get("skills", []):
        if isinstance(s, dict) and "name" in s:
            try:
                prof = max(1, min(5, int(s.get("proficiency", 3))))
            except (TypeError, ValueError):
                prof = 3
            skills.append(Skill(name=s["name"], proficiency=prof))

    stage = data.get("career_stage", "mid")
    valid_stages = {"junior", "mid", "senior", "lead", "exec"}
    if stage not in valid_stages:
        stage = "mid"

    style = data.get("learning_style", "mixed")
    if style not in {"visual", "reading", "hands-on", "mixed"}:
        style = "mixed"

    hours = data.get("weekly_hours_available", 5)
    try:
        hours = max(1, min(40, int(hours)))
    except (ValueError, TypeError):
        hours = 5

    # Normalize list fields
    def _as_list(val) -> list[str]:
        if isinstance(val, list):
            return [str(v) for v in val]
        if isinstance(val, str) and val:
            return [v.strip() for v in val.split(",") if v.strip()]
        return []

    constraints = data.get("constraints", {})
    if not isinstance(constraints, dict):
        constraints = {}

    return UserProfile(
        skills=skills,
        interests=_as_list(data.get("interests")),
        career_stage=stage,
        current_role=data.get("current_role", ""),
        aspirations=data.get("aspirations", ""),
        location=data.get("location", ""),
        languages_frameworks=_as_list(data.get("languages_frameworks")),
        learning_style=style,
        weekly_hours_available=hours,
        goals_short_term=data.get("goals_short_term", ""),
        goals_long_term=data.get("goals_long_term", ""),
        industries_watching=_as_list(data.get("industries_watching")),
        technologies_watching=_as_list(data.get("technologies_watching")),
        constraints=constraints,
        fears_risks=_as_list(data.get("fears_risks")),
        active_projects=_as_list(data.get("active_projects")),
    )


class ProfileInterviewer:
    """Conducts adaptive profile interview via LLM."""

    def __init__(self, llm_caller, storage: ProfileStorage):
        self.llm_caller = llm_caller
        self.storage = storage

    def _call_llm(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        try:
            return self.llm_caller(system_prompt, user_prompt, **kwargs)
        except Exception as exc:
            raise ProfileInterviewError(f"Interview LLM call failed: {exc}") from exc

    def _save_profile(self, profile: UserProfile) -> None:
        try:
            self.storage.save(profile)
        except Exception as exc:
            raise ProfileInterviewError(f"Profile save failed: {exc}") from exc

    def run_interactive(self, input_fn=None, output_fn=None) -> UserProfile:
        """Run interactive interview loop. Returns completed profile.

        Args:
            input_fn: Callable to get user input (default: built-in input)
            output_fn: Callable to display text (default: print)
        """
        input_fn = input_fn or input
        output_fn = output_fn or print

        conversation = []

        # Get first question
        response = self._call_llm(INTERVIEW_SYSTEM, INTERVIEW_START)
        output_fn(f"\n{response}\n")
        conversation.append(("assistant", response))

        turns = 0
        while turns < 10:  # max 10 substantive user turns
            try:
                answer = input_fn("> ")
            except EOFError as exc:
                raise ProfileInterviewAborted("Profile interview aborted by end-of-input") from exc
            if not answer.strip():
                continue
            turns += 1

            conversation.append(("user", answer))

            # Build conversation history for LLM
            history = "\n".join(
                f"{'Coach' if role == 'assistant' else 'User'}: {msg}" for role, msg in conversation
            )
            prompt = f"Interview so far:\n{history}\n\nContinue the interview or finalize the profile if you have enough info."

            response = self._call_llm(INTERVIEW_SYSTEM, prompt, max_tokens=1500)
            conversation.append(("assistant", response))

            # Check if interview is done
            profile_data = _extract_profile_json(response)
            if profile_data:
                profile = _build_profile(profile_data)
                self._save_profile(profile)
                logger.info("profile_created", skills=len(profile.skills))
                return profile

            output_fn(f"\n{response}\n")

        # Fallback: force extraction
        history = "\n".join(
            f"{'Coach' if r == 'assistant' else 'User'}: {m}" for r, m in conversation
        )
        force_prompt = f"""Based on this interview, generate the profile JSON now.

{history}

Output the JSON profile block now."""
        response = self._call_llm(INTERVIEW_SYSTEM, force_prompt, max_tokens=1500)
        profile_data = _extract_profile_json(response)
        if profile_data:
            profile = _build_profile(profile_data)
            self._save_profile(profile)
            return profile

        # Absolute fallback: empty profile
        logger.warning("interview_extraction_failed")
        profile = UserProfile()
        self._save_profile(profile)
        return profile

    def needs_refresh(self, days: int = 90) -> bool:
        """Check if profile needs re-interview."""
        profile = self.storage.load()
        if not profile:
            return True
        return profile.is_stale(days)

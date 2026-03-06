"""Persona simulation harness — drives 2 personas through 10 days of AI coach usage."""

import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import click
import httpx
from jose import jwt

# ---------------------------------------------------------------------------
# Env checks
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("COACH_API_URL", "http://localhost:8000")
NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

OBS_PATH = Path(__file__).parent / "persona_observations.md"


def _require_env():
    missing = []
    for v in ("NEXTAUTH_SECRET", "ANTHROPIC_API_KEY", "SECRET_KEY"):
        if not os.getenv(v):
            missing.append(v)
    if missing:
        click.echo(f"Missing env vars: {', '.join(missing)}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Persona dataclass
# ---------------------------------------------------------------------------


@dataclass
class Persona:
    name: str
    user_id: str
    email: str
    role: str
    experience: str
    location: str
    skills: list[dict]
    interests: list[str]
    goals_short: str
    goals_long: str
    fears: list[str]
    hours_per_week: int
    learning_style: str
    active_projects: list[str]
    industries_watching: list[str]
    technologies_watching: list[str]
    # keyword lists for quality heuristics
    personalization_keywords: list[str] = field(default_factory=list)


MAYA = Persona(
    name="Maya Chen",
    user_id="sim:maya_chen",
    email="maya.chen@example.com",
    role="Senior ML Engineer at a fintech startup",
    experience="6 years in machine learning, currently focused on NLP and model serving",
    location="San Francisco, CA",
    skills=[
        {"name": "Python", "proficiency": 5},
        {"name": "PyTorch", "proficiency": 4},
        {"name": "MLOps", "proficiency": 3},
        {"name": "SQL", "proficiency": 4},
        {"name": "Kubernetes", "proficiency": 3},
    ],
    interests=["LLM fine-tuning", "MLOps automation", "distributed systems"],
    goals_short="Transition to ML platform lead role, start writing a paper on efficient fine-tuning",
    goals_long="Lead an ML platform org, become a recognized voice in applied ML",
    fears=["Being pigeonholed as 'just ML'", "Missing the LLM wave", "Career stagnation"],
    hours_per_week=8,
    learning_style="hands-on",
    active_projects=[
        "Feature extraction pipeline at work",
        "Open-source MLOps dashboard side project",
    ],
    industries_watching=["fintech", "AI/ML infrastructure"],
    technologies_watching=["JAX", "vLLM", "PEFT/LoRA", "Ray"],
    personalization_keywords=[
        "PyTorch",
        "fine-tuning",
        "platform lead",
        "MLOps",
        "LoRA",
        "PEFT",
        "ML platform",
        "pipeline",
        "transformer",
        "A100",
    ],
)

DAVID = Persona(
    name="David Park",
    user_id="sim:david_park",
    email="david.park@example.com",
    role="Solo founder of a devtools startup",
    experience="10 years of software engineering, now building a developer tools product",
    location="Austin, TX",
    skills=[
        {"name": "TypeScript", "proficiency": 5},
        {"name": "React", "proficiency": 4},
        {"name": "Node.js", "proficiency": 4},
        {"name": "AWS", "proficiency": 3},
        {"name": "Go", "proficiency": 3},
    ],
    interests=["Developer experience", "API design", "startup growth", "fundraising"],
    goals_short="Launch MVP by end of Q2, get 100 beta signups, raise pre-seed round",
    goals_long="Build a profitable devtools company, grow to 10-person team",
    fears=["Running out of runway", "Building the wrong thing", "Competition from bigger players"],
    hours_per_week=12,
    learning_style="reading",
    active_projects=["CLI devtool with plugin architecture", "API mocking feature prototype"],
    industries_watching=["devtools", "developer infrastructure", "SaaS"],
    technologies_watching=["Bun", "Effect-TS", "tRPC", "Hono"],
    personalization_keywords=[
        "MVP",
        "devtools",
        "pre-seed",
        "fundraising",
        "API mocking",
        "beta",
        "startup",
        "plugin",
        "TypeScript",
        "runway",
    ],
)

PERSONAS = {"maya": MAYA, "david": DAVID}


# ---------------------------------------------------------------------------
# JWT helper
# ---------------------------------------------------------------------------


def _mint_jwt(persona: Persona) -> str:
    payload = {
        "sub": persona.user_id,
        "email": persona.email,
        "name": persona.name,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,
    }
    return jwt.encode(payload, NEXTAUTH_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# CoachAPIClient
# ---------------------------------------------------------------------------


class CoachAPIClient:
    """httpx wrapper with JWT auth for each persona."""

    def __init__(self, persona: Persona):
        self.persona = persona
        self.token = _mint_jwt(persona)
        self.client = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=120.0,
        )

    def _call(self, method: str, path: str, **kwargs) -> tuple[int, dict, float]:
        t0 = time.monotonic()
        resp = getattr(self.client, method)(path, **kwargs)
        latency = (time.monotonic() - t0) * 1000
        try:
            body = resp.json()
        except Exception:
            body = {"raw": resp.text[:500]}
        return resp.status_code, body, latency

    # -- Settings --
    def settings_put(self, payload: dict) -> tuple[int, dict, float]:
        return self._call("put", "/api/settings", json=payload)

    # -- Onboarding --
    def onboarding_start(self) -> tuple[int, dict, float]:
        return self._call("post", "/api/onboarding/start")

    def onboarding_chat(self, msg: str) -> tuple[int, dict, float]:
        return self._call("post", "/api/onboarding/chat", json={"message": msg})

    # -- Journal --
    def journal_create(
        self,
        content: str,
        entry_type: str = "daily",
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> tuple[int, dict, float]:
        payload: dict = {"content": content, "entry_type": entry_type}
        if title:
            payload["title"] = title
        if tags:
            payload["tags"] = tags
        return self._call("post", "/api/journal", json=payload)

    def journal_list(self) -> tuple[int, dict, float]:
        return self._call("get", "/api/journal")

    # -- Advisor --
    def advisor_ask(
        self,
        question: str,
        advice_type: str = "general",
        conversation_id: str | None = None,
    ) -> tuple[int, dict, float]:
        payload: dict = {"question": question, "advice_type": advice_type}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        return self._call("post", "/api/advisor/ask", json=payload)

    def conversations_list(self) -> tuple[int, dict, float]:
        return self._call("get", "/api/advisor/conversations")

    # -- Goals --
    def goals_create(
        self, title: str, content: str = "", tags: list[str] | None = None
    ) -> tuple[int, dict, float]:
        payload: dict = {"title": title, "content": content}
        if tags:
            payload["tags"] = tags
        return self._call("post", "/api/goals", json=payload)

    def goals_list(self) -> tuple[int, dict, float]:
        return self._call("get", "/api/goals")

    def goals_check_in(self, path: str, notes: str = "") -> tuple[int, dict, float]:
        return self._call("post", f"/api/goals/{path}/check-in", json={"notes": notes})

    # -- Intel --
    def intel_scrape(self) -> tuple[int, dict, float]:
        return self._call("post", "/api/intel/scrape", timeout=300.0)

    def intel_recent(self, days: int = 7) -> tuple[int, dict, float]:
        return self._call("get", f"/api/intel/recent?days={days}")

    # -- Profile --
    def profile_get(self) -> tuple[int, dict, float]:
        return self._call("get", "/api/profile")

    # -- Greeting (chat-first home) --
    def greeting_get(self) -> tuple[int, dict, float]:
        return self._call("get", "/api/greeting")

    # -- Suggestions (unified recs + daily brief) --
    def suggestions_get(self, limit: int = 10) -> tuple[int, dict, float]:
        return self._call("get", f"/api/suggestions?limit={limit}")

    # -- Insights --
    def insights_get(self) -> tuple[int, dict, float]:
        return self._call("get", "/api/insights")

    # -- Milestones --
    def milestone_add(self, goal_path: str, title: str) -> tuple[int, dict, float]:
        return self._call("post", f"/api/goals/{goal_path}/milestones", json={"title": title})

    def milestone_complete(self, goal_path: str, index: int) -> tuple[int, dict, float]:
        return self._call(
            "post", f"/api/goals/{goal_path}/milestones/complete", json={"milestone_index": index}
        )

    def close(self):
        self.client.close()


# ---------------------------------------------------------------------------
# OnboardingDriver
# ---------------------------------------------------------------------------


class OnboardingDriver:
    """Drives multi-turn onboarding with scripted persona responses."""

    # Keyword -> response builder (checked against LLM question)
    @staticmethod
    def _build_response_map(p: Persona) -> dict[str, str]:
        skills_str = ", ".join(f"{s['name']} ({s['proficiency']}/5)" for s in p.skills)
        return {
            "role": f"I'm a {p.role} with {p.experience}. Based in {p.location}.",
            "situation": f"I'm a {p.role} with {p.experience}. Based in {p.location}.",
            "tell me about yourself": f"I'm a {p.role} with {p.experience}. Based in {p.location}.",
            "skill": f"My key skills: {skills_str}.",
            "proficien": f"My key skills: {skills_str}.",
            "language": f"I mainly work with: {', '.join(s['name'] for s in p.skills)}.",
            "framework": f"I mainly work with: {', '.join(s['name'] for s in p.skills)}.",
            "interest": f"I'm most interested in: {', '.join(p.interests)}.",
            "passion": f"I'm most interested in: {', '.join(p.interests)}.",
            "goal": f"Short-term: {p.goals_short}. Long-term: {p.goals_long}.",
            "6 month": f"In the next 6 months: {p.goals_short}.",
            "six month": f"In the next 6 months: {p.goals_short}.",
            "3 year": f"In 3 years: {p.goals_long}.",
            "three year": f"In 3 years: {p.goals_long}.",
            "vision": f"Long-term: {p.goals_long}.",
            "industr": f"I'm watching: {', '.join(p.industries_watching)}.",
            "technolog": f"Technologies on my radar: {', '.join(p.technologies_watching)}.",
            "watching": f"Industries: {', '.join(p.industries_watching)}. Tech: {', '.join(p.technologies_watching)}.",
            "time": f"I have about {p.hours_per_week} hours per week. I'm in {p.location}.",
            "hour": f"About {p.hours_per_week} hours per week.",
            "constraint": f"{p.hours_per_week} hrs/week, based in {p.location}, low budget sensitivity.",
            "fear": f"My concerns: {', '.join(p.fears)}.",
            "concern": f"My concerns: {', '.join(p.fears)}.",
            "worry": f"My concerns: {', '.join(p.fears)}.",
            "risk": f"My concerns: {', '.join(p.fears)}.",
            "project": f"Currently working on: {', '.join(p.active_projects)}.",
            "side": f"Currently working on: {', '.join(p.active_projects)}.",
            "locat": f"I'm based in {p.location}.",
            "where": f"I'm based in {p.location}.",
            "learn": f"I'm a {p.learning_style} learner.",
            "style": f"I'm a {p.learning_style} learner.",
            "track": (
                f"Goals to track: 1) {p.goals_short.split(',')[0].strip()}, "
                f"2) Deepen expertise in {p.interests[0]}, "
                f"3) Ship {p.active_projects[0] if p.active_projects else 'a side project'}."
            ),
        }

    @staticmethod
    def respond(persona: Persona, llm_question: str, turn: int) -> str:
        """Pick a scripted response based on keywords in the LLM's question."""
        q_lower = llm_question.lower()
        rmap = OnboardingDriver._build_response_map(persona)

        for keyword, response in rmap.items():
            if keyword in q_lower:
                return response

        # Fallback: after enough turns, signal completion
        if turn >= 4:
            return (
                f"I think that covers the main points. My key goals are: {persona.goals_short}. "
                f"I'm a {persona.learning_style} learner with {persona.hours_per_week} hrs/week."
            )
        return (
            f"To add more context: I'm a {persona.role}, "
            f"interested in {', '.join(persona.interests[:2])}. "
            f"My biggest concern is {persona.fears[0].lower()}."
        )

    @staticmethod
    def run(client: CoachAPIClient, persona: Persona) -> bool:
        """Drive full onboarding. Returns True on success."""
        click.echo(f"  Starting onboarding for {persona.name}...")
        status, body, lat = client.onboarding_start()
        if status != 200:
            click.echo(f"  ERROR: onboarding/start returned {status}: {body}")
            return False
        click.echo(f"  [turn 0] Coach: {body['message'][:120]}... ({lat:.0f}ms)")

        for turn in range(1, 12):
            if body.get("done"):
                click.echo(
                    f"  Onboarding complete at turn {turn - 1}, goals created: {body.get('goals_created', 0)}"
                )
                return True

            reply = OnboardingDriver.respond(persona, body["message"], turn)
            click.echo(f"  [turn {turn}] {persona.name}: {reply[:100]}...")
            status, body, lat = client.onboarding_chat(reply)
            if status != 200:
                click.echo(f"  ERROR: onboarding/chat returned {status}: {body}")
                return False
            click.echo(f"  [turn {turn}] Coach: {body['message'][:120]}... ({lat:.0f}ms)")

        click.echo(
            f"  Onboarding finished (done={body.get('done')}), goals: {body.get('goals_created', 0)}"
        )
        return True


# ---------------------------------------------------------------------------
# ObservationLogger
# ---------------------------------------------------------------------------


class ObservationLogger:
    """Appends structured observations to persona_observations.md."""

    def __init__(self):
        self.rows: list[dict] = []
        if not OBS_PATH.exists():
            OBS_PATH.write_text(
                "---\ntitle: Persona Simulation Observations\n"
                f"started: {datetime.now().isoformat()}\n---\n\n"
                "| day | persona | action | latency_ms | status | personalized | notes |\n"
                "|-----|---------|--------|-----------|--------|-------------|-------|\n"
            )

    def log(
        self,
        day: int,
        persona: str,
        action: str,
        latency_ms: float,
        status_code: int,
        body: dict,
        persona_obj: Persona | None = None,
    ):
        personalized = ""
        notes = ""

        if action.startswith("advisor") and "answer" in body:
            answer = body["answer"].lower()
            if persona_obj:
                hits = [kw for kw in persona_obj.personalization_keywords if kw.lower() in answer]
                personalized = "yes" if hits else "no"
                if hits:
                    notes = f"keywords: {', '.join(hits[:4])}"
            # Flag slow responses
            if latency_ms > 15000:
                notes += " SLOW" if notes else "SLOW"

        row = {
            "day": day,
            "persona": persona,
            "action": action,
            "latency_ms": round(latency_ms),
            "status": status_code,
            "personalized": personalized,
            "notes": notes,
        }
        self.rows.append(row)

        # Append to file
        with open(OBS_PATH, "a") as f:
            f.write(
                f"| {day} | {persona} | {action} | {round(latency_ms)} | "
                f"{status_code} | {personalized} | {notes} |\n"
            )

    def print_report(self):
        """Print aggregated statistics."""
        if not self.rows:
            # Try to load from file
            self._load_from_file()

        if not self.rows:
            click.echo("No observations recorded.")
            return

        total = len(self.rows)
        successes = sum(1 for r in self.rows if 200 <= r["status"] < 300)
        avg_lat = sum(r["latency_ms"] for r in self.rows) / total if total else 0
        advisor_rows = [r for r in self.rows if r["action"].startswith("advisor")]
        personalized = sum(1 for r in advisor_rows if r["personalized"] == "yes")
        slow = sum(1 for r in self.rows if r["latency_ms"] > 15000)
        errors = [r for r in self.rows if r["status"] >= 400]

        click.echo("\n=== Persona Simulation Report ===")
        click.echo(f"Total actions:        {total}")
        click.echo(f"Success rate:         {successes}/{total} ({100 * successes / total:.0f}%)")
        click.echo(f"Avg latency:          {avg_lat:.0f}ms")
        click.echo(f"Advisor calls:        {len(advisor_rows)}")
        if advisor_rows:
            click.echo(
                f"Personalization rate: {personalized}/{len(advisor_rows)} ({100 * personalized / len(advisor_rows):.0f}%)"
            )
        click.echo(f"Slow (>15s):          {slow}")
        click.echo(f"Errors:               {len(errors)}")

        if errors:
            click.echo("\nError details:")
            for e in errors:
                click.echo(
                    f"  day {e['day']} | {e['persona']} | {e['action']} | {e['status']} | {e['notes']}"
                )

        # Per-persona breakdown
        for pname in ("Maya Chen", "David Park"):
            pr = [r for r in self.rows if r["persona"] == pname]
            if not pr:
                continue
            pavg = sum(r["latency_ms"] for r in pr) / len(pr)
            psuc = sum(1 for r in pr if 200 <= r["status"] < 300)
            pa = [r for r in pr if r["action"].startswith("advisor")]
            pp = sum(1 for r in pa if r["personalized"] == "yes")
            click.echo(f"\n--- {pname} ---")
            click.echo(
                f"  Actions: {len(pr)}, Success: {psuc}/{len(pr)}, Avg latency: {pavg:.0f}ms"
            )
            if pa:
                click.echo(f"  Advisor: {len(pa)}, Personalized: {pp}/{len(pa)}")

    def _load_from_file(self):
        """Parse observations from markdown table."""
        if not OBS_PATH.exists():
            return
        for line in OBS_PATH.read_text().splitlines():
            if not line.startswith("| ") or line.startswith("| day") or line.startswith("|---"):
                continue
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 6:
                try:
                    self.rows.append(
                        {
                            "day": int(parts[0]),
                            "persona": parts[1],
                            "action": parts[2],
                            "latency_ms": int(parts[3]),
                            "status": int(parts[4]),
                            "personalized": parts[5],
                            "notes": parts[6] if len(parts) > 6 else "",
                        }
                    )
                except (ValueError, IndexError):
                    pass


# ---------------------------------------------------------------------------
# DayRunner
# ---------------------------------------------------------------------------


class DayRunner:
    """Execute a single day's actions for a persona."""

    def __init__(self, client: CoachAPIClient, persona: Persona, obs: ObservationLogger):
        self.client = client
        self.persona = persona
        self.obs = obs
        self._last_conv_id: str | None = None
        self._goal_paths: list[str] = []

    def _log(self, day: int, action: str, status: int, body: dict, latency: float):
        self.obs.log(day, self.persona.name, action, latency, status, body, self.persona)
        icon = "✓" if 200 <= status < 300 else "✗"
        click.echo(f"  {icon} {action} [{status}] ({latency:.0f}ms)")

    def _refresh_goals(self):
        """Cache goal paths for check-ins."""
        status, body, _ = self.client.goals_list()
        if status == 200 and isinstance(body, list):
            self._goal_paths = [g["path"] for g in body]

    def _find_goal(self, keyword: str) -> str | None:
        """Find a goal path by keyword in the path."""
        kw = keyword.lower()
        for p in self._goal_paths:
            if kw in p.lower():
                return p
        return self._goal_paths[0] if self._goal_paths else None

    def run_action(self, day: int, action: dict):
        atype = action["type"]

        if atype == "journal":
            status, body, lat = self.client.journal_create(
                content=action["content"],
                entry_type=action.get("entry_type", "daily"),
                title=action.get("title"),
                tags=action.get("tags"),
            )
            self._log(day, f"journal:{action.get('entry_type', 'daily')}", status, body, lat)

        elif atype == "advisor":
            conv_id = self._last_conv_id if action.get("continue_conv") else None
            status, body, lat = self.client.advisor_ask(
                question=action["question"],
                advice_type=action.get("advice_type", "general"),
                conversation_id=conv_id,
            )
            if status == 200 and "conversation_id" in body:
                self._last_conv_id = body["conversation_id"]
            self._log(day, f"advisor:{action.get('advice_type', 'general')}", status, body, lat)
            # Print snippet of answer
            if "answer" in body:
                snippet = body["answer"][:200].replace("\n", " ")
                click.echo(f"    → {snippet}...")

        elif atype == "goal":
            status, body, lat = self.client.goals_create(
                title=action["title"],
                content=action.get("content", ""),
                tags=action.get("tags"),
            )
            self._log(day, "goal:create", status, body, lat)
            if status == 201 and "path" in body:
                self._goal_paths.append(body["path"])

        elif atype == "goal_check_in":
            self._refresh_goals()
            path = self._find_goal(action.get("keyword", ""))
            if path:
                status, body, lat = self.client.goals_check_in(path, notes=action.get("notes", ""))
                self._log(day, "goal:check_in", status, body, lat)
            else:
                click.echo(f"  ⚠ No goal found for keyword '{action.get('keyword')}'")

        elif atype == "scrape":
            click.echo("  Triggering intel scrape (may be slow)...")
            status, body, lat = self.client.intel_scrape()
            self._log(day, "intel:scrape", status, body, lat)

        elif atype == "intel_check":
            status, body, lat = self.client.intel_recent(days=action.get("days", 7))
            count = len(body) if isinstance(body, list) else 0
            self._log(day, f"intel:recent({count})", status, body, lat)

        elif atype == "goals_list":
            self._refresh_goals()
            status, body, lat = self.client.goals_list()
            count = len(body) if isinstance(body, list) else 0
            self._log(day, f"goals:list({count})", status, body, lat)

        elif atype == "greeting":
            status, body, lat = self.client.greeting_get()
            self._log(day, "greeting:get", status, body, lat)
            if "text" in body:
                click.echo(f"    → {body['text'][:150]}...")

        elif atype == "suggestions":
            status, body, lat = self.client.suggestions_get()
            count = len(body) if isinstance(body, list) else 0
            self._log(day, f"suggestions:get({count})", status, body, lat)

        elif atype == "insights":
            status, body, lat = self.client.insights_get()
            count = len(body) if isinstance(body, list) else 0
            self._log(day, f"insights:get({count})", status, body, lat)

        elif atype == "milestone_add":
            self._refresh_goals()
            path = self._find_goal(action.get("keyword", ""))
            if path:
                status, body, lat = self.client.milestone_add(path, action["title"])
                self._log(day, "milestone:add", status, body, lat)
            else:
                click.echo(f"  ⚠ No goal found for keyword '{action.get('keyword')}'")

        elif atype == "milestone_complete":
            self._refresh_goals()
            path = self._find_goal(action.get("keyword", ""))
            if path:
                status, body, lat = self.client.milestone_complete(path, action.get("index", 0))
                self._log(day, "milestone:complete", status, body, lat)
            else:
                click.echo(f"  ⚠ No goal found for keyword '{action.get('keyword')}'")

        else:
            click.echo(f"  ⚠ Unknown action type: {atype}")


# ---------------------------------------------------------------------------
# 10-Day Schedule
# ---------------------------------------------------------------------------


def _get_schedule(persona_key: str) -> dict[int, list[dict]]:  # noqa: C901
    """Return {day: [actions]} for a persona."""
    if persona_key == "maya":
        return {
            1: [
                {
                    "type": "journal",
                    "content": (
                        "Kicked off new feature extraction pipeline at work, debating PyTorch vs JAX "
                        "for the transformer layer. The team is split — JAX has better XLA compilation "
                        "but our existing codebase is all PyTorch. Need to prototype both this week. "
                        "Also attended an internal talk on model serving with vLLM, looks promising for "
                        "our inference latency issues."
                    ),
                    "entry_type": "daily",
                    "title": "Pipeline kickoff — PyTorch vs JAX debate",
                },
            ],
            2: [
                {
                    "type": "journal",
                    "content": (
                        "Team standup — manager hinted at platform team forming, could be my chance. "
                        "She mentioned they're looking for someone who understands both model development "
                        "and infrastructure. Spent the afternoon reviewing our CI/CD for model deployment, "
                        "it's a mess of shell scripts. This is exactly what a platform team should fix."
                    ),
                    "entry_type": "daily",
                    "title": "Platform team opportunity",
                },
                {
                    "type": "advisor",
                    "question": (
                        "What should I prioritize to position myself for an ML platform lead role? "
                        "I'm currently a senior ML engineer with strong PyTorch skills but weaker on "
                        "the infrastructure/MLOps side. My manager hinted a platform team is forming."
                    ),
                    "advice_type": "career",
                },
            ],
            3: [
                {
                    "type": "goal",
                    "title": "Get promoted to ML Platform Lead",
                    "content": "Transition from senior ML engineer to leading the new ML platform team. Need to demonstrate infrastructure skills and cross-team leadership.",
                    "tags": ["career", "leadership"],
                },
                {
                    "type": "goal",
                    "title": "Publish paper on efficient fine-tuning",
                    "content": "Write and submit a paper on PEFT techniques for production ML systems, targeting a top ML conference.",
                    "tags": ["research", "writing"],
                },
                {
                    "type": "goal",
                    "title": "Build open-source MLOps dashboard",
                    "content": "Side project: create a dashboard for monitoring ML model performance, training runs, and data drift.",
                    "tags": ["side-project", "open-source"],
                },
                {
                    "type": "journal",
                    "content": (
                        "Reflecting on my career direction. I've been heads-down on model development "
                        "for 4 years now. The platform lead opportunity feels like the right next step — "
                        "it combines my ML knowledge with systems thinking. But I worry about losing "
                        "my technical edge if I move into management too early."
                    ),
                    "entry_type": "reflection",
                    "title": "Career direction reflection",
                },
            ],
            4: [
                {
                    "type": "journal",
                    "content": (
                        "Explored PEFT techniques today — LoRA seems promising for our use case. "
                        "Ran experiments with rank=8 and rank=16 on our sentiment model, got within "
                        "2% of full fine-tuning accuracy with 10x less compute. This could be the "
                        "basis of my paper. Also looked at QLoRA for our larger models."
                    ),
                    "entry_type": "daily",
                    "title": "LoRA experiments — promising results",
                },
                {
                    "type": "advisor",
                    "question": (
                        "I'm at a crossroads between deepening my ML research path (I have promising "
                        "LoRA experiment results) and going after the platform lead role. Can I do both? "
                        "How should I think about the ML platform vs research track?"
                    ),
                    "advice_type": "career",
                },
            ],
            5: [
                {
                    "type": "goal_check_in",
                    "keyword": "platform",
                    "notes": "Had 1:1 with skip-level manager, expressed interest in the platform team. She said they're finalizing the team charter next month.",
                },
                {
                    "type": "milestone_add",
                    "keyword": "platform",
                    "title": "Complete Kubernetes CKA certification",
                },
                {
                    "type": "milestone_add",
                    "keyword": "platform",
                    "title": "Contribute to platform team RFC",
                },
                {
                    "type": "journal",
                    "content": (
                        "Weekly reflection: Good progress on multiple fronts. The LoRA experiments "
                        "are yielding great results. Had a productive skip-level where I pitched myself "
                        "for the platform lead role. Need to be more visible in cross-team discussions. "
                        "Feeling energized but stretched thin."
                    ),
                    "entry_type": "reflection",
                    "title": "Week 1 reflection — momentum building",
                },
                {
                    "type": "advisor",
                    "question": (
                        "What are the most critical skill gaps I should address to be credible as an "
                        "ML platform lead? I'm strong on PyTorch and model development but weaker on "
                        "Kubernetes, CI/CD, and distributed systems."
                    ),
                    "advice_type": "skill_gap",
                },
                {"type": "suggestions"},
            ],
            6: [
                {
                    "type": "journal",
                    "content": (
                        "Hit a wall — our fine-tuning pipeline keeps OOMing on the A100s. Tried "
                        "gradient checkpointing but throughput dropped 40%. The model is 7B params "
                        "and we need to fine-tune on 50K examples. Tried DeepSpeed ZeRO-3 but the "
                        "communication overhead is killing us. Starting to think we need a fundamentally "
                        "different approach."
                    ),
                    "entry_type": "daily",
                    "title": "OOM crisis on A100 fine-tuning",
                },
                {
                    "type": "advisor",
                    "question": (
                        "I'm running into OOM issues fine-tuning a 7B parameter model on A100s. "
                        "Gradient checkpointing dropped throughput by 40%. DeepSpeed ZeRO-3 has too "
                        "much communication overhead. What other approaches should I consider? "
                        "Would FSDP or a different sharding strategy help?"
                    ),
                    "advice_type": "technical",
                },
            ],
            7: [
                {
                    "type": "journal",
                    "content": (
                        "Weekly review: Mixed week. The OOM issue ate up 2 days but I learned a lot "
                        "about memory-efficient training. On the career front, the platform team charter "
                        "is being drafted and my manager put my name forward. Paper outline is taking "
                        "shape — focusing on practical PEFT for production systems."
                    ),
                    "entry_type": "reflection",
                    "title": "Week 2 review — mixed progress",
                },
                {"type": "intel_check", "days": 7},
                {
                    "type": "advisor",
                    "question": (
                        "How am I tracking against my goals this week? I set goals around the platform "
                        "lead role, publishing a paper on fine-tuning, and building an MLOps dashboard. "
                        "The OOM issues set me back but I made progress on the career front."
                    ),
                    "advice_type": "general",
                },
            ],
            8: [
                {
                    "type": "journal",
                    "content": (
                        "Realized I should contribute to the platform team's RFC even before the role "
                        "opens — shows initiative and gives me a seat at the table. Drafted a section "
                        "on model serving infrastructure based on our vLLM experiments. Also got positive "
                        "feedback on my LoRA results from the research team lead."
                    ),
                    "entry_type": "daily",
                    "title": "Contributing to platform RFC proactively",
                },
                {
                    "type": "goal_check_in",
                    "keyword": "paper",
                    "notes": "Outline complete, LoRA experiments done. Need to write up results section and run ablation studies.",
                },
                {
                    "type": "advisor",
                    "question": (
                        "I'm writing a paper on efficient fine-tuning techniques (LoRA/PEFT) for "
                        "production ML systems. What venues should I target? I'm considering ICML, "
                        "NeurIPS, or maybe a more applied venue like MLSys."
                    ),
                    "advice_type": "general",
                },
            ],
            9: [
                {"type": "intel_check", "days": 7},
                {
                    "type": "advisor",
                    "question": (
                        "What are the latest trends in AI/ML infrastructure and MLOps? I want to make "
                        "sure the platform team RFC I'm contributing to is forward-looking. Particularly "
                        "interested in model serving, training infrastructure, and ML observability."
                    ),
                    "advice_type": "general",
                },
                {
                    "type": "goal",
                    "title": "Contribute to platform team RFC by end of month",
                    "content": "Write and submit the model serving section of the platform team's founding RFC. Use vLLM experiment data as evidence.",
                    "tags": ["career", "writing"],
                },
            ],
            10: [
                {"type": "greeting"},
                {
                    "type": "milestone_complete",
                    "keyword": "platform",
                    "index": 1,
                },
                {
                    "type": "journal",
                    "content": (
                        "Comprehensive reflection after 10 days of focused effort. I've made real "
                        "progress on three fronts: (1) The platform lead opportunity is solidifying — "
                        "my RFC contribution was well-received and I'm on the shortlist. (2) The LoRA "
                        "paper has a clear path forward with strong experimental results. (3) The OOM "
                        "crisis actually deepened my understanding of distributed training. Feeling more "
                        "confident that I can bridge the research-to-platform gap. Next: finalize the "
                        "RFC, run paper ablation studies, and prepare for the platform lead interview."
                    ),
                    "entry_type": "reflection",
                    "title": "10-day retrospective — real momentum",
                },
                {
                    "type": "advisor",
                    "question": (
                        "Looking at my trajectory over the past couple of weeks, I've been working "
                        "toward the ML platform lead role, writing a paper on PEFT, and dealing with "
                        "production challenges. What should my top 3 priorities be for the next month?"
                    ),
                    "advice_type": "career",
                },
                {
                    "type": "advisor",
                    "question": (
                        "As a follow-up: if I get the platform lead role, how should I approach the "
                        "first 90 days? I want to balance quick wins with setting the right long-term "
                        "technical direction for the team."
                    ),
                    "advice_type": "career",
                    "continue_conv": True,
                },
                {"type": "goals_list"},
                {"type": "suggestions"},
                {"type": "insights"},
            ],
        }
    else:  # david
        return {
            1: [
                {
                    "type": "journal",
                    "content": (
                        "Spent the day wireframing the CLI tool. Realized I need to nail the plugin "
                        "architecture before anything else — if plugins are an afterthought, the whole "
                        "DX falls apart. Looked at how Vite and ESBuild handle plugins for inspiration. "
                        "The hook-based approach seems cleanest."
                    ),
                    "entry_type": "daily",
                    "title": "Plugin architecture wireframing",
                },
            ],
            2: [
                {
                    "type": "journal",
                    "content": (
                        "Had coffee chat with a YC founder. They said focus on one workflow, not a "
                        "platform. 'Do one thing insanely well.' Made me reconsider the scope — maybe "
                        "API mocking should be the entire product, not just a feature. Also mentioned "
                        "that devtools founders need to be in the community."
                    ),
                    "entry_type": "daily",
                    "title": "YC founder advice — narrow the scope",
                },
                {
                    "type": "advisor",
                    "question": (
                        "Should I narrow my MVP scope to just API mocking, or keep the broader devtools "
                        "vision? A YC founder advised me to do one thing well. But I worry that API "
                        "mocking alone isn't a big enough market. My current plan includes API mocking, "
                        "schema validation, and test generation."
                    ),
                    "advice_type": "general",
                },
            ],
            3: [
                {
                    "type": "goal",
                    "title": "Launch MVP by end of Q2",
                    "content": "Ship a usable MVP of the devtool CLI with at least API mocking feature complete. Target: public beta on Product Hunt.",
                    "tags": ["product", "launch"],
                },
                {
                    "type": "goal",
                    "title": "Get 100 beta signups",
                    "content": "Reach 100 genuine beta users through community engagement, content marketing, and direct outreach.",
                    "tags": ["growth", "marketing"],
                },
                {
                    "type": "goal",
                    "title": "Raise $500K pre-seed",
                    "content": "Close a $500K pre-seed round from angels and micro-VCs. Need pitch deck, financial model, and warm intros.",
                    "tags": ["fundraising"],
                },
                {
                    "type": "journal",
                    "content": (
                        "Competitor analysis deep dive. Found 3 players in the API mocking space: "
                        "MockServer (open-source, Java, clunky), Prism (Stoplight, good but limited), "
                        "and WireMock (enterprise, expensive). None have great CLI-first DX or "
                        "TypeScript-native support. There's a real gap for a modern, TS-first tool."
                    ),
                    "entry_type": "daily",
                    "title": "Competitor analysis — gap confirmed",
                },
            ],
            4: [
                {
                    "type": "journal",
                    "content": (
                        "Built first prototype of the API mocking feature. Users in Discord seem "
                        "excited — got 15 reactions on the demo video. The mock generation from "
                        "OpenAPI specs is working but needs polish. TypeScript inference is the killer "
                        "feature — full type safety from your API spec to your mocks."
                    ),
                    "entry_type": "daily",
                    "title": "API mocking prototype — Discord buzz",
                },
                {
                    "type": "advisor",
                    "question": (
                        "I'm a solo founder building a devtools startup. My API mocking prototype is "
                        "getting early traction in Discord. What should my go-to-market strategy look "
                        "like? I'm thinking open-source core with a paid cloud hosted version."
                    ),
                    "advice_type": "general",
                },
            ],
            5: [
                {
                    "type": "goal_check_in",
                    "keyword": "MVP",
                    "notes": "API mocking feature working, need auth + billing. Got 15 Discord reactions on demo. Timeline tight for Q2.",
                },
                {
                    "type": "journal",
                    "content": (
                        "Reflection: I'm building in public and it's working — the Discord community "
                        "is growing (now 47 members). But I'm spread too thin between coding, content, "
                        "and fundraising prep. Need to ruthlessly prioritize. The prototype works but "
                        "is far from production-ready. Auth and billing are blocking the beta launch."
                    ),
                    "entry_type": "reflection",
                    "title": "Reflection — spread too thin",
                },
                {
                    "type": "advisor",
                    "question": (
                        "As a solo founder, how should I prioritize between shipping features "
                        "(auth + billing needed for beta), creating content for community growth, "
                        "and preparing my fundraising pitch deck? I have 12 hours per week and "
                        "need to launch by Q2."
                    ),
                    "advice_type": "general",
                },
            ],
            6: [
                {
                    "type": "journal",
                    "content": (
                        "Stripe integration is a nightmare. Spent 3 days on webhook handling. The "
                        "subscription lifecycle edge cases (trials, upgrades, failed payments, refunds) "
                        "are insane. Starting to doubt I can ship by Q2. Maybe I should use Lemon Squeezy "
                        "or Paddle instead — simpler billing for indie devtools."
                    ),
                    "entry_type": "daily",
                    "title": "Stripe nightmare — Q2 deadline at risk",
                },
                {
                    "type": "advisor",
                    "question": (
                        "I'm drowning in Stripe integration complexity as a solo founder. Should I "
                        "switch to a simpler billing provider like Lemon Squeezy or Paddle? The trade-off "
                        "is less control but faster time-to-market. My Q2 launch deadline is at risk."
                    ),
                    "advice_type": "technical",
                },
            ],
            7: [
                {
                    "type": "journal",
                    "content": (
                        "Weekly review: Rough week. Stripe ate most of my development time. On the "
                        "bright side, Discord community is at 62 members and I got my first 3 beta "
                        "signups from the waitlist. The API mocking feature is solid — users love the "
                        "TypeScript inference. Need to make a call on billing ASAP."
                    ),
                    "entry_type": "reflection",
                    "title": "Week 2 review — billing blocking everything",
                },
                {"type": "intel_check", "days": 7},
                {
                    "type": "advisor",
                    "question": (
                        "Give me an honest assessment of my progress. I'm trying to launch a devtools "
                        "MVP by Q2, get 100 beta users, and raise a pre-seed. One week in and I'm "
                        "stuck on Stripe integration while my community is growing organically."
                    ),
                    "advice_type": "general",
                },
            ],
            8: [
                {
                    "type": "journal",
                    "content": (
                        "Talked to 5 potential users — 4 want API mocking, only 1 wants the full "
                        "platform. This confirms the YC advice: narrow the scope. Decided to pivot "
                        "fully to 'the best API mocking tool for TypeScript devs'. Also switching "
                        "from Stripe to Lemon Squeezy — 2 days integration max."
                    ),
                    "entry_type": "daily",
                    "title": "User interviews confirm narrow scope — pivoting",
                },
                {
                    "type": "goal_check_in",
                    "keyword": "beta",
                    "notes": "At 3 signups from 62 Discord members. Need to 10x community outreach. User interviews confirm API mocking focus.",
                },
                {
                    "type": "advisor",
                    "question": (
                        "I just did 5 user interviews and 4 out of 5 want just the API mocking tool, "
                        "not the broader platform. How should I approach user research going forward? "
                        "I want to keep validating as I build. What frameworks or methods work best "
                        "for solo founders?"
                    ),
                    "advice_type": "general",
                },
            ],
            9: [
                {"type": "intel_check", "days": 7},
                {
                    "type": "advisor",
                    "question": (
                        "What are the latest trends in the devtools market? I'm particularly interested "
                        "in how AI is changing developer workflows, the open-source vs SaaS debate for "
                        "devtools, and what investors are looking for in devtools startups."
                    ),
                    "advice_type": "general",
                },
                {
                    "type": "goal",
                    "title": "Run 10 user interviews this month",
                    "content": "Systematic user research: interview 10 TypeScript developers about their API testing/mocking workflows to validate product direction.",
                    "tags": ["research", "validation"],
                },
            ],
            10: [
                {"type": "greeting"},
                {
                    "type": "journal",
                    "content": (
                        "10-day retrospective. Key learnings: (1) Narrowing scope was the right call — "
                        "API mocking for TypeScript devs is a clear, defensible niche. (2) Community-led "
                        "growth works — 62 Discord members with zero ad spend. (3) Billing complexity "
                        "nearly derailed me — Lemon Squeezy is integrated and working. (4) User "
                        "interviews are gold — should have done them earlier. Next month: ship beta, "
                        "hit 100 signups, start fundraising conversations."
                    ),
                    "entry_type": "reflection",
                    "title": "10-day retrospective — clarity through pain",
                },
                {
                    "type": "advisor",
                    "question": (
                        "I'm a solo founder preparing to launch my devtools beta and start fundraising. "
                        "My product is an API mocking tool for TypeScript developers. I have 62 Discord "
                        "members and 3 beta signups. What should my fundraising strategy look like? "
                        "When should I start talking to investors vs focus on traction?"
                    ),
                    "advice_type": "general",
                },
                {
                    "type": "advisor",
                    "question": (
                        "Following up on fundraising: what metrics and milestones should I target "
                        "before approaching pre-seed investors? I'm aiming for $500K. What does a "
                        "compelling pre-seed pitch look like for a devtools startup?"
                    ),
                    "advice_type": "general",
                    "continue_conv": True,
                },
                {"type": "goals_list"},
                {"type": "suggestions"},
                {"type": "insights"},
            ],
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli():
    """Persona simulation harness for AI coach evaluation."""
    pass


@cli.command()
def setup():
    """Create users, set API keys, run onboarding, trigger intel scrape."""
    _require_env()

    for key, persona in PERSONAS.items():
        click.echo(f"\n{'=' * 60}")
        click.echo(f"Setting up {persona.name} ({persona.user_id})")
        click.echo(f"{'=' * 60}")

        client = CoachAPIClient(persona)
        try:
            # Set API key via settings
            click.echo("  Setting LLM API key...")
            status, body, lat = client.settings_put(
                {
                    "llm_api_key": ANTHROPIC_API_KEY,
                    "llm_provider": "anthropic",
                }
            )
            click.echo(f"  Settings: {status} ({lat:.0f}ms)")

            # Run onboarding
            OnboardingDriver.run(client, persona)

            # Verify profile
            status, body, lat = client.profile_get()
            click.echo(f"  Profile check: {status} ({lat:.0f}ms)")
            if status == 200:
                click.echo(f"  Role: {body.get('current_role', 'N/A')}")
                click.echo(f"  Skills: {len(body.get('skills', []))}")
        finally:
            client.close()

    # Trigger shared intel scrape once
    click.echo(f"\n{'=' * 60}")
    click.echo("Triggering shared intel scrape...")
    click.echo(f"{'=' * 60}")
    client = CoachAPIClient(MAYA)  # use Maya's auth, intel is shared
    try:
        status, body, lat = client.intel_scrape()
        click.echo(f"  Scrape: {status} ({lat:.0f}ms)")
    finally:
        client.close()

    click.echo("\nSetup complete.")


@cli.command()
@click.argument("n", type=int)
@click.option(
    "--persona",
    "-p",
    type=click.Choice(["maya", "david"]),
    default=None,
    help="Run for a single persona",
)
def day(n: int, persona: str | None):
    """Run day N activities for persona(s)."""
    _require_env()

    if n < 1 or n > 10:
        click.echo("Day must be 1-10", err=True)
        sys.exit(1)

    obs = ObservationLogger()
    targets = {persona: PERSONAS[persona]} if persona else PERSONAS

    for key, p in targets.items():
        schedule = _get_schedule(key)
        actions = schedule.get(n, [])
        if not actions:
            click.echo(f"\nNo actions for {p.name} on day {n}")
            continue

        click.echo(f"\n{'=' * 60}")
        click.echo(f"Day {n} — {p.name}")
        click.echo(f"{'=' * 60}")

        client = CoachAPIClient(p)
        runner = DayRunner(client, p, obs)
        try:
            for action in actions:
                runner.run_action(n, action)
        finally:
            client.close()

    click.echo(f"\nDay {n} complete. Observations → {OBS_PATH}")


@cli.command()
def report():
    """Print aggregated observation report."""
    obs = ObservationLogger()
    obs.print_report()


if __name__ == "__main__":
    cli()

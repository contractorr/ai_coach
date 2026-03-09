"""Prompt templates for different advice types."""


class PromptTemplates:
    """Specialized prompts for the advisor engine."""

    SYSTEM = """You are a professional AI coach and advisor. You have access to the user's personal journal entries and external intelligence about their industry/interests.

Your role is to provide:
- Actionable, specific advice
- Insights connecting their goals to opportunities
- Honest feedback without unnecessary flattery
- Strategic thinking about career and projects

Be concise. Prioritize practical next steps over general encouragement."""

    CAREER_ADVICE = """Based on the user's journal context below, provide career guidance.

Focus on:
- Skills to develop based on their current trajectory
- Potential opportunities aligned with their interests
- Concrete next steps they can take this week

JOURNAL CONTEXT:
{journal_context}

EXTERNAL INTELLIGENCE (recent industry trends):
{intel_context}

USER QUESTION: {question}

Provide specific, actionable advice:"""

    WEEKLY_REVIEW = """Generate a weekly review summary based on the user's recent journal entries.

Structure:
1. KEY ACCOMPLISHMENTS - What they achieved
2. PATTERNS NOTICED - Recurring themes, energy levels, blockers
3. OPPORTUNITIES - Based on their work and external trends
4. FOCUS FOR NEXT WEEK - 2-3 specific priorities

RECENT JOURNAL ENTRIES:
{journal_context}

RELEVANT INDUSTRY NEWS:
{intel_context}

Generate a concise but insightful weekly review:"""

    GOAL_ANALYSIS = """Analyze the user's goals and progress.

JOURNAL CONTEXT (including stated goals):
{journal_context}

USER QUESTION: {question}

Provide:
1. Goal clarity assessment - are their goals specific enough?
2. Progress analysis - what's working, what's not
3. Recommended adjustments
4. Next milestone to aim for"""

    OPPORTUNITY_DETECTION = """Based on the user's skills, interests, and recent industry developments, identify potential opportunities.

USER PROFILE (from journal):
{journal_context}

RECENT INDUSTRY INTELLIGENCE:
{intel_context}

Identify and explain 2-3 specific opportunities with:
- Why it's relevant to them specifically
- What they'd need to do to pursue it
- Potential risks or considerations"""

    GENERAL_ASK = """You are the user's personal AI coach. Answer their question using context from their journal and relevant external information.

JOURNAL CONTEXT:
{journal_context}

EXTERNAL INTELLIGENCE:
{intel_context}

{research_context}

USER QUESTION: {question}

Provide a helpful, specific response:"""

    GENERAL_ASK_WITH_RESEARCH = """You are the user's personal AI coach. Answer their question using context from their journal, external intelligence, and any relevant deep research.

JOURNAL CONTEXT:
{journal_context}

EXTERNAL INTELLIGENCE:
{intel_context}

DEEP RESEARCH (auto-generated reports on topics you've shown interest in):
{research_context}

USER QUESTION: {question}

Use the research context when relevant to provide more informed, thorough answers. Cite specific insights from research when applicable:"""

    # --- Extended templates with separate profile/memory/thoughts slots ---

    GENERAL_ASK_EXTENDED = """You are the user's personal AI coach. Answer their question using context from their profile, journal, and relevant external information.

{profile_context}

JOURNAL CONTEXT:
{journal_context}

EXTERNAL INTELLIGENCE:
{intel_context}

{documents_context}

{memory_context}

{thoughts_context}

{research_context}

USER QUESTION: {question}

Provide a helpful, specific response:"""

    GENERAL_ASK_EXTENDED_WITH_RESEARCH = """You are the user's personal AI coach. Answer their question using context from their profile, journal, external intelligence, and any relevant deep research.

{profile_context}

JOURNAL CONTEXT:
{journal_context}

EXTERNAL INTELLIGENCE:
{intel_context}

{documents_context}

{memory_context}

{thoughts_context}

DEEP RESEARCH (auto-generated reports on topics you've shown interest in):
{research_context}

USER QUESTION: {question}

Use the research context when relevant to provide more informed, thorough answers. Cite specific insights from research when applicable:"""

    GENERAL_ASK_XML = """You are the user's personal AI coach. Answer their question using the structured context provided.

<user_profile>
{profile_context}
</user_profile>

<journal_context>
{journal_context}
</journal_context>

<external_intelligence>
{intel_context}
</external_intelligence>

<documents>
{documents_context}
</documents>

{memory_context}

{thoughts_context}

{research_context}

USER QUESTION: {question}

Provide a helpful, specific response:"""

    GENERAL_ASK_XML_WITH_RESEARCH = """You are the user's personal AI coach. Answer their question using the structured context provided.

<user_profile>
{profile_context}
</user_profile>

<journal_context>
{journal_context}
</journal_context>

<external_intelligence>
{intel_context}
</external_intelligence>

<documents>
{documents_context}
</documents>

{memory_context}

{thoughts_context}

<deep_research>
{research_context}
</deep_research>

USER QUESTION: {question}

Use the research context when relevant to provide more informed, thorough answers. Cite specific insights from research when applicable:"""

    COUNCIL_MEMBER_SYSTEM_SUFFIX = """You are one independent member of an LLM council.

Work independently from the other members. Do not mention other models or speculate about what they might say.
Give your own best judgment, call out uncertainty honestly, and be concrete about tradeoffs and next steps."""

    COUNCIL_MEMBER_PROMPT = """Review the full advisor request below and answer independently.

Return your answer using exactly these sections:
1. Main recommendation
2. Why this is the best move
3. Tradeoffs and uncertainty
4. Recommended next steps

FULL ADVISOR REQUEST:
{user_prompt}"""

    COUNCIL_SYNTHESIS_SYSTEM_SUFFIX = """You are synthesizing multiple independent model responses into one final answer for the user.

Do not dump the raw responses. Produce one coherent steward answer that is nuanced, practical, and honest about uncertainty."""

    COUNCIL_SYNTHESIS_PROMPT = """Synthesize the council responses below into one final answer for the user.

Your final answer must include:
- Main recommendation
- Where the council agrees
- Meaningful disagreement, uncertainty, or tradeoffs
- Recommended path forward with concrete next steps

Keep the answer concise and actionable. If some providers failed, briefly mention that fewer voices were available.

ORIGINAL ADVISOR REQUEST:
{original_prompt}

FAILED PROVIDERS:
{failed_providers}

COUNCIL RESPONSES:
{member_responses}"""

    @classmethod
    def _build_user_prompt(
        cls,
        *,
        template: str,
        journal_context: str,
        intel_context: str,
        profile_context: str = "",
        documents_context: str = "",
        memory_context: str = "",
        thoughts_context: str = "",
        research_context: str = "",
        question: str,
    ) -> str:
        """Assemble user prompt, omitting empty optional sections."""
        raw = template.format(
            journal_context=journal_context,
            intel_context=intel_context,
            profile_context=profile_context,
            documents_context=documents_context,
            memory_context=memory_context,
            thoughts_context=thoughts_context,
            research_context=research_context,
            question=question,
        )
        # Collapse runs of 3+ blank lines into 2
        import re

        return re.sub(r"\n{3,}", "\n\n", raw)

    @classmethod
    def build_council_member_system(cls, base_system: str) -> str:
        return base_system + "\n\n" + cls.COUNCIL_MEMBER_SYSTEM_SUFFIX

    @classmethod
    def build_council_member_prompt(cls, user_prompt: str) -> str:
        return cls.COUNCIL_MEMBER_PROMPT.format(user_prompt=user_prompt)

    @classmethod
    def build_council_synthesis_system(cls, base_system: str) -> str:
        return base_system + "\n\n" + cls.COUNCIL_SYNTHESIS_SYSTEM_SUFFIX

    @classmethod
    def build_council_synthesis_prompt(
        cls,
        *,
        original_prompt: str,
        member_responses: list[dict[str, str]],
        failed_providers: list[str],
    ) -> str:
        rendered_responses = "\n\n".join(
            f"[{response['provider'].upper()}]\n{response['content']}"
            for response in member_responses
        )
        return cls.COUNCIL_SYNTHESIS_PROMPT.format(
            original_prompt=original_prompt,
            failed_providers=", ".join(failed_providers) or "none",
            member_responses=rendered_responses,
        )

    # === Recommendation Prompts ===

    AI_CAPABILITIES_SECTION = """
AI CAPABILITY CONTEXT (current state of AI systems):
{ai_capabilities_context}

When recommending AI-enabled opportunities, cite specific benchmarks and be realistic about limitations.
Identify where recent AI capability gains create new opportunities that weren't viable 6-12 months ago."""

    UNIFIED_RECOMMENDATIONS = """Generate {category} recommendations for this specific user.

=== USER PROFILE ===
{profile_context}

=== RECENT JOURNAL ENTRIES ===
{journal_context}

=== EXTERNAL INTELLIGENCE ===
{intel_context}

BEFORE generating each recommendation, apply this pre-mortem test:
1. Articulate the strongest case that this recommendation is wrong or that the conventional \
wisdom behind it is outdated.
2. Ask: is this advice that was true 18 months ago but may no longer apply? Is it overrepresented \
in internet discourse in a way that inflates its perceived importance?
3. Only after surviving this test should the recommendation proceed.

Generate exactly {max_items} {category} recommendations. Each must be eerily specific to THIS user — \
not something you'd recommend to anyone in their field.

A GOOD recommendation: "Submit a talk proposal to GopherCon 2026 on your service-mesh migration \
experience — the CFP closes March 15 and your 3 years of Go + Istio is exactly what they're looking for. \
This directly supports your goal of building a public profile for the consulting business you want to launch."

A BAD recommendation: "Consider attending industry conferences to expand your network and stay \
current with trends."

The difference: good recommendations name a SPECIFIC action, tie it to a SPECIFIC intel item, \
and explain why it matters given THIS user's specific goals, skills, and constraints.

For each recommendation:

### [Specific, actionable title]
**What**: Concise description of the specific action or opportunity
**Why you, specifically**: Explain the connection between this recommendation and 2-3 specific \
elements from the user's profile (e.g., "Your goal to X + your skill in Y + the fact that Z"). \
Reference their constraints (time, budget, location) if relevant.
**Intel trigger**: Which specific intelligence item or trend prompted this
**Pre-mortem**: The strongest 1-2 sentence case that this recommendation could be wrong
**Next step**: One concrete action they can take this week
RELEVANCE: [1-10 how personally relevant to this user's goals and situation]
FEASIBILITY: [1-10 given their skills, time constraints, and resources]
IMPACT: [1-10 potential to move the needle on their stated goals]
SCORE: [weighted average: 0.5*RELEVANCE + 0.2*FEASIBILITY + 0.3*IMPACT]

**REASONING**
SOURCE: [specific journal entry or intel item that triggered this]
PROFILE_MATCH: [which profile fields this connects to and how]
CONFIDENCE: [0.0-1.0]
CAVEATS: [risks, time commitment, prerequisites]

Skip any recommendation where RELEVANCE < 6. Quality over quantity — return fewer than \
{max_items} if you can't find enough highly relevant items."""

    UNIFIED_RECOMMENDATIONS_WITH_AI = """Generate {category} recommendations for this specific user.

=== USER PROFILE ===
{profile_context}

=== RECENT JOURNAL ENTRIES ===
{journal_context}

=== EXTERNAL INTELLIGENCE ===
{intel_context}
{ai_capabilities_section}

BEFORE generating each recommendation, apply this pre-mortem test:
1. Articulate the strongest case that this recommendation is wrong or that the conventional \
wisdom behind it is outdated.
2. Ask: is this advice that was true 18 months ago but may no longer apply? Is it overrepresented \
in internet discourse in a way that inflates its perceived importance? For AI-related recs, \
are benchmarks cited from a period that no longer reflects the current state?
3. Only after surviving this test should the recommendation proceed.

Generate exactly {max_items} {category} recommendations. Each must be eerily specific to THIS user — \
not something you'd recommend to anyone in their field.

A GOOD recommendation: "Build an AI-powered code review bot using Claude's tool-use API for your \
team's Django codebase — your Python expertise (5/5) means you can prototype in a weekend, and your \
manager mentioned wanting to improve PR turnaround. Claude's function calling accuracy is >90% per \
recent benchmarks, making this viable now."

A BAD recommendation: "Explore AI tools to improve your workflow."

The difference: good recommendations name a SPECIFIC action, tie it to SPECIFIC intel and benchmarks, \
and explain why it matters given THIS user's specific goals, skills, and constraints.

For each recommendation:

### [Specific, actionable title]
**What**: Concise description of the specific action or opportunity
**Why you, specifically**: Explain the connection between this recommendation and 2-3 specific \
elements from the user's profile. Reference their constraints (time, budget, location) if relevant. \
Cite specific AI capability benchmarks when relevant.
**Intel trigger**: Which specific intelligence item, trend, or benchmark prompted this
**Pre-mortem**: The strongest 1-2 sentence case that this recommendation could be wrong
**Next step**: One concrete action they can take this week
RELEVANCE: [1-10 how personally relevant to this user's goals and situation]
FEASIBILITY: [1-10 given their skills, time constraints, and resources]
IMPACT: [1-10 potential to move the needle on their stated goals]
SCORE: [weighted average: 0.5*RELEVANCE + 0.2*FEASIBILITY + 0.3*IMPACT]

**REASONING**
SOURCE: [specific journal entry or intel item that triggered this]
PROFILE_MATCH: [which profile fields this connects to and how]
CONFIDENCE: [0.0-1.0]
CAVEATS: [risks, time commitment, prerequisites]

Skip any recommendation where RELEVANCE < 6. Quality over quantity — return fewer than \
{max_items} if you can't find enough highly relevant items. Cite AI benchmarks when \
recommending AI-enabled opportunities. Be realistic about current AI limitations."""

    TOP_PICKS = """You are selecting the most important actions for this user this week from a pool \
of recommendations across multiple categories.

=== USER PROFILE ===
{profile_context}

=== ALL RECOMMENDATIONS (across categories) ===
{all_recommendations}

Select the {max_picks} most important recommendations. Rank by: urgency (time-sensitive items \
first), impact on stated goals, and feasibility given constraints.

For each pick, output:

### TOP {rank}: [{category}] {title}
**Why this is #{{rank}} this week**: 1-2 sentences explaining why this rises above the others \
right now — cite time-sensitivity, goal alignment, or compounding value.
**Key action**: The single most important thing to do this week toward this.
ORIGINAL_SCORE: {original_score}
PICK_RANK: {rank}

After the picks, add:

### Parked for later
List 2-3 good recommendations that didn't make the cut this week with a one-line reason why \
they can wait (e.g., "no deadline pressure", "depends on completing X first").

Be ruthless about prioritization. The user has {weekly_hours} hours/week. \
Three focused actions beat ten scattered ones."""

    WEEKLY_ACTION_BRIEF = """Generate a weekly action brief with the top prioritized recommendations.

USER PROFILE (from journal):
{journal_context}

RECENT INTELLIGENCE:
{intel_context}

TOP RECOMMENDATIONS:
{recommendations}

Create a focused action brief with 3-5 priority items for this week.

# Weekly Action Brief - {date}

## Priority Actions This Week

For each item:
### [Priority Number]. [Category]: [Title] [Score: X.X]
**Why Now**: Time-sensitive rationale
**Context**: Brief background from journal/intel
**This Week**: Specific actions for the next 7 days
**Success Metric**: How to know progress was made

End with:
## Quick Wins (optional low-effort items)
## Items to Revisit Next Week

Be specific and actionable. Each item should have clear first steps."""

    ACTION_PLAN = """Generate a concrete action plan for this recommendation.

RECOMMENDATION:
Title: {title}
Category: {category}
Description: {description}
Rationale: {rationale}

USER CONTEXT:
{journal_context}

Create a step-by-step action plan with:

## Week 1: Getting Started
- 2-3 specific, actionable tasks
- Required resources or tools

## Week 2-3: Building Momentum
- 2-3 intermediate milestones
- Potential blockers and solutions

## Week 4+: Completion
- Final deliverables
- How to measure success

## Resources
- Specific links, courses, or tools (if applicable)

## Success Criteria
- 2-3 measurable outcomes

Be specific and practical. Each step should be completable in 1-2 hours."""

    # === Adversarial / Contrarian Prompts ===

    INTEL_CONTRADICTION_CHECK = """Does anything in the following current intelligence contradict, \
complicate, or add important nuance to this recommendation? List any relevant items and explain \
how they affect the recommendation's validity. If nothing contradicts it, say so explicitly.

RECOMMENDATION:
Title: {title}
Description: {description}
Rationale: {rationale}

CURRENT INTELLIGENCE (most recent scraped items):
{recent_intel}

Respond with:
CONTRADICTIONS: [list any items that contradict or complicate the recommendation, or "None found"]
NUANCE: [any important context that should temper the recommendation, or "None"]
VERDICT: [SUPPORTED / COMPLICATED / CONTRADICTED] — one word"""

    ADVERSARIAL_CRITIC = """You are a contrarian technology analyst with a track record of being \
right by questioning consensus. You have been shown the following recommendation generated for \
a user. Your job is to steelman the case against it.

USER PROFILE:
{profile_context}

RECOMMENDATION:
Title: {title}
Description: {description}
Rationale: {rationale}
Pre-mortem from generator: {premortem}

INTELLIGENCE USED:
{intel_summary}

LIVE INTEL CHECK:
{intel_contradictions}

Respond with EXACTLY these fields:

CHALLENGE: [The strongest argument that this recommendation is wrong or misleading — be specific, \
not vaguely contrarian. Reference concrete trends, market shifts, or logical gaps.]
MISSING_CONTEXT: [What information the model may be missing that would change the recommendation. \
What would you want to know before acting on this?]
ALTERNATIVE: [An alternative recommendation if you have one, or "null" if you broadly agree \
with the original despite your challenge]
CONFIDENCE: [High / Medium / Low]
CONFIDENCE_RATIONALE: [One sentence explaining the rating. High = strong evidence supports it \
and the challenge is weak. Medium = reasonable but material uncertainty exists. Low = significant \
chance this is wrong or outdated.]"""

    TOP_PICK_CONTRARIAN = """This is the app's top recommendation for this user this week. \
Before confirming it, check: is there a strong argument that the OPPOSITE of this \
recommendation is actually better advice?

USER PROFILE:
{profile_context}

TOP RECOMMENDATION:
Title: {title}
Description: {description}
Rationale: {rationale}
Critic challenge: {critic_challenge}

CURRENT INTELLIGENCE:
{recent_intel}

If the case for the opposite is genuinely strong — not just contrarian for its own sake — \
surface the alternative as the top pick instead, with explanation. If not, confirm the original.

Respond with:
FLIP: [YES / NO]
REASONING: [Why the opposite is better (if FLIP=YES) or why the original stands (if FLIP=NO)]
ALTERNATIVE_TITLE: [Alternative recommendation title if FLIP=YES, otherwise "null"]
ALTERNATIVE_DESCRIPTION: [1-2 sentence alternative if FLIP=YES, otherwise "null"]"""

    EVENT_RECOMMENDATIONS = """Based on the user's profile and upcoming events, recommend events to attend.

USER PROFILE:
{journal_context}

UPCOMING EVENTS:
{intel_context}

For each recommended event:

### [Event Name]
**Date**: When it happens
**Location**: Where (or Online)
**Why Attend**: Why this is relevant to them specifically (cite profile/journal)
**What to Get Out of It**: Networking, skills, speaking opportunity, etc.
**Deadlines**: CFP deadline, early-bird registration, etc.
SCORE: [0-10]
**Action**: Specific next step (register, submit CFP, etc.)

Prioritize time-sensitive items first (CFP deadlines closing soon, early-bird pricing ending)."""

    SKILL_GAP_ANALYSIS = """Analyze the gap between the user's current skills and their career aspirations.

USER PROFILE:
{profile_context}

JOURNAL CONTEXT (goals, reflections):
{journal_context}

USER QUESTION: {question}

Provide:
1. **Current Strengths** — What they're already good at
2. **Critical Gaps** — Skills they need for their aspirations but lack or are weak in
3. **Recommended Priority** — Which gaps to close first and why
4. **Industry Context** — How these gaps relate to market demand

For each gap:
- Skill name
- Current level (from profile, 1-5)
- Target level needed
- Importance (high/medium/low)
- Why it matters for their aspirations"""

    # DEPRECATED — kept for reference, replaced by goal milestones
    LEARNING_PATH_GENERATION = """Generate a structured learning path for the specified skill.

USER PROFILE:
{profile_context}

TARGET SKILL: {skill_name}
CURRENT LEVEL: {current_level}
TARGET LEVEL: {target_level}
LEARNING STYLE: {learning_style}
WEEKLY HOURS AVAILABLE: {weekly_hours}

Create a multi-week curriculum:

# Learning Path: {skill_name}

## Overview
Brief description of the path and expected outcomes.

## Modules

For each module (~1 week):
### Module N: [Title]
**Focus**: What you'll learn
**Resources**:
- Specific courses, docs, tutorials (include URLs where possible)
- Match to learning style ({learning_style})
**Project**: Small hands-on exercise
**Milestone**: How to know you've completed this module

## Final Project
A capstone project that demonstrates mastery.

## Success Criteria
How to know the learning path is complete.

Keep resources practical and specific. Prefer free resources when available."""

    PROJECT_RECOMMENDATIONS = """Based on the user's skills and interests, recommend open-source projects to contribute to.

USER PROFILE:
{journal_context}

AVAILABLE ISSUES/PROJECTS:
{intel_context}

For each recommendation:

### [Project/Issue Title]
**Repository**: Name and URL
**Why**: Why this matches their skills and interests
**Difficulty**: Easy/Medium/Hard
**Learning Potential**: What they'll learn from contributing
**First Step**: How to get started
SCORE: [0-10]"""

    SIDE_PROJECT_IDEAS = """Based on the user's journal entries (pain points, interests, ideas), suggest side-project ideas.

USER PROFILE:
{profile_context}

JOURNAL CONTEXT (frustrations, ideas, interests):
{journal_context}

Generate 3-5 side-project ideas. For each:

### [Project Idea Name]
**Problem**: What pain point this solves (cite journal entries)
**Description**: What the project does
**Tech Stack**: Suggested technologies (aligned with user's skills)
**Scope**: Weekend project / 1-month / 3-month
**Learning Value**: What new skills they'd develop
**Market Potential**: Could this become a product? (honest assessment)
SCORE: [0-10]"""

    AGENTIC_SYSTEM = """You are a professional AI coach with access to the user's journal, goals, intelligence feed, and profile.

Use tools to look up information before answering. Don't guess — search first.
You can also take actions when the user asks (create goals, check in, write journal entries).

Guidelines:
- Search journal/intel for relevant context before giving advice
- Check goal status when discussing progress
- Be concise and actionable
- Call multiple tools if needed for complete context
- Don't over-fetch — be strategic about which tools to call"""

    @classmethod
    def build_agentic_system(cls, goals_summary: str = "") -> str:
        """Build coaching-oriented system prompt, injecting active goals when available."""
        base = (
            "You are a proactive AI coach. Your primary job is helping the user make "
            "measurable progress on their goals.\n\n"
            "COACHING MANDATE:\n"
            "- Always check the user's goals before advising — tie every suggestion to a goal\n"
            "- Suggest specific events, projects, learning resources, and concrete actions\n"
            "- When a goal is stale, nudge the user with a concrete next step\n"
            "- Use goal_next_steps to get enriched context (progress, matching intel, related journal) "
            "before coaching on a specific goal\n"
            "- Prefer actionable specifics over generic encouragement\n\n"
            "Use tools to look up information before answering. Don't guess — search first.\n"
            "You can also take actions when the user asks (create goals, check in, write journal entries).\n\n"
            "Guidelines:\n"
            "- Search journal/intel for relevant context before giving advice\n"
            "- Check goal status when discussing progress\n"
            "- Be concise and actionable\n"
            "- Call multiple tools if needed for complete context\n"
            "- Don't over-fetch — be strategic about which tools to call"
        )

        if goals_summary:
            base += f"\n\nACTIVE GOALS:\n{goals_summary}"

        return base

    MILESTONE_GENERATION = """Generate ordered milestones for this goal.

GOAL TITLE: {goal_title}
GOAL TYPE: {goal_type}
GOAL CONTENT:
{goal_content}

USER CONTEXT:
{profile_context}

Generate 4-8 ordered milestones that break this goal into achievable steps.
For "learning" type goals, milestones should correspond to learning steps calibrated to the user's learning style and available weekly hours.
For other types, milestones should be concrete, measurable checkpoints.

Output ONLY a numbered list (1. First milestone, 2. Second milestone, etc).
Each milestone should be a concise, actionable title (under 80 chars).
Do not include any other text."""

    # DEPRECATED — kept for reference, replaced by goal milestones
    CHECK_IN_ANALYSIS = """Analyze this learning check-in and provide brief adaptive feedback.

SKILL: {skill}
MODULE {module_number}: {module_title}
ACTION: {action}
CHECK-IN HISTORY: {check_in_history}
PROGRESS: {completed}/{total} modules

Provide 2-3 sentences: acknowledge the action, suggest what to focus on next, and any encouragement or adjustment based on the pattern of check-ins."""

    # DEPRECATED — kept for reference, replaced by goal milestones
    DEEP_DIVE_GENERATION = """Generate a deep-dive subsection for this learning module.

SKILL: {skill}
MODULE: {module_title}
MODULE CONTENT:
{module_content}

Create a focused deep-dive that:
- Expands on the most important concept in this module
- Includes a practical exercise or worked example
- Adds 2-3 additional resources (prefer free)

Format as markdown starting with #### Deep Dive. Keep under 500 words."""

    @classmethod
    def get_prompt(
        cls,
        prompt_type: str,
        with_research: bool = False,
        xml_delimiters: bool = False,
        extended: bool = False,
    ) -> str:
        """Get prompt template by type.

        Args:
            prompt_type: Type of prompt
            with_research: If True and general, use research-aware template
            xml_delimiters: If True and general+extended, use XML-delimited template
            extended: If True and general, use template with separate profile/memory/thoughts slots
        """
        prompts = {
            "career": cls.CAREER_ADVICE,
            "weekly_review": cls.WEEKLY_REVIEW,
            "goals": cls.GOAL_ANALYSIS,
            "opportunities": cls.OPPORTUNITY_DETECTION,
            "skill_gap": cls.SKILL_GAP_ANALYSIS,
            "general": cls.GENERAL_ASK,
            "general_with_research": cls.GENERAL_ASK_WITH_RESEARCH,
            "action_plan": cls.ACTION_PLAN,
        }

        if prompt_type == "general" and extended:
            if xml_delimiters:
                if with_research:
                    return cls.GENERAL_ASK_XML_WITH_RESEARCH
                return cls.GENERAL_ASK_XML
            if with_research:
                return cls.GENERAL_ASK_EXTENDED_WITH_RESEARCH
            return cls.GENERAL_ASK_EXTENDED

        if prompt_type == "general" and with_research:
            return prompts["general_with_research"]
        return prompts.get(prompt_type, cls.GENERAL_ASK)

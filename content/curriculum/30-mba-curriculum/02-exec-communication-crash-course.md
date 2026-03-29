# Module 2: Executive Communication & Influence

**Time Investment:** ~10 hours
**Deep-Dive Book:** *The Pyramid Principle* by Barbara Minto

---

## Why This Matters for You

Technical PMs often have the best ideas in the room—and the worst success rate at getting them funded. The gap isn't intelligence. It's communication architecture. Executives process information differently than engineers. They're time-starved, context-switching constantly, and optimizing for decisions, not understanding.

**What AI can do:** Summarize, structure, polish prose, generate slides.
**What you must do:** Read the room, choose what matters, build relationships, deliver hard truths, influence without authority.

---

## Part 1: The Pyramid Principle

### The Core Idea

Most people communicate inductively: build up evidence → reach conclusion.

Executives need the inverse: conclusion first → supporting evidence on demand.

```
INDUCTIVE (how engineers think):
"We analyzed user data, found drop-off at step 3,
tested 5 variations, the winner improved conversion
by 12%, so we should ship variant B."

PYRAMID (how execs need it):
"We should ship variant B—it improves conversion 12%.
We found the problem at step 3, tested 5 variants."
```

Same information. Radically different processing burden.

### The Structure

```diagram
{
  "title": "Pyramid structure",
  "note": "Lead with the answer, then group the supporting logic underneath it.",
  "nodes": [
    {
      "id": "main-point",
      "title": "Main point",
      "detail": "The answer or recommendation.",
      "column": 2,
      "row": 1,
      "tone": "accent"
    },
    {
      "id": "support-1",
      "title": "Key support 1",
      "detail": "First major supporting argument.",
      "column": 1,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "support-2",
      "title": "Key support 2",
      "detail": "Second major supporting argument.",
      "column": 2,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "support-3",
      "title": "Key support 3",
      "detail": "Third major supporting argument.",
      "column": 3,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "subpoints",
      "title": "Sub-points",
      "detail": "Drill into detail only as needed.",
      "column": 2,
      "row": 3,
      "tone": "default"
    }
  ],
  "edges": [
    { "from": "main-point", "to": "support-1" },
    { "from": "main-point", "to": "support-2" },
    { "from": "main-point", "to": "support-3" },
    { "from": "support-1", "to": "subpoints" },
    { "from": "support-2", "to": "subpoints" },
    { "from": "support-3", "to": "subpoints" }
  ]
}
```

**Rules:**
1. Start with the answer
2. Group supporting arguments (max 3-5)
3. Each group shares a logical theme
4. Drill down only if asked

### SCQA Framework

For situations where you need to set context before the answer:

- **S**ituation: The known, stable context
- **C**omplication: What changed, what's wrong
- **Q**uestion: The question this raises (often implicit)
- **A**nswer: Your recommendation

**Example:**

```
SITUATION: We launched the new checkout flow in Q1.

COMPLICATION: Conversion dropped 8% in the first month,
costing ~$2M ARR.

QUESTION: (implicit) What should we do?

ANSWER: Roll back to the old flow while we fix three
specific UX issues identified in user testing.
```

### The "So What?" Test

Every statement should pass the "So what?" test. If an exec can respond "So what?" and you have no answer, cut it.

```
BAD: "We interviewed 50 customers last quarter."
So what?

BETTER: "Customer interviews revealed pricing is our
#1 barrier to enterprise adoption, blocking $5M pipeline."
```

### Practical Application

**Before sending that email/doc:**
1. What's my main point? (one sentence)
2. What are the 2-3 key supports?
3. Have I buried the lede?
4. Does every paragraph pass "So what?"

---

## Part 2: Influencing Without Authority

### The Reality

As a PM, you have responsibility without authority. You can't fire engineers. You can't force sales to prioritize. You can't mandate exec attention.

Influence is your only lever. And influence is built, not demanded.

### Stakeholder Mapping

**Power/Interest Grid:**

```
                HIGH INTEREST
                     │
         KEEP        │        MANAGE
       SATISFIED     │        CLOSELY
                     │
 LOW ────────────────┼──────────────── HIGH
 POWER               │               POWER
                     │
         MONITOR     │         KEEP
         (minimal)   │        INFORMED
                     │
                LOW INTEREST
```

**For each stakeholder:**
1. What do they care about?
2. What do they fear?
3. What does success look like to them?
4. What's their decision-making style?
5. Who influences them?

### Influence Strategies by Stakeholder

**The Skeptic (challenges everything)**
- Lead with data, not vision
- Acknowledge counterarguments explicitly
- Ask for their input before finalizing
- Give them "wins" in the process

**The Busy Exec (no time for you)**
- Extreme brevity (one paragraph max)
- Attach detailed docs for later
- Make the ask crystal clear
- Create artificial urgency if needed

**The Consensus-Builder (won't decide alone)**
- Pre-wire other stakeholders
- Show broad support
- Make it easy to say yes
- Reduce perceived risk

**The Data-Driven (needs proof)**
- Lead with numbers
- Show methodology
- Provide benchmark comparisons
- Offer to run experiments

**The Visionary (wants the big picture)**
- Connect to strategy
- Paint the future state
- Minimize tactical details
- Appeal to ambition

### The Pre-Wire

Never walk into a meeting hoping to get a decision. Pre-wire key stakeholders:

1. **Identify decision-makers and influencers**
2. **Meet 1:1 before the meeting**
3. **Get their concerns on the table**
4. **Adjust your proposal based on input**
5. **Confirm their support before the room**

The meeting should be confirmation, not persuasion.

### Building Influence Capital

Long-term influence comes from:

**Competence** — Deliver what you promise. Nothing builds trust like consistent execution.

**Reliability** — Do what you say you'll do. Follow up. Close loops.

**Likability** — People help people they like. Be genuinely interested in others' success.

**Reciprocity** — Help others without keeping score. It comes back.

**Knowledge** — Become the expert on something valuable. Information is power.

---

## Part 3: Board & Exec Communication

### What Executives Actually Care About

Executives are paid to:
1. Allocate capital (where to invest)
2. Manage risk (what could kill us)
3. Drive growth (how do we win)
4. Build organization (who do we need)

Filter everything through these lenses.

**They don't care about:**
- Technical implementation details
- Process improvements (unless massive)
- Your workload or challenges
- Interesting data without implications

### The Exec Update Structure

```
1. HEADLINE (1 sentence)
   What's the one thing they need to know?

2. STATUS (traffic light)
   Green/Yellow/Red with brief explanation

3. KEY METRICS (3-5 max)
   Trend + context + implication

4. DECISIONS NEEDED (if any)
   Clear options with recommendation

5. RISKS/BLOCKERS (if any)
   What might derail us + mitigation

6. NEXT MILESTONES
   What's happening next + when
```

**Example Exec Update:**

```
SEARCH RANKING PROJECT — YELLOW

Headline: Behind schedule by 2 weeks due to
infrastructure dependency; on track for revised date.

Metrics:
- Relevance score: 0.82 → 0.89 (+8%, target 0.90)
- Query latency: 45ms → 38ms (target <50ms ✓)
- Coverage: 78% of corpus indexed (target 95%)

Decision Needed: Prioritize coverage vs latency optimization
for remaining sprint. Recommend coverage—latency already
meets bar.

Risk: ML training data pipeline has single point of
failure. Mitigation: backup pipeline ships next week.

Next: 95% coverage milestone in 2 weeks.
```

### Board Communication

Board members are further removed. They need:

1. **Strategic context** — How does this fit the big picture?
2. **Competitive framing** — How do we compare to market?
3. **Financial impact** — What's the $ implication?
4. **Risk assessment** — What keeps you up at night?
5. **Forward-looking** — What's coming next quarter/year?

**Board members hate:**
- Surprises (especially negative)
- Jargon they have to decode
- Defensive posturing
- Missing context on numbers
- Vague status updates

### The 30-Second Elevator Version

For every project/initiative, have ready:

```
"[PROJECT NAME] is [ONE SENTENCE DESCRIPTION].

We're at [STATUS] because [BRIEF WHY].

The key question is [DECISION OR UNCERTAINTY].

Next step is [CONCRETE ACTION] by [DATE]."
```

Practice until it's automatic.

---

## Part 4: Storytelling With Data

### Why Stories + Data

Data convinces the rational brain. Stories convince the emotional brain. Decisions happen when both agree.

Data without story: "Interesting, but I don't feel urgency."
Story without data: "Nice anecdote, but is it representative?"
Data + story: "I understand and I care. Let's act."

### The Structure

```
1. ANCHOR (the human moment)
   A specific user, customer, or scenario

2. TENSION (the problem quantified)
   Data showing the scale of pain

3. RESOLUTION (the path forward)
   Your solution with projected impact

4. PROOF (validation)
   Data showing it works
```

**Example:**

```
ANCHOR: "Sarah is a finance manager at Acme Corp.
Last Tuesday, she spent 4 hours recreating a report
that our system deleted after a sync error."

TENSION: "Sarah isn't alone. 3,200 users hit this bug
last month. Average time lost: 2.5 hours. That's 8,000
hours of customer productivity lost—and 47 escalations
to our CEO."

RESOLUTION: "The fix requires 2 engineering sprints.
We'll implement auto-save with conflict resolution."

PROOF: "We piloted this with 50 users. Zero data loss.
NPS for that cohort jumped 22 points."
```

### Data Visualization Principles

**Choose the right chart:**
- Comparison across categories → Bar chart
- Trend over time → Line chart
- Part of whole → Pie/Donut (only if <5 segments)
- Relationship between variables → Scatter plot
- Distribution → Histogram

**Design principles:**
- One message per chart
- Title states the insight, not the category
- Remove chartjunk (3D effects, excessive gridlines)
- Use color intentionally (highlight, don't decorate)
- Label directly (avoid legend hunting)

**Bad title:** "Monthly Revenue by Region"
**Good title:** "APAC Revenue Surpassed North America for First Time"

### Numbers That Stick

Raw numbers are forgettable. Comparisons stick.

```
FORGETTABLE: "We have 50 million users."

MEMORABLE: "More people use our product than the
population of Spain."

FORGETTABLE: "The bug affects 0.3% of users."

MEMORABLE: "That's 15,000 people—roughly everyone
in a small town—hitting this error every day."
```

**Techniques:**
- Compare to familiar quantities
- Make it human (# of people, not %)
- Calculate time/money impact
- Use "per day/week/month" vs annual totals

---

## Part 5: Managing Up

### Understanding Your Exec

Before you can manage up, you must understand:

1. **What are their goals this quarter/year?**
2. **What are they measured on?**
3. **What are their pain points?**
4. **How do they prefer to receive information?**
5. **What frustrates them?**
6. **Who are they trying to impress?**

Ask them directly: "What's the most important thing I can help you with this quarter?"

### Alignment Tactics

**The 1:1 strategy:**
- Come with an agenda (respect their time)
- Lead with their priorities, not yours
- Bring decisions, not just updates
- Flag risks early (no surprises)
- Ask what success looks like

**The pre-read:**
- Send docs 24+ hours before meetings
- Include a TL;DR at the top
- Highlight decisions needed
- Make it skimmable

**The follow-up:**
- Send notes after key meetings
- Include decisions made + owners + dates
- Make it the official record

### Managing Expectations

**Under-promise, over-deliver:** Build in buffer. Exceed the conservative estimate.

**The 90% rule:** If you're 90% confident in a date, give a date 10% later. Being early is celebrated. Being late is remembered.

**Progressive disclosure:** Share early estimates with ranges. Narrow as you learn.

```
WEEK 1: "Rough estimate: 4-8 weeks"
WEEK 3: "Refined: 5-6 weeks"
WEEK 5: "Committed: shipping March 15"
```

### When Your Exec Is Wrong

This happens. How you handle it defines your career.

**The approach:**
1. Assume positive intent and incomplete information
2. Ask questions before asserting
3. Present as "additional data" not "correction"
4. Give them a path to change position gracefully
5. If they still disagree, execute their decision fully (unless ethical issue)

**The phrasing:**

```
WRONG: "I disagree. The data shows you're wrong."

RIGHT: "That's helpful context. I want to share some
data points I've seen that might affect the decision.
[Share data.] Given this, would you still recommend X,
or should we consider Y?"
```

---

## Part 6: Difficult Conversations

### Delivering Bad News

**The structure:**
1. Be direct (don't soften excessively)
2. State the news clearly
3. Explain the impact
4. Take accountability where appropriate
5. Present the path forward
6. Open for questions

**Example:**

```
"I need to share some difficult news about the launch.

We're going to miss our March 1 date by two weeks.
The integration with the payments provider hit unexpected
complexity.

This means we'll miss the marketing campaign window.
Rachel is working on adjusted plans.

I should have flagged the risk earlier when we first
saw the technical complexity. That's on me.

The path forward: March 15 launch is high confidence,
and we're adding engineering support to de-risk.

What questions do you have?"
```

### Receiving Feedback

**In the moment:**
- Thank them genuinely
- Resist defensiveness (breathe)
- Ask clarifying questions
- Paraphrase to confirm understanding
- Ask for examples if abstract

**After:**
- Reflect honestly
- Separate valid criticism from delivery issues
- Make visible changes
- Follow up on progress

**The killer move:** Proactively ask for feedback. "What's one thing I could do differently to be more effective?" Then actually change.

### Giving Critical Feedback

**The SBI Model:**
- **S**ituation: When/where
- **B**ehavior: What they did (observable, specific)
- **I**mpact: The effect of the behavior

**Example:**

```
"In yesterday's meeting (situation), when you cut off
Sarah mid-sentence (behavior), she stopped contributing
and the team missed her perspective on the technical
approach (impact).

I'd love to see you pause a beat before responding in
group settings. What do you think?"
```

**Never:**
- Deliver critical feedback in public
- Stack multiple criticisms in one conversation
- Use "always" or "never"
- Attribute motivation ("you did this because...")

---

## Part 7: Written vs Verbal

### When to Use Each

**Use WRITTEN when:**
- Complex information needs reference
- Documentation of decision/agreement needed
- Recipient needs time to process
- Async is acceptable/preferred
- Multiple stakeholders need same message

**Use VERBAL when:**
- Sensitive or emotional topic
- Need real-time reactions/course correction
- Building relationship
- Persuasion required
- Speed matters more than precision

**Use BOTH when:**
- High-stakes decisions
- Complex + sensitive
- Need paper trail + human connection

### Writing for Executives

**Email rules:**
- Subject line is a headline (include the ask)
- First sentence is the point
- Bullet points for supporting info
- Explicit ask at the end
- Bold key numbers/deadlines

**Example:**

```
Subject: DECISION NEEDED: Q2 roadmap prioritization by Friday

TL;DR: Requesting approval to deprioritize Feature X
to ship Feature Y two weeks earlier. Revenue impact: +$200K.

Context:
• Feature Y has enterprise customer deadline (Acme, $500K deal)
• Feature X has no external commitments
• Engineering says we can only do one by April 1

Recommendation: Prioritize Y.

I need your decision by Friday EOD to reallocate engineering.

Full analysis attached.
```

### Adapting Your Style

**For detail-oriented execs:**
- Include more supporting data
- Anticipate follow-up questions
- Provide appendices/attachments

**For big-picture execs:**
- Shorter is better
- Focus on strategy/vision alignment
- Minimize tactical detail

**For consensus-builders:**
- Show who else has input/agreed
- Highlight collaborative process
- Emphasize team alignment

**For decisive execs:**
- Strong recommendations
- Clear options with tradeoffs
- Make it easy to decide quickly

---

## Exercises

### Exercise 1: Pyramid Restructure

Take an email you've sent recently (or a doc you wrote). Restructure it using the pyramid principle:

1. What's the main point? (Write it as a single sentence)
2. What are the 2-3 key supporting arguments?
3. Rewrite with the main point first
4. Apply the "So what?" test to every paragraph

Compare the before/after. Which is easier to scan?

**Time:** 45 minutes

### Exercise 2: Stakeholder Map

For a current project or initiative:

1. List all stakeholders who can influence success
2. Plot them on the Power/Interest grid
3. For each high-power stakeholder, answer:
   - What do they care about?
   - What do they fear?
   - How should you communicate with them?
4. Identify one stakeholder you're under-engaging

**Time:** 30 minutes

### Exercise 3: Data Story

Take a product metric that's improved recently. Build a data story:

1. Write the human anchor (one specific user/scenario)
2. Quantify the problem at scale
3. Describe the resolution
4. Present the proof

Deliver this verbally in under 2 minutes to a colleague. Did it land?

**Time:** 1 hour

### Exercise 4: Difficult Conversation Prep

Think of a difficult conversation you need to have (or recently had).

1. Write out exactly what you need to say
2. Use the structures from Part 6
3. Anticipate their likely responses
4. Plan your responses to each
5. Role play with a trusted colleague

**Time:** 45 minutes

### Exercise 5: Executive Update

Write an exec update for your current project using the structure from Part 3:

1. Headline (1 sentence)
2. Status (traffic light + explanation)
3. Key metrics (3-5 max)
4. Decisions needed (if any)
5. Risks/blockers (if any)
6. Next milestones

Have someone outside your team read it. Can they understand the status in 30 seconds?

**Time:** 30 minutes

### Exercise 6: Managing Up Assessment

Answer these questions about your current manager/exec:

1. What are their top 3 priorities this quarter?
2. What frustrates them most?
3. How do they prefer to receive information?
4. What would make them look good to their boss?
5. What's one thing you could do to make their life easier?

If you can't answer these, schedule a 1:1 to find out.

**Time:** 30 minutes

---

## Checklist: Are You Ready?

After completing this module, you should be able to:

- [ ] Restructure any communication using the pyramid principle
- [ ] Apply the SCQA framework for complex situations
- [ ] Map stakeholders and adapt your approach to each
- [ ] Pre-wire key decisions before meetings
- [ ] Write an exec update that conveys status in 30 seconds
- [ ] Build a data story that combines metrics with narrative
- [ ] Deliver bad news directly while maintaining relationship
- [ ] Choose appropriately between written and verbal communication
- [ ] Adapt your communication style to different exec types

---

## Key Frameworks Summary

| Framework | Use When | Structure |
|-----------|----------|-----------|
| Pyramid Principle | Any communication | Answer → Key supports → Details |
| SCQA | Need to set context | Situation → Complication → Question → Answer |
| SBI Feedback | Giving critical feedback | Situation → Behavior → Impact |
| Power/Interest Grid | Stakeholder planning | Map by power and interest level |
| Exec Update | Status reporting | Headline → Status → Metrics → Decisions → Risks → Next |

---

## Common Mistakes

1. **Burying the lede** — The most important information should be first, not last
2. **Too much detail** — Execs want headlines; they'll ask for detail if needed
3. **No clear ask** — Every communication should end with what you need
4. **Surprising people in meetings** — Pre-wire important stakeholders
5. **Data without story** — Numbers need narrative to drive action
6. **Story without data** — Anecdotes need scale to justify investment
7. **One-size-fits-all** — Different execs need different approaches
8. **Defensiveness** — When receiving feedback, absorb before responding

---

## Next Steps

1. **Read:** *The Pyramid Principle* by Barbara Minto — The definitive guide on structured communication. Dense but essential. Focus on Part 1.

2. **Practice:** Do Exercise 1 (Pyramid Restructure) with your last three emails. Notice patterns in how you bury the lede.

3. **Apply:** In your next 1:1 with your manager, explicitly ask: "What's one thing I could communicate differently to be more effective?" Then implement.

---

*Module 3: Strategic Thinking is next.*

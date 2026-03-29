# Module 7: Operations & Execution

**Time Investment:** ~10 hours
**Deep-Dive Book:** *The Goal* by Eliyahu Goldratt

---

## Why This Matters for You

PMs focus on what to build. Operations focuses on how to deliver. Understanding operational thinking—bottlenecks, throughput, continuous improvement—makes you better at roadmap trade-offs, release planning, and understanding why "it's complicated" often means "we have a systems problem."

**What AI can do:** Optimize schedules, analyze workflows, predict capacity.
**What you must do:** Identify the real bottleneck, make difficult trade-offs, improve systems.

---

## Part 1: Theory of Constraints

### The Core Insight

Every system has one constraint that limits overall throughput. Optimizing anything other than the constraint is waste.

**The chain analogy:** A chain's strength equals its weakest link. Strengthening any other link doesn't improve overall strength.

### The Five Focusing Steps

1. **IDENTIFY** the constraint
   - What's limiting the system's output?
   - Follow the work: Where does it pile up?

2. **EXPLOIT** the constraint
   - Make the most of current constraint capacity
   - Don't waste constraint time on non-essential work

3. **SUBORDINATE** everything else
   - All other parts serve the constraint
   - Don't outpace the constraint (creates WIP inventory)

4. **ELEVATE** the constraint
   - Invest to increase constraint capacity
   - Only after exploiting/subordinating

5. **REPEAT**
   - Once resolved, a new constraint emerges
   - Continuous improvement loop

### Finding the Constraint

**Signs of a constraint:**
- Work piles up before this step
- People always waiting on this step
- Schedule always behind here
- Quality issues blamed on rushing through here

**Common constraints:**
- A specific team/person (bottleneck)
- An approval process
- A shared resource (test environment)
- A policy (code review requirements)
- External dependency (vendor, customer)

### Applying TOC to Product Development

**Example: Feature Delivery Pipeline**

```
Idea → Design → Dev → QA → Release

If QA is the constraint:
- Ideas pile up faster than we can ship
- Engineers often waiting on QA feedback
- Releases constantly delayed

EXPLOIT:
- Only have QA test high-value features
- Automate repetitive testing
- Don't context-switch QA team

SUBORDINATE:
- Don't produce more than QA can test
- Match dev capacity to QA capacity
- Earlier QA involvement (shift left)

ELEVATE:
- Hire more QA (if exploit/subordinate insufficient)
- Invest in test automation
- Train engineers in testing
```

### Drum-Buffer-Rope

**The metaphor:** Hikers on a trail. Fastest person at front creates gaps. Slowest person determines group pace.

**Drum:** The constraint sets the pace (beat of the drum)
**Buffer:** Protective inventory before the constraint (ensures it's never starved)
**Rope:** Limits release of new work (prevents overproduction)

**For software:**
- Sprint velocity is your drum
- Work-in-progress limits are your rope
- Ready backlog is your buffer

---

## Part 2: Process Optimization

### Key Metrics

**Throughput:**
- Rate of output (features shipped, tickets closed)
- What matters to customers
- "How much are we producing?"

**Cycle Time:**
- Time from start to finish for one unit
- "How long does one thing take?"
- Lower = faster response

**Lead Time:**
- Time from request to delivery
- Includes wait time
- What customers experience

**Work in Progress (WIP):**
- Items currently in the system
- High WIP = long lead times
- High WIP = context switching

**Utilization:**
- % of capacity being used
- High utilization ≠ high throughput
- 100% utilization = 0% slack = delays cascade

### Little's Law

```
Lead Time = WIP / Throughput
```

**Implications:**
- To reduce lead time: reduce WIP or increase throughput
- High WIP with constant throughput = long waits
- This is math, not opinion

**Example:**
- 20 features in progress
- Ship 5 features per sprint
- Lead time = 20/5 = 4 sprints

**Want 2-sprint lead time?**
- Cut WIP to 10, or
- Increase throughput to 10/sprint

### Why WIP Limits Matter

**High WIP causes:**
- Context switching (cognitive cost)
- Longer feedback loops (don't learn quickly)
- Hidden problems (issues buried in queue)
- Delayed value (customers wait)

**WIP limits force:**
- Finishing before starting
- Identifying blockers (can't hide behind "busy")
- Collaboration (swarm to clear bottlenecks)

### Process Improvement Approaches

**Value Stream Mapping:**
1. Map every step in current process
2. Identify value-add vs waste time
3. Calculate % of time adding value (often <20%)
4. Target waste for elimination

**Waste categories (Lean):**
- Waiting (idle time)
- Transportation (handoffs)
- Overprocessing (unnecessary work)
- Inventory (WIP)
- Motion (searching, context switching)
- Defects (rework)
- Overproduction (building unneeded things)

---

## Part 3: Bottleneck Analysis

### The Bottleneck Is Not Where You Think

**Common assumption:** "Engineering is the bottleneck"
**Reality:** Often it's:
- Decision-making (waiting for approval)
- Requirements clarity (rework from ambiguity)
- Dependencies (other teams, vendors)
- Deployment process (slow release cycles)

### Finding Bottlenecks

**Data approach:**
- Where does work pile up?
- What has longest cycle time stage?
- What causes most delays?

**Observation approach:**
- Walk the process (gemba walk)
- Ask: "What are you waiting on?"
- Watch where people are frustrated

**Queue analysis:**
- Count items waiting at each stage
- Longest queue = likely bottleneck

### Bottleneck Dynamics

**Bottleneck paradox:** Improving non-bottlenecks doesn't improve system throughput—and may make things worse (creates more WIP at bottleneck).

**Example:**
```process-flow
{
  "title": "Bottleneck dynamics",
  "note": "System throughput stays constrained by the narrowest step until that constraint changes.",
  "steps": [
    {
      "title": "Design",
      "detail": "Capacity: 10 per week."
    },
    {
      "title": "Dev",
      "detail": "Capacity: 5 per week and the bottleneck."
    },
    {
      "title": "QA",
      "detail": "Capacity: 8 per week."
    }
  ]
}
```

If Design doubles to 20 per week, Dev still ships only 5 per week. The result is more WIP and longer lead times, not more throughput.

**Correct approach:**
1. Don't increase design capacity
2. Increase Dev capacity (elevate)
3. Or reduce demand on Dev (prioritize better)

### Protecting the Bottleneck

Once identified, protect the constraint:

- **Never idle:** Always have work ready
- **Minimize setup time:** Reduce context switches
- **Quality inputs:** Don't waste constraint time on defective work
- **Reduce interruptions:** Shield from non-essential work

---

## Part 4: Scaling Operations

### What Breaks at Scale

**10 → 100 people:**
- Communication overhead explodes (n² connections)
- Coordination costs dominate
- Informal processes fail
- Context gets lost

**100 → 1000 users:**
- Architecture assumptions break
- Support load increases nonlinearly
- Edge cases become common cases
- Performance problems emerge

**Common scaling failures:**
- Heroic individual efforts stop working
- Tribal knowledge creates bottlenecks
- Processes designed for small scale collapse
- Technical debt compounds

### When to Systematize

**The rule:** Systematize when the cost of not systematizing exceeds the cost of the system.

**Signs you need a system:**
- Same questions asked repeatedly
- Quality varies by who does it
- Information lives in people's heads
- Onboarding takes too long
- Errors from miscommunication

**Signs you're over-systematizing:**
- Process overhead exceeds value
- People routing around the system
- System can't handle exceptions
- Innovation stifled by process

### Scaling Frameworks

**Conway's Law:**
> Organizations design systems that mirror their communication structures.

**Implication:** If you want a certain architecture, organize teams accordingly. Microservices need autonomous teams.

**Two Pizza Teams (Amazon):**
- Teams small enough to feed with two pizzas
- Full ownership of their domain
- Reduces coordination overhead
- Enables parallel work

**API contracts:**
- Define interfaces between teams
- Teams can work independently
- Reduces integration surprises

---

## Part 5: Quality vs Speed Tradeoffs

### The Iron Triangle

```
       SCOPE
        /\
       /  \
      /    \
     /______\
   TIME    QUALITY
```

**You can't optimize all three.** Pick two:
- Fast + Good = Expensive (or small scope)
- Fast + Cheap = Low quality
- Good + Cheap = Slow

### Quality Is Not Free (But It's Cheaper)

**Cost of poor quality:**
- Rework (fix bugs)
- Support (handle complaints)
- Reputation (lost future sales)
- Opportunity cost (not building new things)

**Cost of high quality:**
- More upfront time
- Testing investment
- Slower initial velocity

**The insight:** Quality pays off over time. The breakeven depends on how long the code/product will live.

### Technical Debt

**Definition:** Implied cost of future rework from choosing expedient solution now.

**Types:**
- **Intentional:** Knowingly take shortcut (deadline pressure)
- **Unintentional:** Didn't know better at the time
- **Bit rot:** Code decays as context changes

**Managing technical debt:**
- Make it visible (track in backlog)
- Allocate capacity (20% rule)
- Pay interest (don't let it compound forever)
- Choose debt wisely (some debt is strategic)

### Speed Strategies

**Go faster without sacrificing quality:**

1. **Reduce scope** (not cut corners)
   - Ship smaller increments
   - Focus on core value

2. **Remove waste**
   - Eliminate unnecessary process
   - Automate repetitive work

3. **Parallelize**
   - Work on independent things simultaneously
   - Reduce dependencies

4. **Shift left**
   - Find problems earlier (cheaper to fix)
   - Design reviews, early testing

5. **Increase capability**
   - Better tools
   - Better skills (training)

---

## Part 6: Operational Metrics That Matter

### Choosing Metrics

**Good metrics are:**
- **Actionable:** Change in metric → specific action
- **Accessible:** People can understand and access them
- **Auditable:** Trustworthy, not easily gamed
- **Aligned:** Drive behavior you want

### The Metrics Hierarchy

**Outcome metrics:** What customers experience
- Lead time, quality, availability

**Output metrics:** What you produce
- Features shipped, deployments, tickets closed

**Activity metrics:** What you do
- Commits, PRs, hours worked

**Focus on outcomes.** Activity metrics without outcome connection are vanity.

### Operational Dashboards

**Key elements:**
- Leading indicators (predict future state)
- Lagging indicators (confirm past results)
- Trends over time (not just snapshots)
- Comparison to targets

**DORA metrics (DevOps):**
- Deployment frequency
- Lead time for changes
- Change failure rate
- Time to restore service

These correlate with high-performing engineering organizations.

### Avoiding Metric Dysfunction

**Goodhart's Law:** "When a measure becomes a target, it ceases to be a good measure."

**Examples:**
- Lines of code → verbose, copy-paste code
- Bugs closed → won't-fix everything
- Story points → point inflation

**Countermeasures:**
- Pair metrics (quantity + quality)
- Rotate metrics
- Focus on outcomes over outputs
- Don't tie metrics directly to compensation

---

## Part 7: Continuous Improvement

### The Improvement Cycle

**PDCA (Deming):**
- **Plan:** Identify improvement, design change
- **Do:** Implement change (small scale)
- **Check:** Measure results
- **Act:** Standardize if successful, or adjust

### Kaizen

**Philosophy:** Small, continuous improvements > big, occasional changes

**Principles:**
- Everyone can improve their work
- Small changes are less risky
- Improvement is continuous, never "done"
- Focus on process, not blame

### Retrospectives

**Regular improvement ritual:**
1. What went well?
2. What didn't go well?
3. What will we try differently?

**Keys to effective retros:**
- Psychological safety (no blame)
- Specific, actionable takeaways
- Follow-up on previous commitments
- Focus on process, not personalities

### Learning from Failures

**Blameless post-mortems:**
- Focus on systems, not individuals
- Ask "how" not "who"
- Document learning publicly
- Change systems to prevent recurrence

**Template:**
1. Timeline of events
2. Impact
3. Root cause analysis (5 Whys)
4. Contributing factors
5. Action items with owners

---

## Exercises

### Exercise 1: Find Your Constraint

For a process you're involved in:

1. Map the stages from start to finish
2. Identify where work piles up
3. Calculate cycle time for each stage
4. Identify: What's the constraint?
5. Apply: How would you Exploit? Subordinate? Elevate?

**Time:** 45 minutes

### Exercise 2: WIP Analysis

For your team or project:

1. Count items currently in progress
2. Calculate average throughput (items completed per week)
3. Apply Little's Law: What's your predicted lead time?
4. If you halved WIP, what would lead time be?
5. Propose: What WIP limit would you set?

**Time:** 30 minutes

### Exercise 3: Value Stream Map

For a feature from idea to customer:

1. List every step
2. Estimate time for each step
3. Estimate wait time between steps
4. Calculate: % value-add time
5. Identify: Top 3 waste to eliminate

**Time:** 1 hour

### Exercise 4: Bottleneck Hunting

Over the next week, collect data:

1. Track where you wait for others
2. Track where others wait for you
3. Ask teammates: "What slows you down most?"
4. Synthesize: What's the system bottleneck?
5. Propose: One change to address it

**Time:** Ongoing + 30-minute synthesis

### Exercise 5: Quality Economics

For a recent bug or quality issue:

1. Estimate: Time to find the issue
2. Estimate: Time to fix
3. Estimate: Time for rework (testing, review, deploy)
4. Estimate: Customer impact (support, reputation)
5. Ask: At what stage could this have been caught cheaper?

**Time:** 30 minutes

### Exercise 6: Process Improvement Proposal

Pick one process that frustrates you:

1. Describe current state (steps, time, pain points)
2. Identify the root cause (5 Whys)
3. Propose improved state
4. Define how you'd measure success
5. Plan a small-scale test (PDCA)

**Time:** 45 minutes

---

## Checklist: Are You Ready?

- [ ] Apply Theory of Constraints (identify, exploit, subordinate, elevate)
- [ ] Use Little's Law to predict lead times
- [ ] Identify waste in processes
- [ ] Find the true bottleneck in a system
- [ ] Make quality vs speed tradeoffs explicitly
- [ ] Choose metrics that drive desired behavior
- [ ] Run effective retrospectives and post-mortems
- [ ] Apply PDCA for continuous improvement

---

## Key Frameworks Summary

| Framework | Use When | Core Insight |
|-----------|----------|--------------|
| Theory of Constraints | System optimization | Only the bottleneck matters |
| Little's Law | Predicting performance | Lead Time = WIP / Throughput |
| Value Stream Mapping | Process improvement | Map waste, eliminate it |
| PDCA | Continuous improvement | Plan → Do → Check → Act |
| DORA | Engineering metrics | Deployment freq, lead time, failure rate, MTTR |

---

## Key Concepts Quick Reference

| Concept | Definition |
|---------|------------|
| Throughput | Rate of output |
| Cycle Time | Time to complete one unit |
| Lead Time | Time from request to delivery |
| WIP | Work in Progress |
| Bottleneck | Constraint limiting system throughput |
| Technical Debt | Future cost of expedient solutions |
| Kaizen | Continuous small improvements |

---

## Next Steps

1. **Read:** *The Goal* by Eliyahu Goldratt — Written as a novel about a manufacturing plant, but the principles apply everywhere. Engaging read that makes TOC intuitive.

2. **Practice:** Exercise 2 (WIP Analysis) with your team. The numbers often surprise people.

3. **Observe:** This week, notice where work piles up. Ask yourself: Is this the constraint? What would change if we addressed it?

---

*Module 8: Ethics & AI Governance is next.*

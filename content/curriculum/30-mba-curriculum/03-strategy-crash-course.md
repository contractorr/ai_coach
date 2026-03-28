# Module 3: Strategic Thinking

**Time Investment:** ~10 hours
**Deep-Dive Book:** *Good Strategy Bad Strategy* by Richard Rumelt

---

## Why This Matters for You

Every PM claims to be "strategic." Few actually are. Strategy isn't a roadmap. It's not goals. It's not mission statements. Strategy is a coherent set of choices about where to play and how to winâ€”and critically, what *not* to do.

**What AI can do:** Analyze markets, model scenarios, synthesize competitive data.
**What you must do:** Make hard tradeoffs, choose what to abandon, commit under uncertainty, align humans around a direction.

---

## Part 1: What Strategy Actually Is

### Rumelt's Kernel

Richard Rumelt argues most "strategies" are actually goals in disguise. Real strategy has three parts:

```framework
{
  "title": "Rumelt's kernel of strategy",
  "note": "Use this to separate a real strategy from a vague goal statement.",
  "pillars": [
    {
      "title": "Diagnosis",
      "detail": "Describe the challenge clearly before proposing action.",
      "bullets": [
        "Name what is actually happening in the market or organization.",
        "Focus on the obstacle, not the aspiration."
      ]
    },
    {
      "title": "Guiding Policy",
      "detail": "Choose the overall approach that responds to the diagnosis.",
      "bullets": [
        "Make a directional choice that rules out alternatives.",
        "State the principle that will guide later decisions."
      ]
    },
    {
      "title": "Coherent Actions",
      "detail": "List the reinforcing actions that execute the policy.",
      "bullets": [
        "Make sure the actions support each other.",
        "Tie timelines, resources, and tradeoffs back to the guiding policy."
      ]
    }
  ]
}
```

**Bad "strategy":** "We will be the market leader in AI-powered analytics through innovation and customer focus."

This is a goal with buzzwords. No diagnosis, no choices, no actions.

**Good strategy:**

```
DIAGNOSIS: Enterprise customers want AI analytics but
won't adopt due to data security concerns. Competitors
are cloud-only.

GUIDING POLICY: Offer the only on-premise AI analytics
solution for regulated industries.

COHERENT ACTIONS:
- Build on-prem deployment capability (6 months)
- Get SOC2 + HIPAA certified (3 months)
- Hire enterprise sales team focused on healthcare/finance
- Price at 2x cloud competitors (security premium)
- Partner with compliance consultants for distribution
```

This is strategy: diagnosis of the real challenge, a clear choice (on-prem vs cloud), and coordinated actions.

### Strategy vs Goals vs Tactics

```comparison-table
{
  "title": "Strategy vs. goals vs. tactics",
  "columns": [
    { "key": "concept", "label": "Concept" },
    { "key": "definition", "label": "Definition" },
    { "key": "example", "label": "Example" }
  ],
  "rows": [
    {
      "concept": "Vision",
      "definition": "Aspirational end state.",
      "example": "Organize the world's information."
    },
    {
      "concept": "Mission",
      "definition": "What you do and for whom.",
      "example": "Search engine for everyone."
    },
    {
      "concept": "Goals",
      "definition": "Measurable targets.",
      "example": "50% market share by 2025."
    },
    {
      "concept": "Strategy",
      "definition": "How you'll achieve goals.",
      "example": "Win through superior relevance ranking."
    },
    {
      "concept": "Tactics",
      "definition": "Specific actions.",
      "example": "Ship PageRank algorithm."
    }
  ]
}
```

Most orgs confuse goals for strategy. "Grow revenue 30%" isn't a strategyâ€”it's a goal. Strategy explains *how*.

### The Strategy Test

Ask these questions of any "strategy":

1. **Does it make a clear choice?** If it doesn't say what you *won't* do, it's not strategy.
2. **Is it a response to a real challenge?** Generic strategies are useless.
3. **Do the actions reinforce each other?** Coherent actions compound; random initiatives don't.
4. **Could a competitor copy this easily?** If yes, it's not a source of advantage.

---

## Part 2: Porter's Five Forces

### The Framework

Michael Porter's model for analyzing industry attractiveness:

```diagram
{
  "title": "Porter's five forces",
  "note": "Read the center first, then evaluate how each surrounding force changes industry profit potential.",
  "nodes": [
    {
      "id": "entrants",
      "title": "Threat of New Entrants",
      "detail": "New players can enter when barriers are low.",
      "column": 2,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "suppliers",
      "title": "Bargaining Power of Suppliers",
      "detail": "Suppliers capture value when alternatives are limited.",
      "column": 1,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "rivalry",
      "title": "Competitive Rivalry",
      "detail": "Existing competitors pressure pricing, margins, and differentiation.",
      "column": 2,
      "row": 2,
      "tone": "accent"
    },
    {
      "id": "buyers",
      "title": "Bargaining Power of Buyers",
      "detail": "Customers gain leverage when switching is easy or concentration is high.",
      "column": 3,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "substitutes",
      "title": "Threat of Substitutes",
      "detail": "Alternative solutions cap pricing power.",
      "column": 2,
      "row": 3,
      "tone": "muted"
    }
  ],
  "edges": [
    { "from": "entrants", "to": "rivalry", "label": "raises pressure" },
    { "from": "suppliers", "to": "rivalry", "label": "captures value" },
    { "from": "buyers", "to": "rivalry", "label": "demands concessions" },
    { "from": "substitutes", "to": "rivalry", "label": "caps prices" }
  ]
}
```

### The Forces Explained

**1. Competitive Rivalry**
- How intense is competition among existing players?
- More competitors = more pressure on prices/margins
- High rivalry when: slow growth, high fixed costs, low differentiation

**2. Threat of New Entrants**
- How easy is it for new players to enter?
- Barriers: capital requirements, economies of scale, switching costs, regulations
- Low barriers = profits attract entrants = margins erode

**3. Bargaining Power of Suppliers**
- Can suppliers raise prices or reduce quality?
- High power when: few suppliers, no substitutes, high switching costs
- Example: TSMC's power over chip companies

**4. Bargaining Power of Buyers**
- Can customers demand lower prices or better terms?
- High power when: few buyers, low switching costs, price-sensitive
- Example: Walmart's power over consumer goods companies

**5. Threat of Substitutes**
- Can different products solve the same problem?
- Not competitors but alternatives
- Example: Video calls substituting for business travel

### Using Five Forces

**For market entry decisions:**
- Attractive industries: high barriers to entry, low supplier/buyer power, few substitutes
- Unattractive: intense rivalry, easy entry, powerful buyers

**For product strategy:**
- Increase switching costs (reduce buyer power)
- Create unique value (reduce substitute threat)
- Build scale advantages (raise entry barriers)

### When Porter Is Outdated

Porter's model assumes:
- Clear industry boundaries
- Competition is zero-sum
- Strategy is about positioning

In today's world:
- Industry boundaries blur (is Uber a taxi or tech company?)
- Platform dynamics create positive-sum games
- Ecosystems matter more than positioning

Use Porter for traditional industry analysis. Use network effects/platform frameworks for digital businesses.

---

## Part 3: Competitive Advantage & Moats

### What Is Competitive Advantage?

Competitive advantage = sustainable ability to outperform competitors

Two types (Porter):
1. **Cost leadership** â€” Deliver same value at lower cost
2. **Differentiation** â€” Deliver superior value at similar cost

You can't be both (usually). Trying to be creates "stuck in the middle."

### 7 Powers Framework (Hamilton Helmer)

A more modern framework for understanding moats:

| Power | Definition | Example |
|-------|------------|---------|
| **Scale Economies** | Cost per unit decreases with volume | Amazon distribution |
| **Network Effects** | Product improves as more people use it | Social networks |
| **Counter-Positioning** | New approach incumbents can't copy without self-harm | Netflix vs Blockbuster |
| **Switching Costs** | Customers lose value by leaving | Enterprise software, data lock-in |
| **Branding** | Reputation enables premium pricing | Apple, luxury goods |
| **Cornered Resource** | Exclusive access to valuable asset | Patents, talent, location |
| **Process Power** | Embedded organizational capabilities | Toyota production system |

### Moat Analysis for PMs

When evaluating features or products, ask:

1. **Which power does this build?**
2. **How defensible is the advantage?**
3. **How long before competitors copy?**
4. **What's the compounding effect?**

**Example analysis:**

```
FEATURE: AI-powered recommendation engine

POWERS IT BUILDS:
- Data network effects (more usage = better recs = more usage)
- Switching costs (personalization is lost if customer leaves)

DEFENSIBILITY: Medium
- Competitors can build similar tech
- But data advantage compounds over time
- 18-24 month head start creates significant gap

RECOMMENDATION: High priority - builds durable moat
```

### Network Effects Deep Dive

Network effects are the most powerful moat in digital:

**Types:**
- **Direct:** Product improves for me as others join (phone network)
- **Indirect:** More users attract more complements (iPhone â†’ apps â†’ users)
- **Data:** More usage generates data that improves product (Google search)
- **Platform:** Both sides benefit from the other (Uber riders/drivers)

**Network effects are not viral growth.** Viral = how you acquire users. Network effects = why they stay.

**Defending network effects:**
- Reach critical mass quickly
- Own the data layer
- Prevent multi-homing (users on multiple platforms)
- Win the quality side first (usually supply side)

---

## Part 4: Platform Strategy

### Platform vs Pipeline

**Pipeline business:** Create value, sell it
- Linear: Supplier â†’ Company â†’ Customer
- You control supply, compete on efficiency
- Example: Traditional manufacturing

**Platform business:** Enable value exchange, capture share
- Multi-sided: Connect different user groups
- You orchestrate, compete on ecosystem
- Example: App stores, marketplaces

### Platform Economics

**Chicken-and-egg problem:**
- Users want sellers; sellers want users
- Neither joins without the other
- Solution: Subsidize one side to bootstrap

**Multi-homing:**
- Users active on multiple platforms
- Reduces lock-in, commoditizes platforms
- Strategy: increase switching costs, exclusive content

**Winner-take-all dynamics:**
- Strong network effects â†’ market concentration
- But only in specific conditions:
  - High multi-homing costs
  - Low differentiation potential
  - Global (not local) networks

### Platform Strategy for PMs

**Questions to ask:**
1. Who are the sides of the platform?
2. Which side is harder to get? (Subsidize them)
3. What creates lock-in for each side?
4. What's the minimum viable ecosystem?
5. How do you prevent disintermediation?

**Common platform PM mistakes:**
- Launching both sides simultaneously (pick one to bootstrap)
- Treating platform like product (you're a matchmaker, not a manufacturer)
- Monetizing too early (growth first, monetization after liquidity)
- Ignoring quality (bad supply drives away demand)

---

## Part 5: Disruption Theory

### The Core Idea (Christensen)

Disruption happens when:
1. Incumbents serve mainstream customers
2. New entrant serves overlooked segment (low-end or new market)
3. Entrant improves over time
4. Eventually, entrant's solution is "good enough" for mainstream
5. Incumbent loses to cheaper/simpler alternative

**Classic example:** Minicomputers disrupted mainframes. PCs disrupted minicomputers. Mobile disrupted PCs.

### When Incumbents Win

Disruption theory is overused. Incumbents win when:

1. **Sustaining innovation** â€” Improvements along current trajectory
2. **Integrated value chains** â€” When you need the whole system
3. **Regulatory moats** â€” Government protects incumbents
4. **High switching costs** â€” Too painful to leave
5. **Strong network effects** â€” Ecosystem loyalty

**Example:** Banks weren't disrupted by fintech as predicted because:
- Regulatory barriers (fintech can't easily get banking licenses)
- Switching costs (moving direct deposits, auto-pays is hard)
- Trust advantages (customers trust 100-year-old banks)

### Disruption for PMs

**If you're at an incumbent:**
- Monitor low-end market for "good enough" products
- Consider creating disruptive product yourself (cannibalization)
- Move up-market to higher-margin segments

**If you're a challenger:**
- Target non-consumption first
- Compete on different dimension than incumbent
- Embrace "worse" on traditional metrics if better on new ones
- Avoid direct competition until you're ready

---

## Part 6: Strategy in the AI Era

### What Changes

**Competitive advantage shifts:**
- Data becomes strategic asset (not just operations)
- Prediction costs drop (changes economics of everything)
- Intelligence becomes commodity (execution matters more)
- Speed of learning determines winners

**Industry dynamics change:**
- Barriers to entry lower (AI-powered startups)
- Scale advantages increase (data compounds)
- Bundling dynamics shift (AI enables unbundling)

### What Doesn't Change

- Need for coherent choices
- Tradeoffs remain (can't serve everyone)
- Organizational capability matters
- Human judgment required for ambiguity
- Culture eats strategy
- Execution > planning

### AI Strategy Frameworks

**Build vs Buy vs Partner:**
- Build: core differentiator, control needed
- Buy: commodity capability, speed matters
- Partner: complementary capability, shared incentives

**Data moats:**
- Proprietary data (no one else has it)
- Data network effects (usage improves product)
- Data flywheels (better product â†’ more users â†’ more data â†’ better product)

**AI-era competitive questions:**
1. What decisions can AI make better than humans?
2. What decisions require human judgment?
3. Where does our data advantage compound?
4. How do we learn faster than competitors?

---

## Part 7: Making Strategic Choices

### Strategy Is About Saying No

The essence of strategy is choosing what NOT to do.

**Apple's strategy:** Limited product line, premium only, integrated ecosystem.
- Explicit no to: low-end market, licensing OS, fragmented product portfolio

**Amazon's strategy:** Customer obsession, long-term investment, operational excellence.
- Explicit no to: high margins, quick profits, cushy work environment

**Your job as PM:** Articulate not just what you'll build, but what you won't.

### Strategic Positioning vs Operational Effectiveness

**Operational effectiveness:** Doing things better than competitors
- Necessary but not sufficient
- Can be copied
- Leads to competitive convergence

**Strategic positioning:** Doing different things than competitors
- Sustainable advantage
- Requires tradeoffs
- Creates uniqueness

**Example:** IKEA isn't just operationally excellentâ€”they made different choices:
- Self-assembly (vs delivered assembled)
- Suburban locations (vs downtown)
- Limited service (vs consultative)
- Modular design (vs custom)

These choices reinforce each other. Copying one without the others doesn't work.

### Crafting Product Strategy

**The PM strategy document should answer:**

1. **Where will we play?**
   - Which customers?
   - Which use cases?
   - Which geographies?
   - Which price points?

2. **How will we win?**
   - What's our unique value?
   - Why will customers choose us?
   - What's our moat?

3. **What won't we do?**
   - Which customers are we okay losing?
   - Which features are out of scope?
   - Which competitors are we okay ceding ground to?

4. **What capabilities do we need?**
   - What must we be excellent at?
   - What can we be average at?

---

## Exercises

### Exercise 1: Diagnose a Real Challenge

Pick a challenge you're facing at work. Apply Rumelt's kernel:

1. Write the diagnosis (what's actually going on?)
2. Write a guiding policy (the key choice)
3. Write 3-5 coherent actions

Test: Do the actions reinforce each other? Does the policy rule something out?

**Time:** 45 minutes

### Exercise 2: Five Forces Analysis

Choose an industry you're interested in entering or understanding:

1. Analyze each of the five forces (high/medium/low)
2. What makes this industry attractive or unattractive?
3. Where would you position to minimize force pressure?

**Time:** 45 minutes

### Exercise 3: Moat Assessment

For your current product:

1. Which of the 7 Powers does it have?
2. Rate the strength of each (none/weak/moderate/strong)
3. What could you build to strengthen the strongest moat?
4. What's the weakest point competitors could attack?

**Time:** 30 minutes

### Exercise 4: Disruption Vulnerability

For your company or product:

1. Who serves customers we consider "low end" or "not worth it"?
2. What are they competing on that we dismiss?
3. In what scenario could they become "good enough" for our mainstream?
4. What would we do if that happened?

**Time:** 30 minutes

### Exercise 5: Strategic Choices

Write your product strategy as choices:

1. We will focus on [customer segment] and not [other segments]
2. We will compete on [these dimensions] and not [these dimensions]
3. We will be excellent at [these capabilities] and accept average at [these]
4. We will win because [competitors can't/won't] do [this]

Test: Can a competitor easily copy all of these? If yes, not strategic.

**Time:** 45 minutes

---

## Checklist: Are You Ready?

- [ ] Distinguish strategy from goals, vision, and tactics
- [ ] Apply Rumelt's kernel (diagnosis, guiding policy, coherent actions)
- [ ] Conduct a Five Forces analysis for any industry
- [ ] Identify which of 7 Powers applies to a product
- [ ] Explain when disruptors win vs when incumbents win
- [ ] Articulate strategy as choices and tradeoffs
- [ ] Differentiate strategic positioning from operational effectiveness

---

## Key Frameworks Summary

| Framework | Use When | Core Insight |
|-----------|----------|--------------|
| Rumelt's Kernel | Formulating strategy | Strategy = diagnosis + guiding policy + coherent actions |
| Five Forces | Analyzing industry | Industry structure determines profitability |
| 7 Powers | Assessing moat | Sustainable advantage requires structural power |
| Disruption Theory | Competitive dynamics | Incumbents lose to "worse" products serving different needs |

---

## Next Steps

1. **Read:** *Good Strategy Bad Strategy* by Richard Rumelt â€” The best modern strategy book. Skip Part II on your first read; focus on Part I and III.

2. **Practice:** Do Exercise 1 (Rumelt's Kernel) for a real challenge you're facing. Strategy is a skill built through application.

3. **Observe:** In your next exec meeting, notice how often "strategy" is used to mean "goals." Start distinguishing in your own language.

---

*Module 4: Negotiation is next.*

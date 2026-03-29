# Module 6: Marketing & Customer Psychology

**Time Investment:** ~10 hours
**Deep-Dive Book:** *Positioning* by Al Ries & Jack Trout

---

## Why This Matters for You

PMs who can't think like marketers build features that don't sell. Marketing isn't promotion—it's understanding why customers choose, how they perceive value, and where your product fits in their mind. These skills make the difference between products that launch and products that grow.

**What AI can do:** Analyze markets, generate copy variations, segment data.
**What you must do:** Understand human psychology, craft positioning, make strategic bets on what will resonate.

---

## Part 1: Positioning

### What Positioning Is

Positioning isn't what you do to a product. It's what you do in the mind of the prospect.

**The overcommunicated society:**
- Average person sees 4,000+ messages daily
- Attention is scarce
- Minds filter aggressively

**Positioning is:** Occupying a distinct place in the customer's mind relative to alternatives.

**Positioning is not:**
- Your product features
- Your mission statement
- Your tagline (though tagline reflects positioning)

### The Positioning Framework

```
FOR [target customer]
WHO [statement of need/opportunity]
[PRODUCT NAME] IS A [category]
THAT [key benefit]
UNLIKE [competitor/alternative]
WE [key differentiator]
```

**Example (Slack):**
```
FOR knowledge workers
WHO need to coordinate across teams and tools
SLACK IS A messaging platform
THAT centralizes work communication
UNLIKE email
WE provide real-time collaboration with powerful integrations
```

### Positioning Strategies

**1. Category leadership**
- Be first in a category
- "The original," "The leader"
- Hertz: "We're #1"

**2. Against the leader**
- Position relative to the leader
- Claim what they can't
- Avis: "We're #2, so we try harder"

**3. Create new category**
- Reframe to avoid direct comparison
- Own a new mental space
- "We're not X, we're Y"

**4. Attribute ownership**
- Own a specific attribute
- "Fastest," "Most secure," "Easiest"
- Volvo owns "safety"

**5. Use case specialist**
- Own a specific situation
- "The [product] for [specific need]"
- Liquid Paper: "For typos"

### Positioning Mistakes

**1. Trying to be everything**
- Position for everyone = position for no one
- "Full-featured, easy-to-use, affordable, enterprise-grade, flexible"
- Choose.

**2. Copying the leader**
- Leader already owns that position
- "We're also enterprise-grade security"
- You can't out-position the position holder

**3. Confusing positioning with messaging**
- Positioning is strategic (who, why, vs what)
- Messaging is tactical (how you communicate)
- Get positioning right first

**4. Inside-out thinking**
- "We have advanced ML algorithms"
- Customer doesn't care about your tech
- "You'll find documents 10x faster"

---

## Part 2: STP Framework

### Segmentation

**Divide market into distinct groups:**

**Demographic:** Age, income, education, job title
**Geographic:** Location, region, urban/rural
**Psychographic:** Values, lifestyle, personality
**Behavioral:** Usage, loyalty, benefits sought

**Good segments are:**
- Measurable (you can size them)
- Substantial (big enough to matter)
- Accessible (you can reach them)
- Differentiable (they respond differently)
- Actionable (you can serve them differently)

**B2B segmentation adds:**
- Industry/vertical
- Company size
- Technology stack
- Decision-making process
- Buying stage

### Targeting

**Choose which segments to serve:**

**Evaluation criteria:**
- Segment size and growth
- Segment profitability
- Competitive intensity
- Your ability to serve
- Strategic fit

**Targeting strategies:**
- **Undifferentiated:** Same offering for all (rare in modern marketing)
- **Differentiated:** Different offerings for different segments (resource-intensive)
- **Concentrated:** Focus on one or few segments (niche)
- **Micromarketing:** Customize to individuals (enabled by tech)

**PM implication:** Your roadmap is an implicit targeting decision. Features for enterprise ≠ features for SMB.

### Positioning (Revisited)

With segment chosen, position specifically for them.

**The sequence matters:**
1. Segment the market
2. Target specific segments
3. Position for those targets

Positioning for "everyone" is positioning for no one.

---

## Part 3: Behavioral Economics

### Why Rationality Is a Myth

Classical economics assumes rational actors. Behavioral economics shows we're predictably irrational.

**For PMs:** Understanding irrationality lets you design products and pricing that align with how people actually decide.

### Key Biases

**Anchoring:**
- First number shapes subsequent judgments
- Show a high price first (then discount)
- "Originally $299, now $199" works even if original was fake

**Framing:**
- Same information, different presentation = different decisions
- "90% survival rate" vs "10% mortality rate"
- Frame gains and losses differently

**Loss Aversion:**
- Losses hurt ~2x more than equivalent gains feel good
- "Don't lose your data" > "Protect your data"
- Free trials leverage this (you have it, don't want to lose it)

**Status Quo Bias:**
- Preference for current state
- Default options are powerful
- Make desired behavior the default

**Social Proof:**
- We do what others do
- "10,000 customers trust us"
- Show testimonials, user counts, logos

**Scarcity:**
- Rare things seem more valuable
- "Only 3 left," "Limited time"
- FOMO drives action

**Reciprocity:**
- We feel obligated to return favors
- Give before asking (free content, trials)
- Creates psychological debt

### Application to Product

| Bias | Product Application |
|------|---------------------|
| Anchoring | Pricing tiers (show expensive first) |
| Loss Aversion | "Your free trial ends in 3 days" |
| Status Quo | Default to annual billing |
| Social Proof | Show active users, testimonials |
| Scarcity | Limited seats, time-limited offers |
| Reciprocity | Free features before asking for upgrade |

---

## Part 4: Pricing Psychology

### Pricing Fundamentals

**Three approaches:**
1. **Cost-plus:** Your cost + markup
2. **Competitive:** Match/beat competitors
3. **Value-based:** Price to value delivered

**Value-based is superior** but requires understanding customer's perceived value.

### Psychological Pricing Tactics

**Charm pricing:**
- $9.99 vs $10.00
- Left digits matter disproportionately
- Works less on sophisticated B2B buyers

**Price anchoring:**
- Show higher price first
- "Enterprise: $500/mo | Pro: $100/mo | Basic: $20/mo"
- Makes Pro look reasonable

**Decoy pricing:**
- Third option makes target option look better
- Magazine: Web ($59), Print ($125), Web+Print ($125)
- Decoy (Print only at $125) makes Web+Print obvious

**Bundling:**
- Combine products/features
- Obscures individual prices
- Feels like better deal
- Reduces price comparison

**Price partitioning:**
- Base price + fees shown separately
- "Flight $199" + "$50 seat selection" + "$30 baggage"
- Anchors to base price

### Pricing Tiers

**Why tiers work:**
- Self-segmentation (customers choose)
- Anchoring (higher tier makes middle look reasonable)
- Upgrade path (land and expand)

**Good/Better/Best:**
```comparison-table
{
  "title": "Good / better / best pricing",
  "note": "The middle tier is usually where you want demand to concentrate.",
  "columns": [
    { "key": "tier", "label": "Tier" },
    { "key": "price", "label": "Price" },
    { "key": "offer", "label": "Offer" }
  ],
  "rows": [
    {
      "tier": "Basic",
      "price": "$10/mo",
      "offer": "Feature A, Feature B"
    },
    {
      "tier": "Pro",
      "price": "$30/mo",
      "offer": "Everything in Basic, Feature C, Feature D, most popular"
    },
    {
      "tier": "Enterprise",
      "price": "$100/mo",
      "offer": "Everything in Pro, Feature E, support"
    }
  ]
}
```

### Freemium Strategy

**When freemium works:**
- Low marginal cost (software)
- Network effects (more users = more value)
- Viral distribution (users invite others)
- Clear upgrade triggers (hit limit, need features)

**When it doesn't:**
- High support costs
- No clear free → paid trigger
- Low conversion rates unsustainable
- Gives away too much value

**Freemium metrics:**
- Free → Paid conversion rate (target: 2-5%+)
- Time to convert
- Cost to serve free users
- Virality of free tier

---

## Part 5: Brand vs Performance Marketing

### Brand Marketing

**Goal:** Build awareness, trust, perception
**Timeframe:** Long-term (months to years)
**Metrics:** Brand awareness, consideration, NPS, share of voice
**Tactics:** Content, PR, events, sponsorships, brand advertising

**Characteristics:**
- Hard to measure directly
- Compounds over time
- Builds pricing power
- Creates preference before purchase intent

### Performance Marketing

**Goal:** Drive measurable actions
**Timeframe:** Short-term (days to weeks)
**Metrics:** CAC, ROAS, conversion rate, CPC
**Tactics:** Paid search, paid social, retargeting, affiliate

**Characteristics:**
- Directly measurable
- Immediate results
- Diminishing returns (audiences saturate)
- Easy to over-optimize and under-invest in brand

### The Tension

**Brand people say:** "You can't measure everything that matters"
**Performance people say:** "If you can't measure it, how do you know it works?"

**The truth:** Both are right. Portfolio approach works:

- Performance for near-term acquisition
- Brand for long-term pricing power and consideration

**Typical mix by stage:**
- Early startup: 90% performance, 10% brand
- Growing company: 70% performance, 30% brand
- Mature company: 50-50 or brand-heavy

### PM Implications

**Performance marketing affects:**
- Landing page optimization (your domain)
- Feature messaging (what converts)
- Growth experiments

**Brand affects:**
- Product quality (brand promise must match)
- Customer experience
- Long-term roadmap investments

---

## Part 6: Jobs-to-be-Done (JTBD)

### The Core Framework

**People don't buy products. They hire them to do a job.**

Clayton Christensen's insight: Customers don't want a drill or even a hole—they want the picture hung on the wall.

**The job formula:**
```
When [situation],
I want to [motivation],
So I can [outcome].
```

**Example (Milkshake study):**
```
When I have a long, boring commute,
I want something to keep me occupied and full until lunch,
So I can make it to work alert and not hungry.
```

This explains why milkshakes compete with bananas, donuts, and bagels—not just other milkshakes.

### Finding Jobs

**Interview questions:**
- "Walk me through the last time you [did the thing]"
- "What were you trying to accomplish?"
- "What else did you consider?"
- "Why did you choose this option?"
- "What would you have done if this didn't exist?"

**Look for:**
- Workarounds (what do they hack together?)
- Switching triggers (what made them seek a new solution?)
- Hiring criteria (what factors mattered?)
- Fire criteria (what would make them stop using it?)

### Applying JTBD

**Product development:**
- Build for the job, not the segment
- Ask: What job does this feature help them do?
- Competing against non-consumption often better than head-to-head

**Positioning:**
- Position against the job alternatives, not just product competitors
- "For people who need X, we're better than [alternative] because..."

**Roadmap prioritization:**
- Rank features by how well they serve the core job
- Beware feature creep into adjacent jobs (dilutes value prop)

### Jobs Have Emotional and Social Dimensions

```
FUNCTIONAL: What I'm trying to get done
EMOTIONAL: How I want to feel
SOCIAL: How I want to be perceived
```

**Example (luxury car):**
- Functional: Get from A to B safely
- Emotional: Feel confident and successful
- Social: Be seen as accomplished

Many B2B products underweight emotional/social dimensions. Enterprise buyers are still human.

---

## Exercises

### Exercise 1: Positioning Statement

For your product (or a product you use):

1. Write the positioning statement using the framework
2. Identify: What is the key competitor/alternative?
3. Identify: What is the meaningful differentiator?
4. Test: If you removed the product name, could it be anyone else?

**Time:** 30 minutes

### Exercise 2: Segment Analysis

For your market:

1. List 3-5 possible segmentation criteria
2. Create 3-4 distinct segments
3. Evaluate each: Size, growth, profitability, competitive intensity
4. Recommend: Which segment(s) should you target?

**Time:** 45 minutes

### Exercise 3: Behavioral Audit

Analyze your product's conversion flow:

1. Map the user journey to purchase/upgrade
2. At each step, identify: What bias could we leverage?
3. Identify: What friction points exist?
4. Recommend 3 changes based on behavioral principles

**Time:** 45 minutes

### Exercise 4: Pricing Teardown

Pick a SaaS company with public pricing:

1. Screenshot their pricing page
2. Analyze: What psychological tactics do they use?
3. Identify: What's the decoy? What's the anchor?
4. Recommend: One improvement

**Time:** 30 minutes

### Exercise 5: Jobs-to-be-Done Interview

Interview 2-3 users or customers:

1. Use the JTBD interview questions
2. Document: What job are they hiring your product for?
3. Identify: What are the competing "hires" (alternatives)?
4. Discover: What are the emotional/social dimensions?

**Time:** 2 hours (including interviews)

### Exercise 6: Competitive Positioning Map

Create a positioning map:

1. Pick two attributes that matter to customers
2. Plot your product and 3-5 competitors on 2x2
3. Identify: Where is the "white space"?
4. Ask: Should you move? Or own your position?

**Time:** 30 minutes

---

## Checklist: Are You Ready?

- [ ] Write a clear positioning statement
- [ ] Apply STP framework (Segmentation, Targeting, Positioning)
- [ ] Identify and leverage behavioral biases in product design
- [ ] Design pricing with psychological principles
- [ ] Distinguish brand vs performance marketing and when each applies
- [ ] Conduct Jobs-to-be-Done analysis
- [ ] Identify functional, emotional, and social job dimensions

---

## Key Frameworks Summary

| Framework | Use When | Core Insight |
|-----------|----------|--------------|
| Positioning Statement | Defining market position | Occupy a distinct place in customer's mind |
| STP | Market strategy | Segment → Target → Position |
| Behavioral Economics | Conversion optimization | Leverage predictable irrationality |
| JTBD | Product discovery | People hire products to do jobs |
| Good/Better/Best | Pricing strategy | Self-segmentation through tiers |

---

## Key Concepts Quick Reference

| Concept | Definition |
|---------|------------|
| Positioning | Place you occupy in customer's mind vs alternatives |
| Anchoring | First number shapes judgment |
| Loss Aversion | Losses hurt more than gains please |
| Decoy Effect | Third option makes target look better |
| JTBD | Customers hire products to accomplish jobs |
| Freemium | Free tier to drive paid conversions |
| STP | Segmentation, Targeting, Positioning |

---

## Next Steps

1. **Read:** *Positioning* by Al Ries & Jack Trout — The classic text on positioning. Written in 1981 but principles remain timeless. Quick read, foundational concepts.

2. **Practice:** Exercise 1 (Positioning Statement) for your current product. Share with colleagues and see if they agree.

3. **Apply:** Review your pricing page through the lens of behavioral economics. Identify three quick wins.

---

*Module 7: Operations & Execution is next.*

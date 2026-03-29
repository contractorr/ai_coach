# Module 1: Financial Acumen for Technical PMs

**Time Investment:** ~10 hours
**Deep-Dive Book:** *Financial Intelligence* by Karen Berman & Joe Knight

---

## Why This Matters for You

As a technical PM, you build products. CFOs fund them. The gap between "this feature will improve UX" and "this investment returns 3x in 18 months" is the gap between good PMs and great ones. Finance isn't about becoming an accountant—it's about speaking the language of resource allocation.

**What AI can do:** Crunch numbers, build models, forecast scenarios.
**What you must do:** Interpret, judge tradeoffs, build conviction, persuade.

---

## Part 1: The Three Financial Statements

### The Mental Model

Think of a business like your personal finances:
- **Income Statement (P&L):** Your paycheck minus expenses = savings (or debt)
- **Balance Sheet:** Your net worth snapshot—assets minus what you owe
- **Cash Flow Statement:** Your actual bank account—when money moves

Companies report all three because each tells a different story. Profitable companies go bankrupt (cash timing). Cash-rich companies can be worthless (no future earnings). Net worth means nothing without context.

---

### Income Statement (P&L)

**What it answers:** Did we make money this period?

```
Revenue (Top Line)
- Cost of Goods Sold (COGS)
= Gross Profit
- Operating Expenses (R&D, S&M, G&A)
= Operating Income (EBIT)
- Interest, Taxes
= Net Income (Bottom Line)
```

**Key metrics for PMs:**

| Metric | Formula | Why You Care |
|--------|---------|--------------|
| Gross Margin | Gross Profit / Revenue | Shows scalability—high GM means each $ of revenue adds more profit |
| Operating Margin | Operating Income / Revenue | Shows operational efficiency—are we spending wisely? |
| R&D % of Revenue | R&D / Revenue | Benchmark against industry; too low = underinvesting, too high = inefficient |

**PM Translation:**
- Your feature costs $500K to build (R&D expense)
- It generates $2M incremental revenue at 70% gross margin
- Gross profit impact: $1.4M
- ROI: 180% ($1.4M - $500K) / $500K

---

### Balance Sheet

**What it answers:** What do we own and owe right now?

```
ASSETS = LIABILITIES + EQUITY

Assets:                    Liabilities:
- Cash                     - Accounts Payable
- Accounts Receivable      - Debt
- Inventory                - Deferred Revenue
- Property/Equipment
- Intangibles              Equity:
                           - Stock issued
                           - Retained Earnings
```

**Key concepts for PMs:**

**Deferred Revenue** — Cash received for services not yet delivered. SaaS companies collect annual subscriptions upfront but "earn" it monthly. This is a liability until delivered. Why care? Your product delays affect revenue recognition.

**Working Capital** — Current Assets - Current Liabilities. Measures short-term liquidity. Negative working capital can be good (customers pay before you pay suppliers—Amazon model) or bad (can't pay bills).

**Goodwill** — When Company A buys Company B for more than B's tangible assets, the difference is goodwill. It's the value of brand, talent, customer relationships. PMs building products that create moats create goodwill.

---

### Cash Flow Statement

**What it answers:** Where did cash actually come from and go?

Three sections:
1. **Operating Activities** — Cash from running the business
2. **Investing Activities** — Cash for buying/selling assets, acquisitions
3. **Financing Activities** — Cash from investors, debt, dividends

**The Critical Insight:**

Net Income ≠ Cash Flow

Why? Accrual accounting. Revenue is recognized when earned (contract signed), not when cash arrives. Expenses are recognized when incurred, not when paid.

**Example:**
- You close a $1M annual deal on Dec 15
- Customer pays in January
- P&L shows $1M revenue in December
- Cash arrives in January
- December looks profitable but you can't pay December salaries with January cash

**Free Cash Flow (FCF)** = Operating Cash Flow - Capital Expenditures

This is the money actually available to grow, pay dividends, or survive downturns. Investors love FCF. Profitable companies with negative FCF are burning.

---

### How the Three Connect

```process-flow
{
  "title": "How the three statements connect",
  "steps": [
    {
      "title": "Net income",
      "detail": "Starts on the P&L."
    },
    {
      "title": "Adjustments",
      "detail": "Add back depreciation and reflect working-capital changes."
    },
    {
      "title": "Operating cash flow",
      "detail": "Flows onto the cash flow statement."
    },
    {
      "title": "Ending cash",
      "detail": "Feeds the balance sheet."
    },
    {
      "title": "Retained earnings",
      "detail": "Increase with net income on the balance sheet."
    }
  ]
}
```

**Real example:** A SaaS company reports:
- $10M Net Income (P&L looks great)
- -$5M Operating Cash Flow (customers paying slow)
- $3M cash remaining (Balance Sheet)

Red flag: They're profitable on paper but running out of cash. This is how profitable companies die.

---

## Part 2: Unit Economics

Unit economics answer: "Is each customer profitable, and when?"

### Customer Acquisition Cost (CAC)

**Formula:**
CAC = Total Sales & Marketing Spend / New Customers Acquired

**Nuances:**
- Include salaries, tools, ads, events—everything to acquire
- Segment by channel (CAC for paid ads vs organic vs sales-led)
- Blended CAC hides sins—your paid CAC might be 5x organic

**Benchmark:** Varies wildly by business model
- Self-serve SaaS: $100-500
- SMB sales-led: $1,000-5,000
- Enterprise: $10,000-100,000+

### Lifetime Value (LTV)

**Simple Formula:**
LTV = ARPU × Gross Margin × Customer Lifetime

**Better Formula (with churn):**
LTV = (ARPU × Gross Margin) / Monthly Churn Rate

**Example:**
- $100/month ARPU
- 80% gross margin
- 3% monthly churn

LTV = ($100 × 0.8) / 0.03 = $2,667

### The LTV:CAC Ratio

**The Rule of Thumb:** LTV:CAC > 3:1 for healthy unit economics

Why 3:1?
- 1:1 = break even on customer, nothing for overhead
- 2:1 = some margin but thin
- 3:1 = sustainable, can invest in growth
- 5:1+ = either very efficient or underinvesting in growth

**Warning:** This ratio is easily gamed. Watch for:
- LTV calculated on best cohorts only
- CAC excluding major costs
- Lifetime assumptions that are fantasies

### Payback Period

**Formula:**
Payback Period = CAC / (ARPU × Gross Margin)

**Example:**
- CAC: $1,000
- ARPU: $100/month
- Gross Margin: 80%

Payback = $1,000 / ($100 × 0.8) = 12.5 months

**Why it matters:** Payback period determines growth rate. If payback is 12 months, you need 12 months of cash runway for every new customer. Shorter payback = faster growth possible.

**Benchmarks:**
- < 12 months: Good
- 12-18 months: Acceptable for enterprise
- > 18 months: Better have strong retention

### Contribution Margin

**Formula:**
Contribution Margin = Revenue - Variable Costs

Variable costs scale with each unit sold. Fixed costs don't.

**SaaS example:**
- Revenue per customer: $1,000/year
- Variable costs: $200 (hosting, support, payment processing)
- Contribution margin: $800

**Why PMs care:** When prioritizing features, contribution margin tells you the real incremental value. A feature that adds $50K revenue but $40K variable cost is worse than one adding $30K revenue with $5K variable cost.

---

## Part 3: Valuation Basics

You don't need to build DCF models. AI does that. You need intuition for what drives value and why it matters for your decisions.

### Why Valuation Matters for PMs

1. **Resource allocation** — High-multiple features get funded
2. **Acquisition context** — Understanding acquirer logic
3. **Stakeholder language** — Execs think in value creation

### Revenue Multiples

**Formula:**
Enterprise Value = Revenue × Multiple

**What drives multiples:**
- Growth rate (fastest growing = highest multiple)
- Gross margin (80%+ margin valued higher than 40%)
- Retention (net revenue retention >100% = expansion)
- Market size (TAM)
- Competitive position

**Current SaaS multiples (2024 rough):**
- Slow growth (<20%): 3-5x revenue
- Moderate growth (20-40%): 5-10x revenue
- High growth (>40%): 10-20x revenue
- AI/hot sector: 20x+ revenue

**PM implication:** A feature that adds $1M ARR at a 10x company adds $10M in enterprise value. That's how you frame business cases.

### DCF Intuition

Discounted Cash Flow answers: "What's the present value of all future cash flows?"

**The logic:**
- $100 today > $100 next year (time value of money)
- Future cash is discounted back to present value
- Sum of all discounted future cash = company value

**Key inputs:**
- Projected cash flows (the hard part—assumptions matter enormously)
- Discount rate (risk adjustment—higher risk = higher discount = lower value)
- Terminal value (value beyond projection period)

**PM intuition:** DCF penalizes:
- Distant cash flows (that feature with payoff in 5 years is worth less)
- Risky cash flows (unproven market = higher discount)
- One-time cash (vs recurring revenue)

DCF rewards:
- Near-term cash generation
- Predictable, recurring revenue
- Growing cash flows

### Rule of 40

**Formula:**
Revenue Growth % + Profit Margin % ≥ 40%

**Example:**
- 30% growth + 10% margin = 40% ✓
- 50% growth + -10% margin = 40% ✓
- 15% growth + 15% margin = 30% ✗

This is the investor heuristic for SaaS health. It acknowledges the growth vs. profitability tradeoff.

**PM framing:** Your feature investment might hurt short-term margin but if it accelerates growth enough, you're still creating value per Rule of 40.

---

## Part 4: Capital Allocation & CFO Thinking

### How CFOs Think

CFOs allocate scarce capital across competing demands:
- Keep the lights on (maintenance CapEx)
- Grow the business (growth investments)
- Return to shareholders (dividends, buybacks)
- Safety buffer (cash reserves)

**Their questions for every investment:**
1. What's the return? (IRR, ROI, NPV)
2. What's the risk? (Probability-weighted outcomes)
3. What's the payback? (When do we see returns)
4. What's the alternative? (Opportunity cost)

### CapEx vs OpEx

**Capital Expenditure (CapEx):**
- Large, one-time investments
- Depreciated over time
- Hits balance sheet then gradually hits P&L
- Examples: servers, office buildout, major platform rebuild

**Operating Expense (OpEx):**
- Ongoing costs
- Hits P&L immediately
- Examples: salaries, cloud hosting, marketing spend

**Why it matters for PMs:**

Cloud transformed software economics. Instead of buying servers (CapEx), you rent them (OpEx). This shift:
- Lowers upfront capital needs
- Makes costs variable with usage
- Changes how CFOs evaluate investments

**Strategic consideration:** Some CFOs prefer CapEx (spreads P&L impact). Others prefer OpEx (flexibility). Know your CFO's preference.

### ROI Frameworks

**Simple ROI:**
ROI = (Gain from Investment - Cost) / Cost

**Net Present Value (NPV):**
Sum of discounted future cash flows - initial investment

- NPV > 0 = creates value
- NPV < 0 = destroys value
- Higher NPV = better investment

**Internal Rate of Return (IRR):**
The discount rate at which NPV = 0

- If IRR > cost of capital, invest
- Higher IRR = better return

**Payback Period:**
Time to recover initial investment

**Which to use when:**
- Quick decisions: Simple ROI
- Comparing projects: NPV (absolute value created)
- Communicating returns: IRR (percentage is intuitive)
- Risk-conscious decisions: Payback period

---

## Part 5: Translating Product Metrics to Financial Impact

### The Translation Table

| Product Metric | Financial Translation |
|----------------|----------------------|
| MAU growth | Potential revenue growth (× conversion rate × ARPU) |
| Conversion rate | CAC efficiency (higher conversion = lower effective CAC) |
| Retention/churn | LTV (directly multiplied) |
| Feature adoption | Usage-based revenue OR reduced churn |
| NPS/CSAT | Leading indicator of retention |
| Time-to-value | Payback period, activation rate |
| Support tickets | COGS (support costs) |

### The CFO Translation Framework

When presenting to finance, use this structure:

```
1. CURRENT STATE: [Product metric today]
2. CHANGE: [What you're proposing]
3. PRODUCT IMPACT: [Expected metric change]
4. FINANCIAL IMPACT: [$ impact]
5. INVESTMENT: [Cost to achieve]
6. ROI: [Return calculation]
7. CONFIDENCE: [Risk assessment]
```

**Example:**

```
1. CURRENT STATE: 15% trial-to-paid conversion
2. CHANGE: Improve onboarding flow
3. PRODUCT IMPACT: +5% conversion (15% → 20%)
4. FINANCIAL IMPACT:
   - 10K monthly trials × 5% lift × $1,200 ACV = $600K incremental ARR
   - At 10x multiple = $6M enterprise value
5. INVESTMENT: $200K (2 engineers × 3 months + design)
6. ROI: 200% first year, 30x on valuation impact
7. CONFIDENCE: Medium-high (based on A/B test of similar flow)
```

### Common Mistakes in Translation

1. **Vanity metrics without conversion:** "10M impressions" means nothing without click → signup → paid path
2. **Ignoring cannibalization:** New feature revenue that steals from existing feature isn't incremental
3. **Optimistic timelines:** Execs mentally discount your projections 30-50%
4. **Missing costs:** Engineering time has a cost, even if it's not "new spend"
5. **Certainty theater:** Better to give ranges than false precision

---

## Part 6: Building a Business Case That Gets Funded

### The Structure

**Executive Summary (half page max)**
- The ask: What you want
- The return: What they get
- The risk: Why this might fail

**Problem/Opportunity**
- Quantified current state
- What's being lost/missed

**Proposed Solution**
- What you'll build/do
- Why this approach

**Financial Analysis**
- Investment required (broken down)
- Expected returns (with assumptions explicit)
- Payback period
- Comparison to alternatives

**Risks & Mitigations**
- What could go wrong
- How you'll address it

**Ask**
- Specific resources needed
- Timeline
- Decision needed by when

### Tips That Actually Work

1. **Lead with the answer** — "I'm requesting $500K to build X, returning $2M in 18 months." Then explain.

2. **Show your math** — CFOs trust you more when they can see assumptions. Hidden assumptions look like hidden agendas.

3. **Use ranges** — "Expected return of $1.5-2.5M based on conversion rates of 3-5%" shows sophistication.

4. **Name the opportunity cost** — "If we don't do this, competitor X will capture $Y market."

5. **Pre-answer objections** — You know the "what about..." questions. Address them proactively.

6. **Know your comps** — "Similar investment last quarter returned X" builds credibility.

7. **Make it easy to say yes** — Clear ask, clear timeline, clear success metrics.

---

## Exercises

### Exercise 1: Read Real Financial Statements

Go to the SEC EDGAR database (sec.gov/edgar) and pull the 10-K for a company you use daily.

1. Find the three financial statements
2. Calculate: Gross margin, operating margin, R&D % of revenue
3. Calculate: Revenue growth YoY
4. Look at the cash flow statement: Is operating cash flow > net income? Why?

**Time:** 1 hour

### Exercise 2: Unit Economics Calculation

For a product you work on (or use), estimate:

1. What's the likely CAC? (estimate marketing spend, sales team cost, divide by new customers)
2. What's the ARPU?
3. What's the likely churn rate?
4. Calculate LTV
5. Calculate LTV:CAC ratio
6. Calculate payback period

Are these healthy? What would improve them?

**Time:** 45 minutes

### Exercise 3: Build a Business Case

Take a feature you want to build (or have built). Create a one-page business case using the structure above.

Requirements:
- Quantify the investment (engineering time has cost—estimate $150K/engineer/year fully loaded)
- Quantify the return (be explicit about assumptions)
- Calculate ROI
- Identify top 3 risks

**Time:** 1.5 hours

### Exercise 4: CFO Role Play

Find a colleague. Present your business case. Have them play CFO and push back:

- "Why this over other projects?"
- "How confident are you in these numbers?"
- "What happens if you're wrong?"
- "What's the minimum viable version?"

Iterate your business case based on the grilling.

**Time:** 1 hour

### Exercise 5: Translate Your Roadmap

Take your current product roadmap. For each item:

1. Identify the product metric it impacts
2. Translate to financial impact
3. Estimate investment
4. Rank by ROI

Does the ROI ranking match your current prioritization? If not, why?

**Time:** 1 hour

---

## Checklist: Are You Ready?

After completing this module, you should be able to:

- [ ] Read an income statement and explain gross vs operating margin
- [ ] Explain why profitable companies can go bankrupt (cash flow timing)
- [ ] Calculate CAC, LTV, LTV:CAC, and payback period
- [ ] Explain what drives valuation multiples
- [ ] Distinguish CapEx from OpEx and explain why it matters
- [ ] Translate a product metric improvement to $ impact
- [ ] Build a business case that addresses CFO concerns
- [ ] Use ROI, NPV, and payback period appropriately

---

## Key Terms Glossary

| Term | Definition |
|------|------------|
| ARPU | Average Revenue Per User |
| CAC | Customer Acquisition Cost |
| CapEx | Capital Expenditure |
| COGS | Cost of Goods Sold |
| DCF | Discounted Cash Flow |
| EBIT | Earnings Before Interest and Taxes |
| EBITDA | Earnings Before Interest, Taxes, Depreciation, Amortization |
| FCF | Free Cash Flow |
| GM | Gross Margin |
| IRR | Internal Rate of Return |
| LTV | Lifetime Value |
| NPV | Net Present Value |
| OpEx | Operating Expense |
| P&L | Profit and Loss Statement (Income Statement) |
| ROI | Return on Investment |

---

## Next Steps

1. **Read:** *Financial Intelligence* by Karen Berman & Joe Knight — The best accessible finance book for non-finance managers. Focus on Parts 1-3.

2. **Practice:** Do Exercise 3 (Build a Business Case) before moving to Module 2. Financial framing is a skill that improves with repetition.

3. **Apply:** In your next exec meeting, consciously translate one product metric to financial impact. Note the reaction.

---

*Module 2: Executive Communication & Influence is next.*

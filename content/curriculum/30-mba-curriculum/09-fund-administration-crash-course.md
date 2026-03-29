# Fund Administration Crash Course

**Context:** You work at Carta. This covers the fund administration domain.

---

## What Is Fund Administration?

Fund administration = back-office operations for investment funds.

**The job:** Handle everything that isn't investing—accounting, reporting, compliance, investor communications, capital calls, distributions.

**Why it exists:** Fund managers (GPs) want to invest, not do accounting. LPs want accurate reporting. Regulators want compliance. Fund admin does all of this.

**Market:** ~$300B+ AUM in fund admin industry. Consolidating. Tech-enabled players (Carta) disrupting legacy providers.

---

## Part 1: Fund Structures

### The Basic LP/GP Structure

```
LIMITED PARTNERS (LPs)          GENERAL PARTNER (GP)
├── Pension funds               ├── Fund managers
├── Endowments                  ├── Makes investment decisions
├── Family offices              ├── Unlimited liability
├── Fund of funds               └── Earns management fee + carry
├── HNW individuals
└── Passive investors
         │
         ▼
    LIMITED PARTNERSHIP
    (The actual fund)
         │
         ▼
    PORTFOLIO COMPANIES
```

**LP:** Contributes capital, limited liability, passive role, no control over investments

**GP:** Manages fund, makes decisions, unlimited liability, fiduciary duty to LPs

### Fund Types

| Fund Type | What They Invest In | Typical Life |
|-----------|---------------------|--------------|
| Venture Capital (VC) | Early-stage startups | 10-12 years |
| Private Equity (PE) | Mature companies, buyouts | 10-12 years |
| Hedge Fund | Public markets, various strategies | Open-ended |
| Real Estate | Properties, RE companies | 7-10 years |
| Credit/Debt | Loans, fixed income | 5-8 years |

**Carta focus:** Primarily VC/PE (closed-end funds), expanding to other types.

### Fund Lifecycle

```process-flow
{
  "title": "Fund lifecycle",
  "note": "Capital calls dominate early in the fund life; distributions dominate after exits begin.",
  "steps": [
    {
      "title": "Fundraising",
      "detail": "1-2 years."
    },
    {
      "title": "Investment",
      "detail": "3-5 years. Capital calls fund new deals."
    },
    {
      "title": "Harvest",
      "detail": "3-5 years. Exits begin returning capital."
    },
    {
      "title": "Wind-down",
      "detail": "1-2 years. Final distributions and termination."
    }
  ]
}
```

**Fundraising:** GP raises commitments from LPs
**Investment Period:** GP calls capital, makes investments (typically 3-5 years)
**Harvest Period:** GP exits investments, returns capital to LPs
**Wind-down:** Final distributions, fund termination

### Key Legal Documents

**Limited Partnership Agreement (LPA):**
- Constitution of the fund
- Defines GP/LP rights, economics, governance
- Fee structure, carry waterfall, distribution rules
- Everything flows from the LPA

**Subscription Agreement:**
- LP's commitment to invest
- KYC/AML information
- Representations and warranties

**Side Letters:**
- Individual LP modifications to LPA
- Fee discounts, co-invest rights, reporting requirements
- Nightmare to track—key pain point

**Private Placement Memorandum (PPM):**
- Marketing document for fundraising
- Fund strategy, terms, risks
- Required disclosures

---

## Part 2: Fund Economics

### Management Fee

**What:** Annual fee paid to GP for managing the fund

**Typical:** 2% of committed capital (investment period), then 2% of invested capital (harvest)

**Calculation variations:**
- Committed capital vs invested capital vs NAV
- Step-downs over time
- Offsets for deal fees

**Example:**
```
$100M fund, 2% management fee
Investment period: $2M/year
After investment period: 2% of remaining invested capital
```

### Carried Interest (Carry)

**What:** GP's share of profits above a threshold

**Typical:** 20% of profits after returning capital + preferred return

**The waterfall (simplified):**
```
1. Return of capital (LPs get their money back)
2. Preferred return (LPs get ~8% annual return)
3. GP catch-up (GP gets carry until 20/80 split achieved)
4. 80/20 split (remaining profits split 80% LP, 20% GP)
```

**Example:**
```
$100M fund invests, returns $200M (2x)

Step 1: $100M → LPs (return of capital)
Step 2: ~$47M → LPs (8% pref over 5 years, compounded)
Step 3: ~$12M → GP (catch-up to 20%)
Step 4: Remaining $41M split 80/20
        $33M → LPs, $8M → GP

Total: LPs get $180M, GP gets $20M
```

### Preferred Return (Hurdle Rate)

**What:** Minimum return LPs must receive before GP gets carry

**Typical:** 8% annual (sometimes compounded, sometimes simple)

**Why it exists:** Aligns GP incentive—no carry until LPs see real returns

### Distribution Waterfall

**American waterfall (deal-by-deal):**
- Carry calculated per investment
- GP gets carry on each profitable exit
- Clawback provisions if later investments lose money
- More GP-friendly

**European waterfall (whole fund):**
- Carry calculated on entire fund
- LPs get all capital + pref back before any carry
- More LP-friendly

**Fund admin complexity:** Tracking waterfall precisely is core job. Errors = lawsuits.

### Fee Offsets

**Problem:** GP earns fees from portfolio companies (board seats, transaction fees, monitoring fees)

**Solution:** These often offset management fees to LPs

**Typical:** 80-100% offset

**Admin complexity:** Track all fee income, apply correct offset, reconcile quarterly

---

## Part 3: Capital Calls & Distributions

### Capital Calls

**What:** GP requests committed capital from LPs

**Process:**
1. GP identifies investment opportunity
2. Calculate amount needed
3. Issue capital call notice (typically 10-14 days notice per LPA)
4. LPs wire funds
5. Fund admin reconciles, allocates to LP accounts

**What's in a capital call:**
```
- Total amount called
- Purpose (investment, fees, expenses)
- Each LP's share (pro-rata to commitment)
- Wire instructions
- Due date
- Late payment penalties
```

**Complexity:**
- Side letter variations (some LPs have different terms)
- Excuse/exclude provisions (some LPs can't invest in certain deals)
- Defaulting LPs (don't pay—serious consequences)
- Multiple closings (LPs joining at different times)

### Distributions

**What:** Returning capital/profits to LPs

**Types:**
- **Return of capital:** Original investment coming back
- **Profits:** Returns above capital
- **Recallable:** Can be called again for future investments
- **Non-recallable:** Permanent distribution

**Process:**
1. Exit event (sale, IPO, dividend)
2. Calculate proceeds
3. Apply waterfall
4. Determine tax character (capital gains vs ordinary income)
5. Issue distribution notice
6. Wire to LPs

**In-kind distributions:**
- Distribute stock instead of cash (common post-IPO)
- Valuation challenges
- LP preference varies

### LP Accounting

**For each LP, track:**
- Commitment amount
- Called capital
- Uncalled commitment
- Distributions received
- Current NAV
- IRR, TVPI, DPI (performance metrics)

**Challenge:** Each LP may have different:
- Commitment timing (multiple closings)
- Fee arrangements (side letters)
- Excuse rights (can't invest in certain things)
- Tax status (taxable vs tax-exempt)

---

## Part 4: Fund Accounting

### NAV Calculation

**Net Asset Value (NAV):** Fair value of fund assets minus liabilities

```
NAV = Fair Value of Investments
    + Cash
    + Receivables
    - Payables
    - Accrued Fees
    - Fund Expenses
```

**LP's NAV:** Their share of total fund NAV

### Investment Valuation

**The hard problem:** Private companies don't have market prices

**Valuation hierarchy (ASC 820):**
- Level 1: Quoted prices (public stocks)
- Level 2: Observable inputs (comparable transactions)
- Level 3: Unobservable inputs (models, assumptions)

**Most VC/PE investments are Level 3**—significant judgment required

**Common approaches:**
- Last round price (with adjustments)
- Comparable company multiples
- DCF (less common for early-stage)
- Option pricing models (for complex structures)

**Valuation frequency:**
- Quarterly NAV reporting standard
- Annual third-party valuations common
- Trigger events (new rounds, material changes)

### Fund Expenses

**GP-covered (from management fee):**
- Salaries, office, travel
- Basic operations

**Fund-covered (charged to LPs):**
- Legal (fund formation, deals)
- Audit
- Tax preparation
- Fund admin fees
- Broken deal costs
- D&O insurance

**Allocation methods:**
- Pro-rata by commitment
- Pro-rata by NAV
- Specific allocation (deal-specific costs)

### Accounting Standards

**US GAAP investment company (ASC 946):**
- Fair value accounting for investments
- Specific presentation requirements
- Most US funds

**IFRS:**
- International funds
- Similar fair value approach

**Tax basis:**
- Different from GAAP
- Required for K-1s
- Permanent and timing differences

---

## Part 5: Investor Reporting

### Quarterly Reports

**Standard contents:**
- NAV statement
- Capital account statement
- Portfolio summary
- Investment updates
- Performance metrics

**Capital Account Statement (per LP):**
```
Beginning Balance
+ Capital Contributions
- Distributions
+/- Change in Unrealized Value
+/- Realized Gains/Losses
- Fees & Expenses
= Ending Balance
```

### Performance Metrics

**IRR (Internal Rate of Return):**
- Time-weighted return
- Accounts for timing of cash flows
- Standard PE/VC metric
- Sensitive to early exits

**TVPI (Total Value to Paid-In):**
- (NAV + Distributions) / Paid-In Capital
- Simple multiple
- Doesn't account for time

**DPI (Distributions to Paid-In):**
- Distributions / Paid-In Capital
- "Cash-on-cash" return
- What LPs actually received

**RVPI (Residual Value to Paid-In):**
- NAV / Paid-In Capital
- "Paper" returns still in fund

**Relationship:** TVPI = DPI + RVPI

**Example:**
```
LP invested $1M, received $500K distributions, NAV = $800K

DPI = $500K / $1M = 0.5x
RVPI = $800K / $1M = 0.8x
TVPI = 1.3x

IRR depends on timing of flows
```

### Annual Financials

**Audited financial statements:**
- Required by LPA (usually)
- Required by regulators (for larger funds)
- LP due diligence requirement

**Contents:**
- Balance sheet
- Statement of operations
- Statement of changes in partners' capital
- Statement of cash flows
- Notes (significant)
- Schedule of investments

**Timeline:** Typically 90-120 days after year-end

### K-1s (Tax Reporting)

**What:** Schedule K-1 reports each LP's share of fund income/loss

**Why complex:**
- Different tax character (ordinary, capital gains, qualified dividends)
- State allocations
- UBTI (for tax-exempt investors)
- Foreign tax credits
- Timing differences from GAAP

**Timeline:** March 15 (or extended) for calendar-year funds

**LP pain point:** Late K-1s delay LP tax filings

---

## Part 6: Regulatory & Compliance

### SEC Registration

**Investment Advisers Act of 1940:**
- Funds >$150M AUM generally must register
- Venture capital fund exemption (if qualifying)
- Private fund adviser exemption (<$150M)

**Form ADV:**
- Registration document
- Discloses business, fees, conflicts, disciplinary history
- Part 2 = "brochure" given to investors

### Form PF

**What:** Confidential reporting to SEC for systemic risk monitoring

**Who:** Registered advisers with >$150M private fund AUM

**Content:**
- Fund size, leverage, counterparty exposure
- Liquidity, investor concentration
- More detailed for larger funds

### Anti-Money Laundering (AML)

**Know Your Customer (KYC):**
- Verify LP identity
- Beneficial ownership
- Source of funds

**OFAC screening:**
- Check against sanctions lists
- Required for all investors
- Ongoing monitoring

### ERISA

**What:** If fund has "benefit plan investors" (pensions), special rules apply

**25% test:** If >25% of fund from benefit plans, fund assets become "plan assets" → extensive ERISA compliance

**Most funds:** Structure to stay under 25% or use VCOC exemption

### FATCA/CRS

**FATCA (US):**
- Identify US persons in foreign structures
- Report to IRS

**CRS (global):**
- Common Reporting Standard
- Automatic exchange of tax information between countries

**Fund admin role:** Collect proper tax forms (W-8/W-9), report as required

---

## Part 7: Fund Admin Technology

### Core Systems

**General Ledger:**
- Fund-level accounting
- Investment tracking
- Partner capital

**Investor Portal:**
- LP access to documents, statements
- Capital call/distribution notices
- K-1 delivery

**Document Management:**
- LPAs, side letters, subscription docs
- Version control critical

**Waterfall Engine:**
- Complex distribution calculations
- Scenario modeling
- Audit trail

### The Carta Advantage

**Traditional fund admin:**
- Excel-heavy
- Manual reconciliation
- Disconnected systems
- Paper-based investor communications

**Tech-enabled (Carta model):**
- Integrated cap table + fund admin
- Automated workflows
- Self-service investor portal
- Real-time reporting
- API integrations

### Data Challenges

**Data sources:**
- Portfolio company financials
- Bank/custodian feeds
- Investor communications
- Third-party valuations

**Reconciliation points:**
- Cash (bank vs books)
- Investments (custodian vs ledger)
- Capital accounts (LP statements vs fund records)
- Waterfall (GP vs admin calculations)

---

## Part 8: Key Pain Points

### For GPs

1. **Time to close:** Want fast fund closings, onboarding
2. **Reporting accuracy:** Errors damage LP relationships
3. **Fee calculations:** Complex, must be right
4. **Audit readiness:** Clean books, supporting docs
5. **Visibility:** Real-time view of fund status

### For LPs

1. **K-1 timeliness:** Late K-1s = tax filing extensions
2. **Reporting consistency:** Different funds, different formats
3. **Portal access:** Self-service document retrieval
4. **Performance accuracy:** Trust but verify NAV
5. **Transparency:** What's happening with my money?

### For Fund Admins

1. **Side letter management:** Each LP is different
2. **Waterfall complexity:** Edge cases, amendments
3. **Valuation support:** Substantiating Level 3 values
4. **Multi-fund complexity:** Same GP, many funds, shared costs
5. **Regulatory changes:** Keeping up with requirements

---

## Part 9: Industry Trends

### Consolidation

- Large players acquiring smaller admins
- Scale economies in compliance, tech
- Carta positioning as tech-forward consolidator

### Automation

- Manual processes → automated workflows
- Excel → purpose-built software
- Batch processing → real-time

### Transparency

- LPs demanding more data, faster
- Real-time portals vs quarterly PDFs
- API access to underlying data

### Regulatory Pressure

- Increased SEC scrutiny of private funds
- New rules on fees, expenses, conflicts
- Marketing rule changes

### Democratization

- Smaller funds need admin too
- Solo GPs, emerging managers
- Lower minimums → more LPs to manage

---

## Key Terms Glossary

| Term | Definition |
|------|------------|
| AUM | Assets Under Management |
| Carry | GP's share of profits (typically 20%) |
| Capital Call | Request for LP to contribute committed capital |
| Commitment | Amount LP agrees to invest over fund life |
| DPI | Distributions to Paid-In (cash returned / invested) |
| GP | General Partner (fund manager) |
| IRR | Internal Rate of Return |
| K-1 | Tax form showing LP's share of fund income/loss |
| LP | Limited Partner (investor) |
| LPA | Limited Partnership Agreement |
| Management Fee | Annual fee to GP (typically 2% of commitments) |
| NAV | Net Asset Value |
| Preferred Return | Hurdle rate LPs must receive before carry |
| Side Letter | Individual LP modifications to standard terms |
| TVPI | Total Value to Paid-In (NAV + distributions / invested) |
| Vintage Year | Year fund began investing |
| Waterfall | Order of distributions between LP and GP |

---

## Recommended Reading

**Books:**
- *Venture Deals* by Brad Feld — VC mechanics from founder perspective
- *The Masters of Private Equity* by Robert Finkel — Industry overview
- *Private Equity Operational Due Diligence* by Jason Scharfman — Deep on operations

**Resources:**
- ILPA (Institutional Limited Partners Association) — LP perspective, templates
- SEC.gov Investment Adviser resources — Regulatory requirements
- AICPA PE/VC guide — Accounting standards

---

## Your First 90 Days

**Week 1-2:** Understand Carta's fund admin product offering. What do we do vs competitors?

**Week 3-4:** Shadow customer calls. Hear GP/LP pain points firsthand.

**Month 2:** Deep dive on one fund type (probably VC). Understand full lifecycle.

**Month 3:** Learn the edge cases—side letters, complex waterfalls, multi-fund GPs.

**Ongoing:** Build relationships with fund admin ops team—they know where the bodies are buried.

---

*Welcome to Carta. The fund admin space is complex but learnable. The opportunity is automating a $300B industry that still runs on spreadsheets.*

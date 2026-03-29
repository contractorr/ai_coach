# Module 02: Fund Structure & Participants

## Learning Objectives

By the end of this module, you will understand:
- The Limited Partnership structure and why it's used
- Detailed roles of GPs and LPs
- How the management company relates to the fund
- Governance mechanisms (LPAC, key person provisions)
- Legal documents that govern fund operations

---

## 2.1 The Limited Partnership Structure

### Why Limited Partnership?

Private equity funds are almost universally structured as **Limited Partnerships (LPs)** for three key reasons:

| Benefit | Explanation |
|---------|-------------|
| **Tax efficiency** | Partnership is "pass-through" - no entity-level tax. Income/gains taxed only at partner level |
| **Limited liability** | LPs can only lose what they invested (unlike general partnerships) |
| **Flexibility** | Partnership agreement can be customized extensively |

### Legal Structure Diagram

```diagram
{
  "title": "Fund legal structure",
  "note": "The fund, GP, LP base, and management company are distinct legal actors with different rights and obligations.",
  "nodes": [
    {
      "id": "gp",
      "title": "General partner",
      "detail": "ABC GP VII LLC. Usually 1-2% of capital, controls investments, and bears unlimited liability.",
      "column": 1,
      "row": 1,
      "tone": "accent"
    },
    {
      "id": "fund",
      "title": "Limited partnership fund",
      "detail": "ABC Partners Fund VII, LP. The legal vehicle that pools LP and GP capital.",
      "column": 2,
      "row": 1,
      "tone": "default"
    },
    {
      "id": "lps",
      "title": "Limited partners",
      "detail": "State pension funds, endowments, sovereign wealth funds, insurers, and family offices. Usually 98-99% of capital.",
      "column": 3,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "mgmtco",
      "title": "Management company",
      "detail": "ABC Capital Management LLC. Employs the team, receives management fees, and services the fund.",
      "column": 2,
      "row": 2,
      "tone": "muted"
    }
  ],
  "edges": [
    { "from": "gp", "to": "fund", "label": "controls" },
    { "from": "lps", "to": "fund", "label": "provide capital" },
    { "from": "mgmtco", "to": "fund", "label": "services" },
    { "from": "gp", "to": "mgmtco", "label": "manages" }
  ]
}
```

---

## 2.2 The General Partner (GP) - Deep Dive

### Who is the GP?

The GP is typically a dedicated legal entity (usually an LLC) controlled by the fund manager. It has full authority over fund operations.

### GP Responsibilities

| Category | Responsibilities |
|----------|-----------------|
| **Investment Management** | Source, evaluate, execute, and exit investments |
| **Portfolio Management** | Work with companies to create value |
| **Fund Administration** | Capital calls, distributions, reporting |
| **Regulatory Compliance** | SEC registration, filings, compliance |
| **LP Relations** | Quarterly reports, annual meetings, communications |

### GP Economics

The GP makes money in two ways:

```framework
{
  "title": "GP compensation",
  "pillars": [
    {
      "title": "Management fee",
      "detail": "Steady income, usually 1.5-2.0% of committed capital annually.",
      "bullets": [
        "Covers salaries, office costs, and operations.",
        "Paid regardless of performance.",
        "Example: a $2B fund at 2% generates $40M per year."
      ]
    },
    {
      "title": "Carried interest",
      "detail": "Performance fee, usually 20% of profits after the hurdle is met.",
      "bullets": [
        "Aligns GP economics with LP returns.",
        "Earned only after profit is created.",
        "Example: $2B returned as $3.5B implies $1.5B of profit and $300M of carry at 20%."
      ]
    }
  ]
}
```

### GP Commitment ("Skin in the Game")

GPs typically invest 1-5% of fund capital alongside LPs:

| Purpose | Explanation |
|---------|-------------|
| **Alignment** | GP gains/loses alongside LPs |
| **Credibility** | Demonstrates conviction in strategy |
| **LP expectation** | Most LPs require meaningful GP commit |

**Example**:
- $2B fund
- GP commits 2% = $40M
- Often funded from prior fund profits or partners' personal capital

---

## 2.3 The Limited Partner (LP) - Deep Dive

### Who are LPs?

LPs are the investors who provide the vast majority (typically 98-99%) of fund capital.

### LP Categories

```framework
{
  "title": "LP universe",
  "note": "Institutional investors dominate private markets, but several other channels participate as well.",
  "pillars": [
    {
      "title": "Pension funds",
      "bullets": [
        "CalPERS",
        "Ontario Teachers'",
        "Dutch ABP",
        "UK USS"
      ]
    },
    {
      "title": "Endowments and foundations",
      "bullets": [
        "Yale Endowment",
        "Harvard Management",
        "Ford Foundation",
        "Gates Foundation"
      ]
    },
    {
      "title": "Sovereign wealth",
      "bullets": [
        "GIC",
        "ADIA",
        "Norway GPFG",
        "CIC"
      ]
    },
    {
      "title": "Insurance companies",
      "bullets": [
        "Prudential",
        "MetLife",
        "AXA",
        "Allianz"
      ]
    },
    {
      "title": "Other investors",
      "bullets": [
        "Family offices",
        "Funds of funds",
        "High-net-worth investors",
        "Banks and asset managers"
      ]
    }
  ]
}
```

### LP Rights and Obligations

| Rights | Obligations |
|--------|-------------|
| Limited liability (can only lose investment) | Fund capital when called |
| Receive quarterly/annual reports | Meet call deadlines (usually 10 business days) |
| Vote on certain matters | Maintain confidentiality |
| Transfer interests (with GP consent) | Comply with regulatory requirements |
| Attend annual meetings | |
| LPAC membership (for large LPs) | |

### What LPs Cannot Do

To maintain limited liability, LPs must remain **passive**:

- ❌ Cannot make investment decisions
- ❌ Cannot hire/fire GP employees
- ❌ Cannot direct fund operations
- ❌ Cannot negotiate deal terms

**Why?** Active involvement could make them liable as a general partner.

---

## 2.4 The Management Company

### Separate Entity

The Management Company is distinct from both the GP entity and the Fund:

```diagram
{
  "title": "Management company as a separate entity",
  "note": "One management company can operate across several vintages at the same time.",
  "nodes": [
    {
      "id": "mgmtco",
      "title": "ABC Capital Management LLC",
      "detail": "Employs the team, receives management fees, and owns the operating infrastructure.",
      "column": 2,
      "row": 1,
      "tone": "accent"
    },
    {
      "id": "fund-v",
      "title": "Fund V",
      "detail": "Mature vintage.",
      "column": 1,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "fund-vi",
      "title": "Fund VI",
      "detail": "Currently investing.",
      "column": 2,
      "row": 2,
      "tone": "default"
    },
    {
      "id": "fund-vii",
      "title": "Fund VII",
      "detail": "Currently fundraising.",
      "column": 3,
      "row": 2,
      "tone": "muted"
    }
  ],
  "edges": [
    { "from": "mgmtco", "to": "fund-v", "label": "services" },
    { "from": "mgmtco", "to": "fund-vi", "label": "services" },
    { "from": "mgmtco", "to": "fund-vii", "label": "services" }
  ]
}
```

### Why Separate?

| Reason | Benefit |
|--------|---------|
| **Asset protection** | Fund assets separate from GP business |
| **Multi-fund management** | Same team manages several vintage funds |
| **Operational continuity** | Company continues if individual fund winds down |
| **Clean economics** | Clearer allocation of fees and expenses |

---

## 2.5 Governance Mechanisms

### LP Advisory Committee (LPAC)

Most funds have an advisory committee of 5-15 large LPs:

**Composition**:
- Typically largest LPs by commitment
- Sometimes includes founding/anchor investors
- GP often serves as non-voting secretary

**Responsibilities**:

| Function | Description |
|----------|-------------|
| **Conflict review** | Approve transactions where GP has a conflict |
| **Valuation oversight** | Review/approve valuation policies |
| **Consent rights** | Approve certain GP actions |
| **Advisory role** | Provide guidance (not binding) |

**Examples of LPAC review**:
- GP investing in a company where a partner has personal interest
- Co-investment with another fund managed by GP
- Extension of investment period
- Changes to valuation methodology

### Key Person Provisions

Fund documents typically include **key person clauses** tied to specific senior professionals:

**How it works**:
1. LPA names 2-5 "key persons" (senior partners)
2. If key persons leave or reduce involvement
3. Investment period is suspended
4. LPs vote whether to continue or wind down

**Purpose**: LPs commit based on team track record - protects against team departures.

### No-Fault Divorce

Some LPAs allow LPs to remove the GP through supermajority vote:

- Typically requires 75-80% of capital voting
- Rare but provides ultimate LP protection
- Triggers appointment of new GP or fund wind-down

---

## 2.6 Governing Documents

### Limited Partnership Agreement (LPA)

The **LPA** is the master document governing the fund. Key sections:

| Section | Contents |
|---------|----------|
| **Definitions** | Terms used throughout agreement |
| **Capital Commitments** | Rules for contributions, calls, defaults |
| **Management & Conduct** | GP powers, restrictions, standards |
| **Fees & Expenses** | Management fee, carry, expense allocation |
| **Distributions** | Waterfall, timing, form of distributions |
| **LPAC** | Composition, powers, procedures |
| **Transfers** | Rules for LP interest transfers |
| **Term & Dissolution** | Fund duration, extension, wind-down |
| **Indemnification** | Protection for GP and LPs |

### Side Letters

**Side letters** are separate agreements giving specific LPs special terms:

**Common side letter provisions**:
- Management fee discounts
- Co-investment rights
- Most Favored Nation (MFN) clauses
- Excuse rights (opt out of certain investments)
- Enhanced reporting
- Regulatory accommodations

**Example**:
> "Notwithstanding Section 4.1 of the LPA, LP shall pay a management fee of 1.5% (rather than 2.0%) on its committed capital..."

### Subscription Agreement

Signed by each LP when joining the fund:
- Confirms commitment amount
- Representations about LP status (accredited, etc.)
- Wire instructions
- Signature authority

### Private Placement Memorandum (PPM)

Marketing document provided during fundraising:
- Fund strategy and thesis
- Team biographies
- Track record
- Terms summary
- Risk factors

---

## 2.7 The LP-GP Relationship

### Information Flow

```diagram
{
  "title": "LP-GP information flow",
  "note": "The GP communicates through recurring reporting plus event-driven notices.",
  "nodes": [
    {
      "id": "gp",
      "title": "GP",
      "detail": "Produces reports and notices for LPs.",
      "column": 2,
      "row": 1,
      "tone": "accent"
    },
    {
      "id": "quarterly",
      "title": "Quarterly report",
      "detail": "NAV, IRR/TVPI, portfolio updates, and fund activity.",
      "column": 1,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "annual",
      "title": "Annual report",
      "detail": "Audited financials, detailed portfolio detail, and K-1 tax information.",
      "column": 2,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "notices",
      "title": "Capital call and distribution notices",
      "detail": "Amount, purpose, due date, and wire instructions.",
      "column": 3,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "lp",
      "title": "LP",
      "detail": "Receives recurring reporting and funds or receives cash accordingly.",
      "column": 2,
      "row": 3,
      "tone": "default"
    }
  ],
  "edges": [
    { "from": "gp", "to": "quarterly" },
    { "from": "gp", "to": "annual" },
    { "from": "gp", "to": "notices" },
    { "from": "quarterly", "to": "lp" },
    { "from": "annual", "to": "lp" },
    { "from": "notices", "to": "lp" }
  ]
}
```

### Trust but Verify

The LP-GP relationship is built on trust, with verification mechanisms:

| Trust Elements | Verification Elements |
|----------------|----------------------|
| GP expertise in investing | Audited financial statements |
| Alignment through GP commit | Independent valuations |
| Long-term relationship | LPAC oversight |
| Reputation stakes | Regulatory registration |

---

## 2.8 Summary: Who Does What

| Role | Primary Function | Key Rights | Key Obligations |
|------|-----------------|------------|-----------------|
| **GP** | Manage fund | Full investment discretion | Fiduciary duty to LPs |
| **LP** | Provide capital | Limited liability, reports, voting | Fund capital calls |
| **Management Co** | Employ team | Receive management fees | Provide services |
| **LPAC** | Oversight | Review conflicts | Act in all LPs' interest |

---

## Knowledge Check

1. Why is the Limited Partnership structure preferred for private funds?
2. What are the two ways GPs make money?
3. Why must LPs remain passive?
4. What triggers a "key person" event?
5. What's the difference between the GP entity and the Management Company?

<details>
<summary>Answers</summary>

1. Tax efficiency (pass-through), limited liability for LPs, flexibility in structuring
2. Management fees (1.5-2% annually) and carried interest (20% of profits)
3. Active involvement could expose them to unlimited liability as a general partner
4. When named key persons leave the firm or significantly reduce their involvement
5. GP entity has authority over fund decisions; Management Company employs the team and receives fees (can manage multiple funds)

</details>

---

## Practical Exercise

You're reviewing an LPA. Answer these questions:

**Scenario**: $1.5B fund, 2% management fee, 20% carry over 8% hurdle, 3 key persons, 5-year investment period.

1. What is the annual management fee during the investment period?
2. If key person #1 leaves, what happens?
3. Who approves a transaction where the GP's CFO is also a board member of the target company?

<details>
<summary>Answers</summary>

1. $1.5B × 2% = $30M/year
2. Investment period is suspended; LPs vote on whether to continue
3. LPAC reviews and approves (conflict of interest)

</details>

---

## Next Module

[Module 03: Types of Private Market Funds →](03-fund-types.md)

Explore the different fund strategies: private equity buyout, venture capital, real assets, credit, and fund-of-funds.

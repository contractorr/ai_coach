# Module 05: Capital Mechanics

## Learning Objectives

By the end of this module, you will understand:
- The difference between commitment, contributed capital, and distributions
- How capital calls work operationally
- Distribution mechanics and types
- Recallable vs non-recallable capital
- How to read capital account statements
- The mathematical relationships between these concepts

---

## 5.1 The Three Key Capital Concepts

```process-flow
{
  "title": "Capital concepts",
  "note": "Unfunded commitment is what remains after contributed capital, adjusted for any recallable distributions.",
  "steps": [
    {
      "title": "Commitment",
      "detail": "A legal promise to invest, for example $100M."
    },
    {
      "title": "Contributed capital",
      "detail": "Actual money sent to the GP, for example $85M called so far."
    },
    {
      "title": "Distributions",
      "detail": "Capital and profit returned to the LP, for example $120M received back."
    }
  ]
}
```

### Definitions

| Term | Definition | Also Called |
|------|------------|-------------|
| **Commitment** | Total amount LP legally promised to invest | Committed capital |
| **Contributed Capital** | Cumulative amount actually paid to fund | Paid-in capital, Called capital, Drawn capital |
| **Distributions** | Cumulative amount returned to LP | Distributed capital |
| **Unfunded Commitment** | Remaining amount LP must pay when called | Uncalled capital, Dry powder |

### The Fundamental Equation

```
Unfunded Commitment = Total Commitment
                    - Contributed Capital
                    + Recallable Distributions
```

**Example**:
```
Total Commitment:           $50,000,000
Contributed Capital:        $42,000,000
Recallable Distributions:   $3,000,000
─────────────────────────────────────────
Unfunded Commitment:        $11,000,000

($50M - $42M + $3M = $11M)
```

---

## 5.2 Commitment Deep Dive

### What a Commitment Really Means

When an LP commits capital, they:

1. **Sign legally binding documents** (Subscription Agreement)
2. **Promise to pay** when the GP calls capital
3. **Have a contingent liability** on their balance sheet
4. **Must maintain liquidity** to meet future calls

### Commitment is NOT:

- ❌ Money sitting in an account
- ❌ Money immediately invested
- ❌ Transferable without GP consent
- ❌ Reducible (except in rare circumstances)

### Commitment Timeline

```process-flow
{
  "title": "Commitment lifecycle",
  "steps": [
    {
      "title": "Fund closing",
      "detail": "LP makes a $100M commitment."
    },
    {
      "title": "Years 1-4",
      "detail": "Capital is called in stages: $20M, $25M, $30M, then $15M."
    },
    {
      "title": "Year 5",
      "detail": "$10M is called before the investment period ends."
    },
    {
      "title": "Fund end",
      "detail": "Total called equals $100M, leaving no expiry in this example."
    }
  ]
}
```

### Over-Commitment Strategies

Sophisticated LPs often commit MORE than they can fund at once, banking on:

- Staggered calling across multiple funds
- Distributions from older funds funding calls from newer funds
- Not all commitments being fully drawn

```
```comparison-table
{
  "title": "Over-commitment example",
  "note": "LPs may commit more than current cash on hand because calls are staggered over time.",
  "columns": [
    { "key": "approach", "label": "Approach" },
    { "key": "commitments", "label": "Commitments" },
    { "key": "total", "label": "Total Commitment" },
    { "key": "risk", "label": "Key Tradeoff" }
  ],
  "rows": [
    {
      "approach": "Conservative",
      "commitments": "Fund A $33M, Fund B $33M, Fund C $34M",
      "total": "$100M (1.0x)",
      "risk": "Lower liquidity stress."
    },
    {
      "approach": "Aggressive",
      "commitments": "Fund A $50M, Fund B $50M, Fund C $50M, Fund D $50M",
      "total": "$200M (2.0x)",
      "risk": "Works if vintages stagger; breaks if all funds call at once."
    }
  ]
}
```

---

## 5.3 Capital Calls (Drawdowns)

### What is a Capital Call?

A **capital call** (or drawdown) is the GP's formal request for LPs to send money.

### Capital Call Process

```process-flow
{
  "title": "Capital call workflow",
  "steps": [
    {
      "title": "Day 0: GP decision",
      "detail": "The GP identifies the need, sizes the call, and prepares the notice."
    },
    {
      "title": "Day 1: Notice sent",
      "detail": "LPs receive the amount, purpose, due date, and wire instructions."
    },
    {
      "title": "Days 1-10: LP processing",
      "detail": "LP teams route approvals and treasury arranges the wire."
    },
    {
      "title": "Day 10: Due date",
      "detail": "Funds must arrive; late fees or default provisions apply if missed."
    }
  ]
}
```

### Sample Capital Call Notice

```
╔══════════════════════════════════════════════════════════════╗
║                    CAPITAL CALL NOTICE                        ║
║                    ABC Partners Fund VII                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Date:           March 15, 2024                               ║
║  Call Number:    12                                           ║
║  Due Date:       March 25, 2024                               ║
║                                                               ║
║  ─────────────────────────────────────────────────────────── ║
║  PURPOSE OF CALL                                              ║
║  ─────────────────────────────────────────────────────────── ║
║  Investment in TechCo Holdings         $45,000,000           ║
║  Follow-on: DataSoft Inc.              $12,000,000           ║
║  Management Fee (Q2 2024)              $8,000,000            ║
║  Partnership Expenses                  $500,000              ║
║  ─────────────────────────────────────────────────────────── ║
║  TOTAL CALL (All Partners)             $65,500,000           ║
║  ═══════════════════════════════════════════════════════════ ║
║                                                               ║
║  YOUR SHARE (2.50% Interest)                                  ║
║  ─────────────────────────────────────────────────────────── ║
║  Investment Capital                    $1,425,000            ║
║  Management Fee                        $200,000              ║
║  Partnership Expenses                  $12,500               ║
║  ─────────────────────────────────────────────────────────── ║
║  TOTAL DUE FROM YOU                    $1,637,500            ║
║                                                               ║
║  ─────────────────────────────────────────────────────────── ║
║  WIRE INSTRUCTIONS                                            ║
║  Bank: First National Bank                                    ║
║  ABA: 123456789                                               ║
║  Account: ABC Partners Fund VII                               ║
║  Account #: 9876543210                                        ║
║  Reference: [Your LP Name] - Call 12                          ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
```

### Types of Capital Calls

| Call Type | Purpose | Frequency |
|-----------|---------|-----------|
| **Investment** | Fund portfolio company purchases | As deals close |
| **Management Fee** | Pay GP's management fee | Quarterly |
| **Expenses** | Legal, audit, admin costs | Quarterly or as needed |
| **Working Capital** | Fund operational needs | Occasional |
| **Follow-on** | Additional investment in existing company | As needed |

### Call Components Breakdown

```
TYPICAL CALL BREAKDOWN (Over Fund Life)
───────────────────────────────────────

                            Year 1   Year 2   Year 3   Year 4   Year 5   Total
                            ──────   ──────   ──────   ──────   ──────   ──────
Investment Capital          $15M     $22M     $18M     $10M     $5M      $70M
Management Fees             $4M      $4M      $4M      $4M      $4M      $20M
Partnership Expenses        $0.5M    $0.3M    $0.3M    $0.3M    $0.3M    $1.7M
Working Capital             $1M      $0       $0       $0       $0       $1M
                            ──────   ──────   ──────   ──────   ──────   ──────
TOTAL CALLS                 $20.5M   $26.3M   $22.3M   $14.3M   $9.3M    $92.7M

Of $100M commitment:
• 93% called
• 7% expired at end of investment period
```

### Default on Capital Calls

If an LP fails to fund a capital call, severe consequences follow:

| Consequence | Description |
|-------------|-------------|
| **Late Fee** | Interest charges (often LIBOR + 3-5%) |
| **Forfeiture** | May lose portion of existing interest |
| **Forced Sale** | GP can sell LP's interest to cover |
| **Legal Action** | GP can sue for breach of contract |

**LPs take call obligations extremely seriously** - defaults are rare and career-ending for institutional investors.

---

## 5.4 Distributions

### What is a Distribution?

A **distribution** returns capital from the fund to LPs. This is how investors realize returns.

### Distribution Process

```process-flow
{
  "title": "Distribution workflow",
  "steps": [
    {
      "title": "Exit event",
      "detail": "A sale, dividend recap, or other liquidity event generates proceeds."
    },
    {
      "title": "GP calculation",
      "detail": "The GP applies the waterfall, allocates proceeds, and prepares the notice."
    },
    {
      "title": "Distribution",
      "detail": "LPs receive notice, the wire arrives, and capital accounts are updated."
    }
  ]
}
```

### Sample Distribution Notice

```
╔══════════════════════════════════════════════════════════════╗
║                  DISTRIBUTION NOTICE                          ║
║                  ABC Partners Fund VII                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Date:           June 30, 2024                                ║
║  Distribution #: 8                                            ║
║                                                               ║
║  ─────────────────────────────────────────────────────────── ║
║  SOURCE OF DISTRIBUTION                                       ║
║  ─────────────────────────────────────────────────────────── ║
║  Sale of TechCo Holdings (100%)        $180,000,000          ║
║  Original Investment                   $45,000,000           ║
║  Realized Gain                         $135,000,000          ║
║  ═══════════════════════════════════════════════════════════ ║
║                                                               ║
║  DISTRIBUTION BREAKDOWN (All Partners)                        ║
║  ─────────────────────────────────────────────────────────── ║
║  Return of Capital                     $45,000,000           ║
║  Realized Gain (LP Share 80%)          $108,000,000          ║
║  Less: Carried Interest (GP 20%)       ($27,000,000)         ║
║  ─────────────────────────────────────────────────────────── ║
║  TOTAL LP DISTRIBUTION                 $153,000,000          ║
║                                                               ║
║  ─────────────────────────────────────────────────────────── ║
║  YOUR SHARE (2.50% Interest)                                  ║
║  ─────────────────────────────────────────────────────────── ║
║  Return of Capital                     $1,125,000            ║
║  Realized Gain                         $2,700,000            ║
║  ─────────────────────────────────────────────────────────── ║
║  TOTAL DUE TO YOU                      $3,825,000            ║
║                                                               ║
║  Tax Character:                                               ║
║  • Long-term capital gain: $2,700,000                        ║
║  • Return of capital: $1,125,000                             ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
```

### Distribution Types

| Type | Description | Tax Treatment |
|------|-------------|---------------|
| **Return of Capital** | Return of LP's original investment | Reduces cost basis |
| **Realized Gain** | Profit from sold investment | Capital gain |
| **Dividend Income** | Dividends from portfolio companies | Ordinary income |
| **Interest Income** | Interest earned | Ordinary income |
| **Carried Interest** | GP's profit share (to GP) | Typically capital gain |

### Distribution Timing

```
WHEN DISTRIBUTIONS OCCUR
────────────────────────

INVESTMENT EXITS
├── Trade sale closes
├── Secondary sale closes
├── IPO + lock-up expiration
└── Typically within 30-60 days of exit

DIVIDEND RECAPITALIZATIONS
├── Portfolio company refinances
├── Takes out debt, pays dividend to fund
└── Partial return, company still held

PERIODIC INCOME
├── Interest from debt investments
├── Dividends from portfolio companies
└── Usually quarterly

OTHER
├── Broken deal fee recoveries
├── Escrow releases
└── Insurance proceeds
```

---

## 5.5 Recallable vs Non-Recallable

### What is Recallable Capital?

Some distributions can be "recalled" (called back) by the GP for future investments.

### Why Recallable Exists

```
THE RECALLABLE CONCEPT
──────────────────────

SCENARIO WITHOUT RECALLABLE:
├── Fund commits to 100% deployment
├── Early exit returns $20M
├── $20M distributed to LPs
├── GP finds great new deal
└── ❌ No capital available to invest

SCENARIO WITH RECALLABLE:
├── Fund commits to 100% deployment
├── Early exit returns $20M
├── $20M distributed but "recallable"
├── GP finds great new deal
└── ✅ Can recall up to $20M from LPs
```

### Recallable Rules (Typical)

| Rule | Typical Term |
|------|-------------|
| **What's recallable** | Return of capital only (not gains) |
| **Time limit** | Until end of investment period |
| **Amount limit** | Cannot exceed original commitment |
| **Purpose** | New investments only |

### Example Calculation

```
RECALLABLE CALCULATION EXAMPLE
──────────────────────────────

GIVEN:
• Total Commitment: $50M
• Called to Date: $40M
• Distributed: $15M
  - Return of Capital: $10M
  - Realized Gains: $5M

UNFUNDED CALCULATION:

Original Unfunded:        $50M - $40M = $10M

Plus Recallable:         +$10M (return of capital)

Total Unfunded:          $20M

Note: The $5M of gains is NOT recallable
```

### Non-Recallable Distributions

Distributions become non-recallable when:

- Investment period has ended
- Gains exceed original cost
- Time limits have passed
- Fund terms specify non-recallable

---

## 5.6 The Capital Account

### What is a Capital Account?

The capital account is the LP's "balance" with the fund - tracking all activity.

### Capital Account Components

```
CAPITAL ACCOUNT STRUCTURE
─────────────────────────

OPENING BALANCE (Prior period ending balance)
    │
    + CONTRIBUTIONS
    │   ├── Capital calls paid
    │   └── Other contributions
    │
    - DISTRIBUTIONS
    │   ├── Return of capital
    │   ├── Realized gains
    │   └── Income distributions
    │
    + INCOME
    │   ├── Interest income
    │   ├── Dividend income
    │   └── Other income
    │
    - EXPENSES
    │   ├── Management fees
    │   ├── Partnership expenses
    │   └── Other expenses
    │
    +/- GAINS & LOSSES
    │   ├── Realized gains/(losses)
    │   └── Unrealized gains/(losses)
    │
    +/- FX GAINS & LOSSES
    │
    - CARRIED INTEREST
    │   ├── Realized carry
    │   └── Unrealized carry (accrued)
    │
    ▼
CLOSING BALANCE (= NAV, your current value)
```

### Sample Capital Account Statement

```
═══════════════════════════════════════════════════════════════════
                     CAPITAL ACCOUNT STATEMENT
                     ABC Partners Fund VII
                     For Quarter Ended March 31, 2024
═══════════════════════════════════════════════════════════════════

Limited Partner: State Pension Fund
Commitment: $50,000,000
Ownership: 2.50%

───────────────────────────────────────────────────────────────────
                                          Quarter        Inception
                                        To Date          To Date
───────────────────────────────────────────────────────────────────

OPENING BALANCE                        $47,500,000              $0

CONTRIBUTIONS
  Capital Contributions                        $0      $42,000,000
                                       ───────────     ───────────
  Total Contributions                          $0      $42,000,000

DISTRIBUTIONS
  Return of Capital                   ($1,200,000)    ($15,000,000)
  Realized Gains                        ($800,000)     ($8,000,000)
  Income Distributions                  ($150,000)     ($1,200,000)
                                       ───────────     ───────────
  Total Distributions                 ($2,150,000)    ($24,200,000)

INCOME
  Dividend Income                        $125,000        $850,000
  Interest Income                         $35,000        $220,000
  Other Income                            $15,000         $80,000
                                       ───────────     ───────────
  Total Income                           $175,000      $1,150,000

EXPENSES
  Management Fees (Net)                 ($175,000)     ($2,800,000)
  Partnership Expenses                   ($25,000)       ($350,000)
                                       ───────────     ───────────
  Total Expenses                        ($200,000)     ($3,150,000)

REALIZED GAINS/(LOSSES)
  On Investments                       $1,500,000     $12,500,000
  Foreign Exchange                        $25,000        $150,000
                                       ───────────     ───────────
  Total Realized                       $1,525,000     $12,650,000

UNREALIZED GAINS/(LOSSES)
  On Investments                       $1,800,000     $22,000,000
  Foreign Exchange                       ($50,000)       $100,000
                                       ───────────     ───────────
  Total Unrealized                     $1,750,000     $22,100,000

CARRIED INTEREST
  Unrealized Carried Interest           ($600,000)     ($5,550,000)
                                       ───────────     ───────────
  Total Carried Interest                ($600,000)     ($5,550,000)

───────────────────────────────────────────────────────────────────
CLOSING BALANCE (NAV)                  $48,000,000    $48,000,000
═══════════════════════════════════════════════════════════════════

MEMORANDUM DATA
───────────────────────────────────────────────────────────────────
Unfunded Commitment                                    $8,000,000
Recallable Amount                                      $5,000,000
Total Remaining Obligation                            $13,000,000
LP Ownership                                               2.50%
───────────────────────────────────────────────────────────────────
```

### Key Relationships in Capital Account

```
CAPITAL ACCOUNT MATH
────────────────────

NAV = Contributions
    - Distributions
    + Total Income
    - Total Expenses
    + Realized Gains
    + Unrealized Gains
    - Carried Interest

In our example:
$48,000,000 = $42,000,000
            - $24,200,000
            + $1,150,000
            - $3,150,000
            + $12,650,000
            + $22,100,000
            - $5,550,000

CHECK: $48,000,000 = $48,000,000 ✓
```

---

## 5.7 Net Cash Flow Tracking

### LP Cash Position

```
LP CASH FLOW TRACKING
─────────────────────

Year    Calls       Distributions    Net Cash Flow    Cumulative
────    ─────       ─────────────    ─────────────    ──────────
  1    ($10.0M)            $0         ($10.0M)        ($10.0M)
  2    ($12.0M)            $0         ($12.0M)        ($22.0M)
  3     ($8.0M)         $2.0M          ($6.0M)        ($28.0M)
  4     ($6.0M)         $5.0M          ($1.0M)        ($29.0M)
  5     ($4.0M)         $8.0M           $4.0M         ($25.0M)
  6     ($2.0M)        $12.0M          $10.0M         ($15.0M)
  7          $0        $15.0M          $15.0M              $0   ← Breakeven
  8          $0        $10.0M          $10.0M          $10.0M
  9          $0         $6.0M           $6.0M          $16.0M
 10          $0         $4.0M           $4.0M          $20.0M
────    ─────       ─────────────    ─────────────    ──────────
TOTAL  ($42.0M)        $62.0M          $20.0M          $20.0M

Multiple: $62M / $42M = 1.48x
```

---

## 5.8 Subscription Lines (Bridge Facilities)

### What is a Subscription Line?

A credit facility where the fund borrows against LP commitments instead of calling capital.

### How It Works

```
WITHOUT SUBSCRIPTION LINE:
─────────────────────────
Deal identified → Capital call → 10 days → LPs wire funds → Deal closes

WITH SUBSCRIPTION LINE:
───────────────────────
Deal identified → Draw on line → Same day → Deal closes
                                     │
                     Later: Capital call repays line
```

### Why GPs Use Them

| Benefit | Explanation |
|---------|-------------|
| **Speed** | Close deals without waiting for LP wires |
| **Convenience** | Fewer, larger capital calls |
| **IRR Enhancement** | Delays LP cash outflow, boosts IRR |
| **Flexibility** | Bridge timing mismatches |

### LP Concerns

| Concern | Issue |
|---------|-------|
| **IRR Manipulation** | Artificially inflates early IRR |
| **Hidden Leverage** | Fund-level debt not always transparent |
| **Cost** | Interest expense borne by fund (LPs) |
| **Risk** | Market stress could trigger problems |

### IRR Impact Example

```
SUBSCRIPTION LINE IRR IMPACT
────────────────────────────

SCENARIO A: No Subscription Line
─────────────────────────────────
Year 0: Invest $100M (called from LPs)
Year 4: Exit for $200M
IRR: 18.9%

SCENARIO B: With Subscription Line
──────────────────────────────────
Year 0: Invest $100M (from sub line)
Year 1: Call $100M from LPs, repay line
Year 4: Exit for $200M
IRR: 26.0%

SAME MULTIPLE (2.0x), DIFFERENT IRR
The sub line delayed LP cash outflow by 1 year
```

---

## 5.9 Practical Exercises

### Exercise 1: Calculate Unfunded Commitment

```
Given:
• Commitment: $25,000,000
• Total Called: $20,000,000
• Total Distributed: $8,000,000
  - Return of Capital: $6,000,000
  - Gains: $2,000,000
• Investment period: Still active

Calculate: Unfunded Commitment
```

<details>
<summary>Answer</summary>

```
Unfunded = Commitment - Called + Recallable

Recallable = Return of Capital = $6,000,000
(Gains are not recallable)

Unfunded = $25,000,000 - $20,000,000 + $6,000,000
Unfunded = $11,000,000
```
</details>

### Exercise 2: Capital Account Reconciliation

```
Given:
• Opening NAV: $35,000,000
• Capital Called: $0
• Distributions: ($2,500,000)
• Management Fees: ($150,000)
• Realized Gains: $1,200,000
• Unrealized Gains: $800,000
• Carry Accrual: ($200,000)

Calculate: Closing NAV
```

<details>
<summary>Answer</summary>

```
Closing NAV = Opening NAV
            + Calls
            - Distributions
            - Expenses
            + Realized Gains
            + Unrealized Gains
            - Carry

Closing NAV = $35,000,000
            + $0
            - $2,500,000
            - $150,000
            + $1,200,000
            + $800,000
            - $200,000

Closing NAV = $34,150,000
```
</details>

---

## Knowledge Check

1. What's the difference between commitment and contributed capital?
2. What makes a distribution "recallable"?
3. Why might a GP use a subscription line facility?
4. What happens if an LP defaults on a capital call?
5. How is NAV calculated in a capital account?

<details>
<summary>Answers</summary>

1. Commitment is the total promised amount; contributed capital is what's actually been paid when called
2. Typically, return of capital during the investment period is recallable; gains are generally not recallable
3. Speed (close deals faster), convenience (fewer calls), IRR enhancement (delays cash outflow), flexibility
4. Late fees, potential forfeiture of interest, forced sale of their position, possible legal action
5. NAV = Contributions - Distributions + Income - Expenses + Gains - Carried Interest

</details>

---

## Next Module

[Module 06: The J-Curve & Vintage Years →](06-jcurve-vintage.md)

Understand why early fund returns are misleading and how vintage years affect performance comparison.

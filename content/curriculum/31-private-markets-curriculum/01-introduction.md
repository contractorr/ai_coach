# Module 01: Introduction to Private Markets

## Learning Objectives

By the end of this module, you will understand:
- What private markets are and how they differ from public markets
- Why private market investing exists
- The basic premise of pooled investment vehicles
- Key terminology foundation

---

## 1.1 Public vs Private Markets

### Public Markets

When most people think of investing, they think of **public markets**:

| Characteristic | Public Markets |
|---------------|----------------|
| **Where** | Stock exchanges (NYSE, NASDAQ, LSE) |
| **What** | Publicly traded stocks and bonds |
| **Who can invest** | Anyone with a brokerage account |
| **Liquidity** | High - buy/sell anytime markets are open |
| **Price discovery** | Real-time, transparent pricing |
| **Information** | Mandatory public disclosures (10-K, 10-Q) |
| **Minimum investment** | Price of one share (often < $100) |

### Private Markets

**Private markets** are everything else - investments not traded on public exchanges:

| Characteristic | Private Markets |
|---------------|-----------------|
| **Where** | Direct negotiated transactions |
| **What** | Private company equity, private debt, real estate, infrastructure |
| **Who can invest** | Institutional investors, accredited individuals |
| **Liquidity** | Very low - money locked up 10+ years |
| **Price discovery** | Negotiated, infrequent valuations |
| **Information** | Limited, private disclosures |
| **Minimum investment** | Often $1M - $25M+ |

### Why the Distinction Matters

```
PUBLIC COMPANY                      PRIVATE COMPANY
─────────────────                   ─────────────────
Apple Inc.                          SpaceX
• 15 billion shares outstanding     • ~$200B valuation (estimated)
• Trade on NASDAQ                   • No public trading
• Price: ~$180/share (fluctuates)   • Price: Set by funding rounds
• Buy 1 share for $180              • Min investment: $1M+ typically
• Quarterly public earnings         • Information: Private
• Sell anytime                      • Cannot sell easily
```

---

## 1.2 Why Private Markets Exist

### The Illiquidity Premium

Investors accept illiquidity (locked-up capital) in exchange for potentially higher returns:

```comparison-table
{
  "title": "Illiquidity premium",
  "note": "Private assets usually ask investors to trade liquidity for higher expected returns.",
  "columns": [
    { "key": "asset", "label": "Asset Class" },
    { "key": "liquidity", "label": "Liquidity" },
    { "key": "horizon", "label": "Typical Lock-Up" },
    { "key": "return", "label": "Expected Return" }
  ],
  "rows": [
    {
      "asset": "Bonds",
      "liquidity": "High",
      "horizon": "Daily liquidity",
      "return": "4-6%"
    },
    {
      "asset": "Public equities",
      "liquidity": "Medium-high",
      "horizon": "Daily liquidity",
      "return": "~10%"
    },
    {
      "asset": "Private equity",
      "liquidity": "Low",
      "horizon": "10+ years locked up",
      "return": "15-20% target"
    }
  ]
}
```

### Benefits of Private Market Investing

1. **Higher return potential**: Access to growth before companies go public
2. **Active ownership**: Investors can influence company strategy
3. **Diversification**: Returns often uncorrelated with public markets
4. **Longer time horizon**: No quarterly earnings pressure
5. **Access to unique assets**: Infrastructure, real estate, private credit

### Who Invests in Private Markets?

Private markets are dominated by **institutional investors**:

| Investor Type | Examples | Why They Invest |
|--------------|----------|-----------------|
| Pension Funds | CalPERS, Ontario Teachers | Long liabilities match long-term investments |
| Endowments | Yale, Harvard | Perpetual time horizon |
| Sovereign Wealth | GIC (Singapore), ADIA (UAE) | Diversify national wealth |
| Insurance Companies | Prudential, AXA | Match long-term policy obligations |
| Family Offices | Walton, Koch | Wealth preservation, growth |

---

## 1.3 The Pooled Investment Vehicle

Individual investors (even wealthy ones) face challenges investing directly in private companies:

- **Minimum investment sizes**: One company might require $50M+
- **Due diligence**: Evaluating a company takes expertise and resources
- **Portfolio construction**: Need 15-20+ companies for diversification
- **Active management**: Someone must work with portfolio companies

### Solution: The Fund Structure

**Pooled investment vehicles** (funds) solve these problems:

```diagram
{
  "title": "Pooled fund structure",
  "note": "Many LPs combine capital into one vehicle so the GP can build a diversified portfolio.",
  "nodes": [
    {
      "id": "investor-a",
      "title": "Investor A",
      "detail": "$100M commitment from a pension fund.",
      "column": 1,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "investor-b",
      "title": "Investor B",
      "detail": "$50M commitment from an endowment.",
      "column": 2,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "investor-c",
      "title": "Investor C",
      "detail": "$200M commitment from a sovereign investor.",
      "column": 3,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "fund",
      "title": "Private fund",
      "detail": "A pooled vehicle, for example a $2B fund.",
      "column": 2,
      "row": 2,
      "tone": "accent"
    },
    {
      "id": "portfolio",
      "title": "Portfolio companies",
      "detail": "The fund invests across multiple companies rather than one single deal.",
      "column": 2,
      "row": 3,
      "tone": "default"
    }
  ],
  "edges": [
    { "from": "investor-a", "to": "fund", "label": "pool capital" },
    { "from": "investor-b", "to": "fund", "label": "pool capital" },
    { "from": "investor-c", "to": "fund", "label": "pool capital" },
    { "from": "fund", "to": "portfolio", "label": "invest" }
  ]
}
```

### Benefits of Pooling

| Benefit | Explanation |
|---------|-------------|
| **Lower minimums** | $5M commitment instead of $50M per deal |
| **Diversification** | Access to 15-25 companies through one fund |
| **Professional management** | Expert team finds and manages deals |
| **Economies of scale** | Shared legal, admin, reporting costs |

---

## 1.4 Key Terms to Know

Before diving deeper, internalize these foundational terms:

### Fund Participants

| Term | Definition |
|------|------------|
| **Limited Partner (LP)** | Investor who provides capital to the fund |
| **General Partner (GP)** | Fund manager who makes investment decisions |
| **Portfolio Company** | A company the fund invests in |

### Capital Terms

| Term | Definition |
|------|------------|
| **Commitment** | Amount LP promises to invest |
| **Capital Call** | GP request for LP to send money |
| **Distribution** | GP returns money to LP |
| **NAV** | Net Asset Value - current fund value |

### Return Terms

| Term | Definition |
|------|------------|
| **IRR** | Internal Rate of Return - annualized return |
| **Multiple** | Total value relative to invested capital |
| **Gross Return** | Return before fees |
| **Net Return** | Return after fees (what LP keeps) |

---

## 1.5 The Private Markets Ecosystem

```diagram
{
  "title": "Private markets ecosystem",
  "note": "LPs fund GPs, GPs invest in portfolio assets, and service providers support the operating system around the fund.",
  "nodes": [
    {
      "id": "lps",
      "title": "Capital providers (LPs)",
      "detail": "Pension funds, endowments, sovereign wealth, insurance companies, and family offices.",
      "column": 1,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "gps",
      "title": "Fund managers (GPs)",
      "detail": "Managers such as Blackstone, KKR, Carlyle, Apollo, Sequoia, and Andreessen.",
      "column": 2,
      "row": 1,
      "tone": "accent"
    },
    {
      "id": "service",
      "title": "Service providers",
      "detail": "Fund admins, auditors, law firms, placement agents, and consultants.",
      "column": 1,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "portfolio",
      "title": "Portfolio companies",
      "detail": "Private companies, real estate assets, and infrastructure investments.",
      "column": 2,
      "row": 2,
      "tone": "default"
    }
  ],
  "edges": [
    { "from": "lps", "to": "gps", "label": "commit capital" },
    { "from": "gps", "to": "lps", "label": "return capital" },
    { "from": "gps", "to": "portfolio", "label": "invest" },
    { "from": "service", "to": "gps", "label": "support" },
    { "from": "service", "to": "portfolio", "label": "advise" }
  ]
}
```

---

## 1.6 Why This Matters for LP Reporting

As someone working with LP reporting data, you're extracting and organizing:

1. **Capital flows**: Money moving between LPs and funds
2. **Performance data**: How well investments are doing
3. **Portfolio information**: What the fund actually owns
4. **Fee calculations**: How GPs are compensated

Understanding the underlying mechanics helps you:
- Know which fields matter most
- Spot data anomalies
- Understand relationships between metrics
- Build better analytics products

---

## Knowledge Check

1. What is the key trade-off an LP accepts when investing in private markets?
2. Name three types of institutional investors that invest in private markets
3. What problem does a pooled investment vehicle solve?
4. What's the difference between an LP and a GP?

<details>
<summary>Answers</summary>

1. **Illiquidity** - capital locked up for 10+ years in exchange for potentially higher returns
2. Any three: Pension funds, endowments, sovereign wealth funds, insurance companies, family offices
3. Allows investors to access diversified private market exposure with lower minimums, professional management, and shared costs
4. **LP** = Limited Partner, provides capital but no investment control. **GP** = General Partner, manages the fund and makes investment decisions

</details>

---

## Next Module

[Module 02: Fund Structure & Participants →](02-fund-structure.md)

Learn how LPs and GPs interact through the Limited Partnership structure, their rights and obligations, and how decisions are made.

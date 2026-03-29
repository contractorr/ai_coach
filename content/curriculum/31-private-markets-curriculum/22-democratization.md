# Module 22: Democratization & Registered Alternatives

## Learning Objectives

By the end of this module, you will understand:
- Interval funds and their structure
- Business Development Companies (BDCs)
- Tender offer funds and evergreen structures
- European Long-Term Investment Funds (ELTIFs)
- Retail access trends and regulatory considerations

---

## 22.1 The Democratization Trend

### Why Democratization Now?

```framework
{
  "title": "Forces driving retail PE access",
  "pillars": [
    {
      "title": "Demand factors",
      "bullets": [
        "Institutional PE returns have outperformed public markets",
        "Wealth concentration has created more HNW and UHNW demand",
        "Financial advisors want alternative allocations",
        "Low-yield environments push investors toward alternatives",
        "Retirement portfolios need more diversification"
      ]
    },
    {
      "title": "Supply factors",
      "bullets": [
        "GPs want permanent capital",
        "Wirehouses and new distribution channels expanded access",
        "Interval funds and similar products broadened packaging",
        "Regulation evolved around accredited access",
        "Technology reduced minimum-investment friction"
      ]
    },
    {
      "title": "Market size",
      "bullets": [
        "Institutional PE market: about $5-6T",
        "Retail and HNW alternatives allocation: about $1-2T",
        "Potential retail PE opportunity: about $3-5T",
        "Interval funds: $70B+ AUM",
        "Public BDCs: $100B+ AUM"
      ]
    }
  ]
}
```

### Product Spectrum

```comparison-table
{
  "title": "Retail PE access spectrum",
  "note": "Products trade off liquidity, investor eligibility, and closeness to traditional drawdown structures.",
  "columns": [
    { "key": "bucket", "label": "Structure Type" },
    { "key": "liquidity", "label": "Liquidity" },
    { "key": "examples", "label": "Examples" },
    { "key": "access", "label": "Typical Access" }
  ],
  "rows": [
    {
      "bucket": "Drawdown structures",
      "liquidity": "Low",
      "examples": "Traditional PE funds, co-investment vehicles",
      "access": "Accredited investors only"
    },
    {
      "bucket": "Semi-liquid structures",
      "liquidity": "Medium",
      "examples": "Interval funds, tender offer funds, non-traded BDCs, ELTIFs",
      "access": "Accredited or qualified clients"
    },
    {
      "bucket": "Liquid structures",
      "liquidity": "High",
      "examples": "Public BDCs, listed PE vehicles, PE ETFs",
      "access": "All investors"
    }
  ]
}
```

---

## 22.2 Interval Funds

### What Are Interval Funds?

```framework
{
  "title": "Interval fund structure",
  "note": "Interval funds package illiquid assets inside a regulated vehicle with periodic, not daily, liquidity.",
  "pillars": [
    {
      "title": "Legal structure",
      "bullets": [
        "Registered under the Investment Company Act of 1940",
        "Closed-end rather than open-end",
        "SEC-regulated",
        "Can hold illiquid assets",
        "Offers periodic repurchases"
      ]
    },
    {
      "title": "Continuous offering",
      "bullets": [
        "New shares sold daily or monthly at NAV",
        "Unlike fixed-share closed-end funds",
        "AUM can grow over time"
      ]
    },
    {
      "title": "Periodic redemptions and pricing",
      "bullets": [
        "Usually quarterly repurchases",
        "Often 5-25% of NAV is offered for repurchase",
        "Oversubscription is handled pro rata",
        "NAV is calculated daily, weekly, or monthly"
      ]
    }
  ]
}
```

### Interval Fund Mechanics

```comparison-table
{
  "title": "Interval fund repurchase example",
  "note": "Assume a $1B fund with a quarterly repurchase offer equal to 5% of NAV, or $50M.",
  "columns": [
    { "key": "scenario", "label": "Scenario" },
    { "key": "requests", "label": "Requests Received" },
    { "key": "result", "label": "Repurchase Result" }
  ],
  "rows": [
    {
      "scenario": "Undersubscribed",
      "requests": "$30M",
      "result": "All requests are honored and $20M of capacity goes unused."
    },
    {
      "scenario": "Oversubscribed",
      "requests": "$80M",
      "result": "Only 62.5% of each request is filled, so a $100K request receives $62,500."
    }
  ]
}
```

```process-flow
{
  "title": "Repurchase timeline",
  "steps": [
    {
      "title": "Day 1",
      "detail": "Fund announces the repurchase offer."
    },
    {
      "title": "Days 1-21",
      "detail": "Repurchase window stays open for investor requests."
    },
    {
      "title": "Day 21",
      "detail": "Repurchase deadline."
    },
    {
      "title": "Days 21-28",
      "detail": "Fund calculates the repurchase NAV."
    },
    {
      "title": "Day 30",
      "detail": "Cash is paid to redeeming investors."
    }
  ]
}
```

### Interval Fund Considerations

```framework
{
  "title": "Interval fund trade-offs",
  "note": "Interval funds improve access and operational simplicity, but they still behave like semi-liquid alternatives rather than daily-liquid public funds.",
  "pillars": [
    {
      "title": "Why investors like them",
      "bullets": [
        "Lower minimums such as $10-25K.",
        "Some periodic liquidity through quarterly repurchases.",
        "SEC registration and 1099 tax reporting.",
        "Daily or monthly visibility on reported value.",
        "Easy access through brokerage or advisor channels."
      ]
    },
    {
      "title": "Main trade-offs",
      "bullets": [
        "Liquidity is capped and can be prorated in oversubscription.",
        "Managers need cash buffers, which can create cash drag.",
        "Investors have less control over portfolio construction.",
        "Blind-pool risk and NAV volatility still matter."
      ]
    },
    {
      "title": "Cost stack",
      "bullets": [
        "Management fees often run about 1.25-2.0%.",
        "Incentive fees can range from 0-20%.",
        "Distribution costs can add another 0.5-2.5%.",
        "All-in economics can rival or exceed traditional PE once retail distribution is layered in."
      ]
    }
  ]
}
```

<!--
```
INTERVAL FUND PROS AND CONS
───────────────────────────

PROS:
├── Access to PE/alts with lower minimums ($10-25K)
├── Some liquidity (quarterly redemptions)
├── SEC registration (investor protections)
├── Professional management
├── 1099 tax reporting (not K-1s)
├── Daily/monthly pricing visibility
└── Available through brokerage accounts

CONS:
├── Limited liquidity (5-25% quarterly)
├── Pro-rata in oversubscription
├── Higher fees than traditional PE
│   ├── Management fee: 1.25-2.0%
│   ├── Incentive fee: 0-20%
│   └── Distribution costs: 0.5-2.5%
├── Cash drag (need liquidity buffer)
├── Less control over portfolio
├── Blind pool risk
└── Potential NAV volatility

-->

**Fee comparison:**

```comparison-table
{
  "title": "Traditional PE vs interval fund fees",
  "columns": [
    { "key": "fee", "label": "Fee Component" },
    { "key": "traditional", "label": "Traditional PE" },
    { "key": "interval", "label": "Interval Fund" }
  ],
  "rows": [
    {
      "fee": "Management fee",
      "traditional": "2%",
      "interval": "1.5%"
    },
    {
      "fee": "Carry / incentive fee",
      "traditional": "20%",
      "interval": "10-15%"
    },
    {
      "fee": "Distribution costs",
      "traditional": "None",
      "interval": "1-2.5%"
    },
    {
      "fee": "Other expenses",
      "traditional": "0.5%",
      "interval": "0.5%"
    },
    {
      "fee": "Indicative all-in cost",
      "traditional": "~3.5%",
      "interval": "~3-4.5%"
    }
  ]
}
```

---

## 22.3 Business Development Companies (BDCs)

### What Are BDCs?

```framework
{
  "title": "BDC structure",
  "note": "BDCs are retail-accessible, regulated vehicles that provide private-company exposure with explicit leverage and distribution rules.",
  "pillars": [
    {
      "title": "Legal structure",
      "bullets": [
        "Regulated under the Investment Company Act of 1940",
        "RIC pass-through tax treatment",
        "Must distribute 90%+ of income",
        "Can be public or non-traded"
      ]
    },
    {
      "title": "Purpose",
      "bullets": [
        "Provide capital to middle-market companies",
        "Look economically similar to PE or private credit",
        "Give retail investors access to private assets",
        "Require managerial assistance"
      ]
    },
    {
      "title": "Key requirements",
      "bullets": [
        "70%+ in qualifying private US assets",
        "Target companies often below $250M market cap",
        "150% minimum asset coverage",
        "Effectively up to 2:1 debt-to-equity",
        "Distribute 90%+ of taxable income"
      ]
    }
  ]
}
```

### Public vs Non-Traded BDCs

```comparison-table
{
  "title": "Public vs non-traded BDCs",
  "note": "The key trade-off is public-market liquidity and price volatility versus NAV-based pricing and more limited liquidity windows.",
  "columns": [
    { "key": "attribute", "label": "Attribute" },
    { "key": "public", "label": "Public BDC" },
    { "key": "non_traded", "label": "Non-Traded BDC" }
  ],
  "rows": [
    {
      "attribute": "Listing and access",
      "public": "Listed on NYSE or NASDAQ and accessible through a brokerage account.",
      "non_traded": "Not exchange-listed and commonly sold through broker-dealers."
    },
    {
      "attribute": "Liquidity",
      "public": "Daily market liquidity.",
      "non_traded": "Tender-based or limited periodic liquidity, often quarterly."
    },
    {
      "attribute": "Pricing",
      "public": "Market price can trade at a discount or premium to NAV.",
      "non_traded": "NAV-based pricing without public-market discount or premium."
    },
    {
      "attribute": "Volatility",
      "public": "More visible day-to-day volatility.",
      "non_traded": "Lower quoted volatility because pricing is appraised."
    },
    {
      "attribute": "Minimum investment",
      "public": "As low as one share.",
      "non_traded": "$2,500-25,000 is typical."
    },
    {
      "attribute": "Fees",
      "public": "No sales load, but management and incentive fees still apply.",
      "non_traded": "Can include upfront selling costs on top of management and incentive fees."
    }
  ]
}
```

<!--
```
BDC TYPES COMPARISON
────────────────────

PUBLIC (TRADED) BDCs:
├── Listed on NYSE/NASDAQ
├── Daily liquidity
├── Real-time market pricing
├── Price may differ from NAV (discount/premium)
├── Accessible via brokerage account
├── Examples: ARCC, MAIN, PSEC, ORCC

NON-TRADED BDCs:
├── Not listed on exchange
├── Limited liquidity (tender offers, typically quarterly)
├── NAV pricing (no market discount/premium)
├── Higher fees (upfront sales charges)
├── Sold through broker-dealers
├── May eventually list or merge

COMPARISON:
┌─────────────────────────────────────────────────────────────────┐
│                     Public BDC      Non-Traded BDC              │
│                     ──────────      ──────────────              │
│ Liquidity           Daily           Quarterly tender            │
│ Pricing             Market          NAV                         │
│ Volatility          Higher          Lower (NAV-based)           │
│ Discount risk       Yes             No                          │
│ Min investment      1 share (~$15)  $2,500-25,000              │
│ Sales load          None            0-3%                        │
│ Management fee      1.5-2%          1.5-2%                      │
│ Incentive fee       15-20%          15-20%                      │
└─────────────────────────────────────────────────────────────────┘
```

-->

### BDC Investment Profile

```framework
{
  "title": "BDC investment profile",
  "note": "BDCs are usually income-oriented vehicles with middle-market credit exposure and manager-dependent downside protection.",
  "pillars": [
    {
      "title": "Typical portfolio mix",
      "bullets": [
        "First-lien senior secured loans often represent 60-70% of assets.",
        "Second-lien loans are commonly 10-20%.",
        "Mezzanine debt may be 5-15%.",
        "Equity co-investments may add another 5-15%.",
        "Underlying borrowers are usually middle-market companies."
      ]
    },
    {
      "title": "Return profile",
      "bullets": [
        "Dividend yields often run about 8-12%.",
        "NAV growth is usually modest at 0-5% annually.",
        "Total return targets often land in the 10-15% range.",
        "The structure behaves more like an income vehicle than PE equity."
      ]
    },
    {
      "title": "Main risks",
      "bullets": [
        "Credit losses in the underlying portfolio.",
        "Interest-rate and economic-cycle sensitivity.",
        "Leverage risk under the 2:1 maximum framework.",
        "Manager selection risk.",
        "For public BDCs, discount-to-NAV risk."
      ]
    }
  ]
}
```

<!--
```
BDC INVESTMENT CHARACTERISTICS
──────────────────────────────

TYPICAL PORTFOLIO:
├── First lien senior secured loans: 60-70%
├── Second lien loans: 10-20%
├── Mezzanine debt: 5-15%
├── Equity co-investments: 5-15%
└── Focus: Middle-market companies ($10-250M EBITDA)

RETURN PROFILE:
├── Current yield focus: 8-12% dividend yield typical
├── NAV growth: Modest (0-5% annually)
├── Total return target: 10-15%
├── Income-oriented (like REIT)
└── Less capital appreciation than PE equity

RISK FACTORS:
├── Credit risk (defaults in portfolio)
├── Interest rate sensitivity
├── Leverage risk (2:1 max)
├── Economic cycle sensitivity
├── Manager selection risk
└── For public: Market discount risk

HISTORICAL RETURNS (Public BDCs):
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│ 10-Year Average Total Return: ~8-10%                           │
│ Dividend Yield (current): ~10-12%                              │
│                                                                 │
│ Note: Returns vary widely by manager                           │
│       Top performers: 12-15% total return                      │
│       Poor performers: 0-5% (or negative)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

-->

## 22.4 Tender Offer Funds

### What Are Tender Offer Funds?

```framework
{
  "title": "Tender offer fund structure",
  "note": "Tender offer funds look similar to interval funds from the outside, but managers have more discretion over when and how much liquidity they provide.",
  "pillars": [
    {
      "title": "Legal setup",
      "bullets": [
        "Often registered under the 1940 Act, though private variants also exist.",
        "Closed-end structure with periodic tenders instead of continuous redemption."
      ]
    },
    {
      "title": "Difference from interval funds",
      "bullets": [
        "Interval funds must follow a periodic repurchase policy.",
        "Tender offer funds may offer tenders at board discretion.",
        "Boards can reduce, skip, or suspend tenders more flexibly."
      ]
    },
    {
      "title": "Typical operating terms",
      "bullets": [
        "Quarterly tenders are common but not guaranteed.",
        "Offer sizes around 5% of NAV are common.",
        "Oversubscription is usually handled pro rata.",
        "Many are structured as Delaware statutory trusts."
      ]
    }
  ]
}
```

<!--
```
TENDER OFFER FUND STRUCTURE
───────────────────────────

LEGAL STRUCTURE:
├── Registered under 1940 Act (like interval funds)
├── OR private fund with tender feature
├── Closed-end structure
├── Periodic redemptions via tender offers
└── Not continuous like interval funds

KEY DIFFERENCE FROM INTERVAL FUNDS:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│ INTERVAL FUND:                                                  │
│ ├── MUST offer periodic repurchases (5-25%)                    │
│ ├── Repurchase schedule in policy                              │
│ └── Board can suspend only in emergencies                      │
│                                                                 │
│ TENDER OFFER FUND:                                              │
│ ├── MAY offer periodic tenders (discretionary)                 │
│ ├── Board decides when and how much                            │
│ ├── Can skip tenders if illiquid                               │
│ └── More flexibility for manager                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

COMMON STRUCTURE:
├── Quarterly tender offers (typical but not required)
├── 5% of NAV offered (typical)
├── Pro-rata if oversubscribed
├── Board can modify or suspend
└── Often structured as Delaware statutory trust
```

-->

### Evergreen Structures

```comparison-table
{
  "title": "Traditional PE vs evergreen structures",
  "note": "Evergreen vehicles trade the simplicity of a fixed fund life for continuous capital management and more ongoing liquidity planning.",
  "columns": [
    { "key": "aspect", "label": "Aspect" },
    { "key": "traditional", "label": "Traditional PE" },
    { "key": "evergreen", "label": "Evergreen / Perpetual" }
  ],
  "rows": [
    {
      "aspect": "Fund life",
      "traditional": "Fixed 10-12 year life.",
      "evergreen": "No fixed termination."
    },
    {
      "aspect": "Capital cycle",
      "traditional": "Commit, invest, harvest, and distribute back to LPs.",
      "evergreen": "Continuous operations with potential reinvestment."
    },
    {
      "aspect": "Investor experience",
      "traditional": "LPs must recommit to maintain exposure.",
      "evergreen": "Exposure can continue without re-underwriting a new fund."
    },
    {
      "aspect": "Benefits",
      "traditional": "Clear vintage boundaries and defined exit timing.",
      "evergreen": "Less pacing friction, automatic continuity, and potential compounding."
    },
    {
      "aspect": "Challenges",
      "traditional": "J-curve and reinvestment burden.",
      "evergreen": "Valuation complexity, liquidity management, fee debates, and vintage-mix questions."
    }
  ]
}
```

<!--
```
EVERGREEN FUND CONCEPT
──────────────────────

TRADITIONAL PE:
├── Fixed 10-12 year life
├── Commit-invest-harvest cycle
├── Distributions returned to LP
├── LP must re-commit to maintain exposure

EVERGREEN/PERPETUAL:
├── No fixed termination
├── Continuous operations
├── Distributions can be reinvested
├── Exposure maintained automatically

BENEFITS FOR INVESTORS:
├── No pacing/re-commitment hassle
├── Continuous exposure to PE
├── Compounding without re-underwriting
├── Simplified portfolio management
└── No J-curve (fund always mature)

BENEFITS FOR MANAGERS:
├── Permanent capital base
├── More predictable AUM
├── No fundraising cycles
├── Long-term investment horizon
└── Aligned with patient capital

CHALLENGES:
├── Valuation complexity
├── Liquidity management
├── Fee structure debates
├── Vintage diversification question
└── Exit timing pressure reduced
```

---

-->

## 22.5 European Long-Term Investment Funds (ELTIFs)

### What Are ELTIFs?

```framework
{
  "title": "ELTIF structure",
  "note": "ELTIFs are the EU's regulated wrapper for long-term private-market assets with a retail distribution path.",
  "pillars": [
    {
      "title": "Regulatory framework",
      "bullets": [
        "EU regime introduced in 2015 and expanded through ELTIF 2.0.",
        "Pan-European passport enables cross-border distribution.",
        "Can be sold to retail investors with suitability controls."
      ]
    },
    {
      "title": "Eligible investments",
      "bullets": [
        "Private equity and unlisted companies.",
        "Infrastructure and real estate.",
        "Debt instruments and SME loans.",
        "Assets must support a long-term investment profile."
      ]
    },
    {
      "title": "Key ELTIF 2.0 features",
      "bullets": [
        "Retail minimum investment threshold was removed.",
        "55% of assets must be in eligible long-term holdings, down from 70%.",
        "Redemption and secondary-trade mechanisms are more flexible.",
        "Retail leverage can reach 50% of NAV, while professional-only structures can go higher."
      ]
    }
  ]
}
```

<!--
```
ELTIF STRUCTURE
───────────────

REGULATORY FRAMEWORK:
├── EU regulation (2015, updated 2023)
├── Pan-European passport (sold across EU)
├── Can be sold to retail investors
├── Designed for long-term investment
└── Must invest in "eligible assets"

ELIGIBLE INVESTMENTS:
├── Private equity (unlisted companies)
├── Infrastructure
├── Real estate
├── Debt instruments
├── SME loans
└── Long-term nature required

KEY FEATURES (ELTIF 2.0 - 2024):
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│ RETAIL ACCESS:                                                  │
│ ├── Minimum investment: Removed (was €10K)                     │
│ ├── Suitability assessment required                            │
│ └── 10% portfolio limit (can be waived)                        │
│                                                                 │
│ INVESTMENT RULES:                                               │
│ ├── 55% in eligible long-term assets (was 70%)                │
│ ├── More flexibility in portfolio construction                 │
│ └── Master-feeder structures allowed                           │
│                                                                 │
│ LIQUIDITY:                                                      │
│ ├── Can offer redemptions (with notice/gates)                  │
│ ├── Matching mechanism for secondary trades                    │
│ └── More flexibility than ELTIF 1.0                            │
│                                                                 │
│ LEVERAGE:                                                       │
│ ├── 50% of NAV for retail ELTIFs                               │
│ └── 100% for professional-only                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

-->

### ELTIF 2.0 Changes

```comparison-table
{
  "title": "ELTIF 1.0 vs ELTIF 2.0",
  "note": "ELTIF 2.0 widened the retail-access channel and gave product sponsors much more flexibility, which is why adoption expectations stepped up.",
  "columns": [
    { "key": "area", "label": "Area" },
    { "key": "eltif1", "label": "ELTIF 1.0" },
    { "key": "eltif2", "label": "ELTIF 2.0" }
  ],
  "rows": [
    {
      "area": "Minimum investment",
      "eltif1": "Retail minimum of about EUR10K.",
      "eltif2": "Minimum removed."
    },
    {
      "area": "Redemptions",
      "eltif1": "Strict and less flexible.",
      "eltif2": "More flexible redemption framework."
    },
    {
      "area": "Leverage",
      "eltif1": "Roughly 30% cap.",
      "eltif2": "Up to 50% for retail and 100% for professional-only structures."
    },
    {
      "area": "Eligible assets",
      "eltif1": "Narrower long-term asset set.",
      "eltif2": "Broader asset eligibility and master-feeder flexibility."
    },
    {
      "area": "Market effect",
      "eltif1": "Adoption stayed limited.",
      "eltif2": "Industry expects materially higher growth from a roughly EUR13B starting base."
    }
  ]
}
```

<!--
```
ELTIF EVOLUTION
───────────────

ELTIF 1.0 (2015) LIMITATIONS:
├── High minimum investment (€10K)
├── Strict redemption rules
├── Limited leverage (30%)
├── Narrow eligible assets
├── Complex retail distribution
└── Result: Limited adoption (~€2.4B by 2020)

ELTIF 2.0 (2024) IMPROVEMENTS:
├── No minimum investment
├── Flexible redemption framework
├── Higher leverage (50%/100%)
├── Broader eligible assets
├── Simplified distribution
└── Expected: Significant growth

MARKET EXPECTATIONS:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│ Current ELTIF AUM (2024): ~€13 billion                         │
│                                                                 │
│ Projections for 2030:                                           │
│ ├── Conservative: €50-100 billion                              │
│ ├── Moderate: €100-200 billion                                 │
│ └── Optimistic: €200-400 billion                               │
│                                                                 │
│ KEY DRIVERS:                                                    │
│ ├── Pension/retirement system integration                      │
│ ├── Wealth management adoption                                 │
│ ├── Major GP launches (Blackstone, KKR, etc.)                 │
│ └── EU policy support (CMU)                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

-->

## 22.6 Retail Access Trends

### Distribution Channels

```comparison-table
{
  "title": "Retail private-markets distribution channels",
  "note": "Distribution is broadening from traditional broker channels into advisor platforms, digital marketplaces, and retirement wrappers.",
  "columns": [
    { "key": "channel", "label": "Channel" },
    { "key": "who", "label": "Typical Investor Base" },
    { "key": "role", "label": "How It Works" },
    { "key": "minimum", "label": "Typical Minimum" }
  ],
  "rows": [
    {
      "channel": "Wirehouses and full-service broker-dealers",
      "who": "High-net-worth clients",
      "role": "Largest distribution channel with due-diligence platforms and curated product shelves.",
      "minimum": "$50K-250K"
    },
    {
      "channel": "Registered investment advisors",
      "who": "Advised wealth clients",
      "role": "Access often runs through iCapital, CAIS, or similar platforms.",
      "minimum": "$25K-100K"
    },
    {
      "channel": "Family offices",
      "who": "Ultra-high-net-worth capital",
      "role": "Can use direct GP relationships and customized structures.",
      "minimum": "Varies widely"
    },
    {
      "channel": "Digital platforms",
      "who": "Self-directed or digitally served investors",
      "role": "Technology lowers friction and can widen access.",
      "minimum": "Often below traditional private-fund thresholds"
    },
    {
      "channel": "Defined contribution plans",
      "who": "Retirement savers",
      "role": "Emerging channel through target-date or diversified wrappers.",
      "minimum": "Embedded in plan design"
    }
  ]
}
```

<!--
```
RETAIL PE DISTRIBUTION CHANNELS
───────────────────────────────

1. WIREHOUSES / FULL-SERVICE BROKER-DEALERS
   ├── Morgan Stanley, Merrill, UBS, Wells Fargo
   ├── Largest distribution channel
   ├── High-net-worth clients
   ├── Due diligence platforms
   └── Minimum: $50K-250K typically

2. REGISTERED INVESTMENT ADVISORS (RIAs)
   ├── Independent advisors
   ├── Growing channel
   ├── Platform access (iCapital, CAIS)
   └── Minimum: $25K-100K typically

3. FAMILY OFFICES
   ├── Direct relationships with GPs
   ├── Can access institutional funds
   ├── Custom structures
   └── Minimum: Varies widely

4. DIGITAL PLATFORMS
   ├── iCapital, CAIS, Moonfare
   ├── Technology-enabled access
   ├── Lower minimums possible
   └── Growing rapidly

5. DEFINED CONTRIBUTION (401k)
   ├── Emerging channel
   ├── Regulatory evolution
   ├── Target date fund integration
   └── Future growth area
```

-->

### Technology Platforms

```comparison-table
{
  "title": "Alternative-access platforms",
  "note": "Platforms package sourcing, onboarding, reporting, and compliance so private-market products can be distributed more like wealth products.",
  "columns": [
    { "key": "platform", "label": "Platform" },
    { "key": "focus", "label": "Focus" },
    { "key": "clients", "label": "Primary Clients" },
    { "key": "minimum", "label": "Typical Entry Point" },
    { "key": "notes", "label": "Notes" }
  ],
  "rows": [
    {
      "platform": "iCapital",
      "focus": "Broad alternatives marketplace across PE, private credit, and hedge funds.",
      "clients": "Wirehouses, RIAs, and banks.",
      "minimum": "$25K-100K",
      "notes": "Large platform footprint with subscription, reporting, and education tooling."
    },
    {
      "platform": "CAIS",
      "focus": "Marketplace and diligence workflow for alternatives.",
      "clients": "RIAs and broker-dealers.",
      "minimum": "$25K+",
      "notes": "Strong advisor workflow and trading orientation."
    },
    {
      "platform": "Moonfare",
      "focus": "European private-equity access.",
      "clients": "High-net-worth individuals.",
      "minimum": "EUR50K",
      "notes": "Known for direct GP relationships and Europe-heavy distribution."
    },
    {
      "platform": "Yieldstreet",
      "focus": "Retail-facing access to a broader set of alternative assets.",
      "clients": "Individual investors.",
      "minimum": "$10K+",
      "notes": "Retail-oriented positioning across multiple alternative categories."
    }
  ]
}
```

```framework
{
  "title": "What the platforms actually do",
  "pillars": [
    {
      "title": "Sourcing and diligence",
      "bullets": [
        "Fund and product sourcing",
        "Manager due diligence",
        "Product shelf curation"
      ]
    },
    {
      "title": "Execution",
      "bullets": [
        "Digital subscription workflows",
        "Capital call and distribution processing",
        "Compliance and suitability checks"
      ]
    },
    {
      "title": "Operations and reporting",
      "bullets": [
        "Consolidated reporting",
        "Tax document aggregation",
        "Education and advisor enablement"
      ]
    }
  ]
}
```

<!--
```
ALTS ACCESS PLATFORMS
─────────────────────

iCAPITAL:
├── Founded: 2013
├── AUM: $180B+ platform assets
├── Products: PE, private credit, hedge funds
├── Clients: Wirehouses, RIAs, banks
├── Minimum: $25K-100K
├── Features: Subscription, reporting, education
└── Notable: Acquired by ICONIQ (2024)

CAIS:
├── Founded: 2009
├── AUM: $140B+ platform assets
├── Products: Alts marketplace
├── Clients: RIAs, broker-dealers
├── Minimum: $25K+
├── Features: Due diligence, trading
└── Notable: Strong RIA focus

MOONFARE (Europe):
├── Founded: 2016
├── AUM: €3B+ platform assets
├── Products: Top-tier PE access
├── Clients: HNW individuals
├── Minimum: €50K
├── Features: Direct GP relationships
└── Notable: European focus

YIELDSTREET:
├── Founded: 2015
├── Products: Alts for individuals
├── Minimum: $10K+
├── Features: Art, marine, legal, RE
└── Notable: Retail-focused

PLATFORM FUNCTIONS:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│ □ Fund/product sourcing and due diligence                      │
│ □ Digital subscription documents                               │
│ □ Capital call/distribution processing                         │
│ □ Consolidated reporting                                       │
│ □ Tax document aggregation                                     │
│ □ Education and training                                       │
│ □ Compliance/suitability tools                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

-->

### Regulatory Developments

```framework
{
  "title": "Regulatory evolution shaping retail access",
  "note": "The direction of travel is broader access, but still through suitability, disclosure, and liquidity-control frameworks.",
  "pillars": [
    {
      "title": "US developments",
      "bullets": [
        "The accredited-investor definition widened to include some professional credentials and knowledgeable employees.",
        "Defined-contribution access gained a pathway through diversified retirement structures.",
        "Semi-liquid wrappers such as interval funds and tender offer funds gained acceptance."
      ]
    },
    {
      "title": "European developments",
      "bullets": [
        "ELTIF 2.0 materially liberalized the retail wrapper.",
        "MiFID II and PRIIPs reinforced disclosure, suitability, and cost transparency.",
        "Cross-border product distribution became easier within a clearer framework."
      ]
    },
    {
      "title": "What may come next",
      "bullets": [
        "Further expansion of access definitions.",
        "More retirement-plan integration.",
        "More ESG or impact-oriented retail products.",
        "Greater global harmonization of wrapper design."
      ]
    }
  ]
}
```

<!--
```
REGULATORY EVOLUTION
────────────────────

US DEVELOPMENTS:

1. ACCREDITED INVESTOR DEFINITION (2020)
   ├── Added professional certifications
   ├── Knowledgeable employees of funds
   ├── Spousal wealth combination
   └── Still primarily wealth-based

2. DC PLAN ACCESS (2020 DOL Letter)
   ├── PE in target date funds permitted
   ├── Subject to fiduciary prudence
   ├── Limited adoption so far
   └── Growing interest

3. SEMI-LIQUID PRODUCT GROWTH
   ├── SEC comfort with interval funds
   ├── Tender offer fund acceptance
   ├── Non-traded BDC/REIT evolution
   └── Liquidity gating frameworks

EUROPEAN DEVELOPMENTS:

1. ELTIF 2.0 (2024)
   ├── Major liberalization
   ├── Retail access facilitated
   ├── Redemption flexibility
   └── Expected significant growth

2. MiFID II / PRIIPs
   ├── Disclosure requirements
   ├── Cost transparency
   ├── Suitability rules
   └── Cross-border distribution

FUTURE TRENDS:
├── Further accredited definition expansion
├── DC plan PE integration
├── Digital asset integration
├── ESG/impact retail products
└── Global product harmonization
```

---

-->

## 22.7 Considerations for Retail Investors

### Due Diligence Framework

```process-flow
{
  "title": "Retail due-diligence sequence",
  "note": "A simple review order helps retail investors avoid treating product wrappers as substitutes for real underwriting.",
  "steps": [
    {
      "id": "structure",
      "title": "Understand the structure",
      "detail": "Identify the vehicle type, redemption mechanics, and whether the wrapper is registered or private."
    },
    {
      "id": "fees",
      "title": "Evaluate fees",
      "detail": "Review management, performance, sales, and distribution fees on an all-in basis."
    },
    {
      "id": "manager",
      "title": "Assess the manager",
      "detail": "Look at strategy track record, team stability, process quality, and alignment."
    },
    {
      "id": "risks",
      "title": "Map the real risks",
      "detail": "Focus on illiquidity, valuation uncertainty, leverage, concentration, and correlation."
    },
    {
      "id": "portfolio",
      "title": "Check portfolio fit",
      "detail": "Confirm sizing, liquidity needs, time horizon, and diversification benefit."
    }
  ]
}
```

<!--
```
RETAIL PE DUE DILIGENCE
───────────────────────

1. UNDERSTAND THE STRUCTURE
   □ What type of vehicle? (Interval, BDC, etc.)
   □ What liquidity provisions?
   □ What are redemption limitations?
   □ Is it registered or private?

2. EVALUATE FEES
   □ Management fee (annual)
   □ Incentive/performance fee
   □ Sales load (upfront)
   □ Distribution fees (ongoing)
   □ Compare to alternatives

3. ASSESS THE MANAGER
   □ Track record in strategy
   □ Team experience and stability
   □ Institutional-quality processes
   □ Alignment of interests

4. UNDERSTAND RISKS
   □ Illiquidity
   □ Valuation uncertainty
   □ Leverage
   □ Concentration
   □ Market correlation

5. FIT IN PORTFOLIO
   □ What % of portfolio?
   □ Liquidity needs met?
   □ Time horizon appropriate?
   □ Diversification benefit?
```

-->

### Common Mistakes

```framework
{
  "title": "Retail mistakes to avoid",
  "note": "Most mistakes come from treating semi-liquid alternative wrappers as if they were simple public-market products.",
  "pillars": [
    {
      "title": "Overestimating liquidity",
      "bullets": [
        "Quarterly redemption does not mean truly liquid.",
        "Gates, suspensions, and proration can still apply."
      ]
    },
    {
      "title": "Ignoring total fees",
      "bullets": [
        "Management fee is only part of the cost stack.",
        "Sales and distribution fees can materially reduce net returns."
      ]
    },
    {
      "title": "Chasing yield",
      "bullets": [
        "High stated yield can reflect higher credit or structure risk.",
        "Look through to asset quality and the source of distributions."
      ]
    },
    {
      "title": "Underestimating complexity",
      "bullets": [
        "Tax forms, capital logistics, and estate-planning issues can matter.",
        "Operational friction is still part of the product."
      ]
    },
    {
      "title": "Using the wrong time horizon",
      "bullets": [
        "Private-market exposure still needs multi-year patience.",
        "Emergency-fund or short-term capital should stay out."
      ]
    },
    {
      "title": "Taking too much concentration",
      "bullets": [
        "Alternatives should usually be a measured sleeve, not the whole portfolio.",
        "Diversify within the alternative allocation as well."
      ]
    }
  ]
}
```

<!--
```
RETAIL PE MISTAKES TO AVOID
───────────────────────────

1. OVERESTIMATING LIQUIDITY
   ├── Quarterly redemptions ≠ liquid
   ├── Gates and suspensions possible
   ├── Pro-rata in oversubscription
   └── Plan for full illiquidity

2. IGNORING TOTAL FEES
   ├── Look beyond management fee
   ├── Sales loads matter
   ├── Distribution fees add up
   └── Compare net returns

3. CHASING YIELD
   ├── High yield may = high risk
   ├── BDC yields can be misleading
   ├── ROC vs true income
   └── Credit quality matters

4. UNDERESTIMATING COMPLEXITY
   ├── K-1 tax complexity (some structures)
   ├── Capital call logistics
   ├── UBTI considerations
   └── Estate planning issues

5. WRONG TIME HORIZON
   ├── PE is 7-10+ year commitment
   ├── Even "liquid" structures have constraints
   ├── Don't invest emergency funds
   └── Match investment to goals

6. CONCENTRATION RISK
   ├── Don't over-allocate to alts
   ├── 5-15% reasonable for most
   ├── Diversify within alts
   └── Consider total portfolio
```

---

-->

## 22.8 Summary

### Product Comparison

| Vehicle | Liquidity | Min Invest | Tax Form | Retail Access |
|---------|-----------|------------|----------|---------------|
| Traditional PE | None | $250K+ | K-1 | Accredited only |
| Interval Fund | Quarterly | $10-25K | 1099 | Generally open |
| Public BDC | Daily | $15 (1 share) | 1099 | All investors |
| Non-Traded BDC | Quarterly | $2.5-25K | 1099 | Generally open |
| Tender Offer Fund | Quarterly | $25-100K | 1099/K-1 | Varies |
| ELTIF | Varies | None | Varies | EU retail |

### Key Takeaways

```process-flow
{
  "title": "Democratization summary",
  "note": "Retail access is expanding, but wrapper convenience does not eliminate the core private-markets trade-offs.",
  "steps": [
    {
      "id": "momentum",
      "title": "The trend has real momentum",
      "detail": "GP interest, LP demand, and regulatory support are all pushing access wider."
    },
    {
      "id": "wrappers",
      "title": "There are now multiple wrapper choices",
      "detail": "Interval funds, BDCs, tender offer funds, and ELTIFs each solve access differently."
    },
    {
      "id": "liquidity",
      "title": "Liquidity is still limited",
      "detail": "Semi-liquid wrappers improve access but do not make private assets truly liquid."
    },
    {
      "id": "fees",
      "title": "Fees can stay high",
      "detail": "Distribution, administration, and wrapper design often keep retail cost stacks above institutional ones."
    },
    {
      "id": "discipline",
      "title": "Sizing and due diligence still matter",
      "detail": "Manager quality, product fit, and measured allocation sizing remain the core investor safeguards."
    }
  ]
}
```

<!--
```
DEMOCRATIZATION SUMMARY
───────────────────────

1. GROWING TREND WITH REAL MOMENTUM
   └── GP interest + LP demand + regulatory support

2. MULTIPLE STRUCTURE OPTIONS
   └── Interval funds, BDCs, tender offers, ELTIFs

3. LIQUIDITY IS LIMITED, NOT ELIMINATED
   └── "Semi-liquid" still means mostly illiquid

4. FEES OFTEN HIGHER THAN INSTITUTIONAL
   └── Distribution costs, smaller scale

5. DUE DILIGENCE STILL CRITICAL
   └── Manager selection matters as much as structure

6. APPROPRIATE SIZING IS KEY
   └── 5-15% of portfolio for most retail investors

7. TECHNOLOGY ENABLING ACCESS
   └── Platforms reducing friction and minimums
```

---

-->

## Knowledge Check

1. What is the key difference between interval funds and tender offer funds?
2. What are the main regulatory requirements for BDCs?
3. What changes did ELTIF 2.0 bring to improve retail access?
4. What are the main distribution channels for retail PE products?
5. What mistakes should retail investors avoid with PE products?

<details>
<summary>Answers</summary>

1. Interval funds MUST offer periodic repurchases (5-25% quarterly) as required by their policy. Tender offer funds MAY offer periodic tenders at the board's discretion - they can skip or modify tenders if conditions warrant. This gives tender offer funds more flexibility but less predictable liquidity.

2. BDCs must: (1) invest 70%+ in qualifying assets (private US companies), (2) maintain 150% asset coverage ratio (max 2:1 leverage), (3) distribute 90%+ of investment company taxable income to qualify for pass-through tax treatment, (4) provide managerial assistance to portfolio companies.

3. ELTIF 2.0 removed the €10K minimum investment, increased leverage limits (50% for retail, 100% for professional), broadened eligible assets, allowed more flexible redemption frameworks, and enabled master-feeder structures - all making ELTIFs more accessible and attractive.

4. Main channels: (1) Wirehouses/full-service broker-dealers (Morgan Stanley, Merrill, etc.), (2) RIAs through platforms like iCapital and CAIS, (3) Family offices with direct GP relationships, (4) Digital platforms (Moonfare, Yieldstreet), (5) Emerging: defined contribution plans.

5. Common mistakes: (1) Overestimating liquidity, (2) Ignoring total fees (especially distribution costs), (3) Chasing high yields without understanding risk, (4) Underestimating complexity (tax, admin), (5) Mismatched time horizon, (6) Over-concentrating in alternatives.

</details>

---

## Exercise: Product Selection

```
SCENARIO: Advising a retail client

Client Profile:
├── Age: 55, retiring in 10 years
├── Net worth: $3 million
├── Liquid portfolio: $1.5 million
├── Annual income: $250,000
├── Risk tolerance: Moderate
├── Goal: Diversification, some income
├── Current allocation: 60% stocks, 40% bonds

Questions:
1. What % allocation to PE/alts would you recommend?
2. Which product type(s) would be most appropriate?
3. What specific due diligence would you conduct?
4. What risks would you highlight for the client?
```

<details>
<summary>Answers</summary>

```
1. RECOMMENDED ALLOCATION:
   ├── 10-15% of portfolio to alternatives
   ├── $150K-225K of $1.5M portfolio
   ├── Rationale:
   │   ├── Moderate risk tolerance
   │   ├── 10-year horizon before retirement
   │   ├── Sufficient liquidity for needs
   │   └── Not emergency/near-term funds

2. APPROPRIATE PRODUCTS:
   ├── PRIMARY: Public BDCs or interval funds
   │   ├── Some liquidity (important at 55)
   │   ├── Income component (mentioned as goal)
   │   ├── Lower minimums, accessible
   │   └── 1099 tax reporting (simpler)
   │
   ├── CONSIDER: Diversified interval fund
   │   ├── Multi-strategy exposure
   │   ├── Professional manager selection
   │   └── Quarterly liquidity
   │
   ├── AVOID: Traditional drawdown PE
   │   ├── 10+ year lockup too long
   │   ├── K-1 complexity unnecessary
   │   └── Higher minimums

3. DUE DILIGENCE:
   ├── Manager track record (5+ years)
   ├── Fee comparison (total cost)
   ├── Redemption history (gates triggered?)
   ├── Portfolio composition
   ├── Leverage levels
   └── Distribution stability

4. RISKS TO HIGHLIGHT:
   ├── Liquidity is LIMITED
   │   └── Can't access quickly if needed
   ├── Valuation is quarterly
   │   └── Not daily like stocks
   ├── Pro-rata redemption risk
   │   └── May not get full redemption
   ├── Manager risk
   │   └── Performance varies widely
   ├── Interest rate sensitivity (BDCs)
   │   └── Rising rates may impact returns
   └── Pre-retirement timing
       └── 10 years is minimum appropriate horizon
```

</details>

---

[← Module 21: GP/LP Negotiations](21-gp-lp-negotiations.md)

[← Back to Curriculum Overview](00-curriculum-overview.md)

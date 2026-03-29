# Insurance Industry Crash Course
*Business Models & Technology Focus*

---

## 1. Insurance Fundamentals

### Core Concept: Risk Pooling & Transfer
Insurance = mechanism where many pay small amounts so few who experience losses get compensated. Insurer aggregates risk across pool, uses law of large numbers to predict losses.

**The deal:** Policyholder pays premium → Insurer promises to pay claims → Risk transfers from individual to pool

### Types Overview

| Type | What it covers | Key characteristics |
|------|---------------|---------------------|
| **Life** | Death, retirement | Long-tail, investment-heavy, predictable mortality |
| **Health** | Medical expenses | High frequency, regulatory complexity, network-dependent |
| **P&C (Property & Casualty)** | Property damage, liability | Short-tail (mostly), catastrophe exposure, reinsurance-heavy |

P&C subcategories: auto, home, commercial, specialty/excess & surplus (E&S)

---

## 2. Value Chain & Key Players

### Carriers/Insurers
- Take on risk, hold capital, pay claims
- Regulated entities with capital/solvency requirements
- Examples: State Farm, Allstate, Travelers, Chubb, AIG

### Reinsurers
"Insurance for insurance companies"
- Carriers cede portions of risk to reinsurers
- Enables capacity (write more policies than capital would allow)
- Smooths earnings, protects against catastrophes
- Treaty vs facultative reinsurance
- Examples: Munich Re, Swiss Re, Berkshire Hathaway Re

### Distribution Channels

| Channel | Description | Economics |
|---------|-------------|-----------|
| **Captive agents** | Exclusive to one carrier | Salary + commission, carrier controls relationship |
| **Independent agents/brokers** | Represent multiple carriers | Commission-based, own customer relationship |
| **Direct** | Carrier sells directly | Lower acquisition cost, digital-first |
| **Aggregators** | Lead gen/comparison sites | Pay per lead/quote, high CAC |

### MGAs/MGUs (Managing General Agents/Underwriters)
- Delegated underwriting authority from carrier
- Act as carrier's underwriting arm for specialty lines
- Keep portion of premium, carrier takes risk
- Popular model in E&S/specialty markets
- Growing fast—enables speed-to-market without carrier infrastructure

### TPAs (Third-Party Administrators)
- Handle claims processing, policy servicing on behalf of carriers
- Common in self-insured programs, workers' comp
- Examples: Sedgwick, Gallagher Bassett

### Service Providers
- Core systems vendors (Guidewire, Duck Creek, Majesco)
- Data providers (LexisNexis, Verisk, ISO)
- Reinsurance brokers (Aon, Guy Carpenter, Willis Re)

---

## 3. Business Model Deep Dive

### Revenue Streams

**1. Underwriting Income**
```
Premium Earned - Claims Paid - Expenses = Underwriting Profit/Loss
```

**2. Investment Income (The Float)**
- Premiums collected upfront, claims paid later
- "Float" = money held between collection and payout
- Invested in bonds, equities, alternatives
- Buffett's Berkshire model: use float as cheap capital

### Key Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Loss Ratio** | (Claims + LAE) / Earned Premium | 60-70% typical |
| **Expense Ratio** | Operating Expenses / Written Premium | 25-35% typical |
| **Combined Ratio** | Loss Ratio + Expense Ratio | <100% = underwriting profit |

**Combined ratio interpretation:**
- 95% = $0.95 cost per $1 premium = 5% underwriting profit
- 102% = losing money on underwriting, need investment income to profit
- Many carriers run >100% combined, profit on float

### How Insurers Make Money

**Profitable scenario:**
- Combined ratio: 96%
- Investment yield on float: 4%
- Float leverage: 2x equity
- ROE can exceed 15%+ even with thin underwriting margins

**How they lose money:**
- Underpricing risk (inadequate premium for exposure)
- Reserve deficiency (claims cost more than expected)
- Catastrophes (hurricanes, wildfires, pandemics)
- Investment losses
- Expense bloat

### Reserving & Capital

**Reserves:** Liability on balance sheet for future claim payments
- Case reserves (known claims)
- IBNR (Incurred But Not Reported)
- Reserve releases/strengthening impact earnings

**Capital requirements:**
- Risk-Based Capital (RBC) in US
- Solvency II in Europe
- Rating agency capital models (AM Best, S&P)

---

## 4. Insurance Technology Stack

### Core Systems

| System | Function | Key vendors |
|--------|----------|-------------|
| **Policy Administration** | Quote, bind, issue, endorse, renew | Guidewire, Duck Creek, Majesco, Socotra |
| **Billing** | Premium collection, payment plans, commission | Often bundled with policy admin |
| **Claims** | FNOL, adjudication, payments, litigation | Guidewire ClaimCenter, Snapsheet |

### Data & Analytics Platforms
- **Rating engines:** Real-time premium calculation
- **Predictive models:** Loss propensity, fraud detection, pricing optimization
- **Data enrichment:** Pre-fill, third-party data append
- **BI/Reporting:** Portfolio analytics, reserving, regulatory reporting

### Distribution Technology
- Agent portals and comparative raters
- Digital quoting APIs
- CRM and lead management
- Document management

### Legacy vs Modern Architecture

**Legacy reality:**
- Many carriers run 20-40 year old systems
- Mainframe-based, COBOL, batch processing
- Highly customized, expensive to maintain
- "System of record" mentality

**Modern approach:**
- Cloud-native, API-first
- Microservices architecture
- Real-time processing
- Configurable vs customized
- Headless core + best-of-breed ecosystem

**The challenge:** Carriers can't "rip and replace" overnight. Multi-year modernization, often line-by-line migration.

---

## 5. Insurtech Landscape

### Wave 1 (2012-2018): Disrupt the Carriers
- Full-stack carriers trying to replace incumbents
- Heavy VC funding, growth over profit
- Examples: Lemonade, Oscar, Metromile, Root
- Reality check: insurance is hard, capital-intensive, regulated

### Wave 2 (2018-present): Enable the Ecosystem
- B2B enablers helping incumbents modernize
- Less capital-intensive, faster path to revenue
- Infrastructure, data, workflow tools
- Examples: Socotra, Highspot, Federato, Archipelago

### Business Models

| Model | Description | Examples |
|-------|-------------|----------|
| **Full-stack carrier** | Licensed insurer, takes risk | Lemonade, Root, Hippo |
| **MGA/MGU** | Underwriting authority, carrier paper | Corvus, At-Bay, Coalition |
| **Enabler/SaaS** | Software/services to carriers | Socotra, Snapsheet, Shift |
| **Distribution** | Digital agency/broker | Newfront, Embroker, Cover |

### Key Categories

**Distribution innovation:**
- Embedded insurance (see section 6)
- Digital brokers/agencies
- Comparison/aggregation

**Underwriting tech:**
- Alternative data for pricing
- Real-time risk assessment
- Automated underwriting decisioning

**Claims tech:**
- AI-powered FNOL
- Automated damage assessment (computer vision)
- Fraud detection
- Digital payments

### Notable Companies

| Company | Category | Approach |
|---------|----------|----------|
| Lemonade | Full-stack | AI claims, behavioral economics |
| Coalition | Cyber MGA | Active risk monitoring + insurance |
| Hippo | Home | IoT-connected, proactive |
| Root | Auto | Telematics-based pricing |
| Socotra | Core systems | Modern, API-first policy admin |
| Snapsheet | Claims | Virtual claims, AI estimation |

---

## 6. Emerging Models & Trends

### Embedded Insurance
Insurance sold at point of sale, integrated into purchase flow
- Tesla selling auto insurance at car purchase
- Airbnb host protection built into listing
- E-commerce shipping protection

**Why it matters:** Distribution cost drops dramatically, conversion higher, data advantage

### Usage-Based Insurance (UBI)
Premium tied to actual usage/behavior
- **Telematics auto:** Price based on driving behavior (Root, Progressive Snapshot)
- **Pay-per-mile:** Charge by miles driven (Metromile, Mile Auto)
- **Commercial fleet:** Real-time monitoring, dynamic pricing

### Parametric Insurance
Pays based on trigger event, not actual loss
- Hurricane hits Category 4 → automatic payout
- No claims adjustment needed
- Speed of payment is key value prop
- Growing in climate/cat products

### AI/ML Applications

**Underwriting:**
- Risk selection and pricing
- Appetite matching
- Portfolio optimization

**Claims:**
- Fraud detection
- Damage assessment (photo AI)
- Automated triage and assignment

**Customer experience:**
- Chatbots for service
- Personalized recommendations

### Climate Risk
- Increasing cat losses driving hard market
- New products: parametric weather, carbon credits
- Better modeling needed (wildfire, flood)
- Secondary perils becoming primary concern

---

## 7. Market Dynamics

### Hard vs Soft Markets

**Soft market:**
- Excess capacity, competition for business
- Rates declining or flat
- Broad coverage terms
- Easy to place risk

**Hard market:**
- Capacity constrained
- Rates increasing significantly
- Coverage restrictions, exclusions
- Difficult to place certain risks

**Cycle drivers:** Cat losses, investment returns, reserve development, new capital entry/exit

**2020-2024 context:** Hard market in many lines, especially commercial property, cyber, D&O

### Capacity & Capital Flows
- Alternative capital (ILS, cat bonds) provides additional capacity
- Bermuda market for reinsurance and specialty
- Lloyd's of London as specialty marketplace
- Private equity interest in insurance distribution (MGAs, brokers)

### Regulatory Landscape

**US: State-based regulation**
- Each state has insurance department
- Rate/form filing requirements vary
- Surplus lines for non-admitted carriers
- NAIC provides model laws, coordination

**International:**
- Solvency II (EU) - capital requirements framework
- Lloyd's regulation (UK)
- Bermuda Monetary Authority

**Key regulatory concerns:**
- Solvency/capital adequacy
- Market conduct
- Rate adequacy/fairness
- Data privacy (especially for AI/ML pricing)

---

## 8. Key Terminology Glossary

| Term | Definition |
|------|------------|
| **Admitted carrier** | Licensed in state, rates/forms approved, guaranty fund protection |
| **Surplus lines/E&S** | Non-admitted, more flexibility, no guaranty fund |
| **Binder** | Temporary proof of insurance before policy issued |
| **Endorsement** | Amendment to policy terms |
| **Premium** | Price paid for insurance coverage |
| **Deductible** | Amount insured pays before coverage kicks in |
| **Limit** | Maximum amount insurer will pay |
| **Occurrence vs claims-made** | When coverage triggers (event date vs claim report date) |
| **Facultative** | Reinsurance for individual risks |
| **Treaty** | Reinsurance for portfolio of risks |
| **Cession** | Amount of risk transferred to reinsurer |
| **Quota share** | Proportional reinsurance (% of every policy) |
| **Excess of loss** | Reinsurance above retention threshold |
| **LAE** | Loss Adjustment Expense (cost to settle claims) |
| **IBNR** | Incurred But Not Reported reserves |
| **GWP** | Gross Written Premium |
| **NEP** | Net Earned Premium |
| **Admitted assets** | Assets that count toward regulatory capital |
| **Fronting** | Admitted carrier issues policy, cedes most risk to MGA/reinsurer |
| **Program business** | MGA-originated, specific niche focus |
| **API** | Application Programming Interface |
| **FNOL** | First Notice of Loss |
| **Subrogation** | Insurer recovers from responsible third party |
| **Indemnity** | Compensation for loss (restore to pre-loss position) |

---

## Quick Reference: Who Does What

```diagram
{
  "title": "Insurance market roles",
  "note": "Premiums move up toward risk bearers, while claims and servicing move back down toward policyholders.",
  "nodes": [
    {
      "id": "risk",
      "title": "Risk takers",
      "detail": "Primary carriers and reinsurers.",
      "column": 2,
      "row": 1,
      "tone": "accent"
    },
    {
      "id": "intermediaries",
      "title": "Intermediaries",
      "detail": "MGAs underwrite, brokers distribute, and TPAs service.",
      "column": 2,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "policyholders",
      "title": "Policyholders",
      "detail": "Individuals, businesses, and other insurers.",
      "column": 2,
      "row": 3,
      "tone": "default"
    }
  ],
  "edges": [
    { "from": "policyholders", "to": "intermediaries", "label": "premium + submissions" },
    { "from": "intermediaries", "to": "risk", "label": "placement + premium" },
    { "from": "risk", "to": "intermediaries", "label": "capacity + claims funding" },
    { "from": "intermediaries", "to": "policyholders", "label": "distribution + service" }
  ]
}
```

---

*Last updated: January 2025*

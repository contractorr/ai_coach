# Financial Services Industry Crash Course
*Business Models & Technology Focus*

---

## 1. Financial Services Fundamentals

### Core Concept: Money Movement & Risk Management
Financial services = intermediating between those with capital and those who need it. Core functions: payments, lending, investing, risk management.

**The deal:** Savers deposit/invest → Intermediaries allocate capital → Borrowers/businesses get funding → Returns flow back

### Major Sectors

| Sector | What it does | Key players |
|--------|--------------|-------------|
| **Banking** | Deposits, lending, payments | JPMorgan, BofA, Wells, regional/community banks |
| **Payments** | Move money between parties | Visa, Mastercard, PayPal, Stripe |
| **Lending** | Credit products | Banks, credit unions, fintech lenders |
| **Capital Markets** | Securities trading, investment banking | Goldman, Morgan Stanley, Citadel |
| **Asset Management** | Invest on behalf of clients | BlackRock, Vanguard, Fidelity |
| **Insurance** | Risk transfer | (see insurance crash course) |

---

## 2. Value Chain & Key Players

### Banking

**Commercial banks:**
- Take deposits, make loans
- Net interest margin business
- Examples: JPMorgan Chase, Bank of America, Wells Fargo, regional banks

**Investment banks:**
- M&A advisory, underwriting (IPOs, debt)
- Sales & trading
- Examples: Goldman Sachs, Morgan Stanley, boutiques (Lazard, Evercore)

**Credit unions:**
- Member-owned, not-for-profit
- Typically local/regional focus

### Payments Ecosystem

```process-flow
{
  "title": "Payments ecosystem",
  "steps": [
    { "title": "Cardholder" },
    { "title": "Merchant" },
    { "title": "Acquirer" },
    { "title": "Card network" },
    { "title": "Issuer" }
  ]
}
```

| Player | Role | Examples |
|--------|------|----------|
| **Issuer** | Issues card, extends credit | Chase, Capital One, banks |
| **Network** | Routes transactions, sets rules | Visa, Mastercard, Amex |
| **Acquirer** | Signs up merchants, processes | Fiserv, Worldpay, Chase Merchant Services |
| **Processor** | Backend transaction processing | FIS, TSYS, Global Payments |
| **Gateway** | API layer to acquirer | Stripe, Braintree, Adyen |
| **PSP** | Full-service payment acceptance | Stripe, Square, PayPal |

### Lending Value Chain

- **Origination:** Acquire borrowers, underwrite
- **Funding:** Capital source (deposits, warehouse lines, securitization)
- **Servicing:** Collect payments, manage accounts
- **Secondary market:** Sell loans to investors (GSEs for mortgages)

### Capital Markets

- **Buy-side:** Asset managers, hedge funds, pension funds
- **Sell-side:** Investment banks, broker-dealers
- **Exchanges:** NYSE, NASDAQ, CME
- **Market makers:** Provide liquidity (Citadel Securities, Virtu)
- **Custodians:** Hold assets (BNY Mellon, State Street)
- **Prime brokers:** Services for hedge funds

---

## 3. Business Model Deep Dive

### Banking Economics

**Net Interest Income (NII):**
```
Interest Earned on Assets - Interest Paid on Liabilities = NII
```

**Net Interest Margin (NIM):**
```
NII / Average Earning Assets = NIM (typically 2.5-4%)
```

**Revenue mix:**
- Net interest income: 50-70%
- Fee income: 30-50% (interchange, wealth management, advisory, trading)

**Key metrics:**
| Metric | Definition | Target |
|--------|------------|--------|
| **NIM** | Net interest margin | 2.5-4% |
| **Efficiency ratio** | Non-interest expense / Revenue | <60% good |
| **ROA** | Return on assets | 1%+ |
| **ROE** | Return on equity | 10-15% |
| **NPL ratio** | Non-performing loans / Total loans | <2% |
| **CET1** | Common Equity Tier 1 ratio | >10% |

### Payments Economics

**Interchange economics (card transaction):**
```
$100 purchase
- Interchange: ~1.5-2% → Issuer
- Network fee: ~0.1% → Visa/MC
- Acquirer markup: ~0.2-0.5% → Acquirer/processor
= Merchant pays ~2-2.5%
```

**Revenue models:**
- Transaction fees (% + fixed per txn)
- Subscription/platform fees
- FX spread on cross-border
- Value-added services (fraud, analytics)

### Lending Economics

**Spread business:**
```
Interest Rate Charged - Cost of Funds - Credit Losses - Operating Costs = Profit
```

**Key metrics:**
- Origination volume
- Loan yield
- Cost of funds
- Charge-off rate / NCO (Net Charge-Offs)
- Delinquency rates (30/60/90 DPD)

### Capital Markets Economics

- **Trading:** Bid-ask spread, market-making revenue
- **Investment banking:** Advisory fees (% of deal), underwriting spread
- **Asset management:** AUM × management fee (typically 0.1-2%)
- **Prime brokerage:** Securities lending, margin interest, execution

---

## 4. Financial Services Technology Stack

### Core Banking Systems

| System | Function | Key vendors |
|--------|----------|-------------|
| **Core banking** | Accounts, ledger, transactions | Temenos, FIS, Fiserv, Thought Machine |
| **Loan origination (LOS)** | Application to funding | Blend, Encompass (ICE), nCino |
| **Loan servicing** | Payment processing, escrow | Black Knight, Sagent |
| **Treasury management** | Cash management, FX | Kyriba, GTreasury |

### Payments Infrastructure

- **Card processing:** FIS, TSYS, Global Payments
- **ACH/wires:** Federal Reserve, The Clearing House
- **Real-time payments:** RTP (TCH), FedNow
- **Cross-border:** SWIFT, Wise, Payoneer
- **Crypto rails:** Blockchain networks

### Capital Markets Technology

- **Order management (OMS):** Charles River, Bloomberg AIM
- **Execution management (EMS):** FlexTrade, Virtu Triton
- **Risk management:** Numerix, MSCI RiskMetrics
- **Market data:** Bloomberg, Refinitiv, ICE
- **Trading platforms:** FIX protocol connectivity

### Modern Fintech Stack

**BaaS (Banking-as-a-Service):**
- Sponsor banks: Cross River, Evolve, Column
- BaaS platforms: Unit, Treasury Prime, Synctera
- Enables non-banks to offer banking products

**Infrastructure:**
- Identity verification: Plaid, Alloy, Persona
- Compliance/AML: Chainalysis, Sardine, Unit21
- Underwriting: Zest AI, Upstart models
- Card issuing: Marqeta, Lithic

---

## 5. Fintech Landscape

### Category Overview

| Category | Description | Examples |
|----------|-------------|----------|
| **Neobanks** | Digital-only banks | Chime, Current, Varo |
| **Payments** | Payment acceptance/processing | Stripe, Square, Adyen |
| **Lending** | Alternative credit | Upstart, Affirm, SoFi |
| **Wealthtech** | Digital investing | Robinhood, Betterment, Wealthfront |
| **B2B fintech** | Embedded finance, infrastructure | Plaid, Marqeta, Unit |
| **Crypto/Web3** | Digital assets | Coinbase, Circle, Fireblocks |

### Business Models

| Model | Description | Examples |
|-------|-------------|----------|
| **Interchange** | Revenue from card transactions | Chime, Cash App |
| **Spread** | Interest margin on lending | SoFi, Affirm |
| **SaaS** | Software subscription | Stripe (Atlas), Plaid |
| **Transaction fees** | Per-transaction revenue | Stripe, PayPal |
| **AUM/advisory** | % of assets managed | Betterment, Wealthfront |

### Notable Companies

| Company | Category | Approach |
|---------|----------|----------|
| Stripe | Payments | Developer-first APIs, full stack |
| Plaid | Infrastructure | Data connectivity layer |
| Chime | Neobank | Fee-free banking, interchange model |
| Affirm | BNPL | Point-of-sale lending |
| Robinhood | Brokerage | Commission-free, PFOF model |
| Marqeta | Card issuing | Modern card issuing platform |
| Ramp | Corp cards | Expense management + cards |

---

## 6. Emerging Models & Trends

### Embedded Finance
Financial services integrated into non-financial products
- **Embedded payments:** Shopify Payments, Uber
- **Embedded lending:** BNPL at checkout (Affirm, Klarna)
- **Embedded banking:** Vertical SaaS with banking (Toast, Mindbody)
- **Embedded insurance:** Coverage at point of sale

### Real-Time Payments
- FedNow launched 2023
- RTP (The Clearing House) since 2017
- Instant settlement vs T+1/T+2
- Enables new use cases: payroll, gig economy, B2B

### Open Banking / Open Finance
- PSD2 in Europe mandates data sharing
- US moving toward standards (FDX)
- Plaid, Finicity enabling connectivity
- Consumer data portability

### AI/ML Applications

**Credit decisioning:**
- Alternative data underwriting
- Cash flow-based lending
- Real-time risk assessment

**Fraud prevention:**
- Transaction monitoring
- Identity verification
- Behavioral biometrics

**Operations:**
- Document processing
- Customer service automation
- Regulatory reporting

### Crypto/Digital Assets
- Stablecoins (USDC, USDT) as payment rails
- Central Bank Digital Currencies (CBDCs)
- Tokenization of real-world assets
- DeFi protocols

---

## 7. Market Dynamics

### Market Size
- US financial services: ~$2T revenue
- Global payments: ~$2T revenue
- US consumer lending: ~$17T outstanding
- US mortgage market: ~$13T

### Regulatory Landscape

**Banking regulators:**
- OCC (national banks)
- Federal Reserve (BHCs, state member banks)
- FDIC (deposit insurance, state non-member)
- State regulators

**Key regulations:**
| Regulation | What it covers |
|------------|----------------|
| **Dodd-Frank** | Post-2008 reforms, CFPB creation |
| **Basel III** | Bank capital requirements |
| **Bank Secrecy Act** | AML/KYC requirements |
| **Reg E** | Electronic funds transfers |
| **TILA/Reg Z** | Truth in Lending |
| **ECOA/Reg B** | Fair lending |

**Fintech regulatory challenges:**
- Bank charter vs partnership model
- State-by-state licensing (money transmission)
- "True lender" debates
- Rent-a-charter scrutiny

### Competitive Dynamics

**Traditional vs fintech:**
- Banks have deposits, trust, regulatory moat
- Fintechs have UX, speed, specialization
- Convergence: banks buying fintechs, fintechs getting charters

**Big tech entry:**
- Apple (Card, Pay Later, Savings)
- Google (Pay, partnerships)
- Amazon (lending to sellers, payments)

### Key Challenges
- Interest rate sensitivity
- Credit cycle risk
- Regulatory compliance costs
- Fraud and cybersecurity
- Legacy system modernization
- Fintech competition for deposits

---

## 8. Key Terminology Glossary

| Term | Definition |
|------|------------|
| **NIM** | Net Interest Margin - spread between earning and paying rates |
| **NII** | Net Interest Income |
| **Interchange** | Fee paid by merchant's bank to cardholder's bank |
| **Acquirer** | Bank/processor that handles merchant card acceptance |
| **Issuer** | Bank that issues payment cards |
| **MDR** | Merchant Discount Rate - total fee merchant pays |
| **PSP** | Payment Service Provider |
| **ACH** | Automated Clearing House - US bank transfer network |
| **Wire** | Real-time high-value transfer (Fedwire, CHIPS) |
| **SWIFT** | Cross-border messaging network |
| **AML/KYC** | Anti-Money Laundering / Know Your Customer |
| **BSA** | Bank Secrecy Act |
| **CIP** | Customer Identification Program |
| **SAR** | Suspicious Activity Report |
| **CTR** | Currency Transaction Report |
| **Reg E** | Electronic Fund Transfer Act rules |
| **CFPB** | Consumer Financial Protection Bureau |
| **CET1** | Common Equity Tier 1 capital ratio |
| **RWA** | Risk-Weighted Assets |
| **LCR** | Liquidity Coverage Ratio |
| **NPL** | Non-Performing Loan |
| **NCO** | Net Charge-Offs |
| **DPD** | Days Past Due (30/60/90 delinquency) |
| **FICO** | Credit score model |
| **DTI** | Debt-to-Income ratio |
| **LTV** | Loan-to-Value ratio |
| **APR** | Annual Percentage Rate |
| **APY** | Annual Percentage Yield |
| **BaaS** | Banking-as-a-Service |
| **BNPL** | Buy Now Pay Later |
| **POS** | Point of Sale |
| **FBO** | For Benefit Of (account structure) |
| **Omnibus account** | Pooled account structure |
| **Sponsor bank** | Licensed bank enabling fintech products |
| **Money transmission** | Regulated activity of moving money |
| **MSB** | Money Services Business |
| **Ledger** | Record of account balances and transactions |
| **Float** | Money in transit between accounts |
| **Settlement** | Final transfer of funds |
| **Clearing** | Process of reconciling transactions |
| **T+1/T+2** | Settlement timing (trade date + days) |
| **PFOF** | Payment for Order Flow |
| **AUM** | Assets Under Management |
| **Basis point (bp)** | 0.01% (100 bps = 1%) |

---

## Quick Reference: Money Flow

```process-flow
{
  "title": "Financial system money flow",
  "steps": [
    {
      "title": "Capital sources",
      "detail": "Depositors, investors, the central bank, and capital markets."
    },
    {
      "title": "Intermediaries",
      "detail": "Banks, asset managers, lenders, and payment networks."
    },
    {
      "title": "Capital users",
      "detail": "Consumers, businesses, governments, and investors."
    }
  ]
}
```

```process-flow
{
  "title": "Payment flow",
  "note": "Authorization and settlement messages move back from issuer toward merchant after the transaction request moves forward.",
  "steps": [
    { "title": "Consumer" },
    { "title": "Merchant" },
    { "title": "Acquirer" },
    { "title": "Network" },
    { "title": "Issuer" }
  ]
}
```

---

*Last updated: January 2025*

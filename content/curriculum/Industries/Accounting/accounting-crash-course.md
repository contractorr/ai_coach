# Accounting & Back-Office Tech Industry Crash Course
*Business Models & Technology Focus*

---

## 1. Accounting Tech Fundamentals

### Core Concept: Financial Operations and Compliance
Accounting/back-office = systems and processes for tracking financial transactions, managing compliance, and producing financial statements. Every business needs it; complexity scales with size.

**The functions:** Record → Categorize → Report → Comply → Analyze

### Major Function Areas

| Function | Activities | Systems |
|----------|------------|---------|
| **General ledger** | Chart of accounts, journal entries | GL/ERP |
| **Accounts payable** | Vendor bills, payments | AP automation |
| **Accounts receivable** | Invoicing, collections | AR/billing |
| **Expense management** | Employee spend, reimbursements | Expense tools |
| **Payroll** | Pay processing (see HR course) | Payroll systems |
| **Tax compliance** | Filing, reporting | Tax software |
| **Treasury** | Cash, banking, FX | Treasury management |
| **Audit/compliance** | Controls, reporting | Audit tools |

---

## 2. Value Chain & Key Players

### ERP/GL Platforms (System of Record)

| Segment | Vendors | Market position |
|---------|---------|-----------------|
| **Enterprise** | SAP S/4HANA, Oracle Cloud ERP, Workday Financials | Large enterprises |
| **Mid-market** | NetSuite, Sage Intacct, Microsoft Dynamics 365 | Growth companies |
| **SMB** | QuickBooks, Xero, FreshBooks, Wave | Small business |

### Accounts Payable

- **AP automation:** Bill.com, Tipalti, AvidXchange, Coupa Pay
- **Invoice processing:** Stampli, MineralTree
- **Procurement:** Coupa, SAP Ariba, Jaggaer

### Accounts Receivable

- **Billing/invoicing:** Zuora, Chargebee, Maxio (Chargify + SaaSOptics)
- **Collections:** Tesorio, Gaviti, HighRadius
- **Revenue recognition:** Zuora Revenue, Softrax

### Expense Management

- **Corporate cards + expense:** Brex, Ramp, Navan (TripActions)
- **Expense only:** Expensify, Concur (SAP), Chrome River

### Financial Close

- **Close management:** FloQast, BlackLine, Trintech
- **Consolidation:** Planful, OneStream, Workiva

### Tax

- **Corporate tax:** Thomson Reuters ONESOURCE, Avalara
- **Sales tax:** Avalara, Vertex, TaxJar
- **Indirect tax:** Sovos, Thomson Reuters

### Accounting Services

- **Big Four:** Deloitte, EY, PwC, KPMG
- **National firms:** BDO, Grant Thornton, RSM
- **Outsourced accounting:** Pilot, Bench, ScaleFactor (failed)

---

## 3. Business Model Deep Dive

### Pricing Models

| Model | Description | Typical use |
|-------|-------------|-------------|
| **Subscription (flat)** | Monthly/annual fee | SMB accounting software |
| **Tiered** | Features or volume tiers | Mid-market ERP |
| **Transaction-based** | Per invoice, payment, transaction | AP automation, expense |
| **% of spend** | Percentage of processed amount | Some AP/expense tools |
| **Per-seat** | Per user | Enterprise ERP |

**Benchmarks:**
- SMB accounting: $20-200/month
- Mid-market ERP: $1-5K/month
- Enterprise ERP: $100K-1M+/year
- AP automation: $0.50-3 per invoice
- Expense: $5-15 PEPM

### Corporate Card Economics

**Revenue streams:**
- Interchange (1.5-2.5% of spend)
- SaaS fees (some models)
- Interest (if extending credit)

**Unit economics:**
- Revenue per customer: $500-5K/month (based on spend)
- CAC: $500-2K
- Gross margin: 60-80%

### Outsourced Accounting Economics

**Models:**
- Monthly retainer (fixed scope)
- Hourly rates
- Per-transaction pricing

**Typical pricing:**
- Bookkeeping: $300-2K/month (SMB)
- Full-service: $1-10K/month
- CFO-as-a-service: $3-15K/month

### Key Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **ARR/MRR** | Annual/Monthly recurring revenue | Growth |
| **NRR** | Net revenue retention | >110% |
| **Processing volume** | Transaction/spend volume | Drives revenue |
| **Take rate** | Revenue / Processing volume | 0.5-3% |
| **Automation rate** | % of transactions automated | Higher = more value |

---

## 4. Accounting Technology Stack

### Core Architecture

| Layer | System | Function |
|-------|--------|----------|
| **System of Record** | ERP/GL | Financial data, chart of accounts |
| **Subledgers** | AR, AP, Inventory | Transaction detail |
| **Process automation** | AP automation, expense | Workflow, approvals |
| **Reporting** | BI, FP&A tools | Analysis, dashboards |
| **Compliance** | Tax, audit | Regulatory reporting |

### Modern Stack (Growth Company)

```diagram
{
  "title": "Modern accounting stack",
  "note": "Treasury and the ERP/GL sit at the center while spend, billing, close, and audit workflows connect around them.",
  "nodes": [
    {
      "id": "banking",
      "title": "Banking",
      "detail": "Cash accounts and bank data feeds.",
      "column": 1,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "treasury",
      "title": "Treasury",
      "detail": "Cash positioning and movement controls.",
      "column": 2,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "erp",
      "title": "ERP / GL",
      "detail": "Core ledger and accounting system of record.",
      "column": 3,
      "row": 1,
      "tone": "accent"
    },
    {
      "id": "close",
      "title": "Close management",
      "detail": "Checklist, reconciliations, and close orchestration.",
      "column": 4,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "expense",
      "title": "Corp card and expense",
      "detail": "Employee spend capture and expense workflows.",
      "column": 1,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "ap",
      "title": "AP automation",
      "detail": "Invoice intake, approvals, and payables operations.",
      "column": 2,
      "row": 2,
      "tone": "accent"
    },
    {
      "id": "payments",
      "title": "Payments",
      "detail": "Vendor disbursements and cash execution.",
      "column": 3,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "procurement",
      "title": "Procurement",
      "detail": "Optional intake and purchasing controls.",
      "column": 2,
      "row": 3,
      "tone": "muted"
    },
    {
      "id": "ar",
      "title": "AR / Billing",
      "detail": "Customer invoicing and receivables management.",
      "column": 3,
      "row": 3,
      "tone": "accent"
    },
    {
      "id": "collections",
      "title": "Collections",
      "detail": "Customer follow-up and cash application support.",
      "column": 4,
      "row": 3,
      "tone": "muted"
    },
    {
      "id": "revrec",
      "title": "Revenue recognition",
      "detail": "Policy-driven revenue timing and compliance.",
      "column": 3,
      "row": 4,
      "tone": "muted"
    },
    {
      "id": "audit",
      "title": "Audit",
      "detail": "Evidence, controls, and external review.",
      "column": 4,
      "row": 4,
      "tone": "muted"
    }
  ],
  "edges": [
    { "from": "banking", "to": "treasury" },
    { "from": "treasury", "to": "erp" },
    { "from": "close", "to": "erp" },
    { "from": "banking", "to": "expense" },
    { "from": "erp", "to": "ap" },
    { "from": "expense", "to": "ap" },
    { "from": "ap", "to": "payments" },
    { "from": "procurement", "to": "ap" },
    { "from": "ap", "to": "ar" },
    { "from": "ar", "to": "collections" },
    { "from": "ar", "to": "revrec" },
    { "from": "revrec", "to": "audit" }
  ]
}
```

### Integration Landscape

**Key integrations:**
- Bank feeds → GL
- Expense → GL
- AP → GL + Banking
- AR → GL
- Payroll → GL
- CRM → Billing

**Integration methods:**
- Native integrations
- iPaaS (Workato, Tray.io)
- API-first architecture
- CSV import (legacy)

### Enterprise vs SMB

**Enterprise:**
- SAP/Oracle ERP as core
- Multiple subledgers
- Heavy customization
- Shared services centers
- Global consolidation

**SMB:**
- QuickBooks/Xero
- Integrated add-ons
- Minimal customization
- Accountant/bookkeeper support

---

## 5. Accounting Tech Landscape

### Category Overview

| Category | Description | Examples |
|----------|-------------|----------|
| **SMB accounting** | Small business GL | QuickBooks, Xero, Wave |
| **Mid-market ERP** | Growing companies | NetSuite, Sage Intacct |
| **AP automation** | Invoice processing, payments | Bill.com, Tipalti, Stampli |
| **Expense/cards** | Corporate spend | Ramp, Brex, Expensify |
| **AR/billing** | Invoicing, subscription billing | Stripe Billing, Chargebee |
| **Close management** | Month-end close | FloQast, BlackLine |
| **FP&A** | Planning, budgeting | Anaplan, Planful, Pigment |
| **Tax** | Sales tax, compliance | Avalara, Vertex |

### Business Models

| Model | Description | Examples |
|-------|-------------|----------|
| **SaaS** | Subscription | QuickBooks Online, NetSuite |
| **Transaction** | Per invoice/payment | Bill.com |
| **Spend-based** | % or flat on volume | Corporate cards |
| **Services** | Outsourced accounting | Pilot, Bench |
| **Hybrid** | Software + services | Some mid-market |

### Notable Companies

| Company | Category | Approach |
|---------|----------|----------|
| Intuit (QuickBooks) | SMB accounting | Dominant SMB, ecosystem |
| NetSuite (Oracle) | Mid-market ERP | Cloud ERP pioneer |
| Bill.com | AP automation | SMB/mid-market AP |
| Ramp | Corporate cards | Spend management platform |
| Brex | Corporate cards | Startup/growth focus |
| Stripe (Billing) | Subscription billing | Developer-first |
| FloQast | Close management | Accountant-centric |
| Avalara | Tax | Sales tax automation |

---

## 6. Emerging Models & Trends

### AI/ML in Accounting

**Invoice processing:**
- OCR and data extraction
- Auto-coding to GL accounts
- Exception handling
- Fraud detection

**Expense:**
- Receipt scanning
- Policy compliance
- Anomaly detection
- Auto-categorization

**Close/audit:**
- Reconciliation matching
- Variance analysis
- Anomaly detection
- Audit sampling

**Forecasting:**
- Cash flow prediction
- Revenue forecasting
- Scenario modeling

### Embedded Finance/Accounting

- Banking embedded in accounting (QBO + QuickBooks Cash)
- Payments embedded in AP (Bill.com)
- Lending embedded in spend (Brex, Ramp)
- Insurance embedded in expense

### Real-Time Finance

- Continuous close vs month-end
- Real-time dashboards
- Same-day settlement
- Instant reconciliation

### Spend Management Convergence

**All-in-one spend:**
- Corporate cards
- AP automation
- Expense management
- Travel
- Procurement

Players: Ramp, Brex, Airbase, Navan

### Accountant-Led Ecosystem

- Accountants as channel to SMB
- Accountant program economics
- Wholesale/referral models
- Intuit, Xero, QBO ecosystem

---

## 7. Market Dynamics

### Market Size

- Global accounting software: ~$15B
- US SMB accounting: ~$5B
- AP automation: ~$3B
- Expense management: ~$5B
- Corporate cards (fintech): ~$2B+ (revenue)
- ERP market: ~$50B

### Industry Structure

**SMB (highly concentrated):**
- Intuit (QuickBooks): ~70% US SMB market
- Xero: Strong in UK, Australia, growing US
- FreshBooks, Wave: Niche players

**Mid-market:**
- NetSuite: Leading cloud ERP
- Sage Intacct: Strong in professional services
- Microsoft Dynamics: Growing

**Enterprise:**
- SAP, Oracle dominate
- Workday growing in financials

### Competitive Dynamics

**Vertical integration:**
- Accounting → banking (Intuit)
- Cards → accounting (Ramp, Brex)
- Payroll → accounting (Gusto)

**Bundling vs best-of-breed:**
- Platforms bundling more functionality
- Point solutions must integrate well
- Accountant/CFO preferences matter

### Key Challenges

**Vendors:**
- SMB market dominated by Intuit
- Long ERP sales cycles
- Implementation complexity
- Integration requirements
- Competition from banks

**Buyers:**
- Integration complexity
- Data migration
- Change management
- Finding right fit for stage
- CFO/controller bandwidth

### Regulatory Environment

**Financial reporting:**
- GAAP (US)
- IFRS (International)
- SOX compliance (public companies)
- Audit requirements

**Tax:**
- Sales tax (Wayfair decision)
- Income tax
- International tax (transfer pricing)
- 1099/W-2 reporting

**Data:**
- PCI compliance (payment data)
- SOC 2 (service organizations)
- Data residency requirements

---

## 8. Key Terminology Glossary

| Term | Definition |
|------|------------|
| **GL** | General Ledger |
| **ERP** | Enterprise Resource Planning |
| **COA** | Chart of Accounts |
| **Journal entry** | Record of debit/credit transaction |
| **Subledger** | Detailed ledger feeding GL |
| **AP** | Accounts Payable |
| **AR** | Accounts Receivable |
| **Accrual** | Recording expense/revenue when incurred |
| **Cash basis** | Recording when cash moves |
| **GAAP** | Generally Accepted Accounting Principles |
| **IFRS** | International Financial Reporting Standards |
| **ASC 606** | Revenue recognition standard |
| **ASC 842** | Lease accounting standard |
| **Deferred revenue** | Cash received before earned |
| **Accrued expense** | Expense incurred but not paid |
| **Prepaid** | Payment before expense incurred |
| **Depreciation** | Allocating asset cost over time |
| **Amortization** | Depreciation for intangibles |
| **Reconciliation** | Matching records (bank rec, etc.) |
| **Variance** | Difference from budget/forecast |
| **Month-end close** | Finalizing monthly books |
| **Trial balance** | Pre-close account balances |
| **P&L** | Profit and Loss (Income Statement) |
| **Balance sheet** | Assets, liabilities, equity |
| **Cash flow statement** | Cash movements |
| **Working capital** | Current assets - current liabilities |
| **DSO** | Days Sales Outstanding |
| **DPO** | Days Payable Outstanding |
| **Invoice** | Bill sent to customer |
| **PO** | Purchase Order |
| **3-way match** | Match PO, receipt, invoice |
| **Net terms** | Payment due in X days (Net 30) |
| **Early pay discount** | Discount for fast payment (2/10 Net 30) |
| **Float** | Time between payment sent/received |
| **ACH** | Automated Clearing House |
| **Wire** | Bank wire transfer |
| **Virtual card** | Single-use card number |
| **Reconciliation** | Matching bank to books |
| **Intercompany** | Transactions between related entities |
| **Consolidation** | Combining subsidiary financials |
| **Elimination** | Removing intercompany transactions |
| **FX** | Foreign exchange |
| **Translation** | Converting foreign currency |
| **Tax nexus** | Presence requiring tax collection |
| **Use tax** | Tax on untaxed purchases |
| **1099** | Contractor payment form |
| **W-9** | Request for taxpayer ID |
| **SOX** | Sarbanes-Oxley Act |
| **SOC 2** | Service Organization Control report |
| **Audit trail** | Record of changes |
| **Materiality** | Threshold for significance |
| **EBITDA** | Earnings before interest, taxes, depreciation, amortization |
| **Burn rate** | Cash spending rate |
| **Runway** | Months of cash remaining |
| **ARR/MRR** | Annual/Monthly Recurring Revenue |
| **Deferred rev** | Revenue received but not earned |
| **Rev rec** | Revenue recognition |
| **Booking vs billing vs revenue** | Order, invoice, recognized rev |
| **Cost center** | Expense grouping |
| **Profit center** | Revenue + expense grouping |

---

## Quick Reference: Financial Close Process

```process-flow
{
  "title": "Financial close process",
  "note": "Monthly close moves from daily posting through consolidation and reporting.",
  "steps": [
    {
      "title": "Transaction processing",
      "detail": "Daily AP, AR, expense, payroll, and journal entries."
    },
    {
      "title": "Period close",
      "detail": "Cut-off, accruals, reconciliations, and adjustments."
    },
    {
      "title": "Consolidation",
      "detail": "Entity close, intercompany, elimination, and FX translation."
    },
    {
      "title": "Reporting",
      "detail": "Trial balance, financial statements, analysis, and filing."
    }
  ]
}
```

```process-flow
{
  "title": "Procure-to-pay",
  "steps": [
    { "title": "Req" },
    { "title": "PO" },
    { "title": "Receipt" },
    { "title": "Invoice" },
    { "title": "3-way match" },
    { "title": "Approval" },
    { "title": "Payment" }
  ]
}
```

```process-flow
{
  "title": "Order-to-cash",
  "steps": [
    { "title": "Order" },
    { "title": "Fulfill" },
    { "title": "Invoice" },
    { "title": "Collections" },
    { "title": "Cash application" },
    { "title": "Revenue recognition" }
  ]
}
```

---

*Last updated: January 2025*

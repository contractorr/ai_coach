# HR & People Tech Industry Crash Course
*Business Models & Technology Focus*

---

## 1. HR Tech Fundamentals

### Core Concept: Managing the Employee Lifecycle
HR/People tech = software and services enabling organizations to attract, hire, manage, develop, and retain employees. Every company has HR needs; scale drives complexity.

**The lifecycle:** Attract → Hire → Onboard → Manage → Develop → Retain → Offboard

### Major Function Areas

| Function | Activities | Systems |
|----------|------------|---------|
| **Talent acquisition** | Recruiting, hiring | ATS, sourcing, assessment |
| **Core HR** | Records, org structure | HRIS/HCM |
| **Payroll** | Pay processing, taxes | Payroll systems |
| **Benefits** | Health, retirement, perks | Benefits admin |
| **Talent management** | Performance, L&D, succession | TM suites |
| **Workforce management** | Time, scheduling, labor | WFM systems |
| **Employee experience** | Engagement, culture | Engagement platforms |

---

## 2. Value Chain & Key Players

### HRIS/HCM Platforms (System of Record)

| Segment | Vendors | Market position |
|---------|---------|-----------------|
| **Enterprise** | Workday, Oracle HCM, SAP SuccessFactors | Large enterprises |
| **Mid-market** | ADP, UKG, Ceridian | Mid-size companies |
| **SMB** | Gusto, Rippling, BambooHR, Paylocity | Small business |
| **Global** | Deel, Remote, Papaya Global | Distributed workforce |

### Talent Acquisition

- **ATS:** Greenhouse, Lever, iCIMS, Workday Recruiting
- **Sourcing:** LinkedIn Recruiter, SeekOut, Hiretual
- **Assessment:** HackerRank, Codility, Criteria
- **Background checks:** Checkr, Sterling, HireRight
- **Job boards:** Indeed, LinkedIn, ZipRecruiter

### Payroll & Benefits

- **Payroll:** ADP, Paychex, Paylocity, Gusto
- **Benefits admin:** Benefitfocus, Businessolver, Ease
- **Benefits brokers:** Mercer, Aon, Willis Towers Watson
- **PEO:** TriNet, Justworks, Insperity

### Talent Management

- **Performance:** Lattice, 15Five, Culture Amp, Betterworks
- **Learning:** Cornerstone, Degreed, LinkedIn Learning
- **Engagement:** Culture Amp, Glint (LinkedIn), Peakon (Workday)

### Workforce Management

- **Time/attendance:** Kronos (UKG), ADP, Deputy
- **Scheduling:** When I Work, Deputy, Legion
- **Contingent:** Beeline, Fieldglass (SAP)

---

## 3. Business Model Deep Dive

### Pricing Models

| Model | Description | Typical use |
|-------|-------------|-------------|
| **PEPM** | Per-employee-per-month | Core HR, most SaaS |
| **Per seat** | Per user/admin | Recruiting tools |
| **Transaction** | Per payroll run, per hire | Payroll, ATS |
| **Flat subscription** | Fixed monthly fee | SMB tools |
| **Revenue share** | % of premiums/benefits | Benefits platforms |

**PEPM benchmarks:**
- Full HRIS/HCM: $8-25 PEPM
- Payroll only: $2-8 PEPM
- Point solutions: $2-10 PEPM
- ATS: $300-800/month flat or per-seat

### PEO Economics

**Professional Employer Organization:**
- Co-employment model: PEO is employer of record
- Bundles: HR, payroll, benefits, compliance
- Revenue: Admin fee + benefits markup
- Value prop: Benefits access for small companies

**Economics:**
- Admin fee: $100-200 per employee/month
- Benefits margin: 3-10% of premium
- Typical customer: 10-200 employees
- Gross profit/employee: $150-300/month

### Payroll Economics

**Revenue:**
- Base processing fee
- Per-employee fee
- Tax filing fees
- Add-on services

**Float income:**
- Hold payroll funds briefly before distribution
- Interest on float (significant for large providers)
- ADP ~$2T annual payroll flow

### Key Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **ARR** | Annual recurring revenue | Growth metric |
| **PEPM** | Per-employee-per-month revenue | $8-25 typical HCM |
| **NRR** | Net revenue retention | >100% (expand > churn) |
| **Logo churn** | % customers leaving | <10% annual |
| **Employee churn** | Seat loss from customer layoffs | Macro-dependent |
| **Implementation time** | Days to go-live | 30-90 days typical |

---

## 4. HR Technology Stack

### Core Systems Architecture

| Layer | System | Function |
|-------|--------|----------|
| **System of Record** | HRIS/HCM | Employee data, org structure |
| **Payroll** | Often bundled or integrated | Pay processing |
| **Talent acquisition** | ATS | Recruiting workflow |
| **Talent management** | Performance, learning | Development |
| **Workforce management** | Time, scheduling | Hourly workforce |
| **Analytics** | People analytics | Workforce insights |

### Integration Landscape

**Key integrations:**
- Payroll ↔ HRIS (employee data)
- ATS → HRIS (new hire data)
- Benefits → Payroll (deductions)
- Time → Payroll (hours worked)
- Learning → TM (completions)

**Integration standards:**
- APIs (REST, GraphQL)
- SFTP/flat files (legacy)
- Integration platforms (Workato, Merge)
- HR data standards emerging

### Enterprise vs SMB Stack

**Enterprise (1000+ employees):**
- Workday/Oracle/SAP HCM as core
- Best-of-breed point solutions
- Custom integrations
- Global complexity

**SMB (<100 employees):**
- All-in-one platforms (Gusto, Rippling)
- Simpler needs
- Lower customization
- Faster implementation

---

## 5. HR Tech Landscape

### Category Overview

| Category | Description | Examples |
|----------|-------------|----------|
| **All-in-one HRIS** | Full platform | Workday, Rippling, Gusto |
| **Recruiting/ATS** | Hiring workflow | Greenhouse, Lever, Ashby |
| **Performance** | Goals, reviews, feedback | Lattice, 15Five, Culture Amp |
| **Learning** | Training, development | Degreed, Cornerstone, 360Learning |
| **Engagement** | Surveys, culture | Culture Amp, Peakon, Officevibe |
| **Compensation** | Pay planning, equity | Pave, Carta, Figures |
| **Global/EOR** | International hiring | Deel, Remote, Oyster |
| **Benefits** | Health, perks | Benefitfocus, Forma, Benepass |

### Business Models

| Model | Description | Examples |
|-------|-------------|----------|
| **SaaS (PEPM)** | Per-employee subscription | Workday, Lattice |
| **PEO** | Co-employment bundle | TriNet, Justworks |
| **EOR** | Employer of record (global) | Deel, Remote |
| **Marketplace** | Connect buyers/sellers | Job boards, benefits marketplaces |
| **Transaction** | Per hire, per payroll | ATS, payroll |

### Notable Companies

| Company | Category | Approach |
|---------|----------|----------|
| Workday | HCM | Enterprise cloud leader |
| Rippling | All-in-one | IT + HR unified platform |
| Gusto | SMB payroll/HR | Small business focus |
| Greenhouse | ATS | Structured hiring |
| Lattice | Performance | OKRs, reviews, engagement |
| Deel | Global payroll/EOR | International workforce |
| Carta | Equity management | Cap table + compensation |
| Checkr | Background checks | API-first verification |

---

## 6. Emerging Models & Trends

### AI/ML in HR

**Recruiting:**
- Resume parsing and matching
- Candidate sourcing
- Interview scheduling
- Skill assessment
- Bias detection in job descriptions

**HR operations:**
- Chatbots for employee questions
- Document processing
- Predictive attrition
- Compensation benchmarking

**Development:**
- Learning recommendations
- Career pathing
- Skills gap analysis

**Concerns:**
- Algorithmic bias in hiring
- Privacy (monitoring)
- Transparency requirements
- EEOC scrutiny

### Global/Distributed Workforce

**EOR (Employer of Record):**
- Hire internationally without entity
- Compliance handled by EOR
- Growing fast (remote work trend)
- Players: Deel, Remote, Oyster, Velocity Global

**Global payroll:**
- Pay employees in any country
- Currency, compliance, taxes handled
- Consolidation with EOR offerings

### Skills-Based Organizations

- Shift from jobs to skills
- Skills taxonomies and ontologies
- Internal talent marketplaces
- Gig/project-based work
- Platforms: Gloat, Fuel50, Eightfold

### Employee Experience

- Comprehensive experience platforms
- Moments that matter (onboarding, promotion, etc.)
- Wellness integration
- Recognition and rewards
- Remote/hybrid work tools

### Compensation Transparency

- Pay equity analysis
- Salary range disclosures (legal requirements)
- Compensation benchmarking tools
- Equity management maturity
- Players: Pave, Figures, Syndio

---

## 7. Market Dynamics

### Market Size

- Global HCM market: ~$25B
- US HR tech: ~$15B
- Payroll services: ~$25B
- Staffing/recruiting: ~$150B
- Benefits administration: ~$10B

### Industry Structure

**Consolidation:**
- HCM platforms acquiring point solutions
- Workday, UKG, ADP making acquisitions
- PE roll-ups in payroll, staffing

**Market by segment:**
- Enterprise: Workday, Oracle, SAP dominate
- Mid-market: ADP, UKG, Ceridian compete
- SMB: Highly fragmented, Gusto/Rippling growing

### Competitive Dynamics

**Platform vs best-of-breed:**
- Platforms: Single vendor, integrated, good enough
- Best-of-breed: Specialized, better features, integration overhead
- Trend: Platforms winning on convenience

**Switching costs:**
- HRIS: High (data, integrations, change management)
- Point solutions: Lower
- Creates sticky revenue but slow sales cycles

### Key Challenges

**Vendors:**
- Long enterprise sales cycles
- Implementation complexity
- Integration burden
- Employee churn (customer layoffs)
- Competition from platform bundling

**Buyers:**
- Integration complexity
- Change management
- Data quality/migration
- Vendor sprawl
- Global complexity

### Regulatory Environment

**US:**
- ACA (benefits reporting)
- ERISA (retirement plans)
- FMLA, ADA, Title VII (employment law)
- State laws (CA, NY particularly complex)
- Pay transparency laws (growing)

**Global:**
- GDPR (employee data in EU)
- Country-specific labor laws
- Works councils (EU)
- Statutory benefits requirements

---

## 8. Key Terminology Glossary

| Term | Definition |
|------|------------|
| **HRIS** | Human Resource Information System |
| **HCM** | Human Capital Management |
| **HRMS** | Human Resource Management System |
| **ATS** | Applicant Tracking System |
| **TMS** | Talent Management System |
| **LMS** | Learning Management System |
| **WFM** | Workforce Management |
| **PEPM** | Per-Employee-Per-Month |
| **PEO** | Professional Employer Organization |
| **EOR** | Employer of Record |
| **ASO** | Administrative Services Only |
| **Co-employment** | Shared employer responsibilities (PEO) |
| **Payroll float** | Funds held between deduction and payment |
| **Benefits admin** | Benefits enrollment and management |
| **Open enrollment** | Annual benefits selection period |
| **COBRA** | Continued health coverage after employment |
| **401(k)** | Retirement plan |
| **FSA/HSA** | Flexible/Health Savings Account |
| **PTO** | Paid Time Off |
| **FTE** | Full-Time Equivalent |
| **Headcount** | Number of employees |
| **Turnover** | Employee departure rate |
| **Attrition** | Natural employee departures |
| **Retention** | Keeping employees |
| **eNPS** | Employee Net Promoter Score |
| **Engagement** | Employee commitment/satisfaction |
| **Performance review** | Formal evaluation |
| **OKR** | Objectives and Key Results |
| **KPI** | Key Performance Indicator |
| **Competency** | Skill or behavior standard |
| **Succession planning** | Identifying future leaders |
| **L&D** | Learning and Development |
| **Onboarding** | New hire integration |
| **Offboarding** | Employee departure process |
| **I-9** | Employment eligibility verification |
| **W-4** | Tax withholding form |
| **W-2** | Annual wage statement |
| **1099** | Contractor payment form |
| **ACA** | Affordable Care Act |
| **ERISA** | Employee Retirement Income Security Act |
| **FMLA** | Family and Medical Leave Act |
| **ADA** | Americans with Disabilities Act |
| **EEOC** | Equal Employment Opportunity Commission |
| **DOL** | Department of Labor |
| **Exempt/Non-exempt** | Overtime eligibility classification |
| **At-will** | Employment terminable by either party |
| **Offer letter** | Employment offer document |
| **Background check** | Pre-employment verification |
| **Reference check** | Contacting previous employers |
| **Req** | Job requisition |
| **Time-to-hire** | Days from req open to offer accept |
| **Cost-per-hire** | Total recruiting cost per hire |
| **Quality of hire** | New hire performance measure |
| **Passive candidate** | Not actively job seeking |
| **Sourcing** | Finding candidates |
| **Pipeline** | Candidate funnel |
| **ATS workflow** | Recruiting process stages |
| **Offer acceptance rate** | % of offers accepted |

---

## Quick Reference: Employee Lifecycle

```process-flow
{
  "title": "Employee lifecycle",
  "steps": [
    {
      "title": "Attract",
      "detail": "Employer brand, job posting, sourcing, and careers site."
    },
    {
      "title": "Hire",
      "detail": "Apply, screen, interview, offer, background check, and accept."
    },
    {
      "title": "Onboard",
      "detail": "Paperwork, setup, training, integration, and 30/60/90 plans."
    },
    {
      "title": "Manage and develop",
      "detail": "Performance, feedback, learning, career, and compensation."
    },
    {
      "title": "Retain or exit",
      "detail": "Engagement, recognition, growth, or offboarding."
    }
  ]
}
```

```diagram
{
  "title": "HR system integration",
  "note": "The HRIS acts as the core system of record while adjacent tools handle recruiting, pay, benefits, time, and development.",
  "nodes": [
    {
      "id": "ats",
      "title": "ATS",
      "detail": "Candidate pipeline and recruiting workflow.",
      "column": 1,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "hris",
      "title": "HRIS",
      "detail": "System of record for employees and org data.",
      "column": 2,
      "row": 1,
      "tone": "accent"
    },
    {
      "id": "payroll",
      "title": "Payroll",
      "detail": "Compensation, tax withholding, and pay runs.",
      "column": 3,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "benefits",
      "title": "Benefits",
      "detail": "Enrollment and plan administration.",
      "column": 4,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "time",
      "title": "Time",
      "detail": "Hours, leave, and attendance tracking.",
      "column": 5,
      "row": 1,
      "tone": "muted"
    },
    {
      "id": "learning",
      "title": "Performance and learning",
      "detail": "Development, reviews, and growth planning.",
      "column": 3,
      "row": 2,
      "tone": "muted"
    }
  ],
  "edges": [
    { "from": "ats", "to": "hris", "label": "hire" },
    { "from": "hris", "to": "payroll", "label": "pay" },
    { "from": "payroll", "to": "benefits", "label": "enroll" },
    { "from": "benefits", "to": "time", "label": "track" },
    { "from": "hris", "to": "learning", "label": "develop" }
  ]
}
```

---

*Last updated: January 2025*

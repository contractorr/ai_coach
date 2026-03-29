# Healthcare Industry Crash Course
*Business Models & Technology Focus*

---

## 1. Healthcare Fundamentals

### Core Concept: Care Delivery & Payment
Healthcare = services to diagnose, treat, prevent illness. Unique market: third-party payer model (someone other than patient usually pays), information asymmetry, regulatory intensity.

**The flow:** Patient receives care → Provider bills payer → Payer adjudicates/pays → Patient pays remainder

### System Overview

| System Type | Description | Examples |
|-------------|-------------|----------|
| **Single-payer** | Government pays, private delivery | Canada, UK (NHS) |
| **Multi-payer** | Mix of private/public insurance | US, Germany |
| **Out-of-pocket** | Direct patient payment | Many developing nations |

US breakdown: ~50% private insurance, ~35% government (Medicare/Medicaid), ~10% uninsured

---

## 2. Value Chain & Key Players

### Providers
- **Health systems:** Integrated networks (Kaiser, HCA, Ascension)
- **Hospitals:** Acute care facilities
- **Physician groups:** Primary care, specialists
- **ASCs:** Ambulatory surgery centers (outpatient)
- **Post-acute:** SNFs, home health, hospice

### Payers/Insurers
- **Commercial:** Employer-sponsored, individual market (UnitedHealthcare, Anthem, Aetna)
- **Medicare:** Federal program, 65+, disabled
- **Medicaid:** State/federal, low-income
- **Medicare Advantage:** Private plans managing Medicare benefits
- Examples: UHC, Elevance, CVS/Aetna, Cigna, Humana

### PBMs (Pharmacy Benefit Managers)
- Middlemen between payers, pharmacies, drug manufacturers
- Negotiate rebates, manage formularies
- Top 3 control ~80% market: CVS Caremark, Express Scripts, OptumRx

### Life Sciences
- **Pharma:** Drug development and manufacturing (Pfizer, J&J, Merck)
- **Biotech:** Biologics, gene therapy (Amgen, Gilead, Moderna)
- **Medical devices:** Equipment, implants (Medtronic, Abbott, Stryker)

### Distribution
- **Distributors:** McKesson, Cardinal, AmerisourceBergen (now Cencora)
- **Retail pharmacy:** CVS, Walgreens, independents
- **Specialty pharmacy:** High-cost, complex medications

---

## 3. Business Model Deep Dive

### Provider Economics

**Revenue model:**
```
Patient Volume × Reimbursement Rate × Payer Mix = Revenue
- Operating Costs = Margin
```

**Reimbursement models:**

| Model | Description | Risk |
|-------|-------------|------|
| **Fee-for-service (FFS)** | Pay per procedure/visit | Volume incentive, low risk |
| **Capitation** | Fixed per-member-per-month (PMPM) | Provider takes utilization risk |
| **Bundled payment** | Fixed payment for episode | Provider takes episode risk |
| **Value-based** | Tied to quality/outcomes | Shared savings/losses |

**Key metrics:**
- Case mix index (CMI): Severity/complexity of patients
- Average length of stay (ALOS)
- Bed utilization rate
- Net patient revenue per adjusted discharge

### Payer Economics

**Revenue:** Premiums + investment income

**Medical Loss Ratio (MLR):**
```
Medical Costs / Premium Revenue = MLR
```
ACA requires: 80% (individual/small group), 85% (large group)

**Key metrics:**
- MLR: 80-88% typical
- Administrative costs: 12-20%
- Per-member-per-month (PMPM) cost
- Days in claims payable

### Value-Based Care Progression

```process-flow
{
  "title": "Value-based care progression",
  "note": "Provider risk generally increases as the model moves from fee-for-service toward capitation.",
  "steps": [
    { "title": "FFS" },
    { "title": "Pay-for-performance" },
    { "title": "Bundled" },
    { "title": "Shared savings" },
    { "title": "Full capitation" }
  ]
}
```

---

## 4. Healthcare Technology Stack

### Core Clinical Systems

| System | Function | Key vendors |
|--------|----------|-------------|
| **EHR/EMR** | Clinical documentation, orders | Epic, Oracle Health (Cerner), MEDITECH |
| **Practice Management** | Scheduling, billing | athenahealth, eClinicalWorks |
| **PACS** | Medical imaging storage | Change Healthcare, Philips |
| **LIS** | Lab information systems | Sunquest, Orchard |

**Epic dominance:** ~35% hospital market, ~60% of beds in large systems. Network effects (Care Everywhere).

### Revenue Cycle Management (RCM)
- Patient registration → Eligibility → Charge capture → Coding → Billing → Collections
- Vendors: Waystar, R1 RCM, Change Healthcare
- Key challenge: Denials management (5-10% of claims denied initially)

### Payer Systems
- Claims adjudication platforms
- Member portals
- Care management platforms
- Analytics/risk stratification
- Vendors: HealthEdge, QNXT, Facets (TriZetto)

### Interoperability Standards
- **HL7v2:** Legacy messaging (still dominant)
- **FHIR (HL7):** Modern REST API standard
- **X12 (EDI):** Claims, eligibility transactions
- **ICD-10:** Diagnosis codes
- **CPT:** Procedure codes
- **SNOMED CT:** Clinical terminology

### Data & Analytics
- Population health platforms
- Clinical decision support
- Risk adjustment/HCC coding
- Social determinants of health (SDOH)
- Vendors: Health Catalyst, Innovaccer, Arcadia

---

## 5. Health Tech Landscape

### Category Overview

| Category | Description | Examples |
|----------|-------------|----------|
| **Virtual care** | Telehealth, remote monitoring | Teladoc, Amwell, MDLive |
| **Care navigation** | Guide patients through system | Accolade, Included Health, Transcarent |
| **Digital therapeutics** | Software as treatment | Livongo, Omada, Pear Therapeutics |
| **Clinical workflow** | Provider efficiency tools | Notable, Abridge, Ambience |
| **RCM/Admin** | Revenue cycle, prior auth | Olive AI, Akasa, Cohere Health |

### Business Models

| Model | Description | Examples |
|-------|-------------|----------|
| **B2B2C (employer)** | Sell to employers for employees | Livongo, Hinge Health |
| **B2B (provider)** | Sell software to health systems | Notable, Abridge |
| **B2B (payer)** | Sell to insurance companies | Cohere Health, Clarify |
| **Direct-to-consumer** | Patient pays directly | Ro, Hims, Nurx |
| **Risk-bearing** | Take capitation, own clinics | Oak Street, ChenMed |

### Notable Companies

| Company | Category | Approach |
|---------|----------|----------|
| Teladoc/Livongo | Virtual + chronic care | Merged telehealth + remote monitoring |
| Oak Street Health | Primary care | Medicare-focused, value-based |
| Hinge Health | MSK digital | Physical therapy via app + sensors |
| Abridge | Clinical AI | Ambient documentation |
| Color Health | Population health | Employer health programs |
| Devoted Health | MA payer | Tech-enabled Medicare Advantage |

---

## 6. Emerging Models & Trends

### AI/ML Applications

**Clinical:**
- Ambient documentation (Abridge, Nuance DAX, Nabla)
- Diagnostic imaging AI (Viz.ai, Aidoc)
- Clinical decision support
- Drug discovery (Recursion, Insilico)

**Administrative:**
- Prior authorization automation
- Coding optimization
- Denial prediction and prevention
- Claims fraud detection

### Value-Based Care Enablers
- Risk adjustment optimization (HCC coding)
- Care gap identification
- Patient attribution
- Quality measure tracking
- Cost/utilization analytics

### Care Model Innovation

**Primary care transformation:**
- Direct primary care (DPC): Subscription model, no insurance
- Employer clinics: On-site/near-site
- Medicare-focused: Oak Street, Iora (One Medical), ChenMed

**Specialty care:**
- Virtual-first specialty (Cerebral, Done)
- Centers of excellence (Carrum, Lantern)
- Specialty pharmacy integration

### Consumer Health
- Wearables/remote monitoring
- Mental health apps (Calm, Headspace, Cerebral)
- Fertility (Kindbody, Progyny)
- Genomics/personalized medicine (23andMe, Tempus)

---

## 7. Market Dynamics

### Healthcare Spending
- US: ~$4.5T/year, ~18% of GDP
- Per capita: ~$13K (2x other developed nations)
- Growth: 5-6% annually
- Hospital care: ~30%, Physician services: ~20%, Rx drugs: ~10%

### Consolidation Trends

**Vertical integration:**
- Payers buying providers (UHC/Optum owns physician groups)
- Retail entering (CVS/Aetna, Amazon/One Medical)
- PBM consolidation with payers

**Horizontal:**
- Health system mergers
- Physician practice roll-ups (private equity)
- Payer consolidation (Big 5 control ~45% commercial)

### Regulatory Environment

**Key regulations:**
- ACA (Obamacare): Coverage expansion, MLR requirements
- HIPAA: Privacy and security
- Stark Law/Anti-Kickback: Prohibit referral payments
- 21st Century Cures: Interoperability mandates
- No Surprises Act: Protect patients from surprise bills

**CMS initiatives:**
- Value-based care programs (MSSP, ACOs)
- Price transparency rules
- Interoperability requirements
- Drug pricing reforms

### Key Challenges
- Labor shortages (nursing, physicians)
- Margin pressure (inflation > reimbursement growth)
- Burnout and documentation burden
- Cybersecurity threats
- Health equity and SDOH

---

## 8. Key Terminology Glossary

| Term | Definition |
|------|------------|
| **ACO** | Accountable Care Organization - provider group taking shared savings/risk |
| **Capitation** | Fixed per-member-per-month payment regardless of utilization |
| **PMPM** | Per-member-per-month - standard unit for healthcare costs |
| **MLR** | Medical Loss Ratio - % of premium spent on care |
| **HCC** | Hierarchical Condition Category - risk adjustment methodology |
| **Prior auth** | Payer approval required before service |
| **Formulary** | List of covered drugs with tier structure |
| **PBM** | Pharmacy Benefit Manager |
| **EHR/EMR** | Electronic Health/Medical Record |
| **FHIR** | Fast Healthcare Interoperability Resources - modern API standard |
| **DRG** | Diagnosis Related Group - hospital payment classification |
| **CPT** | Current Procedural Terminology - procedure codes |
| **ICD-10** | International Classification of Diseases - diagnosis codes |
| **NPI** | National Provider Identifier |
| **EOB** | Explanation of Benefits |
| **Deductible** | Amount patient pays before insurance kicks in |
| **Coinsurance** | Patient's % share after deductible |
| **Copay** | Fixed patient payment per service |
| **Out-of-pocket max** | Annual cap on patient payments |
| **Network** | Contracted providers with negotiated rates |
| **In-network/OON** | Within or outside contracted network |
| **Allowed amount** | Maximum payer will pay for service |
| **Write-off** | Difference between charge and allowed amount |
| **Denial** | Claim rejected by payer |
| **Appeal** | Challenge to claim denial |
| **HEDIS** | Healthcare Effectiveness Data and Information Set - quality measures |
| **Star Ratings** | CMS quality ratings for MA plans (1-5 stars) |
| **Risk adjustment** | Adjusting payments based on patient health status |
| **SNF** | Skilled Nursing Facility |
| **ASC** | Ambulatory Surgery Center |
| **MA** | Medicare Advantage |
| **MSP** | Medicare Secondary Payer |
| **COB** | Coordination of Benefits |
| **Utilization management** | Payer oversight of care appropriateness |
| **Care management** | Programs to coordinate care for high-risk patients |
| **SDOH** | Social Determinants of Health |

---

## Quick Reference: Money Flow

```diagram
{
  "title": "Healthcare money flow",
  "note": "Care, premiums, reimbursement, and cost sharing move through different parts of the stack at different times.",
  "nodes": [
    {
      "id": "payers",
      "title": "Payers",
      "detail": "Commercial plans, Medicare, Medicaid, and self-insured employers.",
      "column": 2,
      "row": 1,
      "tone": "accent"
    },
    {
      "id": "intermediaries",
      "title": "Intermediaries",
      "detail": "PBMs, TPAs, care management, and RCM vendors.",
      "column": 2,
      "row": 2,
      "tone": "muted"
    },
    {
      "id": "providers",
      "title": "Providers",
      "detail": "Hospitals, physicians, post-acute providers, and pharmacies.",
      "column": 2,
      "row": 3,
      "tone": "accent"
    },
    {
      "id": "patients",
      "title": "Patients",
      "detail": "Care recipients who also fund part of the system through deductibles, copays, and coinsurance.",
      "column": 2,
      "row": 4,
      "tone": "default"
    }
  ],
  "edges": [
    { "from": "patients", "to": "payers", "label": "premiums" },
    { "from": "payers", "to": "intermediaries", "label": "claims admin" },
    { "from": "intermediaries", "to": "providers", "label": "network + claims" },
    { "from": "providers", "to": "patients", "label": "care delivery" },
    { "from": "patients", "to": "providers", "label": "cost sharing" }
  ]
}
```

---

*Last updated: January 2025*

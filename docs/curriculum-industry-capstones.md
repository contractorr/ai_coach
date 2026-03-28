# Industry Curriculum Capstones

This document converts the current one-file industry crash courses from standalone survey pages
into explicit capstone or applied modules inside the broader curriculum.

## Why these modules need conversion

The current industry guides all follow roughly the same survey pattern:

1. Fundamentals
2. Value chain and key players
3. Business model deep dive
4. Technology stack
5. Industry landscape
6. Emerging models and trends
7. Market dynamics
8. Glossary

That shape is useful as a rough industry scan, but it is weak as a curriculum endpoint:

- it repeats the same sector-survey structure regardless of learner intent
- it assumes the module should stand alone instead of sitting on top of prerequisite guides
- it overweights market mapping and technology landscape coverage
- it underweights decision cases, constraints, and transfer from core programs
- it ends as a dead-end leaf rather than a capstone with next-step connections

## Shared capstone contract

Every industry module should be rewritten as an applied capstone with this shape:

1. Sector brief
2. How value is created and captured
3. Core workflow or operating model
4. Important metrics, constraints, and regulation
5. Decision case or capstone exercise
6. Next-step connections

## Module-by-module capstone map

### `industry-accounting`

- **Capstone role:** Apply accounting and business-acumen concepts to back-office workflow, systems, and compliance trade-offs.
- **Prerequisite path:** `28-accounting`
- **Programs served:** `business-acumen`
- **Required content changes:** Replace generic accounting-tech landscape coverage with a decision case around close, reconciliation, audit-readiness, or ERP workflow design. Add operator-facing KPIs such as days-to-close, error rate, audit burden, and implementation risk.

### `industry-construction`

- **Capstone role:** Translate engineering and business fundamentals into project-delivery, contractor-economics, and construction-tech operating judgment.
- **Prerequisite path:** `35-engineering-guide`
- **Programs served:** `industry-transition`
- **Required content changes:** Replace broad sector surveying with a workflow-centered module covering estimate-to-build, subcontractor coordination, schedule risk, and margin leakage. Add a decision case on bid/no-bid, project-controls software, or modular/off-site adoption.

### `industry-energy`

- **Capstone role:** Apply energy-systems knowledge to generation, infrastructure, regulation, and transition-era capital-allocation trade-offs.
- **Prerequisite path:** `11-energy-materials-guide`
- **Programs served:** `industry-transition`, `strategy-investing`
- **Required content changes:** Collapse generic energy-tech landscape sections into a capstone comparing generation, grid, storage, and regulatory bottlenecks. Add a decision case on resource mix, interconnection delays, or utility-scale versus distributed deployment.

### `industry-financialservices`

- **Capstone role:** Use MBA and business-model lenses to reason about risk, distribution, compliance, and fintech operating strategy.
- **Prerequisite path:** `30-mba-curriculum`
- **Programs served:** `business-acumen`, `industry-transition`, `strategy-investing`
- **Required content changes:** Replace broad fintech landscape coverage with operating-model comparisons across banking, payments, lending, and asset management. Add a decision case on product expansion, channel strategy, or regulated-versus-embedded-finance trade-offs.

### `industry-government`

- **Capstone role:** Connect policy, institutional design, and AI/operator themes to public-sector procurement, delivery, and mission-risk decisions.
- **Prerequisite path:** `24-government-politics-guide`
- **Programs served:** `ai-for-operators`, `policy-regulation`, `industry-transition`
- **Required content changes:** Replace generic GovTech landscape summaries with a module centered on procurement cycles, stakeholder complexity, and public accountability. Add a decision case on digitization, AI adoption in agencies, or vendor-versus-in-house delivery.

### `industry-healthcare`

- **Capstone role:** Apply medicine and physiology foundations to care-delivery workflows, reimbursement constraints, and health-tech adoption.
- **Prerequisite path:** `17-medicine-human-physiology-guide`
- **Programs served:** `ai-for-operators`, `industry-transition`
- **Required content changes:** Replace health-tech market scans with patient-flow, payer-provider, and compliance-focused operating models. Add a decision case on clinical workflow tooling, reimbursement incentives, or deployment risk in regulated care settings.

### `industry-hr`

- **Capstone role:** Turn sociology and institutional-design concepts into people-operations, hiring-market, and HR-tech judgment.
- **Prerequisite path:** `23-sociology-institutional-design-guide`
- **Programs served:** `industry-transition`
- **Required content changes:** Replace generic HR-tech landscape sections with workforce-planning, recruiting-funnel, performance-system, and compliance workflows. Add a decision case on ATS adoption, compensation design, or organizational redesign under growth pressure.

### `industry-insurance`

- **Capstone role:** Apply probability, risk, and legal-system concepts to underwriting, claims, distribution, and regulatory trade-offs.
- **Prerequisite path:** `04-statistics-probability-guide`, `25-law-legal-systems-guide`
- **Programs served:** `decision-quality`, `policy-regulation`, `industry-transition`
- **Required content changes:** Replace insurtech cataloging with an operating module spanning underwriting, claims, reserving, pricing, and channel economics. Add a decision case on loss-ratio management, automation in claims, or product expansion under regulatory constraints.

### `industry-legal`

- **Capstone role:** Connect legal-systems understanding to law-firm workflow, in-house counsel priorities, and legal-tech adoption decisions.
- **Prerequisite path:** `25-law-legal-systems-guide`
- **Programs served:** `decision-quality`, `policy-regulation`, `industry-transition`
- **Required content changes:** Replace legal-tech landscape review with concrete workflows such as matter intake, contract review, discovery, and outside-counsel management. Add a decision case on build-versus-buy tooling, workflow automation, or risk escalation.

### `industry-realestate`

- **Capstone role:** Use economics and business-model lenses to reason about property markets, development, brokerage, and PropTech decisions.
- **Prerequisite path:** `26-economics-guide`
- **Programs served:** `business-acumen`, `industry-transition`, `strategy-investing`
- **Required content changes:** Replace PropTech survey coverage with an operating model spanning acquisition, financing, leasing, development, and property management. Add a decision case on asset class selection, occupancy risk, or software workflow changes in brokerage or operations.

### `industry-supplychain`

- **Capstone role:** Apply economics and engineering concepts to sourcing, fulfillment, logistics, and systems-design trade-offs.
- **Prerequisite path:** `26-economics-guide`, `35-engineering-guide`
- **Programs served:** `ai-for-operators`, `industry-transition`
- **Required content changes:** Replace supply-chain-tech landscape sections with an end-to-end operating model from planning through last-mile execution. Add a decision case on inventory strategy, network design, automation, or resilience-versus-efficiency trade-offs.

## Shared rewrite checklist

Every capstone conversion should make these structural changes:

- remove the generic technology-stack and landscape-tour sections unless they directly support a decision
- replace glossary-heavy endings with a concrete decision case or capstone exercise
- state the prerequisite guide path up front so the module is clearly not beginner-first
- name the target programs the module serves
- add explicit next-step connections back into the core curriculum and sideways into adjacent industries where useful
- frame the learner task as sector transfer and judgment, not encyclopedic industry coverage

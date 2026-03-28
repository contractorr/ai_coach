# Curriculum Program Map

This document operationalizes issue `#175` by taking the six manifest-backed programs and
mapping the current guide corpus onto them. The goal is not to force every guide into a
single-path bootcamp. It is to make the corpus legible for mid-career learners who need
clear outcomes, cleaner sequencing, and faster transfer into work.

## Program roles

Use four program roles when placing guides:

- `core`: required path material for the program outcome
- `shared foundation`: reusable guide that anchors multiple programs
- `supporting elective`: optional depth that sharpens a program for a specific context
- `applied module`: industry or domain capstone that converts theory into sector fluency

## Program definitions

The six primary programs are already defined in `content/curriculum/skill_tree.yaml`:

1. `business-acumen`
2. `ai-for-operators`
3. `decision-quality`
4. `policy-regulation`
5. `industry-transition`
6. `strategy-investing`

The mapping below extends those manifest definitions to the rest of the corpus.

## Corpus mapping

### Shared foundations

| Guide | Primary home | Secondary programs | Role | Why it belongs |
| --- | --- | --- | --- | --- |
| `01-philosophy-guide` | `decision-quality` | `policy-regulation`, `strategy-investing` | shared foundation | Clarifies argument quality, assumptions, and normative trade-offs. |
| `02-epistemology-decision-theory-guide` | `decision-quality` | `ai-for-operators`, `strategy-investing` | core | Best base for probabilistic judgment, causality, and forecasting. |
| `03-mathematics-pure-applied-guide` | `decision-quality` | `ai-for-operators` | shared foundation | Quantitative prerequisite for statistics, algorithms, and model-based thinking. |
| `04-statistics-probability-guide` | `decision-quality` | `ai-for-operators`, `industry-transition`, `strategy-investing` | shared foundation | Required for uncertainty, experimentation, risk, and model evaluation. |
| `08-information-theory-complex-systems-guide` | `ai-for-operators` | `decision-quality`, `strategy-investing` | supporting elective | Adds systems thinking, scaling intuition, and network effects. |
| `16-cognitive-neuroscience-guide` | `decision-quality` | `ai-for-operators`, `industry-transition` | supporting elective | Useful bridge from biological cognition to behavioral and AI reasoning. |
| `18-behavioral-psychology-guide` | `decision-quality` | `business-acumen`, `strategy-investing` | core | Directly improves decision hygiene, persuasion, and organizational judgment. |
| `19-linguistics-language-guide` | `ai-for-operators` | `decision-quality` | supporting elective | Strongest fit is language, semantics, and communication transfer into AI/NLP use cases. |
| `20-history-of-science-guide` | `decision-quality` | `ai-for-operators`, `strategy-investing` | supporting elective | Helps learners reason about paradigm shifts, evidence, and model replacement. |

### Business and market stack

| Guide | Primary home | Secondary programs | Role | Why it belongs |
| --- | --- | --- | --- | --- |
| `26-economics-guide` | `business-acumen` | `industry-transition`, `strategy-investing` | core | Shared commercial foundation for incentives, markets, and trade-offs. |
| `27-economic-history-guide` | `strategy-investing` | `policy-regulation`, `business-acumen` | core | Gives cycle, regime, and institutional context for long-horizon judgment. |
| `28-accounting` | `business-acumen` | `industry-transition` | core | Fastest route to reading performance, cash flow, and operating reality. |
| `29-personal-finance-guide` | `business-acumen` | `strategy-investing` | supporting elective | Valuable, but not a primary mid-career program anchor. |
| `30-mba-curriculum` | `business-acumen` | `ai-for-operators`, `industry-transition`, `strategy-investing` | core | Shared management layer that turns theory into cross-functional operating judgment. |
| `31-private-markets-curriculum` | `strategy-investing` | `business-acumen` | core | Advanced capital allocation and investment-judgment path. |
| `34-game-theory-strategic-interaction-guide` | `decision-quality` | `business-acumen`, `policy-regulation`, `strategy-investing` | shared foundation | Strong complement to negotiation, competition, policy, and market strategy. |

### Policy, institutions, and civilization context

| Guide | Primary home | Secondary programs | Role | Why it belongs |
| --- | --- | --- | --- | --- |
| `21-religion-comparative-theology-guide` | `policy-regulation` | `industry-transition`, `strategy-investing` | supporting elective | Cultural and institutional context for sectors and regions where belief systems matter. |
| `22-world-history-civilizational-dynamics-guide` | `policy-regulation` | `strategy-investing` | supporting elective | Broad background for state capacity, conflict, and institutional path dependence. |
| `23-sociology-institutional-design-guide` | `policy-regulation` | `decision-quality`, `industry-transition` | core | Best starting point for institutions, incentives, collective action, and organizational design. |
| `24-government-politics-guide` | `policy-regulation` | `strategy-investing`, `industry-transition` | core | Core machinery of political systems and state decision-making. |
| `25-law-legal-systems-guide` | `policy-regulation` | `industry-transition`, `strategy-investing` | core | Required for contracts, regulation, enforcement, and legal exposure. |
| `34-demography-urbanization-infrastructure-guide` | `strategy-investing` | `policy-regulation`, `industry-transition` | supporting elective | Useful for long-range market sizing, migration, infrastructure, and urban systems. |
| `35-geopolitics-guide` | `policy-regulation` | `strategy-investing` | core | Shared capstone for external constraints, state rivalry, and global operating risk. |

### Technology and operator tooling

| Guide | Primary home | Secondary programs | Role | Why it belongs |
| --- | --- | --- | --- | --- |
| `36-computer-science-algorithms-guide` | `ai-for-operators` | `industry-transition` | core | Technical grounding for systems, architectures, and computational limits. |
| `37-ai-ml-fundamentals-guide` | `ai-for-operators` | `strategy-investing` | core | Central guide for model categories, training, limitations, and deployment trade-offs. |
| `38-cybersecurity-guide` | `ai-for-operators` | `policy-regulation`, `industry-transition` | core | Critical risk and controls layer for any production AI or digital operations program. |

### Science and sector depth

| Guide | Primary home | Secondary programs | Role | Why it belongs |
| --- | --- | --- | --- | --- |
| `06-physics-fundamentals-guide` | `industry-transition` | `strategy-investing` | supporting elective | Foundation for engineering, energy, and industrial sectors. |
| `07-chemistry-biochemistry-guide` | `industry-transition` | `strategy-investing` | supporting elective | Base layer for biotech, materials, agriculture, and healthcare sectors. |
| `09-geology-earth-science-guide` | `industry-transition` | `strategy-investing`, `policy-regulation` | supporting elective | Useful for energy, mining, infrastructure, and climate-linked sector work. |
| `10-oceanography-marine-systems-guide` | `industry-transition` | `strategy-investing`, `policy-regulation` | supporting elective | Relevant to maritime trade, fisheries, defense, and climate adaptation contexts. |
| `11-energy-materials-guide` | `strategy-investing` | `industry-transition`, `policy-regulation` | supporting elective | Strongest sector-diligence guide for energy, semiconductors, and industrial bottlenecks. |
| `12-climate-earth-systems-guide` | `policy-regulation` | `strategy-investing`, `industry-transition` | supporting elective | Climate constraints increasingly shape regulation, infrastructure, and capital allocation. |
| `13-evolutionary-biology-guide` | `industry-transition` | `strategy-investing` | supporting elective | Prerequisite layer for biotech, healthcare, and agriculture depth. |
| `14-genetics-biotech-guide` | `industry-transition` | `strategy-investing`, `policy-regulation` | supporting elective | Sector-relevant depth for biotech operators and investors. |
| `15-ecology-biodiversity-guide` | `policy-regulation` | `industry-transition`, `strategy-investing` | supporting elective | Best fit where environmental regulation, land use, and sustainability matter. |
| `17-medicine-human-physiology-guide` | `industry-transition` | `policy-regulation`, `strategy-investing` | supporting elective | Core science bridge for healthcare and health-policy transitions. |
| `33-agriculture-food-systems-guide` | `industry-transition` | `policy-regulation`, `strategy-investing` | supporting elective | Strong domain pack for agriculture, food security, and supply system transitions. |
| `35-engineering-guide` | `industry-transition` | `strategy-investing` | supporting elective | Applied systems lens for construction, manufacturing, infrastructure, and operations. |

### Industry capstones

| Guide | Primary home | Secondary programs | Role | Why it belongs |
| --- | --- | --- | --- | --- |
| `industry-accounting` | `business-acumen` | `industry-transition` | applied module | Converts accounting basics into function-specific workflows. |
| `industry-construction` | `industry-transition` | `strategy-investing` | applied module | Uses engineering and business basics in an asset-heavy operating sector. |
| `industry-energy` | `strategy-investing` | `industry-transition`, `policy-regulation` | applied module | Best sector capstone for regulation-heavy infrastructure and commodity exposure. |
| `industry-financialservices` | `strategy-investing` | `business-acumen`, `industry-transition` | applied module | Strong bridge from business core into capital markets and financial intermediation. |
| `industry-government` | `policy-regulation` | `ai-for-operators`, `industry-transition` | applied module | Connects institutional constraints to public-sector execution and govtech. |
| `industry-healthcare` | `industry-transition` | `policy-regulation`, `ai-for-operators` | applied module | Good capstone for regulated operations, care delivery, and healthcare workflows. |
| `industry-hr` | `industry-transition` | `business-acumen` | applied module | Practical transfer point for org design, incentives, and people operations. |
| `industry-insurance` | `policy-regulation` | `decision-quality`, `industry-transition` | applied module | Strong fit for probabilistic reasoning, regulation, and risk pricing. |
| `industry-legal` | `policy-regulation` | `decision-quality`, `industry-transition` | applied module | Direct translation layer for legal process, client work, and regulated decisions. |
| `industry-realestate` | `strategy-investing` | `business-acumen`, `industry-transition` | applied module | Converts economics, accounting, and capital-allocation judgment into a tangible asset class. |
| `industry-supplychain` | `industry-transition` | `ai-for-operators` | applied module | Strong transfer surface for process design, forecasting, and operational AI. |

## Recommended program sequencing

These are the default entry paths for the six programs.

### Business Acumen

`28-accounting` -> `26-economics-guide` -> `30-mba-curriculum` -> selected applied module

Recommended electives: `34-game-theory-strategic-interaction-guide`, `29-personal-finance-guide`

### AI for Operators

`30-mba-curriculum` -> `36-computer-science-algorithms-guide` + `04-statistics-probability-guide`
-> `37-ai-ml-fundamentals-guide` -> `38-cybersecurity-guide` -> selected applied module

Recommended electives: `08-information-theory-complex-systems-guide`, `19-linguistics-language-guide`

### Decision Quality

`01-philosophy-guide` -> `02-epistemology-decision-theory-guide`
-> `03-mathematics-pure-applied-guide` + `04-statistics-probability-guide`
-> `34-game-theory-strategic-interaction-guide` -> `18-behavioral-psychology-guide`

Recommended electives: `16-cognitive-neuroscience-guide`, `20-history-of-science-guide`

### Policy & Regulation

`23-sociology-institutional-design-guide` -> `24-government-politics-guide`
-> `25-law-legal-systems-guide` -> `35-geopolitics-guide` -> selected applied module

Recommended electives: `22-world-history-civilizational-dynamics-guide`,
`34-demography-urbanization-infrastructure-guide`, `12-climate-earth-systems-guide`

### Industry Transition

`28-accounting` -> `26-economics-guide` -> `30-mba-curriculum`
-> sector science/domain pack -> selected applied module

Typical sector packs:

- healthcare: `17-medicine-human-physiology-guide`, `14-genetics-biotech-guide`
- energy / infrastructure: `11-energy-materials-guide`, `12-climate-earth-systems-guide`, `35-engineering-guide`
- supply chain / industrials: `35-engineering-guide`, `34-demography-urbanization-infrastructure-guide`
- agriculture / food: `33-agriculture-food-systems-guide`, `15-ecology-biodiversity-guide`

### Strategy / Investing

`26-economics-guide` -> `27-economic-history-guide` -> `30-mba-curriculum`
-> `35-geopolitics-guide` + `34-game-theory-strategic-interaction-guide`
-> `31-private-markets-curriculum` -> selected sector elective or applied module

Recommended electives: `11-energy-materials-guide`,
`34-demography-urbanization-infrastructure-guide`, `industry-financialservices`

## Gaps and sequencing problems

### Major gaps

1. `28-accounting` is still a one-file bottleneck even though it is a hard prerequisite for
   both `business-acumen` and `industry-transition`. The program architecture assumes a stronger
   business core than the current corpus actually provides.
2. `ai-for-operators` has a gap between technical understanding and operating deployment. The
   current path jumps from algorithms / ML / security into industry modules without a dedicated
   layer for data products, process redesign, measurement, and change management.
3. `policy-regulation` relies heavily on `24-government-politics-guide`, which is thin relative
   to how much downstream load it carries into law, geopolitics, and government-industry modules.
4. `industry-transition` lacks explicit bridge guides from the shared business core into sector
   domain packs. The science-heavy guides exist, but the transfer path into "what this means in
   the industry" is still mostly implicit.
5. `strategy-investing` is strong on domain inputs but lighter on synthesis artifacts. There is
   no single guide that explicitly teaches thesis formation, diligence structure, or portfolio
   decision-making before learners hit `31-private-markets-curriculum`.

### Major redundancies

1. `02-epistemology-decision-theory-guide` and `18-behavioral-psychology-guide` both cover bias,
   judgment failure, and decision quality. The overlap is useful, but the handoff should be
   cleaner: epistemology for reasoning frameworks, behavioral psychology for human failure modes.
2. `30-mba-curriculum` overlaps with multiple industry crash courses on strategy, operations,
   communication, and finance. The MBA guide should own the generalist operating playbook while
   industry guides stay sector-specific.
3. `35-geopolitics-guide`, `22-world-history-civilizational-dynamics-guide`, and
   `27-economic-history-guide` all cover regime shifts and long-range context. They need clearer
   boundaries so learners understand when they are learning historical pattern recognition versus
   live operating constraints.
4. `37-ai-ml-fundamentals-guide` and `30-mba-curriculum/08-ethics-ai-crash-course.md` both touch
   AI risk, governance, and deployment judgment. One should own technical limitations while the
   other owns executive decision framing.

## Recommended next follow-on work

1. Keep the six programs in manifest data as the learner-facing top layer.
2. Turn this mapping into product metadata only after the roles (`core`, `shared foundation`,
   `supporting elective`, `applied module`) are stabilized.
3. Prioritize rewrites that unblock multiple programs at once: `28-accounting`,
   `24-government-politics-guide`, and the industry-transition bridge material.

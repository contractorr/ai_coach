# Curriculum Redesign Roadmap

This document is the first-pass design and rewrite plan for the Learn curriculum after the
transition toward mid-career programs.

## Program architecture

The curriculum should be presented as a small set of outcome-based programs for busy
professionals. Guides remain reusable building blocks, but the primary framing shifts from
"topic coverage" to "what capability this unlocks at work."

### 1. Business Acumen

- Outcome: Read a business clearly enough to reason about unit economics, incentives, and trade-offs.
- Core guides: `28-accounting`, `26-economics-guide`, `30-mba-curriculum`
- Applied modules: `industry-accounting`, `industry-financialservices`, `industry-realestate`

### 2. AI for Operators

- Outcome: Scope, evaluate, and deploy AI use cases without magical thinking.
- Core guides: `30-mba-curriculum`, `36-computer-science-algorithms-guide`, `37-ai-ml-fundamentals-guide`, `38-cybersecurity-guide`
- Applied modules: `industry-government`, `industry-healthcare`, `industry-supplychain`

### 3. Decision Quality

- Outcome: Make better repeated decisions under uncertainty and strategic interaction.
- Core guides: `01-philosophy-guide`, `02-epistemology-decision-theory-guide`, `03-mathematics-pure-applied-guide`, `04-statistics-probability-guide`, `34-game-theory-strategic-interaction-guide`, `18-behavioral-psychology-guide`
- Applied modules: `industry-insurance`, `industry-legal`

### 4. Policy & Regulation

- Outcome: Understand institutional, legal, and geopolitical constraints before they become execution surprises.
- Core guides: `23-sociology-institutional-design-guide`, `24-government-politics-guide`, `25-law-legal-systems-guide`, `35-geopolitics-guide`
- Applied modules: `industry-government`, `industry-legal`, `industry-insurance`

### 5. Industry Transition

- Outcome: Ramp into a new sector through one shared business core plus an applied capstone.
- Core guides: `26-economics-guide`, `28-accounting`, `30-mba-curriculum`
- Applied modules: all `industry-*` guides, selected based on the target sector

### 6. Strategy / Investing

- Outcome: Form stronger strategic and investment judgments about sectors, firms, and long-horizon bets.
- Core guides: `26-economics-guide`, `27-economic-history-guide`, `30-mba-curriculum`, `31-private-markets-curriculum`, `35-geopolitics-guide`
- Applied modules: `industry-energy`, `industry-financialservices`, `industry-realestate`

## Standard chapter template

Every rewrite should use the standard mid-career chapter shape:

1. Executive summary
2. Why this is worth understanding (optional)
3. Core model/framework
4. Worked example
5. Failure modes
6. Checkpoint
7. Next-step connections

The relevance section is optional and should not be narrowly workplace-framed by default. Use it
when it helps the learner understand why the chapter matters, whether that case is practical,
conceptual, historical, or aesthetic.

Reference template: `docs/templates/curriculum-chapter-template.mdx`

## Thin-guide audit

### Method

- Chapter count is the fastest signal for obviously thin guides.
- Total word count is the next signal for underdeveloped multi-chapter guides.
- Dependency leverage matters: thin guides that unlock many downstream guides should be rewritten first.
- Program leverage matters: guides used by multiple named programs should move up even when raw thinness is similar.
- Superseded aliases (`05-game-theory...`, `32-engineering...`) are not rewrite targets; they are already canonicalization cleanup items.
- One-file industry guides are treated as capstone modules, not first-wave deep rewrites.

### Explicit rewrite scoring

The audit command now makes the ranking implementable with a fixed score:

- `+60` if the guide is a single-file guide
- `+(16000 - total_word_count) // 500`, floored at `0`
- `+8` for each downstream dependent guide
- `+4` for each program that includes the guide

Tie-breakers:

1. Lower chapter count
2. Lower total word count
3. Guide id alphabetically for stability

This keeps the rewrite queue reproducible instead of editorially hand-wavy.

### Immediate capstone conversions

All current industry guides are one-file modules around roughly 1.6k-2.0k words. They should be
reframed as capstones/applied modules, not standalone destinations:

- `industry-accounting`
- `industry-construction`
- `industry-energy`
- `industry-financialservices`
- `industry-government`
- `industry-healthcare`
- `industry-hr`
- `industry-insurance`
- `industry-legal`
- `industry-realestate`
- `industry-supplychain`

Recommended capstone shape:

1. Sector brief
2. Value creation and capture
3. Core workflow / operating model
4. Important metrics, constraints, and regulation
5. Decision case
6. Next-step connections

## Rewrite priority ranking

Current audit snapshot on 2026-03-28:

### Tier 1: highest leverage

1. `28-accounting`
Reason: score `114`; one-file guide, only 4,952 words, unlocks 3 downstream guides, and appears in 2 programs. This is the biggest business-program bottleneck.

2. `24-government-politics-guide`
Reason: score `47`; only 6,465 words across 8 chapters while unlocking `25-law-legal-systems-guide`, `35-geopolitics-guide`, and `industry-government`.

3. `13-evolutionary-biology-guide`
Reason: score `39`; only 8,239 words while unlocking `14-genetics-biotech-guide`, `15-ecology-biodiversity-guide`, and `33-agriculture-food-systems-guide`.

4. `16-cognitive-neuroscience-guide`
Reason: score `29`; only 9,301 words while serving as the scientific base for `18-behavioral-psychology-guide`.

### Tier 2: strategic but lower dependency leverage

5. `15-ecology-biodiversity-guide`
Reason: score `13`; 13,111 words and still a real prerequisite inside the biology-to-agriculture branch.

6. `18-behavioral-psychology-guide`
Reason: score `12`; barely under the thin-guide threshold at 15,694 words, but it still unlocks a downstream guide and sits inside the `decision-quality` program.

7. `12-climate-earth-systems-guide`
Reason: score `9`; thin relative to importance at 11,325 words, but without the dependency leverage of the higher-ranked guides.

8. `20-history-of-science-guide`
Reason: score `8`; 15,629 words and some downstream leverage, but weaker than the guides above.

9. `14-genetics-biotech-guide`
Reason: score `0`; 15,725 words and no current dependency or program bonus, so it is the lowest-priority core thin-guide rewrite.

### Capstone conversion queue

All `industry-*` guides
Reason: do not expand these into pseudo-textbooks first. Convert them into consistent capstones, then deepen only the highest-demand sectors.

### Not a thin-guide rewrite target

`31-private-markets-curriculum`
Reason: not thin; this is a later harmonization pass to align chapter shape, not a rewrite-priority problem.

## Recommended sequence

### Phase 1

- Lock the six mid-career programs in manifest data.
- Standardize authoring around the chapter template.
- Rewrite `28-accounting`.
- Convert all industry guides to explicit capstone positioning.

### Phase 2

- Rewrite `24-government-politics-guide`, `13-evolutionary-biology-guide`, and `16-cognitive-neuroscience-guide`.
- Backfill next-step connections so the programs feel intentional rather than merely grouped.

### Phase 3

- Rewrite the Tier 2 science/history guides.
- Expand the strongest industry capstones into multi-part applied modules only after demand is clear.

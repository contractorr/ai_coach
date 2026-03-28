# Curriculum Redesign Roadmap

This document defines the default chapter template and the first rewrite queue for obviously thin
guides.

## Standard chapter template

Every rewrite should use the standard chapter shape:

1. Executive summary
2. Why this is worth understanding (optional)
3. Core model/framework
4. Worked example
5. Failure modes
6. Checkpoint
7. Next-step connections

The relevance section is optional and should not be narrowly workplace-framed by default. Use it
when it sharpens the chapter's motivation, whether that case is practical, conceptual, historical,
or aesthetic.

Reference template: `docs/templates/curriculum-chapter-template.mdx`

## Weak chapter patterns to rewrite away from

- Survey-dump chapters that enumerate facts without one governing model.
- Chapters with no worked example, so the reader never sees how the idea is actually used.
- Chapters that end without a checkpoint, which makes application invisible.
- Chapters whose only motivation is generic workplace relevance, even when the subject deserves broader framing.
- Single-file guides pretending to be complete domains when they are really placeholders for future depth.

## Thin-guide audit

### Method

- Chapter count is the fastest signal for obviously thin guides.
- Total word count is the next signal for underdeveloped multi-chapter guides.
- Dependency leverage matters: thin guides that unlock many downstream guides should be rewritten first.
- Superseded aliases are not rewrite targets even if they look thin; they are cleanup items.
- One-file industry guides are treated as capstone modules, not first-wave deep rewrites.

### Explicit rewrite scoring

Use this scoring rubric for the core rewrite queue:

- `+60` if the guide is a single-file guide
- `+(16000 - total_word_count) // 500`, floored at `0`
- `+8` for each downstream dependent guide

Tie-breakers:

1. Lower chapter count
2. Lower total word count
3. Guide id alphabetically for stability

## Rewrite priority ranking

Current audit snapshot on 2026-03-28:

1. `28-accounting`
Reason: score `106`; one-file guide, only 4,952 words, and unlocks 3 downstream guides.

2. `24-government-politics-guide`
Reason: score `43`; only 6,465 words across 8 chapters while unlocking `25-law-legal-systems-guide`, `35-geopolitics-guide`, and `industry-government`.

3. `13-evolutionary-biology-guide`
Reason: score `39`; only 8,239 words while unlocking `14-genetics-biotech-guide`, `15-ecology-biodiversity-guide`, and `33-agriculture-food-systems-guide`.

4. `16-cognitive-neuroscience-guide`
Reason: score `29`; only 9,301 words while serving as the scientific base for `18-behavioral-psychology-guide`.

5. `15-ecology-biodiversity-guide`
Reason: score `13`; 13,111 words and still a real prerequisite inside the biology-to-agriculture branch.

6. `12-climate-earth-systems-guide`
Reason: score `9`; thin relative to importance at 11,325 words, but with less dependency leverage than the guides above.

7. `20-history-of-science-guide`
Reason: score `8`; 15,629 words and one downstream dependent, which edges it ahead of the next guide on the tie-breaker.

8. `18-behavioral-psychology-guide`
Reason: score `8`; barely under the thin-guide threshold at 15,694 words and still foundational for later work.

9. `14-genetics-biotech-guide`
Reason: score `0`; 15,725 words and no current dependency bonus, so it is the lowest-priority core thin-guide rewrite.

### Excluded from the core rewrite queue

- `32-engineering-guide`: thin, but a superseded alias rather than the canonical engineering guide.
- `05-game-theory-strategic-interaction-guide`: thin, but a superseded alias rather than the canonical game theory guide.

### Capstone conversion queue

All `industry-*` guides should be converted into explicit applied modules before any attempt to
deepen them into pseudo-textbooks.

Detailed capstone roles, prerequisite paths, and rewrite scope for the current industry modules
live in `docs/curriculum-industry-capstones.md`.

## Recommended sequence

### Phase 1

- Standardize authoring around the chapter template.
- Rewrite `28-accounting`.
- Convert industry guides to explicit capstone positioning.

### Phase 2

- Rewrite `24-government-politics-guide`, `13-evolutionary-biology-guide`, and `16-cognitive-neuroscience-guide`.
- Backfill next-step connections so the rewrite wave feels intentional rather than isolated.

### Phase 3

- Rewrite the lower-priority thin guides.
- Expand the strongest industry capstones only after there is evidence of demand.

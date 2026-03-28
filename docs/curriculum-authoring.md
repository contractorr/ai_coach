# Curriculum Authoring

Curriculum chapters now support a schema-first authoring format based on `MDX + frontmatter`.
Rewrites should converge on a shared chapter contract so they feel consistent instead of
editorially improvised. The target reader is increasingly a mid-career operator, not a
full-time student, but the content should justify itself broadly rather than assuming every
topic only matters through workplace utility.

## Chapter format

Every chapter should live in a guide directory as `NN-topic.mdx` and start with frontmatter:

```mdx
---
schema_version: 1
title: Introduction to Philosophy
summary: A short paragraph describing the chapter.
objectives:
  - Identify the central questions philosophy asks.
  - Distinguish major branches of philosophy.
checkpoints:
  - Explain the difference between metaphysics and epistemology.
  - Summarize the historical eras covered in the chapter.
references:
  - curriculum:01-philosophy-guide/02-logic-reasoning
content_format: mdx
---

# Introduction to Philosophy
...
```

The canonical working example lives in `docs/templates/curriculum-chapter-template.mdx`.

## Required frontmatter

- `schema_version`: current schema version. Use `1`.
- `title`: human-readable chapter title.
- `summary`: one short paragraph for indexing, previews, and migration review.
- `objectives`: specific learning outcomes for the chapter.
- `checkpoints`: quick checks that verify the learner can apply the material.

## Standard chapter shape

Every rewrite and net-new chapter should follow the same reader-facing flow:

1. Executive summary
2. Why this is worth understanding (optional)
3. Core model or framework
4. Worked example
5. Failure modes
6. Checkpoint
7. Next-step connections

This is a content contract, not just a formatting suggestion. The frontmatter supports
indexing and tooling; the section shape supports consistent comprehension and applied use.
The relevance section is optional because some topics are worth learning for intrinsic,
conceptual, historical, or aesthetic reasons in addition to workplace transfer.

## Weak chapter patterns to rewrite away from

- Survey-dump chapters that enumerate facts without one governing model.
- Chapters with no worked example, so the reader never sees how the idea is actually used.
- Chapters that end without a checkpoint, which makes application invisible.
- Chapters whose only motivation is generic workplace relevance, even when the subject deserves broader framing.
- Single-file guides pretending to be complete domains when they are really placeholders for future depth.

### Section intent

- **Executive summary**: Give the reader the 60-second version and the key distinction they must retain.
- **Why this is worth understanding (optional)**: Explain why the topic matters. This can point to decisions, trade-offs, and communication failures at work, but it can also justify the chapter through conceptual importance, historical leverage, or intellectual beauty when that framing is stronger.
- **Core model/framework**: Present the durable mental model, not a loose survey.
- **Worked example**: Show the model in action on a realistic business, policy, or operational situation.
- **Failure modes**: Cover the common misreads, edge cases, and ways the model gets abused.
- **Checkpoint**: End with one or more short prompts that force application, not recall alone.
- **Next-step connections**: Link forward into adjacent guides or capstone modules using `curriculum:` references where possible.

### Mid-career writing rules

- Assume high general intelligence but limited uninterrupted study time.
- Prefer executive clarity over textbook completeness.
- Use one core model per section before layering nuance.
- Tie abstract concepts to meetings, decisions, metrics, and stakeholder trade-offs.
- Keep jargon only when it is professionally necessary; define it fast.
- End each chapter with where the learner should go next.

## Optional frontmatter

- `references`: canonical chapter references (for example `curriculum:01-philosophy-guide/02-logic-reasoning`) or relative file paths.
- `content_format`: keep as `mdx` for authored schema files.

## Visual blocks

Chapters can embed typed visual blocks inside fenced code blocks. The curriculum renderer will
prefer these structured blocks over legacy ASCII diagrams, while older markdown still falls back
safely during migration.

Current supported block languages:

- `diagram`
- `process-flow`
- `framework`
- `comparison-table`
- `chart`
- `visual` for JSON payloads that include a `"type"` field explicitly

Use JSON payloads only for now. Keep the schema small, explicit, and readable in source control.

### Example: process flow

````md
```process-flow
{
  "title": "Decision flow",
  "note": "Use this when a learner should follow a sequence.",
  "steps": [
    { "title": "Observe", "detail": "Gather the relevant signals." },
    { "title": "Decide", "detail": "Choose the operating response." },
    { "title": "Act", "detail": "Execute and monitor outcomes." }
  ]
}
```
````

### Example: framework

````md
```framework
{
  "title": "Three-part framework",
  "pillars": [
    {
      "title": "Diagnosis",
      "detail": "Name the actual problem.",
      "bullets": ["Separate symptoms from causes."]
    },
    {
      "title": "Policy",
      "detail": "Choose the governing approach."
    },
    {
      "title": "Actions",
      "detail": "List reinforcing moves."
    }
  ]
}
```
````

### Example: chart

````md
```chart
{
  "title": "Illustrative trend",
  "chartType": "line",
  "xLabel": "Year",
  "yLabel": "Value",
  "series": ["Value"],
  "data": [
    { "Year": "2022", "Value": 10 },
    { "Year": "2023", "Value": 14 },
    { "Year": "2024", "Value": 19 }
  ]
}
```
````

## Applied modules / industry capstones

One-file industry guides should be authored as **applied modules**, not mini-textbooks.
Their job is to help a learner transfer a core program into a sector.

Use this shape for industry modules:

1. Sector brief
2. How value is created and captured
3. Core workflow / operating model
4. Important metrics, constraints, and regulation
5. Decision case or capstone exercise
6. Suggested next guides

Industry modules should stay narrow, practical, and case-oriented. If a sector needs deep
multi-chapter treatment later, that should be a separate dedicated guide rather than accidental
scope creep inside a crash course.

Current capstone roles, prerequisite paths, and conversion scope for the existing industry modules
are documented in `docs/curriculum-industry-capstones.md`.

## Reference conventions

- Prefer `curriculum:<guide-id>/<chapter-stem>` for stable chapter-to-chapter references, for example `curriculum:01-philosophy-guide/02-logic-reasoning`.
- Relative links to `.md` or `.mdx` files are also linted.
- External URLs are ignored by curriculum lint checks.

## Tooling

- Lint the corpus: `coach curriculum lint --path content/curriculum`
- Audit thin guides and applied modules: `coach curriculum audit --path content/curriculum`
- Emit JSON lint output for CI: `coach curriculum lint --format json`
- Generate MDX from the legacy markdown corpus:
  `coach curriculum migrate --source content/curriculum --output tmp/curriculum-mdx`

Lint currently checks:

- broken `curriculum:` references, `/learn/...` links, and relative chapter links
- missing `title`, `summary`, `objectives`, and `checkpoints` frontmatter
- thin non-glossary chapters (warning below 500 body words)
- chapter-order gaps or duplicate numbered chapter paths within a guide
- duplicate chapter titles inside a guide
- `skill_tree.yaml` graph issues such as missing guides, missing prerequisites, duplicate track assignments, missing track assignments, and prerequisite cycles

## Migration notes

- The migration command preserves existing body content and synthesizes frontmatter from current markdown.
- Generated objectives and checkpoints are a starting point, not final editorial copy.
- Lint failures after migration should be treated as authoring follow-up, not ignored.

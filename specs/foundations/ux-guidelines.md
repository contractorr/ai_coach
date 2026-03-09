# UX Guidelines

**Status:** Draft
**Author:** -
**Date:** 2026-03-07

## Purpose

Define shared user-experience rules for StewardMe so workflows across journaling, goals, intelligence, research, and settings feel consistent and intentional.

This document is a cross-cutting foundation spec. It captures product-level UX expectations that should inform all functional and technical specs.

## Product UX Principles

1. **Reduce cognitive overhead** - Users should understand what to do next without decoding the interface.
2. **Support momentum** - Common tasks should require minimal clicks, mode switches, and re-entry.
3. **Make AI legible** - AI-generated suggestions should feel useful, bounded, and inspectable rather than magical.
4. **Preserve user agency** - The product can recommend and prioritize, but the user stays in control.
5. **Reward return visits** - Surfaces should quickly answer: what changed, what matters now, and what needs action.

## Page Structure

Most pages should follow a predictable top-to-bottom structure:

1. Page title and short framing context
2. Primary action or most likely next step
3. Filters, scope controls, or tabs when needed
4. Main content area
5. Secondary details, metadata, or advanced controls

Do not force users to hunt for the core action on each page.

For long-form settings and configuration pages, add two extra safeguards when needed:

- Section jump links near the top to reduce orientation cost
- A persistent save/discard affordance once unsaved changes exist

## Navigation and Orientation

- Each workspace should have a clear purpose and primary job.
- Navigation labels should describe user goals, not internal systems.
- Users should be able to tell where they are, what data they are viewing, and how to get back.
- Cross-links between related work should be explicit, especially between goals, recommendations, research, and journal context.

## Actions and Prioritization

- Prefer one clear primary action per screen or panel.
- Secondary actions should remain available, but visually subordinate.
- Destructive actions should require deliberate intent.
- Batch actions should appear only when users are likely to need them.
- Quick actions are valuable when they preserve flow, such as rating, saving, filtering, or capturing a note inline.
- If a page has many editable sections, the save action should stay accessible without forcing a full-page scroll.

## Lists, Feeds, and Work Queues

- Sort by usefulness or urgency before exhaustiveness.
- Let users narrow noisy collections with search, filters, and lightweight grouping.
- Keep metadata scannable: timestamp, status, source, tags, and next action should be easy to spot.
- Empty results after filtering should offer a reset path.
- Saved or pinned items should behave like a lightweight queue, not a hidden archive.

## Forms and Input

- Ask only for information needed to complete the task.
- Use sensible defaults and examples to reduce hesitation.
- Put validation close to the field and explain how to recover.
- Distinguish optional from required clearly.
- Prefer inline editing for small changes and dedicated forms for more involved workflows.

## AI-Specific UX

- Make it clear when content is generated, inferred, or user-authored.
- Explain why a recommendation or result is being shown when that context helps trust.
- Give users a way to act on AI output: save it, rate it, refine it, dismiss it, or turn it into a next step.
- Avoid presenting low-confidence AI output with the same visual weight as confirmed user data.
- Where helpful, show the source context behind research, recommendations, or summaries.

## Feedback States

### Loading

- Prefer skeletons or optimistic continuity over blank waiting screens.
- Loading states should hint at the shape of incoming content.

### Empty

- Empty states should explain the situation in plain language.
- Whenever possible, include a clear next action.

### Error

- Errors should explain what failed, what the user can do next, and whether data is safe.
- Avoid dead ends; provide retry, reset, or fallback paths.

### Success

- Confirm completed actions briefly and clearly.
- Avoid celebratory friction for routine saves and updates.

## Content and Microcopy

- Use direct, calm, supportive language.
- Prefer concrete labels over product jargon.
- Keep button text action-oriented, such as `Save`, `Continue`, `Retry`, or `Mark complete`.
- Helper text should answer likely user questions, not restate the obvious.
- AI voice should sound useful and grounded, not theatrical.

## Accessibility and Inclusivity

- Core workflows must work with keyboard navigation.
- Instructions should not rely on color, position, or hover alone.
- Time-sensitive or destructive actions should be recoverable where possible.
- Dense information should still remain readable at common zoom levels.
- Touch targets and spacing should stay usable on smaller screens.

## Responsive Behavior

- Preserve task completion on smaller screens rather than mirroring desktop layouts exactly.
- Collapse secondary panels before hiding primary actions.
- Filters and metadata can compress, but users should still be able to understand item priority and state.
- Sheets and dialogs should remain usable without trapping important context unnecessarily.
- Tables should gain horizontal overflow before they clip essential labels or values.

## StewardMe-Specific Heuristics

- Journaling should favor capture speed and later retrieval.
- Goals should favor current status, next steps, and recent movement over archival detail.
- Intelligence should favor triage and follow-up over passive browsing.
- Projects and opportunities should pair tactical execution options with broader ideation, not bury both in chat alone.
- Research should favor synthesis with traceability.
- Settings should favor safety, clarity, and explicit consequences.

## Using This Document

- Reference these guidelines when writing or reviewing feature specs in `specs/functional/`.
- Reference these guidelines when implementing shared UI patterns in `web/`.
- If a feature intentionally breaks a guideline, call it out in the relevant spec and explain why.

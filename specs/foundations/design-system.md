# Design System

**Status:** Draft
**Author:** -
**Date:** 2026-03-07

## Purpose

Define the shared visual and component foundation for StewardMe's web product so new screens feel coherent, trustworthy, and easy to extend.

This document is a cross-cutting foundation spec. It does not replace feature specs in `specs/functional/` or module specs in `specs/technical/`; it sets the design guardrails those specs should follow.

## Scope

- Browser UI in `web/`
- Shared tokens, primitives, and reusable component conventions
- Interaction states that should look and feel consistent across features

## Source of Truth

- Theme tokens live in `web/src/app/globals.css`
- Shared UI primitives are based on `shadcn/ui` and configured in `web/components.json`
- Feature screens may compose these primitives, but should not redefine base tokens ad hoc

## Design Principles

1. **Calm clarity first** - The UI should feel dependable and low-noise, especially for reflection and decision-making workflows.
2. **Operational, not ornamental** - Visual emphasis should support action, prioritization, and comprehension rather than decoration.
3. **Consistent primitives** - Similar interactions should reuse the same components, spacing, labels, and states.
4. **Readable at speed** - Dense views are acceptable, but hierarchy must remain obvious.
5. **Accessible by default** - Keyboard support, visible focus, contrast, and semantic structure are not optional.

## Tokens

### Color roles

The system should use semantic roles instead of hard-coded per-screen colors.

- `background`, `foreground` for app canvas and default text
- `card`, `popover` for elevated surfaces
- `primary` for the main call to action and selected states
- `secondary`, `muted`, `accent` for supporting emphasis
- `destructive`, `success`, `warning`, `info` for stateful feedback
- `border`, `input`, `ring` for structure and focus treatment
- `chart-*` and `sidebar-*` for visualization and navigation contexts

### Radius

- Use the shared radius scale rather than introducing custom one-off rounding.
- Keep surfaces soft and modern, but avoid overly playful shapes.

### Motion

- Motion should clarify state changes, not draw attention to itself.
- Prefer short, subtle transitions for sheets, collapsibles, dialogs, and feedback.
- Respect reduced-motion preferences where supported by the component stack.

## Typography

- Use sentence case for page titles, section titles, button labels, and navigation.
- Favor concise, direct labels over clever wording.
- Reserve stronger weight for hierarchy, not decoration.
- Long-form helper text should explain why something matters, not repeat the label.

## Layout and Spacing

- Use a predictable page rhythm: page title, supporting context, primary actions, filters, then content.
- Prefer whitespace and grouping to divider-heavy layouts.
- Default to a comfortable reading width for reflective or text-heavy screens.
- In data-dense screens, preserve alignment and scanability before adding new visual treatments.

## Components

### Shared primitives

Prefer existing primitives under `web/src/components/ui` before creating a new base component.

Expected shared primitives include:

- Buttons
- Inputs and textareas
- Selects, comboboxes, and filters
- Cards and panels
- Tabs
- Dialogs, sheets, popovers, and tooltips
- Badges, chips, and status indicators
- Tables, lists, and empty states
- Toasts and inline alerts

### Composition rules

- Add app-specific wrappers only when they capture a repeated product pattern.
- Keep base primitives generic; put product logic in feature components.
- Avoid duplicate variants that differ only by spacing or wording.
- If a pattern appears in three or more places, consider promoting it into a shared component.

### Workspace headers

- Use a shared page-header pattern for dashboard workspaces: context or eyebrow, title, short framing copy, then primary actions.
- Header actions should wrap cleanly on smaller screens rather than forcing overflow.
- Header badges should communicate state or scope, not decorative labels.

### Section jump chips

- Use lightweight outline chips for long-form workspace navigation when a page has four or more distinct sections.
- Chips should jump within the page and reduce orientation cost; they should not replace the main sidebar.

### Sticky action bars

- Long settings or configuration flows should use a sticky action bar when save/discard controls would otherwise sit below the fold.
- Sticky bars should summarize pending changes and keep the primary save action obvious.
- Use sticky bars sparingly; reserve them for workflows where users edit multiple sections before committing.

## State Patterns

Every reusable surface should account for the following states where relevant:

- Default
- Hover
- Focus-visible
- Active or selected
- Disabled
- Loading
- Empty
- Error
- Success or confirmed

State styling should remain recognizable across screens. A destructive action should feel destructive everywhere; a loading placeholder should feel related to the content it replaces.

## Accessibility Baseline

- Interactive controls must be keyboard reachable.
- Focus indicators must remain visible on all actionable elements.
- Color alone should not carry essential meaning.
- Icon-only actions must have accessible names.
- Form controls need explicit labels or equivalent accessible labeling.
- Status changes should be announced appropriately when using toasts, inline alerts, or async updates.

## StewardMe Product Patterns

The product has a few recurring interaction families that should stay visually aligned:

- **Workspace pages**: dashboard, journal, goals, intel, settings
- **Opportunity workspaces**: a tactical list plus a strategic side rail, as used in projects/opportunities
- **AI result surfaces**: recommendations, summaries, suggested actions, research outputs
- **Triage surfaces**: feeds, queues, saved items, filters, search results
- **Capture surfaces**: forms, note creation, follow-up entry, ratings, check-ins

Each family may have different density, but should still share the same visual language for actions, states, and feedback.

## Governance

- When introducing a new shared token or component variant, update this doc and the code in the same change.
- When a feature needs an exception, document the reason in the related feature or technical spec.
- If the system evolves substantially, this document should graduate from `Draft` to `Ready for Review` and then `Approved`.

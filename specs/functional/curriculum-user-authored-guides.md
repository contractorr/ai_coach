# User-Authored Curriculum Guides

**Status:** Deferred
**Date:** 2026-03-29

## Decision

User-authored guide generation is deferred while the core learning experience is simplified.

The current product direction for Learn is to make learning feel minimalist and intuitive. That
means the primary workflow should stay focused on:

- choosing a guide
- reading chapters
- completing lightweight reviews

Custom guide creation, guide extension, and guide archival introduce extra concepts, extra states,
and extra UI surface area before the core loop is simple enough.

## Why Deferred

- It adds creation flows before the browse-and-study flow is fully clear.
- It introduces ownership concepts (`built-in`, `user`, `extension`) that are not necessary for the
  default learning experience.
- It makes the Learn landing page more complex by adding separate sections and dialogs.
- It pushes the product toward a content-generation tool instead of a simple learning workspace.

## Revisit Conditions

This spec should only be reactivated after the simplified learning loop is working well and the
team still sees a strong need for custom content.

Signals that justify revisiting it:

- users consistently finish built-in guides and want adjacent topics not covered by the catalog
- search and browsing are working well, but catalog breadth is the main blocker
- the core learning UI is simple enough that adding creation does not dilute the main path

## Out of Scope For Now

- create guide
- extend guide
- archive and restore custom guides
- user-owned guide sections on the landing page
- mixing generated guides into the default Learn experience

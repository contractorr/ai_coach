# Extraction Receipt

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-08

## Problem

Journaling currently triggers embeddings, memory extraction, and thread detection in the background, but the user has limited visibility into what the system actually learned from a new entry. That creates trust gaps and makes it harder to understand why later advice, recommendations, or dossier suggestions changed.

## Overview

An extraction receipt is a user-visible summary of what the system did with a journal entry after post-create processing completes. It should make extraction transparent without forcing the user into a complex review workflow, and it should connect directly to downstream actions such as viewing a matched thread, creating a goal, running research, or starting a dossier.

## Users

All journaling users. It is especially valuable for new users, trust-sensitive users, and users whose entries often contain goals, blockers, or strategic themes.

## User Stories

- As a user, after I save a journal entry, I want to see what the system extracted so I do not have to guess what changed.
- As a user, I want to understand which extracted items are high-confidence versus tentative.
- As a user, I want to act on a useful extraction immediately by creating a goal, viewing a thread, or starting research.
- As a user, I want a lightweight way to dismiss or correct bad extractions without rewriting my journal entry.

## Dependencies

- Depends on journal post-create processing described in `specs/functional/journaling.md`.
- Depends on memory extraction and thread detection described in `specs/functional/memory-threads.md`.
- Integrates with goals from `specs/functional/goal-tracking.md`, research from `specs/functional/deep-research.md`, and dossiers from `specs/functional/research-dossiers.md`.
- May surface escalation suggestions from `specs/functional/dossier-escalation-engine.md` when that feature exists.
- Current implementation includes a durable extraction-receipt store, post-create receipt finalization, and a receipt read API for journal entries. Follow-up work is mainly richer user-review controls and stronger goal-candidate extraction.

## Detailed Behavior

### Receipt generation

1. User creates a journal entry through the web journal page or a web quick-capture surface.
2. System saves the entry immediately and starts the normal best-effort post-create pipeline.
3. When post-create processing completes, the system generates an extraction receipt for that entry.
4. The receipt appears inline beneath the newly created entry in the journal flow.
5. For quick-capture surfaces, the receipt appears as a non-blocking expandable card or sheet attached to the success state rather than as a modal that interrupts the user.
6. The receipt can be reopened later from the entry detail view through a `View extraction receipt` action.

### Receipt shape

Each receipt is scoped to one journal entry and includes:

- `receipt_id` - stable identifier for the receipt
- `entry_path` - the source journal entry path
- `entry_title` - title shown to the user
- `created_at` - when the receipt was generated
- `status` - `complete`, `partial`, or `failed`
- `themes` - extracted themes with label, confidence, and optional supporting snippet
- `memory_facts` - extracted facts with text, category, confidence, and source link
- `thread_match` - matched thread or newly created thread, including label, thread id, and match type when available
- `goal_candidates` - suggested possible goals with confidence and reason
- `next_steps` - suggested actions such as `view_thread`, `make_goal`, `run_research`, `start_dossier`, or `dismiss`
- `warnings` - plain-language notices when a step produced weak or partial output

The receipt is descriptive rather than a hidden system log. It should only surface user-comprehensible items.

### Confidence handling

1. High-confidence items are shown expanded by default.
2. Low-confidence items are grouped under a `Needs review` or similar secondary section.
3. Low-confidence items do not auto-create downstream artifacts.
4. When all extraction output is weak, the receipt should say so explicitly rather than pretending certainty.
5. If no meaningful extraction is produced, the receipt should still exist and say that no durable themes or facts were confidently identified.

### Review and correction

1. The receipt is not a freeform editor for journal text.
2. Users can dismiss individual themes, goal candidates, or suggested next steps from the receipt.
3. Users can remove incorrect memory facts through the existing memory-management flow linked from the receipt.
4. Users can rename or inspect a matched thread through the thread workspace linked from the receipt.
5. Users can create a goal, run research, or start a dossier directly from receipt actions.

Current interface scope:
- V1 should support dismissing receipt items and launching downstream actions.
- V1 does not require inline editing of memory fact text or inline thread merging.
- If a downstream feature is unavailable, the receipt should show the item but disable the action with explanatory copy.

### Downstream connections

1. If a thread match exists, the receipt links to that thread in the recurring-thread workspace.
2. If goal candidates exist, the receipt can prefill goal creation with title and rationale.
3. If the extracted topic appears strategically important, the receipt can offer `Run research` or `Start dossier` actions.
4. If the user dismisses a receipt item, that dismissal affects the receipt UI but does not rewrite the underlying journal entry.

### Partial and failed processing

1. If embeddings succeed but memory extraction fails, the receipt should still show themes or thread results and mark the receipt `partial`.
2. If all post-create steps fail or time out, the entry save remains successful and the receipt shows `Processing unavailable` rather than blocking the user.
3. The user should never lose the journal entry because receipt generation failed.

## Acceptance Criteria

- [ ] After a journal entry is processed, the user can see a receipt describing what the system extracted.
- [ ] The receipt appears inline for normal journal creation and as a non-blocking attached surface for quick capture.
- [ ] The receipt can be reopened from the journal entry detail view.
- [ ] Receipt output distinguishes between high-confidence and low-confidence items.
- [ ] The receipt can show themes, memory facts, thread matches, goal candidates, and suggested next steps when available.
- [ ] Users can dismiss individual receipt items without editing the original journal entry.
- [ ] Receipt actions can launch downstream flows such as viewing a thread, creating a goal, running research, or starting a dossier.
- [ ] Partial extraction results remain visible even when one post-create step fails.
- [ ] An entry save is never blocked by receipt-generation failure.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Entry produces no strong extraction | Receipt says that no durable themes or facts were confidently identified |
| Only one subsystem succeeds | Receipt shows available output and marks itself partial |
| User writes a very short entry | Receipt may contain no themes or facts without treating that as an error |
| Receipt contains an incorrect memory fact | User can navigate to memory management and delete it |
| Thread routes are unavailable | Receipt can still show that a thread match occurred, but thread-view action is disabled with explanatory copy |
| User closes the receipt immediately | Entry remains saved; receipt is reopenable later from entry detail |

## Success Metrics

- Increase in users opening or revisiting extraction details after entry creation
- Decrease in confusion-driven support or feedback about "what the app learned"
- Increase in downstream conversions from receipts into goals, research runs, or dossiers
- Healthy dismissal rate on low-confidence items without suppressing high-confidence actions

## Out of Scope

- Rewriting the original journal entry based on extracted output
- Inline editing of extracted memory fact text inside the receipt
- Manual thread creation or thread merging from the receipt
- Fully blocking review workflows that force the user to approve every extraction before saving

## Open Questions

- Should quick-capture receipts appear in the home chat stream, a side sheet, or both?
- Should dismissed receipt items feed back into future extraction ranking immediately, or only after enough repeated dismissals?

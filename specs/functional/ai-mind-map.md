# AI-generated Mind Maps from User Journals

**Status:** Draft

## Problem statement

Journal capture is strong at collecting raw context, but weak at helping the user quickly see how ideas, recurring themes, constraints, next steps, and relevant outside evidence connect. Long-form entries are easy to save and hard to synthesize later. Users also build context across Research runs, RSS-fed intelligence, and prior conversations with StewardMe, but that context stays fragmented across surfaces. The product needs a lightweight way to turn journal context into a visual structure that combines the user's own note with the most relevant external and conversational signals without slowing capture or overstating low-confidence AI output.

## Product approach

StewardMe should generate a compact mind map from a journal entry when there is enough signal to form a useful structure. The map should not try to be a perfect knowledge graph. It should give the user a fast visual answer to:

- what this entry is mainly about
- what related themes or constraints it surfaced
- what action or follow-up direction is implied
- whether the note connects to a recurring thread
- what outside research, RSS-fed developments, or previous app discussions reinforce or challenge the note

The updated version should still favor user agency and capture speed by generating maps from the Journal entry detail view, then caching the result per entry. Unlike the first version, the generated map should also augment the entry with matched:

- Research reports and dossier updates
- relevant RSS-derived intelligence items
- prior user-app conversations

Future versions can expand to recent-entry and cross-entry maps once interaction patterns are proven.

## User stories

- As a user, I want to generate a mind map for a journal entry so I can understand the structure of my own thinking faster than rereading the whole note.
- As a user, I want the map to distinguish between my original text and inferred system output so I can trust it appropriately.
- As a user, I want the map to surface likely follow-up areas such as themes, constraints, and next steps without automatically mutating my goals or memory.
- As a user, I want the map to show when my note connects to earlier research, RSS signals, or advisor conversations so I can understand whether this thought is isolated or part of a broader pattern.
- As a user, I want mind maps to feel optional and reversible so AI support does not interfere with journaling flow.

## UX flow

1. User opens a journal entry from the Journal workspace.
2. The entry detail view checks whether a cached mind map already exists for that entry.
3. If a map exists, StewardMe shows a generated summary plus a compact visual graph.
4. If no map exists, StewardMe shows a low-noise empty state with a single primary action: `Generate mind map`.
5. When generation succeeds, the map appears inline beneath the entry content with a short explanation of what the graph represents and which source families were used.
6. If the entry is too short or too low-signal, StewardMe explains that there is not enough structure to map yet instead of forcing a weak diagram.
7. If the user edits the entry later, the cached map is invalidated and can be regenerated from the updated content.
8. If a cached map already exists and relevant research, RSS intel, or conversation context has changed, StewardMe may refresh the cached artifact on read so the user does not have to manually rebuild a stale map.

## AI decision logic

StewardMe should generate a map only when the entry meets at least one of these criteria:

- the entry has enough content to extract multiple distinct concepts
- the entry already produced useful downstream signals such as themes, memory facts, goal candidates, or a recurring thread match
- the user explicitly requests a map from the entry detail view

StewardMe should augment a map with research, RSS intel, or conversation context only when:

- the external source has meaningful lexical or thematic overlap with the entry
- the external signal improves interpretation rather than merely adding noise
- the system can still keep the graph compact and readable

StewardMe should avoid or down-rank generation when:

- the entry is too short to support more than one or two concepts
- the extracted concepts are low-confidence or duplicate the title with no added structure
- the resulting graph would imply certainty that the system does not have
- external context is only weakly related and would make the graph feel magical or cluttered

The generated map should visually center the user-authored entry, then attach AI-derived concepts around it with lower visual emphasis than the entry itself. External context nodes from research, RSS, and conversations should have lower emphasis than direct journal-derived themes or actions.

## Edge cases

| Scenario | Expected behavior |
|---|---|
| Entry is very short | Explain that there is not enough signal yet; do not render a noisy graph |
| Entry has no tags, thread, or memory signals | Fall back to content-only concept extraction if enough structure exists |
| Entry has no relevant external context | Still generate a local-only map if journal signals are strong enough |
| Relevant external context exists but is contradictory or stale | Show it as related context, not confirmed truth |
| User has many past conversations on the same topic | Compress to the strongest one or two conversation signals |
| RSS feeds are noisy but topically adjacent | Require a stronger match threshold before including them |
| Entry was updated after a map was generated | Invalidate the cached map and require regeneration |
| Entry was deleted | Delete the derived map artifact as part of journal cleanup |
| Generated graph has duplicate concepts | Deduplicate labels and keep the strongest source |
| The system finds only one follow-up concept | Prefer an empty-state explanation over a trivial graph |
| Generation fails | Keep the entry readable and offer a retry path |

## Success metrics

- Mind-map generation rate for eligible journal entries
- Mind-map open rate from Journal entry detail
- Regeneration rate after entry edits
- Refresh rate caused by new external context
- Follow-up action rate after viewing a mind map
- User feedback signal on usefulness of the generated map
- Click-through rate on research, intel, or conversation-connected nodes when those affordances are added later
- Reduction in repeated rereads of the same long journal entry before follow-up action

## Non-goals

- Full graph-database modeling of journal knowledge
- Cross-user graph sharing
- Automatic goal creation or memory writes directly from the map
- Dense whiteboard-style editing inside the first version
- Auto-including every matching intelligence item or conversation regardless of signal quality

## Alignment with Product Foundations

### Alignment with `specs/foundations/design-system.md`

- The feature uses calm, low-noise cards and a clear workspace-header hierarchy rather than a decorative visualization-first layout.
- The primary action remains singular and obvious: generate or regenerate the map.
- Generated output is shown inside the existing Journal detail surface using shared card, badge, button, and empty-state patterns.
- Visual emphasis stays operational: the entry is primary, inferred concepts are secondary, and externally sourced nodes are tertiary. Loading or error states follow shared feedback patterns.

### Alignment with `specs/foundations/ux-guidelines.md`

- The feature reduces cognitive overhead by summarizing long-form notes into inspectable structure.
- It preserves momentum because map generation is inline in the existing Journal workflow rather than a separate tool.
- It makes AI legible by labeling generated content, explaining what the map is based on, and distinguishing user-authored context from research, RSS, and conversation-derived augmentation.
- It preserves user agency by making maps optional, on demand, and non-mutating.
- It supports return visits by helping users quickly answer what themes, next steps, and external evidence were present around earlier notes.

**Problem**
Deep research is currently designed as a one-off report that is saved into the journal and intel store. That is useful, but it falls short of a chief-of-staff workflow where important topics need ongoing monitoring, cumulative context, and periodic reassessment.

The spec explicitly says multi-day research that accumulates over time is out of scope, but this is one of the highest-leverage upgrades for making advice feel truly bespoke.

Relevant spec references:
- `specs/functional/deep-research.md`: research auto-selects topics from goals and journal themes, synthesizes multiple sources with citations, and saves reports to journal + intel.
- `specs/functional/deep-research.md`: "Multi-day research that accumulates over time" is currently out of scope.

**Proposed solution**
Introduce persistent research dossiers: long-lived research threads that accumulate new findings over time instead of producing isolated snapshots.

Suggested behavior:
- Let users create a dossier for a topic such as a company, career path, market trend, job search thesis, or technical decision.
- Each dossier stores scope, core questions, assumptions, related goals, and tracked subtopics.
- Scheduled research runs append updates to the dossier instead of creating unrelated reports.
- Each update should include: what changed, why it matters, evidence, confidence, and recommended next actions.
- Show a dossier timeline with source-backed updates, summary deltas, and open questions.
- Allow the advisor to use dossier state directly when answering related questions.

MVP acceptance criteria:
- Users can create and list dossiers.
- Scheduled or manual research can target an existing dossier.
- Dossier updates accumulate over time with citations and timestamps.
- The system can summarize what changed since the last update.
- Dossiers are queryable from the advisor and recommendation engine.

**Alternatives considered**
- Keep storing standalone research reports and rely on search. This loses continuity and makes important topics harder to revisit.
- Auto-merge research reports by title similarity. This is fragile and opaque compared with explicit dossiers.

**Context**
This would turn deep research from a nice feature into an ongoing strategic memory system.

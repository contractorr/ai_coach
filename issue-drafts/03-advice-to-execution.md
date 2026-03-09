**Problem**
The app is already good at generating insights and recommendations, but it still behaves more like an advisor than a chief of staff. Suggestions often stop at "here is what you should do" rather than helping the user translate advice into an actual plan, sequence of tasks, and follow-up loop.

This matters even more because we are not adding intrusive live integrations. Without an execution layer inside the product, recommendations remain easy to ignore.

Relevant spec references:
- `specs/functional/recommendations.md`: recommendations are ranked, scored, and can be rated or dismissed.
- `specs/functional/ask-advice.md`: suggestions unify brief items and recommendations into "things the system suggests I do."
- `specs/functional/goal-tracking.md`: goal tracking exists, but deadline/calendar integration is out of scope.

**Proposed solution**
Add an internal advice-to-execution workflow that turns recommendations into plans, tasks, and review loops without needing external task or calendar integrations.

Suggested behavior:
- Let users convert any recommendation, insight, or research finding into an action plan.
- Generate a lightweight execution artifact with fields such as objective, next step, estimated effort, due window, blockers, and success criteria.
- Support "today / this week / later" prioritization and a small weekly capacity budget.
- Allow users to mark actions as accepted, deferred, blocked, completed, or abandoned.
- At the end of the week, prompt for a quick review so the system learns which advice translated into real outcomes.
- Feed completion and review outcomes back into future recommendation quality, not just ratings.

MVP acceptance criteria:
- Any recommendation can be converted into a tracked action item.
- Action items support status, effort estimate, and review notes.
- The app can assemble a small weekly plan from accepted actions.
- Completed and ignored actions influence future ranking.
- Users can see which recommendations led to execution versus drift.

**Alternatives considered**
- Continue relying only on recommendation ratings. Ratings capture preference, but not whether advice was actually useful in practice.
- Add full project management features. That would be too heavy; a lightweight execution loop is enough for the chief-of-staff use case.

**Context**
This is the highest-impact product change after personalization because it closes the loop from advice to measurable follow-through.

**Problem**
The app already has heartbeat, insights, recommendations, and daily briefs, but most delivery is still pull-based. Users need to remember to open the app and ask for help. That limits the product's ability to feel like a real chief of staff.

We do not want intrusive live integrations, but the app can still be much more proactive about surfacing timely prompts and summaries at the right moment.

Relevant spec references:
- `specs/functional/ask-advice.md`: heartbeat and insights exist, but daily brief is on-demand.
- `specs/functional/ask-advice.md`: push notifications are currently out of scope.
- `specs/functional/recommendations.md`: suggestions unify recommendations and brief items, but not around a stronger delivery cadence.

**Proposed solution**
Add a proactive delivery layer that packages existing intelligence into timely, low-noise nudges and structured briefs without requiring deep third-party integrations.

Suggested behavior:
- Add configurable delivery cadences such as morning brief, weekly review, and urgent alert digest.
- Let users choose channels such as in-app inbox, email digest, or optional browser notifications.
- Introduce priority levels and quiet-hours controls to prevent spam.
- Trigger delivery from existing product signals: stale goals, watchlist matches, dossier updates, overdue action items, and high-confidence recommendations.
- For each item, explain why now, why it matters, and what action is recommended.
- Track opens, deferrals, and follow-through so the system can learn what is actually timely and useful.

MVP acceptance criteria:
- Users can opt into at least one scheduled brief and one urgent-alert threshold.
- Existing insights and recommendations can be routed into a unified inbox/digest.
- Each proactive item includes reason, urgency, and suggested action.
- Users can snooze or mute categories to tune noise.
- Delivery engagement feeds back into prioritization.

**Alternatives considered**
- Keep everything pull-only. This preserves simplicity but caps the product's usefulness as a chief-of-staff tool.
- Add aggressive push notifications first. Better to start with configurable digests and an inbox to keep trust high.

**Context**
This builds on systems that already exist and makes them noticeably more valuable without requiring Outlook, Gmail, or calendar access.

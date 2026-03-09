# Profile & Onboarding

**Status:** Partially Implemented
**Author:** -
**Date:** 2026-03-07

## Problem

The advisor needs to know who the user is - their skills, interests, career stage, goals, and constraints - to give relevant advice. Without a profile, advice quality is generic and onboarding feels cold.

## Users

All users. New users go through onboarding; returning users can update their profile.

## Desired Behavior

### Onboarding (new users)

1. System detects that no profile exists.
2. Web routes the user into onboarding before normal dashboard use.
3. Web onboarding captures the user's preferred display name.
4. User can either add their own key or continue in shared/lite mode.
5. System runs a conversational interview: up to 10 turns in CLI and up to 15 turns in web, with the model aiming for a shorter interview when possible.
6. Questions cover current role, skills and proficiency, interests, career stage, short- and long-term goals, technologies and industries to watch, learning style, weekly hours available, constraints, and active projects.
7. The system extracts structured profile data from the conversation.
8. If extraction fails after normal turns, the system uses a force-extraction fallback.
9. Profile is saved as YAML; web also re-embeds profile context for retrieval.
10. Web onboarding creates initial goal entries from extracted goals.
11. After the interview, web onboarding offers feed-category selection so the user's radar starts with relevant sources.
12. The flow ends with a completion summary that reflects created goals and added feeds.

Current interface scope:
- Shared/lite mode is a real onboarding path in web.
- Lite mode unlocks core chat and journaling but keeps deep research unavailable until the user adds their own key.

### Viewing profile

1. User can inspect profile data at any time.
2. The profile system maintains both:
   - `summary` - a compact paragraph for prompt injection and quick context
   - `structured_summary` - a richer multi-section representation for internal or tool-driven use
3. User can also review individual profile fields directly.

Current interface scope:
- Web settings renders editable structured fields and stale-state badges.
- Web does not currently expose a dedicated summary-vs-structured toggle view.
- Summary text is still available through the profile API for downstream consumers.

### Updating profile

1. User can update individual fields without re-running the full interview.
2. Updates stamp `updated_at`.
3. User can restart onboarding to refresh the profile more holistically.

### Staleness check

1. System marks a profile as stale when it is older than 90 days.
2. Stale state is surfaced as a prompt or badge.
3. The current web product does not force a stale user back through onboarding automatically; it nudges them to refresh.

### Profile fields

- Skills (name plus proficiency 1-5)
- Interests
- Career stage
- Current role
- Aspirations
- Location
- Languages and frameworks
- Learning style
- Weekly hours available
- Goals short-term
- Goals long-term
- Industries watching
- Technologies watching
- Constraints
- Fears and risks
- Active projects

## Acceptance Criteria

- [ ] New users without a profile are prompted to complete onboarding.
- [ ] Web onboarding can continue with either the user's own key or shared/lite mode.
- [ ] Interview extracts profile fields from conversational input.
- [ ] Profile is saved as YAML and loadable across sessions.
- [ ] Web onboarding creates goal entries from extracted goals.
- [ ] Web onboarding includes a feed-category selection step and reports what was added.
- [ ] Skill proficiency is clamped to the 1-5 range.
- [ ] Empty/new profiles construct with sensible defaults.
- [ ] User can update individual fields without re-running full onboarding.
- [ ] Stale profiles surface refresh prompts or badges rather than silently drifting.
- [ ] Web currently presents profile data as editable structured fields rather than a dedicated summary/structured toggle.

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User gives vague or evasive interview answers | Force-extraction fallback kicks in after max turns |
| Proficiency value falls outside 1-5 | Clamped to the valid range |
| User has no skills to report | Empty skills list; advisor still works with lower personalization |
| Profile YAML is corrupted | Fallback to an empty/default profile and log a warning |
| Multiple users in web mode | Each user gets isolated profile and onboarding state |
| User skips adding their own key | Onboarding continues in lite mode |
| Profile is stale but still present | User can continue using the app and is nudged to refresh |

## Out of Scope

- LinkedIn or external-profile import
- Profile sharing between users
- Profile version history
- Admin-managed profile templates

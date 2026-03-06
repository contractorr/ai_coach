# Profile & Onboarding

**Status:** Approved
**Author:** —
**Date:** 2026-03-02

## Problem

The advisor needs to know who the user is — their skills, interests, career stage, goals, and constraints — to give relevant advice. Without a profile, all advice is generic.

## Users

All users. New users go through onboarding; returning users can update their profile.

## Desired Behavior

### Onboarding (new users)

1. System detects no profile exists (or profile is stale >90 days)
2. System starts an interactive interview: LLM asks questions conversationally across up to 10 turns (CLI) or up to 15 turns (web). The LLM is prompted to aim for 5-7 questions
3. Questions cover: current role, skills + proficiency (1-5 scale), interests, career stage, short/long-term goals, technologies/industries watching, learning style, weekly hours available, constraints, active projects
4. LLM extracts structured data from conversational responses
5. If extraction fails after normal turns, system uses a force-extraction fallback
6. Profile is saved as YAML; in web mode, also embedded into ChromaDB for retrieval
7. Web onboarding additionally creates initial goal journal entries from extracted goals

### Viewing profile

1. User can view their profile at any time
2. Two rendering modes:
   - **Summary**: compact one-paragraph description for LLM context injection
   - **Structured**: multi-section breakdown for detailed review

### Updating profile

1. User can update individual fields (e.g., change role, add a skill)
2. Updates stamp `updated_at` timestamp
3. User can re-run the full interview to refresh the entire profile

### Staleness check

1. System checks if profile is >90 days old
2. If stale, prompts user to refresh via interview
3. Check runs on advisor startup and on web profile status endpoint

### Profile fields

- Skills (name + proficiency 1-5)
- Interests (list)
- Career stage (junior / mid / senior / lead / exec)
- Current role
- Aspirations
- Location
- Languages & frameworks
- Learning style (visual / reading / hands-on / mixed)
- Weekly hours available
- Goals short-term (6-month horizon)
- Goals long-term (3-year horizon)
- Industries watching
- Technologies watching
- Constraints (time, geography, budget)
- Fears/risks
- Active projects

## Acceptance Criteria

- [ ] New users without a profile are prompted to complete onboarding
- [ ] Interview extracts all profile fields from conversational input
- [ ] Profile saved as YAML and loadable across sessions
- [ ] Stale profiles (>90 days) trigger a refresh prompt
- [ ] User can view profile in summary or structured format
- [ ] User can update individual fields without re-running full interview
- [ ] Web onboarding creates goal entries from extracted goals
- [ ] Skill proficiency is always 1-5; out-of-range values are clamped
- [ ] Empty/new profile constructs with sensible defaults (career_stage=mid, etc.)

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| User gives vague/evasive interview answers | Force-extraction fallback kicks in after max turns |
| Proficiency value out of 1-5 range | Clamped to [1, 5] |
| User has no skills to report | Empty skills list; advisor works but less personalized |
| Profile YAML is corrupted | Fallback to empty profile; log warning |
| Multiple users in web mode | Each user gets isolated profile under `~/coach/users/{id}/` |

## Out of Scope

- Profile import from LinkedIn or other platforms
- Profile sharing between users
- Profile history / versioning
- Admin-managed profile templates

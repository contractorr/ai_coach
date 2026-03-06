# Learning Paths

**Status:** Approved
**Author:** —
**Date:** 2026-03-02

## Problem

Users know they have skill gaps but struggle to create structured learning plans. They need personalized paths that account for their current level, available time, learning style, and goals.

## Users

Users with a completed profile (especially skills, learning style, and weekly hours). Most useful for users actively trying to level up in specific areas.

## Desired Behavior

### Skill gap detection

1. System sends user's profile context (skills, aspirations) and journal context to the LLM, which identifies gaps
2. Gap detection is LLM-driven from free text, not a programmatic field-by-field comparison
3. Gaps are prioritized by the LLM based on goal relevance and career trajectory

### Path generation

1. For each identified gap (or user-requested topic), system generates a structured learning path
2. Path includes: topic, current level assessment, target level, ordered learning steps, estimated weekly time commitment
3. Steps are calibrated to user's learning style (visual → video resources, reading → articles/books, hands-on → project suggestions)
4. Path respects user's `weekly_hours_available` constraint

### Progress tracking

1. User can check in on learning path progress
2. System tracks which steps are completed
3. Progress updates feed back into skill proficiency estimates

### Viewing

1. User can list all active learning paths
2. User can view a specific path with its steps and progress
3. Paths are stored persistently and survive across sessions

## Acceptance Criteria

- [ ] Skill gaps identified by LLM using profile and journal context
- [ ] Learning paths are personalized to learning style and time constraints
- [ ] Paths include ordered steps with actionable content
- [ ] User can track progress through path steps
- [ ] Available via CLI, web, and MCP
- [ ] Works with partial profile (degrades to generic paths)

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| No skills in profile | Cannot detect gaps; offer generic paths or prompt onboarding |
| No aspirations set | Gaps based on goal requirements only |
| 0 weekly hours available | Path generated but flagged as time-constrained |
| Skill already at level 5 | Not flagged as a gap |
| User requests path for unknown topic | LLM generates best-effort path without gap analysis |

## Out of Scope

- Course enrollment or LMS integration
- Certifications or credential tracking
- Peer learning or study groups
- Content hosting (paths link out, don't host materials)

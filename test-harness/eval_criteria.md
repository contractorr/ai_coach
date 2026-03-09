# Evaluation Criteria

For each session, evaluate and rate (1-5):

## Functionality
- [ ] Login works without errors
- [ ] Journal entry saves and appears in list
- [ ] Advisor responds with relevant advice
- [ ] Intel page loads with recent content
- [ ] No console errors or network failures

## Personalization
- [ ] Advisor references past journal entries (after first session)
- [ ] Recommendations feel relevant to persona's interests
- [ ] Intel shown matches persona's domain

## Adaptation
- [ ] Advice quality improves with more context (compare to first session)
- [ ] System recognizes recurring themes across entries
- [ ] Weekly summary captures actual patterns

## UX
- [ ] Page load times feel reasonable
- [ ] Navigation is intuitive
- [ ] Error states are handled gracefully
- [ ] Empty states (first session) are helpful, not confusing

## Bugs / Issues
- List any errors, broken UI, or unexpected behavior
- Note console errors and network failures
- Screenshot any visual glitches

## Council (Beats 8+)
- [ ] "Council-assisted answer" prefix appears on advisor response when council is enabled
- [ ] Synthesis quality — response incorporates multiple perspectives, not just one model's output
- [ ] Graceful degradation — if one provider key is invalid/missing, advisor still responds (single-model fallback)
- [ ] Keys entered via Settings > LLM Providers persist across sessions

## Memory (Beats 10+)
- [ ] Memory facts appear on the Focus page
- [ ] Advisor references remembered facts in responses (e.g., "you mentioned X previously")
- [ ] Facts are accurate — no hallucinated or misattributed memories
- [ ] Fact list updates after new journal entries / advisor interactions

## Threads (Beats 11+)
- [ ] Recurring themes detected and shown on Focus page
- [ ] Thread descriptions accurately summarize the recurring topic
- [ ] Advisor references active threads when relevant to the question
- [ ] Threads evolve — new entries on the same topic update the thread

## Milestones (Beats 9+)
- [ ] Milestone creation works (via "break this down" or advisor suggestion)
- [ ] Milestones appear under the parent goal on the Focus page
- [ ] Progress bar updates when a milestone is marked complete
- [ ] Milestone descriptions are specific and actionable

## Insights & Suggestions (Beats 12+)
- [ ] Insights populated after 2+ sessions of data
- [ ] Insight descriptions are accurate and non-trivial
- [ ] Suggestions are ranked (brief items first, then remaining recommendations)
- [ ] Suggestions are deduped — no duplicate entries across brief and recommendations

# Functional Spec Index

This index is intentionally small. The canonical machine-readable source of
truth is [specs/catalog.yaml](../catalog.yaml).
Use this file for quick human scanning of the active tracked features.

## Tracked Features

| Feature ID | File | Status | Primary Surface |
| --- | --- | --- | --- |
| `analytics-admin` | [analytics-admin.md](analytics-admin.md) | `stable` | Admin and settings analytics |
| `ask-advice` | [ask-advice.md](ask-advice.md) | `stable` | Home and advisor |
| `curriculum` | [curriculum.md](curriculum.md) | `implemented` | Learn |
| `deep-research` | [deep-research.md](deep-research.md) | `experimental` | Research |
| `goal-tracking` | [goal-tracking.md](goal-tracking.md) | `experimental` | Goals |
| `intelligence-feed` | [intelligence-feed.md](intelligence-feed.md) | `stable` | Radar |
| `journaling` | [journaling.md](journaling.md) | `stable` | Home and Journal |
| `landing-page` | [landing-page.md](landing-page.md) | `stable` | Public root route |
| `library-reports` | [library-reports.md](library-reports.md) | `partially_implemented` | Research library |
| `memory-threads` | [memory-threads.md](memory-threads.md) | `experimental` | Settings and Radar |
| `profile-onboarding` | [profile-onboarding.md](profile-onboarding.md) | `stable` | Onboarding |
| `recommendations` | [recommendations.md](recommendations.md) | `stable` | Home and Goals |
| `research-dossiers` | [research-dossiers.md](research-dossiers.md) | `experimental` | Radar and Research |
| `settings-account` | [settings-account.md](settings-account.md) | `stable` | Settings |

## Supporting Specs

All other active files under `specs/functional/` are supporting specs. They are
still active, but they refine or extend a tracked feature instead of acting as
the first routing target for implementation work.

Check `specs/catalog.yaml` for the complete supporting-spec list and future
archive moves.

# Technical Spec Index

This index is intentionally small. The canonical machine-readable source of
truth is [specs/catalog.yaml](../catalog.yaml).

## Tracked Modules

| Module ID | File | Status | Primary Code Area |
| --- | --- | --- | --- |
| `architecture` | [architecture.md](architecture.md) | `updated` | Cross-repo topology |
| `advisor` | [advisor.md](advisor.md) | `updated` | `src/advisor/` and advisor routes |
| `cli` | [cli.md](cli.md) | `stable` | `src/cli/` |
| `curriculum` | [curriculum.md](curriculum.md) | `stable` | `src/curriculum/` and learn routes |
| `intelligence` | [intelligence.md](intelligence.md) | `updated` | `src/intelligence/` and Radar routes |
| `journal` | [journal.md](journal.md) | `stable` | `src/journal/` and journal routes |
| `library` | [library.md](library.md) | `updated` | `src/library/` and research library routes |
| `llm` | [llm.md](llm.md) | `stable` | `src/llm/` |
| `mcp` | [mcp.md](mcp.md) | `stable` | `src/coach_mcp/` |
| `memory` | [memory.md](memory.md) | `stable` | `src/memory/` and memory routes |
| `profile` | [profile.md](profile.md) | `stable` | `src/profile/` and onboarding/profile routes |
| `research` | [research.md](research.md) | `experimental` | `src/research/` |
| `research-dossiers` | [research-dossiers.md](research-dossiers.md) | `experimental` | dossier storage and escalation |
| `web` | [web.md](web.md) | `updated` | `src/web/` and `web/src/` |

## Supporting Specs

All other active files under `specs/technical/` are supporting specs. They are
still active, but they refine a tracked module or document a specific subsystem
instead of acting as the top-level technical routing point.

Check `specs/catalog.yaml` for the complete supporting-spec list and future
archive moves.

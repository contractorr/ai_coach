# Recurring Thread Inbox

## Overview

Recurring Thread Inbox turns the existing thread-detection subsystem into a first-class web workspace without redefining how threads are detected. The architecture keeps thread detection in `journal` and adds a separate user-state overlay for inbox actions such as dismissing a thread or marking that it already produced a goal, research run, or dossier.

## Dependencies

**Depends on:** `journal` (ThreadDetector + ThreadStore), `web` (thread routes + UI), `research` (run from thread), `goal tracking`, `research dossiers`, `db`
**Depended on by:** `dossier-escalation-engine`, `extraction-receipt` deep links, thread-aware home or suggestion surfaces

---

## Components

### ThreadStore Web Fixes

**Files:** `src/web/deps.py`, `src/web/routes/threads.py`
**Status:** Experimental

#### Behavior

The existing web thread routes are currently miswired because they expect `get_user_paths(user_id)["data_dir"]`, which does not exist. This feature depends on correcting thread route bootstrapping so routes instantiate `ThreadStore` and related services from explicit per-user paths already available in `get_user_paths()`.

Expected path usage:

- `threads_db` from the per-user directory
- `journal_dir` for entry resolution

#### Invariants

- Thread APIs remain fully user-scoped.
- Fixing route wiring must not change thread-detection logic itself.

#### Error Handling

- Missing or corrupt `threads.db` initializes empty state rather than crashing the workspace.

---

### ThreadInboxStateStore

**File:** `src/journal/thread_inbox.py`
**Status:** Experimental

#### Behavior

Stores user workflow state layered on top of detected threads. This state does not change detection membership in `ThreadStore`; it only changes how the thread is surfaced in the inbox.

Suggested schema in the existing per-user `threads.db`:

```sql
CREATE TABLE IF NOT EXISTS thread_inbox_state (
    thread_id TEXT PRIMARY KEY,
    inbox_state TEXT NOT NULL DEFAULT 'active',
    linked_goal_path TEXT,
    linked_dossier_id TEXT,
    last_action TEXT DEFAULT '',
    snoozed_until TEXT,
    updated_at TEXT NOT NULL
);
```

Suggested `inbox_state` values:

- `active`
- `dismissed`
- `goal_created`
- `research_started`
- `dossier_started`
- `dormant`

#### Inputs / Outputs

```python
def get_state(self, thread_id: str) -> dict | None
def upsert_state(self, thread_id: str, *, inbox_state: str, linked_goal_path: str | None = None, linked_dossier_id: str | None = None, last_action: str = "") -> dict
def clear_state(self, thread_id: str) -> bool
```

#### Invariants

- A thread may exist with no inbox-state row; callers should treat that as `active`.
- Dismissing a thread does not delete thread entries or thread membership.
- Inbox state is per-user and per-thread.

#### Error Handling

- Unknown `thread_id` on state update is allowed only if the underlying thread exists; otherwise callers should translate to 404.

---

### ThreadInboxService

**File:** `src/journal/thread_inbox.py`
**Status:** Experimental

#### Behavior

Builds the thread inbox view model from `ThreadStore`, entry previews from `JournalStorage`, and the inbox-state overlay. Eligibility is based on `ThreadStore.get_active_threads(min_entries=2)` so the inbox stays consistent with the existing detection thresholds.

Sort order:

1. active threads first
2. most recent activity descending
3. `updated_at` descending

Each row includes:

- thread metadata
- inbox state
- recent entry snippets (bounded)
- action availability

#### Inputs / Outputs

```python
def list_inbox(self, *, state: str | None = None, query: str = "", limit: int = 50) -> list[dict]
def get_thread_detail(self, thread_id: str) -> dict | None
```

#### Invariants

- Inbox eligibility is never looser than the underlying active-thread definition.
- Search is label- and snippet-based over the loaded thread set; it is not a new semantic search system.

#### Caveats

- `ThreadDetector.reindex_all()` is destructive; if thread IDs are regenerated, inbox-state rows tied to old IDs become stale. V1 should clear inbox-state rows on reindex rather than attempt fuzzy remapping.

---

### Web Routes + Actions

**Files:** `src/web/routes/threads.py`, `src/web/routes/goals.py`, `src/web/routes/research.py`, `src/web/routes/dossiers.py` (or equivalent)
**Status:** Experimental

#### Behavior

Suggested additions:

- `GET /api/threads/inbox`
- `GET /api/threads/{thread_id}`
- `PATCH /api/threads/{thread_id}/state`
- `POST /api/threads/{thread_id}/actions/make-goal`
- `POST /api/threads/{thread_id}/actions/run-research`
- `POST /api/threads/{thread_id}/actions/start-dossier`
- `POST /api/threads/reindex`

The action endpoints call the existing goal, research, and dossier flows with thread-derived defaults, then persist the corresponding inbox-state transition.

#### Invariants

- Thread actions are idempotent at the inbox-state level even when downstream flows create new artifacts.
- Reindex updates thread membership; it is not a cheap metadata refresh.

#### Error Handling

- Unknown thread → 404.
- Downstream action failure returns the downstream error without mutating inbox state.
- Reindex failure returns error and leaves existing thread rows intact when possible.

---

## Cross-Cutting Concerns

### UX foundation alignment

- The inbox page should follow the shared workspace-header, filter, and actionable-card patterns from the design system.
- Thread cards should have one visually primary action and subordinate secondary actions per UX guidelines.

## Test Expectations

- Route wiring tests verifying the current `data_dir` bug is removed.
- `ThreadInboxStateStore`: CRUD, default-state fallback, state validation.
- `ThreadInboxService`: sort order, state filters, recent-snippet inclusion, empty-state behavior.
- Action route tests: goal/research/dossier actions set inbox state only on downstream success.
- Reindex tests: inbox-state reset behavior when thread IDs are rebuilt.
- Mock: `ThreadStore`, `JournalStorage`, goal/research/dossier services, per-user temp dirs.

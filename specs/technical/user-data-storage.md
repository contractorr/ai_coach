# User Data Storage — Technical Reference

## Coach Home Resolution

All runtime data paths MUST be resolved through `storage_paths.get_coach_home()`:

```python
from storage_paths import get_coach_home
base = get_coach_home()  # resolves COACH_HOME env var, falls back to ~/coach
```

Resolution order:
1. `COACH_HOME` env var (if set) — used in production containers
2. `Path.home() / "coach"` — local dev default

**Invariant:** Never hardcode `Path.home() / "coach"` for data paths. In containers where `HOME=/data/coach`, this produces `/data/coach/coach/` (doubled). Always call `get_coach_home()`.

Exception: config file *discovery* (`cli/config.py`, `coach_config.py`) searches multiple candidate paths including `~/coach/config.yaml` and `~/.coach/config.yaml` — this is intentional for backwards compatibility.

## Directory Layout

```
$COACH_HOME/
├── config.yaml              # user config
├── secrets.enc              # legacy CLI encrypted secrets
├── intel.db                 # shared intelligence DB (all users)
├── users.db                 # user accounts + encrypted per-user secrets
├── context_cache.db         # RAG context cache
├── logs/
│   └── weekly_summary.txt
└── users/
    └── {safe_user_id}/      # per-user data directory
        ├── profile.yaml     # user profile (YAML)
        ├── journal/         # markdown entries + ChromaDB embeddings
        ├── recommendations/ # markdown recommendation files
        ├── memory/          # persistent memory facts
        ├── threads/         # conversation threads
        ├── insights/        # generated insights
        ├── library/         # reports + uploads
        └── ...
```

`safe_user_id` converts `google:12345` → `google_12345` (colons replaced with underscores).

## Path TypedDicts

Two `TypedDict` classes enforce key correctness at type-check time:

**`StoragePaths`** (17 keys) — defined in `storage_paths.py`, returned by `_build_paths()`, `get_user_paths()`, `get_single_user_paths()`. Contains all canonical keys: `data_dir`, `journal_dir`, `chroma_dir`, `recommendations_dir`, `profile`, `profile_path`, `memory_db`, `threads_db`, `receipts_db`, `mind_maps_db`, `escalations_db`, `outcomes_db`, `assumptions_db`, `watchlist_path`, `follow_up_path`, `intel_follow_ups_path`, `intel_db`.

**`LegacyPaths`** (4 keys) — defined in `coach_config.py`, returned by `get_paths()`. Contains: `journal_dir`, `chroma_dir`, `intel_db`, `log_file`.

Factory functions in `storage_access.py` accept `PathMap = Mapping[str, Path]` which is compatible with both shapes at runtime. mypy does not recognize TypedDict as Mapping-compatible (known limitation), so these calls produce advisory `arg-type` warnings.

## Per-User Path Resolution

For per-user paths, use `storage_paths.get_user_paths(user_id)` which returns a `StoragePaths` dict of canonical paths. In the web layer, `web.deps.get_user_paths(user_id)` wraps this.

```python
paths = get_user_paths(user_id)
# paths["data_dir"]    → $COACH_HOME/users/{safe_id}/
# paths["profile"]     → $COACH_HOME/users/{safe_id}/profile.yaml
# paths["journal_dir"] → $COACH_HOME/users/{safe_id}/journal/
# paths["intel_db"]    → $COACH_HOME/intel.db (shared)
```

## Account Deletion

`DELETE /api/user/me` performs:
1. DB cleanup: cascading deletes across `user_secrets`, `onboarding_responses`, etc. — removes the entire `users` row.
2. Filesystem cleanup: `shutil.rmtree(get_coach_home() / "users" / safe_user_id(user_id))`

On re-login, `get_or_create_user()` inserts a fresh row with `onboarded=false`, triggering the onboarding gate.

## Onboarding Gate

The `has_profile` field in `GET /api/settings` is backed by the `users.onboarded` DB column (not filesystem state).

- `users.onboarded` defaults to `true` for existing rows (migration) and `false` for new inserts.
- `mark_onboarded(user_id)` is called at onboarding completion (`web/routes/onboarding.py`).
- The frontend gate in `DashboardShell.tsx` redirects to `/onboarding` when `has_profile` is false.

**Why not filesystem?** `get_user_paths()` eagerly creates the data directory via `mkdir(parents=True)`, so directory existence is always true. And `profile.yaml` predates most users — only created by the profile interviewer, not the standard onboarding flow.

## Key Files

| Concern | File |
|---------|------|
| Path resolution | `src/storage_paths.py` |
| Storage factory | `src/storage_access.py` |
| Web dependency injection | `src/web/deps.py` |
| User DB operations | `src/user_state_store.py` |
| Account deletion route | `src/web/routes/user.py` |
| Onboarding gate (frontend) | `web/src/components/DashboardShell.tsx` |
| Onboarding completion | `src/web/routes/onboarding.py` |
| Encrypted secrets (legacy) | `src/crypto_utils.py`, `src/web/crypto.py` |

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

## Per-User Path Resolution

For per-user paths, use `storage_paths.get_user_paths(user_id)` which returns a dict of canonical paths. In the web layer, `web.deps.get_user_paths(user_id)` wraps this.

```python
paths = get_user_paths(user_id)
# paths["data_dir"]    → $COACH_HOME/users/{safe_id}/
# paths["profile"]     → $COACH_HOME/users/{safe_id}/profile.yaml
# paths["journal_dir"] → $COACH_HOME/users/{safe_id}/journal/
# paths["intel_db"]    → $COACH_HOME/intel.db (shared)
```

## Account Deletion

`DELETE /api/user/me` performs:
1. DB cleanup: cascading deletes across `user_secrets`, `onboarding_responses`, etc.
2. Filesystem cleanup: `shutil.rmtree(get_coach_home() / "users" / safe_user_id(user_id))`

Both steps are required for `has_profile` to correctly return `false` on re-login.

## Key Files

| Concern | File |
|---------|------|
| Path resolution | `src/storage_paths.py` |
| Storage factory | `src/storage_access.py` |
| Web dependency injection | `src/web/deps.py` |
| User DB operations | `src/user_state_store.py` |
| Account deletion route | `src/web/routes/user.py` |
| Encrypted secrets (legacy) | `src/crypto_utils.py`, `src/web/crypto.py` |

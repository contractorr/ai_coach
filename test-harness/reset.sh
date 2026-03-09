#!/usr/bin/env bash
set -euo pipefail

# Reset all persona data for a fresh 14-beat test run.
# Idempotent — safe to rerun. Does NOT touch ~/coach/intel.db (shared).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USERS_DB="$HOME/coach/users.db"
PERSONAS=(junior_dev founder switcher)

echo "=== Test Harness Reset ==="

# --- Wipe persona user directories ---

for p in "${PERSONAS[@]}"; do
  USER_DIR="$HOME/coach/users/credentials_${p}"
  if [ -d "$USER_DIR" ]; then
    rm -rf "$USER_DIR"
    echo "[cleared] $USER_DIR"
  else
    echo "[skip]    $USER_DIR (not found)"
  fi
done

# --- Purge persona rows from users.db ---

if [ -f "$USERS_DB" ]; then
  for p in "${PERSONAS[@]}"; do
    USER_ID="credentials:${p}"
    # Order matters: delete children before parent
    # conversation_messages references conversations, not users directly
    sqlite3 "$USERS_DB" "DELETE FROM conversation_messages WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = '${USER_ID}');"
    for table in user_secrets onboarding_responses engagement_events \
                 usage_events user_rss_feeds conversations; do
      sqlite3 "$USERS_DB" "DELETE FROM ${table} WHERE user_id = '${USER_ID}';"
    done
    # users table uses 'id' not 'user_id'
    sqlite3 "$USERS_DB" "DELETE FROM users WHERE id = '${USER_ID}';"
    echo "[cleared] users.db rows for ${USER_ID}"
  done
else
  echo "[skip]    $USERS_DB (not found)"
fi

# --- Clear harness state files ---

for p in "${PERSONAS[@]}"; do
  STATE_DIR="$SCRIPT_DIR/state/$p"
  if [ -d "$STATE_DIR" ]; then
    rm -f "$STATE_DIR/session_log.md"
    rm -f "$STATE_DIR/latest_run_output.txt"
    rm -rf "$STATE_DIR/screenshots"
    echo "[cleared] harness state for $p"
  fi
done

echo ""
echo "Reset complete. Ready for fresh 14-beat run."

#!/usr/bin/env bash
set -e

COACH_DIR="${COACH_HOME:-/data/coach}/coach"
CONFIG_PATH="$COACH_DIR/config.yaml"

# Seed default config if none exists (preserves user customizations on redeploy)
if [ ! -f "$CONFIG_PATH" ]; then
    mkdir -p "$COACH_DIR"
    cp /app/config.default.yaml "$CONFIG_PATH"
    echo "Seeded default config at $CONFIG_PATH"
fi

# Activate uv-managed venv so uvicorn is on PATH
export PATH="/app/.venv/bin:$PATH"

exec "$@"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
ALL_PERSONAS=(junior_dev founder switcher)

# --- Preflight checks ---

echo "=== Preflight checks ==="

# AWS SSO session
if ! aws sts get-caller-identity &>/dev/null; then
  echo "ERROR: AWS SSO session expired. Run: aws sso login"
  exit 1
fi
echo "[ok] AWS SSO session valid"

# Frontend
if ! curl -sf http://localhost:3000 >/dev/null 2>&1; then
  echo "ERROR: Frontend not running on localhost:3000"
  echo "  Start with: cd web && npm run dev"
  exit 1
fi
echo "[ok] Frontend running on :3000"

# Backend
if ! curl -sf http://localhost:8000/api/health >/dev/null 2>&1; then
  echo "ERROR: Backend not running on localhost:8000"
  echo "  Start with: uvicorn src.web.app:app --reload --port 8000"
  exit 1
fi
echo "[ok] Backend running on :8000"

# API key (needed by backend for shared LLM calls)
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "WARNING: ANTHROPIC_API_KEY not set — backend LLM calls will fail"
  echo "  Export it before running: export ANTHROPIC_API_KEY=sk-..."
  exit 1
fi
echo "[ok] ANTHROPIC_API_KEY set"

echo ""
echo "NOTE: Council requires per-persona API keys entered in Settings > LLM Providers."
echo "      Env vars alone do NOT enable council. Each persona must add keys during their run."
echo ""

# --- Determine personas to run ---

if [ $# -gt 0 ]; then
  PERSONAS=("$@")
else
  PERSONAS=("${ALL_PERSONAS[@]}")
fi

# --- Run each persona ---

for persona in "${PERSONAS[@]}"; do
  if [ ! -f "$SCRIPT_DIR/personas/${persona}.md" ]; then
    echo "ERROR: No persona file for '${persona}'"
    continue
  fi

  echo "=== Running persona: ${persona} ==="
  "$SCRIPT_DIR/run_persona.sh" "$persona"
  echo "=== Done: ${persona} ==="
  echo ""
done

echo "All persona runs complete. Check test-harness/state/ for results."

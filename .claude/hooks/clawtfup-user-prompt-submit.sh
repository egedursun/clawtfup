#!/usr/bin/env bash
# Injects evaluate status on each user message. Stdin is Claude hook JSON.
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-}"
if [[ -z "$ROOT" ]]; then
  exit 0
fi
cd "$ROOT" || exit 0
if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python -m policy_eval hook-user-prompt-submit
fi
if command -v clawtfup >/dev/null 2>&1; then
  exec clawtfup hook-user-prompt-submit
fi
exit 0

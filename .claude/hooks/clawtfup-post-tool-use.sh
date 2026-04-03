#!/usr/bin/env bash
# Runs policy after Edit/Write/etc. Stdin is Claude hook JSON (passed through to Python).
set -euo pipefail
ROOT="${CLAUDE_PROJECT_DIR:-}"
if [[ -z "$ROOT" ]]; then
  exit 0
fi
cd "$ROOT" || exit 0
if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python -m policy_eval hook-post-tool-use
fi
if command -v clawtfup >/dev/null 2>&1; then
  exec clawtfup hook-post-tool-use
fi
exit 0

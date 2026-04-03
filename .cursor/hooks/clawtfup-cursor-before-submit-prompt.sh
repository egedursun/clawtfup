#!/usr/bin/env bash
# Cursor beforeSubmitPrompt: stdin is Cursor hook JSON (passed through to Python).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -n "$ROOT" ]]; then
  cd "$ROOT" || true
fi
if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python -m policy_eval hook-cursor-before-submit-prompt
fi
if command -v clawtfup >/dev/null 2>&1; then
  exec clawtfup hook-cursor-before-submit-prompt
fi
printf '%s' '{"continue":true}'
exit 0

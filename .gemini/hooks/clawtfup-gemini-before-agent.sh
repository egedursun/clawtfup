#!/usr/bin/env bash
# Gemini CLI BeforeAgent: stdin is Gemini hook JSON (passed through to Python).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  exit 0
fi
cd "$ROOT" || exit 0
if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python -m policy_eval hook-gemini-before-agent
fi
if command -v clawtfup >/dev/null 2>&1; then
  exec clawtfup hook-gemini-before-agent
fi
exit 0

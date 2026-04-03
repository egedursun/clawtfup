#!/usr/bin/env bash
# OpenAI Codex PostToolUse: stdin is Codex hook JSON (passed through to Python).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  exit 0
fi
cd "$ROOT" || exit 0
if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python -m policy_eval hook-codex-post-tool-use
fi
if command -v clawtfup >/dev/null 2>&1; then
  exec clawtfup hook-codex-post-tool-use
fi
exit 0

#!/usr/bin/env bash
# Qwen Code Stop: block session end on policy failure (hook-qwen-stop).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  exit 0
fi
cd "$ROOT" || exit 0
if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python -m policy_eval hook-qwen-stop
fi
if command -v clawtfup >/dev/null 2>&1; then
  exec clawtfup hook-qwen-stop
fi
exit 0

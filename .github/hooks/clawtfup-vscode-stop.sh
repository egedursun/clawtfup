#!/usr/bin/env bash
# VS Code / Antigravity Stop: block session end on policy failure (hook-vscode-stop).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  exit 0
fi
cd "$ROOT" || exit 0
if [[ -x .venv/bin/python ]]; then
  exec .venv/bin/python -m policy_eval hook-vscode-stop
fi
if command -v clawtfup >/dev/null 2>&1; then
  exec clawtfup hook-vscode-stop
fi
exit 0

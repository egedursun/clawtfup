"""Google Gemini CLI hook entrypoints (stdin JSON → stdout hook JSON).

Gemini uses ``AfterTool`` (post-tool) and ``BeforeAgent`` (prompt-time context), not
Codex/Claude event names. Output shape matches Gemini's hook reference:
https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/reference.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .agent_proxy_support import (
    evaluation_passed,
    format_findings_human,
    run_evaluate_subprocess,
    stdin_hook_event_name,
    truncate_hook_context,
)
from .defaults import default_policies_dir


def hook_gemini_after_tool_cmd() -> int:
    """
    Gemini ``AfterTool``: run evaluate; on failure deny/block so the agent sees policy
    feedback instead of a clean tool result.
    """
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    cwd = event.get("cwd")
    if not cwd or not isinstance(cwd, str):
        return 0
    ws = Path(cwd).resolve()
    if not default_policies_dir(ws).is_dir():
        return 0

    code, report = run_evaluate_subprocess(ws)
    if evaluation_passed(report, code):
        return 0

    human = format_findings_human(report or {})
    msg = truncate_hook_context(
        "clawtfup: policy failed after this tool run. Revert or fix every finding before continuing.\n\n"
        + human
    )
    hook_name = stdin_hook_event_name(event, "AfterTool")
    out = {
        "decision": "deny",
        "reason": "Workspace policy failed after this tool run (see hook context for findings).",
        "hookSpecificOutput": {
            "hookEventName": hook_name,
            "additionalContext": msg,
        },
    }
    sys.stdout.write(json.dumps(out))
    return 0


def hook_gemini_before_agent_cmd() -> int:
    """Gemini ``BeforeAgent``: run evaluate; inject context. Never denies the user's prompt."""
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    cwd = event.get("cwd")
    if not cwd or not isinstance(cwd, str):
        return 0
    ws = Path(cwd).resolve()
    if not default_policies_dir(ws).is_dir():
        return 0

    code, report = run_evaluate_subprocess(ws)
    ok = evaluation_passed(report, code)
    hook_name = stdin_hook_event_name(event, "BeforeAgent")

    if ok:
        msg = (
            "clawtfup: evaluate passed on this workspace at prompt time. "
            "After further edits, run `clawtfup evaluate --pretty` before finishing.\n"
            f"Root: {ws}"
        )
    else:
        human = format_findings_human(report or {})
        msg = truncate_hook_context(
            "clawtfup: evaluate FAILS on this workspace right now. Fix before adding more changes.\n\n"
            + human
            + "\n\nRun `clawtfup evaluate --pretty` from the root until exit 0."
        )

    out = {
        "hookSpecificOutput": {
            "hookEventName": hook_name,
            "additionalContext": msg,
        },
    }
    sys.stdout.write(json.dumps(out))
    return 0

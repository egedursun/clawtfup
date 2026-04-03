"""OpenAI Codex CLI hook entrypoints (stdin JSON → stdout hook JSON)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .agent_proxy_support import (
    evaluation_passed,
    format_findings_human,
    run_evaluate_subprocess,
    truncate_hook_context,
)
from .defaults import default_policies_dir


def hook_codex_post_tool_use_cmd() -> int:
    """
    Codex PostToolUse: run evaluate; on failure block the turn with findings.

    See https://developers.openai.com/codex/hooks/ — ``suppressOutput`` is not
    applied here (Codex does not implement it for this event).
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
    hook_name = event.get("hook_event_name") or "PostToolUse"
    out = {
        "decision": "block",
        "reason": "Workspace policy failed after this tool run (see hook context for findings).",
        "hookSpecificOutput": {
            "hookEventName": hook_name,
            "additionalContext": msg,
        },
    }
    sys.stdout.write(json.dumps(out))
    return 0


def hook_codex_user_prompt_submit_cmd() -> int:
    """Codex UserPromptSubmit: run evaluate; inject context. Never blocks the user's prompt."""
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
    hook_name = event.get("hook_event_name") or "UserPromptSubmit"

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

"""Cursor IDE hook entrypoints (stdin JSON → stdout JSON or exit codes).

Contract follows Cursor agent lifecycle hooks (see https://cursor.com/docs/agent/hooks).
Community typings: https://github.com/johnlindquist/cursor-hooks
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .agent_proxy_support import (
    evaluation_passed,
    format_findings_compact_for_hook,
    format_findings_human,
    run_evaluate_subprocess,
    truncate_hook_context,
)
from .defaults import default_policies_dir


def _parse_stdin_event() -> dict | None:
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    try:
        ev = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return ev if isinstance(ev, dict) else None


def workspace_from_cursor_event(event: dict) -> Path | None:
    """Resolve workspace from ``workspace_roots`` (multi-root) or cwd."""
    roots = event.get("workspace_roots")
    if isinstance(roots, list) and roots:
        first = roots[0]
        if isinstance(first, str) and first.strip():
            return Path(first).resolve()
    cwd = event.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        return Path(cwd).resolve()
    return Path.cwd().resolve()


def hook_cursor_before_submit_prompt_cmd() -> int:
    """
    beforeSubmitPrompt: gate new prompts when the workspace fails policy.

    Cursor accepts ``{"continue": true|false}`` on stdout. There is no
    Claude-style ``additionalContext`` inject on this event in the published
    schema, so we only allow or block the prompt.
    """
    event = _parse_stdin_event()
    if event is None:
        sys.stdout.write(json.dumps({"continue": True}))
        return 0

    ws = workspace_from_cursor_event(event)
    if not default_policies_dir(ws).is_dir():
        sys.stdout.write(json.dumps({"continue": True}))
        return 0

    code, report = run_evaluate_subprocess(ws)
    if evaluation_passed(report, code):
        sys.stdout.write(json.dumps({"continue": True}))
        return 0

    human = format_findings_human(report or {})
    prefix = (
        "clawtfup: workspace policy fails. "
        "Fix findings (or run `clawtfup evaluate --pretty`) before continuing.\n\n"
    )
    um = truncate_hook_context(prefix + human)
    out: dict = {"continue": False, "userMessage": um}
    sys.stdout.write(json.dumps(out))
    return 0


def hook_cursor_after_file_edit_cmd() -> int:
    """
    afterFileEdit: run evaluate after each AI file edit.

    The documented response type is void (no stdout JSON). On failure we exit
    non-zero and write details to stderr so the Hooks output channel surfaces
    the failure; Cursor may still continue the agent session.
    """
    event = _parse_stdin_event()
    if event is None:
        return 0

    ws = workspace_from_cursor_event(event)
    if not default_policies_dir(ws).is_dir():
        return 0

    code, report = run_evaluate_subprocess(ws)
    if evaluation_passed(report, code):
        return 0

    msg = format_findings_compact_for_hook(report or {})
    sys.stderr.write(truncate_hook_context(msg) + "\n")
    return 2


def hook_cursor_stop_cmd() -> int:
    """
    stop: when the agent run finishes with status ``completed``, enforce policy.

    On failure exit ``2`` and print compact findings on stderr. No stdout JSON
    (void response in published typings).
    """
    event = _parse_stdin_event()
    if event is None:
        return 0

    status = event.get("status")
    if status != "completed":
        return 0

    ws = workspace_from_cursor_event(event)
    if not default_policies_dir(ws).is_dir():
        return 0

    code, report = run_evaluate_subprocess(ws)
    if evaluation_passed(report, code):
        return 0

    msg = format_findings_compact_for_hook(report or {})
    sys.stderr.write(truncate_hook_context(msg) + "\n")
    return 2

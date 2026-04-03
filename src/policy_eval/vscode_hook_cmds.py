"""VS Code / Google Antigravity agent hook entrypoints (preview agent hooks).

VS Code loads workspace hooks from ``.github/hooks/*.json``. The ``Stop`` event uses a
different response shape than Cursor's ``stop`` hook — see:
https://code.visualstudio.com/docs/copilot/customization/hooks

``PostToolUse`` and ``UserPromptSubmit`` reuse the Codex-oriented handlers (no
``suppressOutput``): ``hook-codex-post-tool-use`` and ``hook-codex-user-prompt-submit``.
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
    stop_hook_retry_active,
    truncate_hook_context,
)
from .defaults import default_policies_dir


def hook_vscode_stop_cmd() -> int:
    """
    VS Code ``Stop``: if evaluate fails, block the session from ending so the agent can fix.

    When ``stop_hook_active`` is true (retry already in progress), no-op to avoid loops.
    """
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    if stop_hook_retry_active(event):
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
    reason = truncate_hook_context(
        "clawtfup: policy still fails; fix every finding before ending the session.\n\n" + human
    )
    hook_name = stdin_hook_event_name(event, "Stop")
    out = {
        "hookSpecificOutput": {
            "hookEventName": hook_name,
            "decision": "block",
            "reason": reason,
        },
    }
    sys.stdout.write(json.dumps(out))
    return 0

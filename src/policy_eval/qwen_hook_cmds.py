"""Qwen Code CLI hook entrypoints (stdin JSON → stdout hook JSON).

Qwen Code uses the same lifecycle names as Claude Code (``PostToolUse``, ``UserPromptSubmit``,
``Stop``) and loads hooks from ``.qwen/settings.json``. Post-tool and prompt-time behavior
matches the Codex-shaped handlers (no ``suppressOutput``). The ``Stop`` hook expects
top-level ``decision`` / ``reason`` per Qwen docs:

https://github.com/QwenLM/qwen-code/blob/main/docs/users/features/hooks.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .agent_proxy_support import (
    evaluation_passed,
    format_findings_human,
    run_evaluate_subprocess,
    stop_hook_retry_active,
    truncate_hook_context,
)
from .codex_hook_cmds import (
    hook_codex_post_tool_use_cmd,
    hook_codex_user_prompt_submit_cmd,
)
from .defaults import default_policies_dir


def hook_qwen_post_tool_use_cmd() -> int:
    """Qwen ``PostToolUse``: same stdout contract as OpenAI Codex (``hook-codex-post-tool-use``)."""
    return hook_codex_post_tool_use_cmd()


def hook_qwen_user_prompt_submit_cmd() -> int:
    """Qwen ``UserPromptSubmit``: same as ``hook-codex-user-prompt-submit``."""
    return hook_codex_user_prompt_submit_cmd()


def hook_qwen_stop_cmd() -> int:
    """
    Qwen ``Stop``: on policy failure emit top-level ``decision`` (``block``) and ``reason``.

    When ``stop_hook_active`` is true, no-op to avoid retry loops.
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
    out = {
        "decision": "block",
        "reason": reason,
    }
    sys.stdout.write(json.dumps(out))
    return 0

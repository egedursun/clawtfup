"""Transparent subprocess proxy for agent CLIs.

``clawtfup cli`` only relays I/O. Wire hooks in ``.claude/settings.json`` (Claude Code) or
``.codex/hooks.json`` (OpenAI Codex) so they run ``evaluate`` and return PostToolUse
``decision: block`` when policy fails after edits.
"""

from __future__ import annotations

from .agent_proxy_run import run_claude_proxy, run_codex_proxy
from .agent_proxy_support import (
    evaluation_passed,
    format_findings_compact_for_hook,
    format_findings_human,
    run_evaluate_subprocess,
)

__all__ = [
    "evaluation_passed",
    "format_findings_compact_for_hook",
    "format_findings_human",
    "run_claude_proxy",
    "run_codex_proxy",
    "run_evaluate_subprocess",
]

"""Transparent subprocess proxy for agent CLIs.

``clawtfup cli`` only relays I/O. Wire hooks in ``.claude/settings.json`` (Claude Code),
``.codex/hooks.json`` (OpenAI Codex), ``.gemini/settings.json`` (Gemini CLI),
``.qwen/settings.json`` (Qwen Code),
``.opencode/plugins/*.mjs`` (Kilocode / Kilo CLI and OpenCode — ``tool.execute.after`` plugin), or
``.github/hooks/*.json`` (VS Code / Google Antigravity agent hooks) so they run ``evaluate``
and return a blocking decision when policy fails after edits.

Charm Crush has no published hook channel in ``crush.json`` — use ``evaluate`` in your workflow
or context files when using ``clawtfup cli --provider crush``.

Aider has no stdin/JSON hook protocol — use ``clawtfup cli --provider aider`` for a cwd-safe
proxy and wire ``clawtfup evaluate`` via ``--lint-cmd`` or manual runs (see README).

Cline CLI has no documented hook protocol for clawtfup — use ``clawtfup cli --provider cline``
for a cwd-safe proxy and run ``evaluate`` after tasks or in CI wrappers (see README).
"""

from __future__ import annotations

from .agent_proxy_run import (
    run_aider_proxy,
    run_claude_proxy,
    run_cline_proxy,
    run_codex_proxy,
    run_crush_proxy,
    run_gemini_proxy,
    run_kilo_proxy,
    run_qwen_proxy,
)
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
    "run_gemini_proxy",
    "run_qwen_proxy",
    "run_kilo_proxy",
    "run_crush_proxy",
    "run_aider_proxy",
    "run_cline_proxy",
    "run_evaluate_subprocess",
]

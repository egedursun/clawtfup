"""Argparse subparsers for hook subcommands (keeps cli.py under size limits)."""

from __future__ import annotations

import argparse


def add_hook_subparsers(sub: argparse._SubParsersAction) -> None:
    """Register all `hook-*` subcommands on *sub*."""
    rf = argparse.RawDescriptionHelpFormatter

    sub.add_parser(
        "hook-post-tool-use",
        formatter_class=rf,
        help=(
            "Claude Code PostToolUse hook: run evaluate on cwd; on failure emit JSON with "
            "decision block + findings (tool already ran; block stops the turn until fixed)."
        ),
        description=(
            "This repo ships `.claude/settings.json` + shell wrappers under `.claude/hooks/` "
            "so Claude Code runs this command with hook JSON on stdin.\n\n"
            "Behavior: runs `clawtfup evaluate` (via the same Python as the hook process). "
            "Exit 0 always. On policy pass: empty stdout. On failure: stdout JSON with top-level "
            "`decision: \"block\"`, `reason`, and `hookSpecificOutput.additionalContext` "
            "(human findings, truncated near 10k chars). See Claude Code hooks docs for "
            "PostToolUse + decision control."
        ),
    )

    sub.add_parser(
        "hook-user-prompt-submit",
        formatter_class=rf,
        help=(
            "Claude Code UserPromptSubmit hook: run evaluate; inject pass/fail context "
            "(does not block or erase the user's prompt)."
        ),
        description=(
            "Runs evaluate on each user message when `.clawtfup/policies/` exists. "
            "Always exit 0 with JSON: `hookSpecificOutput.additionalContext` summarizes "
            "pass/fail and findings on failure. Never uses `decision: block` here so the "
            "submitted prompt is not rejected."
        ),
    )

    sub.add_parser(
        "hook-codex-post-tool-use",
        formatter_class=rf,
        help=(
            "OpenAI Codex PostToolUse hook: run evaluate; on failure emit JSON with "
            "decision block + findings (tool already ran)."
        ),
        description=(
            "Wire this command from `.codex/hooks.json` (enable `codex_hooks` in config.toml). "
            "Codex sends hook JSON on stdin with `cwd`. On policy pass: empty stdout. "
            "On failure: JSON with `decision: \"block\"`, `reason`, and "
            "`hookSpecificOutput.additionalContext`. See OpenAI Codex hooks documentation."
        ),
    )

    sub.add_parser(
        "hook-codex-user-prompt-submit",
        formatter_class=rf,
        help=(
            "OpenAI Codex UserPromptSubmit hook: run evaluate; inject pass/fail context "
            "(does not block the user's prompt)."
        ),
        description=(
            "Same behavior as `hook-user-prompt-submit` but emits Codex-oriented JSON "
            "(no `suppressOutput`; Codex UserPromptSubmit schema)."
        ),
    )

    sub.add_parser(
        "hook-gemini-after-tool",
        formatter_class=rf,
        help=(
            "Gemini CLI AfterTool hook: run evaluate; on failure emit JSON with "
            "decision deny + findings (tool already ran)."
        ),
        description=(
            "Wire from `.gemini/settings.json` under the `AfterTool` event. "
            "Gemini sends hook JSON on stdin with `cwd`. On policy pass: empty stdout. "
            "On failure: JSON with `decision: \"deny\"`, `reason`, and "
            "`hookSpecificOutput.additionalContext`. See Gemini CLI hooks reference."
        ),
    )

    sub.add_parser(
        "hook-gemini-before-agent",
        formatter_class=rf,
        help=(
            "Gemini CLI BeforeAgent hook: run evaluate; inject pass/fail context "
            "(does not deny the user's prompt)."
        ),
        description=(
            "Same idea as `hook-user-prompt-submit` / `hook-codex-user-prompt-submit` "
            "but for Gemini's `BeforeAgent` event (hookEventName in output)."
        ),
    )

    sub.add_parser(
        "hook-qwen-post-tool-use",
        formatter_class=rf,
        help=(
            "Qwen Code PostToolUse hook: same behavior as `hook-codex-post-tool-use`."
        ),
        description=(
            "Wire from `.qwen/settings.json`. Qwen sends `hook_event_name` and `cwd` on stdin. "
            "Delegates to the Codex-shaped PostToolUse response (no `suppressOutput`). "
            "See https://github.com/QwenLM/qwen-code/blob/main/docs/users/features/hooks.md"
        ),
    )

    sub.add_parser(
        "hook-qwen-user-prompt-submit",
        formatter_class=rf,
        help=(
            "Qwen Code UserPromptSubmit hook: same behavior as `hook-codex-user-prompt-submit`."
        ),
        description=(
            "Wire from `.qwen/settings.json`. Injects `hookSpecificOutput.additionalContext` only. "
            "See Qwen Code hooks documentation."
        ),
    )

    sub.add_parser(
        "hook-qwen-stop",
        formatter_class=rf,
        help=(
            "Qwen Code Stop hook: on evaluate failure emit top-level `decision: block` and `reason`."
        ),
        description=(
            "Qwen expects top-level `decision` / `reason` (not VS Code's `hookSpecificOutput` shape). "
            "No-ops when `stop_hook_active` is true. See Qwen Code hooks documentation."
        ),
    )

    sub.add_parser(
        "hook-cursor-before-submit-prompt",
        formatter_class=rf,
        help=(
            "Cursor beforeSubmitPrompt hook: block new prompts when evaluate fails "
            "(stdout JSON `continue: false`)."
        ),
        description=(
            "Wire from `.cursor/hooks.json`. See https://cursor.com/docs/agent/hooks "
            "(e.g. https://cursor.com/tr/docs/hooks). "
            "When `.clawtfup/policies/` exists, runs evaluate; on failure prints "
            "`{\"continue\": false, \"userMessage\": \"...\"}`."
        ),
    )

    sub.add_parser(
        "hook-cursor-after-file-edit",
        formatter_class=rf,
        help=(
            "Cursor afterFileEdit hook: run evaluate; exit 2 + stderr on failure "
            "(no blocking JSON on this event per Cursor docs)."
        ),
        description=(
            "Can be noisy (full evaluate after every edit). Remove from hooks.json if too slow."
        ),
    )

    sub.add_parser(
        "hook-cursor-stop",
        formatter_class=rf,
        help=(
            "Cursor stop hook: when status is completed, run evaluate; exit 2 on failure."
        ),
        description="Primary gate when the agent run finishes; stderr carries compact findings.",
    )

    sub.add_parser(
        "hook-vscode-stop",
        formatter_class=rf,
        help=(
            "VS Code / Antigravity Stop hook: on evaluate failure, block session end via stdout JSON."
        ),
        description=(
            "Wire from `.github/hooks/*.json` (VS Code agent hooks preview) or the same paths "
            "Antigravity loads. On policy pass: empty stdout. On failure: JSON with "
            "`hookSpecificOutput.decision: \"block\"` and `reason` so the agent cannot stop yet. "
            "No-ops when `stop_hook_active` / `stopHookActive` is true (retry loop guard). "
            "See https://code.visualstudio.com/docs/copilot/customization/hooks"
        ),
    )

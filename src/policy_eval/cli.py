from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PATCH_DEPRECATION = (
    "warning: --patch is deprecated; use --diff-file (same meaning).\n"
)

from .agent_proxy import run_claude_proxy, run_codex_proxy, run_gemini_proxy
from .claude_hook_cmds import hook_post_tool_use_cmd, hook_user_prompt_submit_cmd
from .codex_hook_cmds import hook_codex_post_tool_use_cmd, hook_codex_user_prompt_submit_cmd
from .gemini_hook_cmds import hook_gemini_after_tool_cmd, hook_gemini_before_agent_cmd
from .cursor_hook_cmds import (
    hook_cursor_after_file_edit_cmd,
    hook_cursor_before_submit_prompt_cmd,
    hook_cursor_stop_cmd,
)
from .vscode_hook_cmds import hook_vscode_stop_cmd
from .cli_hooks import add_hook_subparsers
from .defaults import default_policies_dir
from .evaluate import EvaluateOptions, evaluate
from .exceptions import ManifestError, OpaEngineError, PatchApplyError, PolicyEvalError
from .git_changes import git_diff_head


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="clawtfup",
        description=(
            "Evaluate workspace against OPA policies in <workspace>/.clawtfup/policies/. "
            "Default full scan indexes the working tree (no git diff). Use .cfupignore "
            "(gitignore-style) to exclude paths. Use --diff-only without --diff-file to "
            "scope changes to git diff HEAD (legacy). "
            "Pass --diff-file to apply a unified diff on top of the disk index."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("evaluate", help="Run OPA evaluation on workspace + proposed changes")
    ev.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Project root to index (default: current directory). Policies: <workspace>/.clawtfup/policies/",
    )
    ev.add_argument(
        "--diff-file",
        type=str,
        default=None,
        dest="diff_file",
        metavar="PATH",
        help=(
            "Unified diff of proposed edits (file path, or '-' for stdin). "
            "Default: run `git diff HEAD` in --workspace."
        ),
    )
    ev.add_argument(
        "--patch",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )
    ev.add_argument(
        "--input-json",
        type=Path,
        default=None,
        help="Optional JSON merged into OPA input (after workspace fragment).",
    )
    ev.add_argument(
        "--query",
        action="append",
        dest="queries",
        default=None,
        help="OPA query (repeatable). Overrides policy_eval.yaml queries.",
    )
    ev.add_argument(
        "--max-files",
        type=int,
        default=10_000,
        help="Max files to index (0 = no cap).",
    )
    ev.add_argument(
        "--max-file-bytes",
        type=int,
        default=512 * 1024,
        help="Skip files larger than this many bytes (0 = no cap).",
    )
    ev.add_argument(
        "--exclude-glob",
        action="append",
        dest="exclude_globs",
        default=[],
        help="Exclude workspace paths (glob, repeatable).",
    )
    ev.add_argument(
        "--use-gitignore",
        action="store_true",
        help="Also apply .gitignore patterns when indexing (off by default; prefer .cfupignore).",
    )
    ev.add_argument(
        "--no-cfupignore",
        action="store_true",
        help="Do not apply .cfupignore rules when indexing.",
    )
    ev.add_argument(
        "--diff-only",
        action="store_true",
        help=(
            "Only run policy on paths touched by the unified diff (--diff-file / stdin, "
            "or git diff HEAD when no file is given). Default is full-tree scan."
        ),
    )
    ev.add_argument(
        "--scan-prefix",
        type=str,
        default=None,
        metavar="PATH",
        help=(
            "Restrict the scan to files under this path (posix, relative to workspace), "
            "e.g. examples/blog. Implies full content under that prefix, not diff-only."
        ),
    )
    ev.add_argument(
        "--no-strict",
        action="store_true",
        help="Exit 0 even when allow is false or there are error-severity findings (default: strict).",
    )
    ev.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )

    agent = sub.add_parser(
        "cli",
        help=(
            "Proxy a provider CLI (Claude Code, OpenAI Codex, Gemini CLI): relay I/O only. "
            "Project hooks run `evaluate` (see hook subcommands and `.claude/`, `.codex/`, "
            "`.gemini/`, `.github/hooks/`, `.cursor/` samples)."
        ),
    )
    agent.add_argument(
        "--provider",
        choices=["claude", "codex", "gemini"],
        required=True,
        help="Agent CLI to spawn (forwards remaining args to that executable).",
    )
    agent.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Project root (default: current directory). Passed as cwd for the child process.",
    )
    agent.add_argument(
        "--claude-bin",
        type=str,
        default=None,
        help="Path to the claude executable (default: $CLAWTFUP_CLAUDE_BIN or 'claude' on PATH).",
    )
    agent.add_argument(
        "--codex-bin",
        type=str,
        default=None,
        help="Path to the codex executable (default: $CLAWTFUP_CODEX_BIN or 'codex' on PATH).",
    )
    agent.add_argument(
        "--gemini-bin",
        type=str,
        default=None,
        help="Path to the gemini executable (default: $CLAWTFUP_GEMINI_BIN or 'gemini' on PATH).",
    )
    agent.add_argument(
        "provider_args",
        nargs=argparse.REMAINDER,
        help="Arguments for the provider; use '--' before flags meant for the provider.",
    )

    add_hook_subparsers(sub)

    args = parser.parse_args(argv)

    if args.cmd == "cli":
        return _cli_cmd(args)
    if args.cmd == "hook-post-tool-use":
        return hook_post_tool_use_cmd()
    if args.cmd == "hook-user-prompt-submit":
        return hook_user_prompt_submit_cmd()
    if args.cmd == "hook-codex-post-tool-use":
        return hook_codex_post_tool_use_cmd()
    if args.cmd == "hook-codex-user-prompt-submit":
        return hook_codex_user_prompt_submit_cmd()
    if args.cmd == "hook-gemini-after-tool":
        return hook_gemini_after_tool_cmd()
    if args.cmd == "hook-gemini-before-agent":
        return hook_gemini_before_agent_cmd()
    if args.cmd == "hook-cursor-before-submit-prompt":
        return hook_cursor_before_submit_prompt_cmd()
    if args.cmd == "hook-cursor-after-file-edit":
        return hook_cursor_after_file_edit_cmd()
    if args.cmd == "hook-cursor-stop":
        return hook_cursor_stop_cmd()
    if args.cmd == "hook-vscode-stop":
        return hook_vscode_stop_cmd()
    if args.cmd != "evaluate":
        return 2

    return _evaluate_cmd(args)


def _evaluate_cmd(args: argparse.Namespace) -> int:
    workspace = (args.workspace or Path.cwd()).resolve()
    policies = default_policies_dir(workspace).resolve()

    if not policies.is_dir():
        sys.stderr.write(
            json.dumps(
                {
                    "error": (
                        f"policies directory not found: {policies}. "
                        "Create .clawtfup/policies/ with policy_eval.yaml and rego/."
                    )
                }
            ) + "\n"
        )
        return 1

    diff_arg = args.diff_file
    if args.patch is not None:
        if diff_arg is not None:
            sys.stderr.write(
                json.dumps({"error": "use only one of --diff-file and --patch"}) + "\n"
            )
            return 1
        sys.stderr.write(_PATCH_DEPRECATION)
        diff_arg = args.patch

    scan_prefix = (args.scan_prefix or "").strip() or None
    # Full-tree scan is default; --diff-only narrows to patch-touched paths only.
    use_full_scan = (scan_prefix is None) and (not args.diff_only)

    change_source: str
    patch_text: str
    if diff_arg is None:
        if use_full_scan:
            patch_text = ""
            change_source = "working_tree"
        else:
            try:
                patch_text = git_diff_head(workspace)
            except PolicyEvalError as e:
                sys.stderr.write(json.dumps({"error": str(e)}) + "\n")
                return 1
            change_source = "git_head"
    elif diff_arg == "-":
        patch_text = sys.stdin.read()
        change_source = "stdin"
    else:
        p = Path(diff_arg)
        if not p.is_file():
            sys.stderr.write(json.dumps({"error": f"diff file not found: {p}"}) + "\n")
            return 1
        patch_text = p.read_text(encoding="utf-8")
        change_source = "diff_file"

    opts = EvaluateOptions(
        workspace=workspace,
        bundle_root=policies,
        patch_text=patch_text,
        input_json_path=args.input_json,
        queries=args.queries,
        max_files=args.max_files,
        max_file_bytes=args.max_file_bytes,
        exclude_globs=list(args.exclude_globs or []),
        use_gitignore=bool(args.use_gitignore),
        use_cfupignore=not args.no_cfupignore,
        change_source=change_source,
        index_from_git_head=(change_source == "git_head"),
        full_scan=use_full_scan,
        scan_prefix=scan_prefix,
    )

    try:
        report = evaluate(opts)
    except (PolicyEvalError, ManifestError, PatchApplyError, OpaEngineError) as e:
        sys.stderr.write(json.dumps({"error": str(e)}) + "\n")
        return 1

    indent = 2 if args.pretty else None
    sys.stdout.write(json.dumps(report, indent=indent) + "\n")

    if not args.no_strict:
        if not report.get("allow"):
            return 2
        for f in report.get("findings") or []:
            if f.get("severity") == "error":
                return 2
    return 0


def _cli_cmd(args: argparse.Namespace) -> int:
    workspace = (args.workspace or Path.cwd()).resolve()
    raw = list(args.provider_args or [])
    if raw and raw[0] == "--":
        raw = raw[1:]
    if args.provider == "claude":
        return run_claude_proxy(raw, workspace, claude_executable=args.claude_bin)
    if args.provider == "codex":
        return run_codex_proxy(raw, workspace, codex_executable=args.codex_bin)
    if args.provider == "gemini":
        return run_gemini_proxy(raw, workspace, gemini_executable=args.gemini_bin)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

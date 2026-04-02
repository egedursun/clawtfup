from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PATCH_DEPRECATION = (
    "warning: --patch is deprecated; use --diff-file (same meaning).\n"
)

from .defaults import default_policies_dir
from .evaluate import EvaluateOptions, evaluate
from .exceptions import ManifestError, OpaEngineError, PatchApplyError, PolicyEvalError
from .git_changes import git_diff_head


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="policy-eval",
        description=(
            "Evaluate proposed code changes against OPA policies. "
            "Defaults: workspace = cwd, policies = .clawtfup/policies/, "
            "changes = git diff HEAD (or pass --diff-file)."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("evaluate", help="Run OPA evaluation on workspace + proposed changes")
    ev.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Project root to index (default: current directory).",
    )
    ev.add_argument(
        "--policies",
        type=Path,
        default=None,
        help=(
            "Policy bundle root: policy_eval.yaml, optional feedback.yaml, rego/. "
            "Default: <workspace>/.clawtfup/policies/"
        ),
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
        "--no-gitignore",
        action="store_true",
        help="Do not apply .gitignore rules when indexing.",
    )
    ev.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 if allow is false or any error-severity finding.",
    )
    ev.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )

    args = parser.parse_args(argv)

    if args.cmd != "evaluate":
        return 2

    workspace = (args.workspace or Path.cwd()).resolve()
    policies = (args.policies or default_policies_dir(workspace)).resolve()

    if not policies.is_dir():
        print(
            json.dumps(
                {
                    "error": (
                        f"policy bundle directory not found: {policies}. "
                        "Add .clawtfup/policies/ with policy_eval.yaml and rego/, or pass --policies."
                    )
                }
            ),
            file=sys.stderr,
        )
        return 1

    diff_arg = args.diff_file
    if args.patch is not None:
        if diff_arg is not None:
            print(
                json.dumps({"error": "use only one of --diff-file and --patch"}),
                file=sys.stderr,
            )
            return 1
        print(_PATCH_DEPRECATION, file=sys.stderr, end="")
        diff_arg = args.patch

    change_source: str
    if diff_arg is None:
        try:
            patch_text = git_diff_head(workspace)
        except PolicyEvalError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1
        change_source = "git_head"
    elif diff_arg == "-":
        patch_text = sys.stdin.read()
        change_source = "stdin"
    else:
        p = Path(diff_arg)
        if not p.is_file():
            print(json.dumps({"error": f"diff file not found: {p}"}), file=sys.stderr)
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
        use_gitignore=not args.no_gitignore,
        change_source=change_source,
        index_from_git_head=(change_source == "git_head"),
    )

    try:
        report = evaluate(opts)
    except (PolicyEvalError, ManifestError, PatchApplyError, OpaEngineError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    print(json.dumps(report, indent=indent))

    if args.strict:
        if report.get("allow") is False:
            return 2
        for f in report.get("findings") or []:
            if f.get("severity") == "error":
                return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

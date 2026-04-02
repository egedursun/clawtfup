from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .exceptions import ManifestError, OpaEngineError, PatchApplyError, PolicyEvalError
from .feedback import enrich_finding, load_workspace_feedback
from .findings_normalize import normalize_from_report_value, summarize_severities
from .input_merge import deep_merge
from .manifest import (
    load_manifest,
    manifest_findings_query,
    manifest_queries,
)
from .git_workspace import index_at_git_head
from .opa_runner import opa_eval_query, opa_version, resolve_opa_binary
from .patch_apply import apply_unified_diff, combined_changed_content
from .workspace import IndexResult as WorkspaceIndexResult
from .workspace import index_workspace


def opa_bundle_dir(bundle_root: Path) -> Path:
    """Directory passed to `opa eval -d` (Rego only; YAML manifests stay outside)."""
    rego = bundle_root / "rego"
    if rego.is_dir():
        return rego.resolve()
    return bundle_root.resolve()


@dataclass
class EvaluateOptions:
    workspace: Path
    bundle_root: Path  #: Policies root: ``<workspace>/.clawtfup/policies`` (``policy_eval.yaml`` + ``rego/``)
    patch_text: str
    input_overlay: dict[str, Any] | None = None
    input_json_path: Path | None = None
    queries: list[str] | None = None
    max_files: int = 10_000
    max_file_bytes: int = 512 * 1024
    exclude_globs: list[str] = field(default_factory=list)
    use_gitignore: bool = True
    opa_binary: str | None = None
    #: e.g. ``git_head``, ``diff_file``, ``stdin`` — recorded in the report for transparency
    change_source: str | None = None
    #: When True, index ``HEAD`` (+ untracked) so a ``git diff HEAD`` applies to the right baseline.
    index_from_git_head: bool = False
    #: When True (default), every indexed file is treated as changed (full-tree policy scan).
    #: Set False with CLI ``--diff-only`` to scope policies to git diff / ``--diff-file`` paths only.
    full_scan: bool = True
    #: If set, only these paths (prefix match, posix) are treated as changed during a full scan.
    scan_prefix: str | None = None


def _load_overlay_path(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.is_file():
        raise PolicyEvalError(f"input JSON not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PolicyEvalError("input JSON root must be an object")
    return data


def _overlay_input_fragment(data: dict[str, Any]) -> dict[str, Any]:
    """If file wraps with {\"input\": {...}}, use inner object; else whole file is input fragment."""
    inner = data.get("input")
    if isinstance(inner, dict):
        return inner
    return data


def build_workspace_fragment(
    workspace: Path,
    patch_text: str,
    *,
    max_files: int,
    max_file_bytes: int,
    exclude_globs: list[str],
    use_gitignore: bool,
    index_from_git_head: bool = False,
    full_scan: bool = True,
    scan_prefix: str | None = None,
) -> tuple[dict[str, Any], WorkspaceIndexResult]:
    if index_from_git_head:
        idx = index_at_git_head(
            workspace,
            max_files=max_files,
            max_file_bytes=max_file_bytes,
            exclude_globs=exclude_globs,
            use_gitignore=use_gitignore,
        )
    else:
        idx = index_workspace(
            workspace,
            max_files=max_files,
            max_file_bytes=max_file_bytes,
            exclude_globs=exclude_globs,
            use_gitignore=use_gitignore,
        )
    try:
        files_after, changed_paths = apply_unified_diff(idx.files, patch_text)
    except PatchApplyError:
        raise
    if scan_prefix is not None:
        pfx = scan_prefix.strip().replace("\\", "/").strip("/")
        changed_paths = sorted(
            path
            for path in files_after
            if path == pfx or path.startswith(f"{pfx}/")
        )
    elif full_scan:
        changed_paths = sorted(files_after.keys())
    combined = combined_changed_content(files_after, changed_paths)
    fragment = {
        "workspace": {
            "root": str(workspace.resolve()),
            "files_before": idx.files,
            "files_after": files_after,
            "changed_paths": changed_paths,
            "combined_after": combined,
        },
        "change": {"format": "unified", "text": patch_text},
        "requirements": {"must_contain": [], "must_not_contain": []},
        "policy": {"enforce_anchor_on_changed_python": False},
    }
    return fragment, idx


def evaluate(opts: EvaluateOptions) -> dict[str, Any]:
    t0 = time.perf_counter()
    eval_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()

    bundle_root = opts.bundle_root.resolve()
    manifest = load_manifest(bundle_root)
    queries = list(opts.queries) if opts.queries else manifest_queries(manifest)
    if not queries:
        raise ManifestError(
            "No OPA queries: add 'queries' to policy_eval.yaml or pass --query"
        )

    file_overlay = _overlay_input_fragment(_load_overlay_path(opts.input_json_path))
    inline_overlay = opts.input_overlay or {}

    frag, widx = build_workspace_fragment(
        opts.workspace,
        opts.patch_text,
        max_files=opts.max_files,
        max_file_bytes=opts.max_file_bytes,
        exclude_globs=opts.exclude_globs,
        use_gitignore=opts.use_gitignore,
        index_from_git_head=opts.index_from_git_head,
        full_scan=opts.full_scan,
        scan_prefix=opts.scan_prefix,
    )

    # OPA -i document root is Rego's `input`
    merged_input: dict[str, Any] = deep_merge(frag, file_overlay)
    merged_input = deep_merge(merged_input, inline_overlay)

    opa_dir = opa_bundle_dir(bundle_root)
    opa = opts.opa_binary or resolve_opa_binary()
    o_ver = opa_version(opa)

    results: dict[str, Any] = {}
    query_errors: list[dict[str, Any]] = []
    for q in queries:
        try:
            results[q] = opa_eval_query(
                bundle_dir=opa_dir,
                input_doc=merged_input,
                query=q,
                opa_binary=opa,
            )
        except OpaEngineError as e:
            query_errors.append({"query": q, "error": str(e)})

    findings_query = manifest_findings_query(manifest)
    findings: list[dict[str, Any]] = []
    allow: bool | None = None

    if findings_query and findings_query in results and not any(
        e["query"] == findings_query for e in query_errors
    ):
        allow, raw_findings = normalize_from_report_value(results[findings_query])
        fb_map = load_workspace_feedback(opts.workspace)
        findings = [enrich_finding(f, fb_map) for f in raw_findings]
    elif findings_query and findings_query not in results:
        pass

    duration_ms = int((time.perf_counter() - t0) * 1000)

    merged_sources: list[str] = []
    if opts.input_json_path:
        merged_sources.append(str(opts.input_json_path))
    if opts.input_overlay:
        merged_sources.append("inline_overlay")

    report: dict[str, Any] = {
        "schema_version": 1,
        "evaluation_id": eval_id,
        "timestamp": ts,
        "duration_ms": duration_ms,
        "inputs": {
            "workspace": str(opts.workspace.resolve()),
            "policy_bundle": str(bundle_root),
            "opa_data_dir": str(opa_dir),
            "changed_paths": merged_input["workspace"]["changed_paths"],
            "change_source": opts.change_source,
            "scan_mode": (
                "prefix"
                if opts.scan_prefix
                else ("full_tree" if opts.full_scan else "diff_only")
            ),
            "scan_prefix": opts.scan_prefix,
            "index_baseline": "git_head" if opts.index_from_git_head else "working_tree",
            "patch_stats": {
                "bytes": len(opts.patch_text.encode("utf-8")),
                "lines": opts.patch_text.count("\n") + (0 if opts.patch_text.endswith("\n") else 1),
            },
            "merged_input_sources": merged_sources,
            "index_warnings": widx.warnings,
            "skipped_binary_count": len(widx.skipped_binary),
            "skipped_large_count": len(widx.skipped_large),
        },
        "results": results,
        "engine": {
            "opa_version": o_ver,
            "queries": queries,
        },
    }

    if query_errors:
        report["query_errors"] = query_errors

    if findings:
        report["findings"] = findings
        report["summary"] = {"by_severity": summarize_severities(findings)}
    if allow is not None:
        report["allow"] = allow

    return report

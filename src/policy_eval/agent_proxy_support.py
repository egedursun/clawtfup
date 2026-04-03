"""Evaluate subprocess helpers for agent CLI hooks (no workspace JSON artifacts)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

# Claude / Codex hook context caps (~10k); stay under typical limits.
_HOOK_CONTEXT_MAX = 10_000


def truncate_hook_context(text: str, *, max_len: int = _HOOK_CONTEXT_MAX) -> str:
    if len(text) <= max_len:
        return text
    tail = "\n...(truncated; run `clawtfup evaluate --pretty` for the full report.)"
    return text[: max_len - len(tail)] + tail


def stdin_hook_event_name(event: dict, default: str) -> str:
    """Normalize Claude/Codex (``hook_event_name``) vs VS Code / Antigravity (``hookEventName``)."""
    for key in ("hook_event_name", "hookEventName"):
        v = event.get(key)
        if isinstance(v, str) and v.strip():
            return v
    return default


def format_findings_human(report: dict) -> str:
    lines: list[str] = []
    findings = report.get("findings") or []
    for f in findings:
        if not isinstance(f, dict):
            continue
        code = f.get("code") or ""
        msg = f.get("message") or ""
        if code and msg:
            lines.append(f"- [{code}] {msg}")
        elif msg:
            lines.append(f"- {msg}")
        elif code:
            lines.append(f"- [{code}]")
    if not lines:
        if "allow" in report and not report.get("allow"):
            lines.append("- Policy denied (see evaluate JSON for details).")
    return "\n".join(lines)


def format_findings_compact_for_hook(
    report: dict,
    *,
    max_items: int = 6,
    max_line_len: int = 96,
) -> str:
    """Short text for Claude hooks: counts + a few truncated lines, not a full dump."""
    findings = [f for f in (report.get("findings") or []) if isinstance(f, dict)]
    err_n = sum(1 for f in findings if f.get("severity") == "error")
    warn_n = sum(1 for f in findings if f.get("severity") == "warning")
    head = f"clawtfup: policy failed ({err_n} error(s), {warn_n} warning(s))."
    if not findings and not report.get("allow", True):
        return head + " Run `clawtfup evaluate --pretty` in the repo for details."

    lines_out: list[str] = [head, ""]
    for i, f in enumerate(findings):
        if i >= max_items:
            rest = len(findings) - i
            if rest > 0:
                lines_out.append(
                    f"… +{rest} more (run `clawtfup evaluate --pretty` for full list)."
                )
            break
        code = (f.get("code") or "?").strip()
        msg = (f.get("message") or "").replace("\n", " ").strip()
        path = (f.get("path") or "").strip()
        if len(msg) > max_line_len:
            msg = msg[: max_line_len - 1] + "…"
        if path:
            line = f"• [{code}] {path}: {msg}"
        else:
            line = f"• [{code}] {msg}"
        lines_out.append(line)

    if len(findings) == 0:
        lines_out.append("Run `clawtfup evaluate --pretty` in the repo root.")

    return "\n".join(lines_out)


def run_evaluate_subprocess(workspace: Path) -> tuple[int, dict | None]:
    """Run evaluate in a child interpreter; returns (exit_code, parsed_report_or_none)."""
    cmd = [
        sys.executable,
        "-m",
        "policy_eval",
        "evaluate",
        "--workspace",
        str(workspace),
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    raw_out = (proc.stdout or "").strip()
    raw_err = (proc.stderr or "").strip()
    data: dict | None = None
    if raw_out.startswith("{"):
        try:
            data = json.loads(raw_out)
        except json.JSONDecodeError:
            data = None
    if data is None and raw_err.startswith("{"):
        try:
            data = json.loads(raw_err)
        except json.JSONDecodeError:
            data = None
    if data is None and raw_out:
        try:
            data = json.loads(raw_out.splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            data = None
    return proc.returncode, data


def evaluation_passed(report: dict | None, exit_code: int) -> bool:
    if exit_code != 0:
        return False
    if not report:
        return False
    if not report.get("allow", True):
        return False
    for f in report.get("findings") or []:
        if isinstance(f, dict) and f.get("severity") == "error":
            return False
    return True


def _posix_stdin_forward(child_stdin, stop: threading.Event) -> None:
    fd = sys.stdin.fileno()
    while not stop.is_set():
        try:
            data = os.read(fd, 65536)
        except (BrokenPipeError, OSError):
            break
        if not data:
            break
        try:
            child_stdin.write(data)
            child_stdin.flush()
        except BrokenPipeError:
            break


def _win32_stdin_forward(child_stdin, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            data = sys.stdin.buffer.read1(4096)
        except (BrokenPipeError, OSError):
            break
        if not data:
            break
        try:
            child_stdin.write(data)
            child_stdin.flush()
        except BrokenPipeError:
            break

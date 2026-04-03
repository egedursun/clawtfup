"""Spawn agent CLIs with PTY (interactive) or pipes (scripted); plain I/O relay."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

from .agent_proxy_pty import run_agent_proxy_pty
from .agent_proxy_support import _posix_stdin_forward, _win32_stdin_forward
from .defaults import default_policies_dir


def _pipe_copy_stdout(proc: subprocess.Popen, stop: threading.Event) -> None:
    out = proc.stdout
    if out is None:
        return
    while not stop.is_set():
        chunk = out.read(65536)
        if not chunk:
            break
        os.write(1, chunk)


def _pipe_copy_stderr(proc: subprocess.Popen, stop: threading.Event) -> None:
    err = proc.stderr
    if err is None:
        return
    while not stop.is_set():
        chunk = err.read(65536)
        if not chunk:
            break
        os.write(2, chunk)


def _run_agent_proxy_pipes(
    exe: str,
    child_argv: list[str],
    ws: Path,
) -> int:
    try:
        proc = subprocess.Popen(
            [exe, *child_argv],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(ws),
        )
    except FileNotFoundError:
        sys.stderr.write(f"clawtfup cli: executable not found: {exe!r}\n")
        return 127

    if proc.stdin is None or proc.stdout is None or proc.stderr is None:
        sys.stderr.write("clawtfup cli: failed to open child stdio pipes\n")
        proc.terminate()
        return 1

    stop = threading.Event()
    tout = threading.Thread(
        target=_pipe_copy_stdout,
        args=(proc, stop),
        daemon=False,
        name="clawtfup-out",
    )
    terr = threading.Thread(
        target=_pipe_copy_stderr,
        args=(proc, stop),
        daemon=False,
        name="clawtfup-err",
    )
    stdin_target = _win32_stdin_forward if sys.platform == "win32" else _posix_stdin_forward
    stdin_thread = threading.Thread(
        target=stdin_target,
        args=(proc.stdin, stop),
        daemon=False,
        name="clawtfup-stdin",
    )
    tout.start()
    terr.start()
    stdin_thread.start()

    proc.wait()
    stop.set()
    stdin_thread.join(timeout=5.0)
    tout.join(timeout=5.0)
    terr.join(timeout=5.0)
    return proc.returncode or 0


def _run_agent_cli_proxy(
    child_argv: list[str],
    workspace: Path,
    *,
    executable: str | None,
    env_bin_var: str,
    default_bin: str,
) -> int:
    ws = workspace.resolve()
    policies = default_policies_dir(ws)
    if not policies.is_dir():
        sys.stderr.write(
            f"clawtfup cli: policies directory not found: {policies}\n"
            "Create .clawtfup/policies/ before using the proxy.\n"
        )
        return 1

    exe = executable or os.environ.get(env_bin_var) or default_bin
    posix = sys.platform != "win32"

    if posix and sys.stdin.isatty():
        return run_agent_proxy_pty(exe, child_argv, ws)
    return _run_agent_proxy_pipes(exe, child_argv, ws)


def run_claude_proxy(
    child_argv: list[str],
    workspace: Path,
    *,
    claude_executable: str | None = None,
) -> int:
    """
    Spawn ``claude`` (or *claude_executable*) with *child_argv* and relay stdio.

    Policy enforcement for Claude Code is via project hooks (``.claude/settings.json``),
    not via this proxy.
    """
    return _run_agent_cli_proxy(
        child_argv,
        workspace,
        executable=claude_executable,
        env_bin_var="CLAWTFUP_CLAUDE_BIN",
        default_bin="claude",
    )


def run_codex_proxy(
    child_argv: list[str],
    workspace: Path,
    *,
    codex_executable: str | None = None,
) -> int:
    """
    Spawn the Codex CLI (``codex`` or *codex_executable*) with *child_argv* and relay stdio.

    Policy enforcement uses Codex ``hooks.json`` (see ``.codex/hooks.json`` in this repo);
    enable hooks in ``config.toml`` with ``[features] codex_hooks = true``.
    """
    return _run_agent_cli_proxy(
        child_argv,
        workspace,
        executable=codex_executable,
        env_bin_var="CLAWTFUP_CODEX_BIN",
        default_bin="codex",
    )


def run_gemini_proxy(
    child_argv: list[str],
    workspace: Path,
    *,
    gemini_executable: str | None = None,
) -> int:
    """
    Spawn the Gemini CLI (``gemini`` or *gemini_executable*) with *child_argv* and relay stdio.

    Policy enforcement uses project ``.gemini/settings.json`` hooks (see this repo's
    ``.gemini/settings.json``) wired to ``hook-gemini-*`` commands.
    """
    return _run_agent_cli_proxy(
        child_argv,
        workspace,
        executable=gemini_executable,
        env_bin_var="CLAWTFUP_GEMINI_BIN",
        default_bin="gemini",
    )


def run_qwen_proxy(
    child_argv: list[str],
    workspace: Path,
    *,
    qwen_executable: str | None = None,
) -> int:
    """
    Spawn Qwen Code (``qwen`` or *qwen_executable*) with *child_argv* and relay stdio.

    Policy enforcement uses project ``.qwen/settings.json`` hooks wired to ``hook-qwen-*``.
    """
    return _run_agent_cli_proxy(
        child_argv,
        workspace,
        executable=qwen_executable,
        env_bin_var="CLAWTFUP_QWEN_BIN",
        default_bin="qwen",
    )


def run_kilo_proxy(
    child_argv: list[str],
    workspace: Path,
    *,
    kilo_executable: str | None = None,
) -> int:
    """
    Spawn Kilocode / Kilo CLI (``kilo`` or *kilo_executable*) with *child_argv* and relay stdio.

    Policy enforcement uses the OpenCode-compatible plugin under ``.opencode/plugins/`` (see
    ``clawtfup-policy.mjs``). Kilo reads the same config layout as OpenCode under
    ``~/.config/kilo/`` and project ``opencode.json`` / ``.opencode/``.
    """
    return _run_agent_cli_proxy(
        child_argv,
        workspace,
        executable=kilo_executable,
        env_bin_var="CLAWTFUP_KILO_BIN",
        default_bin="kilo",
    )

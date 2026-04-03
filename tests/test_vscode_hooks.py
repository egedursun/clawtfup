"""Unit tests for VS Code / Antigravity hook commands and shared stdin normalization."""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import patch

from policy_eval.agent_proxy_support import stdin_hook_event_name


def test_stdin_hook_event_name_prefers_snake_then_camel() -> None:
    assert stdin_hook_event_name({"hook_event_name": "A"}, "d") == "A"
    assert stdin_hook_event_name({"hookEventName": "B"}, "d") == "B"
    assert stdin_hook_event_name({"hook_event_name": "", "hookEventName": "C"}, "d") == "C"
    assert stdin_hook_event_name({"hook_event_name": "  ", "hookEventName": "C"}, "d") == "C"
    assert stdin_hook_event_name({}, "Stop") == "Stop"


def _mkdir_policies(root) -> None:
    (root / ".clawtfup" / "policies").mkdir(parents=True)


def test_codex_post_tool_use_respects_hook_event_name_camelcase(tmp_path) -> None:
    from policy_eval.codex_hook_cmds import hook_codex_post_tool_use_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hookEventName": "PostToolUse"}
    out = io.StringIO()
    fake_report = {
        "allow": False,
        "findings": [{"code": "X", "message": "bad", "severity": "error"}],
    }
    with patch(
        "policy_eval.codex_hook_cmds.run_evaluate_subprocess",
        return_value=(2, fake_report),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_codex_post_tool_use_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert parsed["hookSpecificOutput"]["hookEventName"] == "PostToolUse"


def test_vscode_stop_blocks_on_policy_fail(tmp_path) -> None:
    from policy_eval.vscode_hook_cmds import hook_vscode_stop_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hookEventName": "Stop", "stop_hook_active": False}
    out = io.StringIO()
    fake_report = {
        "allow": False,
        "findings": [{"code": "E", "message": "nope", "severity": "error"}],
    }
    with patch(
        "policy_eval.vscode_hook_cmds.run_evaluate_subprocess",
        return_value=(2, fake_report),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_vscode_stop_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert parsed["hookSpecificOutput"]["decision"] == "block"
    assert parsed["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert "nope" in parsed["hookSpecificOutput"]["reason"]


def test_vscode_stop_no_stdout_on_pass(tmp_path) -> None:
    from policy_eval.vscode_hook_cmds import hook_vscode_stop_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hookEventName": "Stop"}
    out = io.StringIO()
    with patch(
        "policy_eval.vscode_hook_cmds.run_evaluate_subprocess",
        return_value=(0, {"allow": True, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_vscode_stop_cmd() == 0
    assert out.getvalue() == ""


def test_vscode_stop_skips_when_stop_hook_active(tmp_path) -> None:
    from policy_eval.vscode_hook_cmds import hook_vscode_stop_cmd

    _mkdir_policies(tmp_path)
    event = {
        "cwd": str(tmp_path),
        "stop_hook_active": True,
    }
    out = io.StringIO()
    with patch(
        "policy_eval.vscode_hook_cmds.run_evaluate_subprocess",
        return_value=(2, {"allow": False, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_vscode_stop_cmd() == 0
    assert out.getvalue() == ""


def test_vscode_stop_skips_when_stop_hook_active_camelcase(tmp_path) -> None:
    from policy_eval.vscode_hook_cmds import hook_vscode_stop_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "stopHookActive": True}
    out = io.StringIO()
    called: list = []

    def _track(*args, **kwargs):
        called.append(1)
        return 0, {"allow": True, "findings": []}

    with patch(
        "policy_eval.vscode_hook_cmds.run_evaluate_subprocess",
        side_effect=_track,
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_vscode_stop_cmd() == 0
    assert called == []
    assert out.getvalue() == ""

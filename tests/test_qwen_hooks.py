"""Unit tests for Qwen Code hook commands."""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import patch

from policy_eval.agent_proxy_support import stop_hook_retry_active


def test_stop_hook_retry_active() -> None:
    assert stop_hook_retry_active({"stop_hook_active": True})
    assert stop_hook_retry_active({"stopHookActive": True})
    assert not stop_hook_retry_active({"stop_hook_active": False})
    assert not stop_hook_retry_active({})


def _mkdir_policies(root) -> None:
    (root / ".clawtfup" / "policies").mkdir(parents=True)


def test_qwen_post_tool_use_delegates_to_codex(tmp_path) -> None:
    from policy_eval.qwen_hook_cmds import hook_qwen_post_tool_use_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "PostToolUse"}
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
        assert hook_qwen_post_tool_use_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert parsed["decision"] == "block"
    assert "[X]" in parsed["hookSpecificOutput"]["additionalContext"]


def test_qwen_stop_top_level_block_on_fail(tmp_path) -> None:
    from policy_eval.qwen_hook_cmds import hook_qwen_stop_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "Stop", "stop_hook_active": False}
    out = io.StringIO()
    fake_report = {
        "allow": False,
        "findings": [{"code": "E", "message": "nope", "severity": "error"}],
    }
    with patch(
        "policy_eval.qwen_hook_cmds.run_evaluate_subprocess",
        return_value=(2, fake_report),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_qwen_stop_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert parsed["decision"] == "block"
    assert "hookSpecificOutput" not in parsed
    assert "nope" in parsed["reason"]


def test_qwen_stop_no_stdout_on_pass(tmp_path) -> None:
    from policy_eval.qwen_hook_cmds import hook_qwen_stop_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "Stop"}
    out = io.StringIO()
    with patch(
        "policy_eval.qwen_hook_cmds.run_evaluate_subprocess",
        return_value=(0, {"allow": True, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_qwen_stop_cmd() == 0
    assert out.getvalue() == ""


def test_qwen_stop_skips_when_retry_active(tmp_path) -> None:
    from policy_eval.qwen_hook_cmds import hook_qwen_stop_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "stop_hook_active": True}
    out = io.StringIO()
    with patch(
        "policy_eval.qwen_hook_cmds.run_evaluate_subprocess",
        return_value=(2, {"allow": False, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_qwen_stop_cmd() == 0
    assert out.getvalue() == ""

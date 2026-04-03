"""Unit tests for Gemini CLI hook commands."""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import patch


def _mkdir_policies(root) -> None:
    (root / ".clawtfup" / "policies").mkdir(parents=True)


def test_gemini_hook_after_tool_denies_on_policy_fail(tmp_path) -> None:
    from policy_eval.gemini_hook_cmds import hook_gemini_after_tool_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "AfterTool"}
    out = io.StringIO()
    fake_report = {
        "allow": False,
        "findings": [{"code": "X", "message": "bad", "severity": "error"}],
    }
    with patch(
        "policy_eval.gemini_hook_cmds.run_evaluate_subprocess",
        return_value=(2, fake_report),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_gemini_after_tool_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert parsed["decision"] == "deny"
    assert parsed["hookSpecificOutput"]["hookEventName"] == "AfterTool"
    ctx = parsed["hookSpecificOutput"]["additionalContext"]
    assert "[X]" in ctx
    assert "bad" in ctx


def test_gemini_hook_after_tool_no_stdout_on_pass(tmp_path) -> None:
    from policy_eval.gemini_hook_cmds import hook_gemini_after_tool_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "AfterTool"}
    out = io.StringIO()
    with patch(
        "policy_eval.gemini_hook_cmds.run_evaluate_subprocess",
        return_value=(0, {"allow": True, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_gemini_after_tool_cmd() == 0
    assert out.getvalue() == ""


def test_gemini_hook_before_agent_injects_eval_instruction(tmp_path) -> None:
    from policy_eval.gemini_hook_cmds import hook_gemini_before_agent_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "BeforeAgent"}
    out = io.StringIO()
    with patch(
        "policy_eval.gemini_hook_cmds.run_evaluate_subprocess",
        return_value=(0, {"allow": True, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_gemini_before_agent_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert "decision" not in parsed
    assert parsed["hookSpecificOutput"]["hookEventName"] == "BeforeAgent"
    ctx = parsed["hookSpecificOutput"]["additionalContext"]
    assert "passed" in ctx.lower()
    assert "clawtfup evaluate --pretty" in ctx


def test_gemini_hook_before_agent_skips_without_policies_dir(tmp_path) -> None:
    from policy_eval.gemini_hook_cmds import hook_gemini_before_agent_cmd

    event = {"cwd": str(tmp_path), "hook_event_name": "BeforeAgent"}
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_gemini_before_agent_cmd() == 0
    assert out.getvalue() == ""

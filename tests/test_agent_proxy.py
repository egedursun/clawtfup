"""Unit tests for agent proxy helpers and Claude PostToolUse hook."""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import patch

from policy_eval.agent_proxy import evaluation_passed, format_findings_human
from policy_eval.agent_proxy_support import format_findings_compact_for_hook, truncate_hook_context


def test_format_findings_compact_for_hook() -> None:
    text = format_findings_compact_for_hook(
        {
            "allow": False,
            "findings": [
                {"code": "A", "message": "one", "severity": "error", "path": "p.py"},
                {"code": "B", "message": "two", "severity": "warning", "path": ""},
            ],
        }
    )
    assert "1 error(s), 1 warning(s)" in text
    assert "[A]" in text
    assert "p.py" in text


def test_format_findings_human() -> None:
    text = format_findings_human(
        {
            "findings": [
                {"code": "X", "message": "bad"},
                {"message": "no code"},
            ]
        }
    )
    assert "[X]" in text
    assert "bad" in text
    assert "no code" in text


def test_truncate_hook_context() -> None:
    short = "hello"
    assert truncate_hook_context(short) == short
    long_body = "x" * 20_000
    out = truncate_hook_context(long_body, max_len=100)
    assert len(out) <= 100
    assert "truncated" in out


def test_evaluation_passed() -> None:
    assert evaluation_passed({"allow": True, "findings": []}, 0)
    assert not evaluation_passed({"allow": False, "findings": []}, 0)
    assert not evaluation_passed(
        {"allow": True, "findings": [{"severity": "error"}]},
        0,
    )
    assert not evaluation_passed(None, 2)


def _mkdir_policies(root) -> None:
    (root / ".clawtfup" / "policies").mkdir(parents=True)


def test_hook_post_tool_use_blocks_on_policy_fail(tmp_path) -> None:
    from policy_eval.claude_hook_cmds import hook_post_tool_use_cmd

    _mkdir_policies(tmp_path)
    event = {
        "cwd": str(tmp_path),
        "hook_event_name": "PostToolUse",
    }
    out = io.StringIO()
    fake_report = {
        "allow": False,
        "findings": [{"code": "X", "message": "bad", "severity": "error"}],
    }
    with patch(
        "policy_eval.claude_hook_cmds.run_evaluate_subprocess",
        return_value=(2, fake_report),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_post_tool_use_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert parsed["decision"] == "block"
    assert parsed["suppressOutput"]
    assert parsed["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    ctx = parsed["hookSpecificOutput"]["additionalContext"]
    assert "[X]" in ctx
    assert "bad" in ctx


def test_hook_post_tool_use_no_stdout_on_pass(tmp_path) -> None:
    from policy_eval.claude_hook_cmds import hook_post_tool_use_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "PostToolUse"}
    out = io.StringIO()
    with patch(
        "policy_eval.claude_hook_cmds.run_evaluate_subprocess",
        return_value=(0, {"allow": True, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_post_tool_use_cmd() == 0
    assert out.getvalue() == ""


def test_hook_user_prompt_submit_injects_eval_instruction(tmp_path) -> None:
    from policy_eval.claude_hook_cmds import hook_user_prompt_submit_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "UserPromptSubmit"}
    out = io.StringIO()
    with patch(
        "policy_eval.claude_hook_cmds.run_evaluate_subprocess",
        return_value=(0, {"allow": True, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_user_prompt_submit_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert "decision" not in parsed
    assert parsed["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    ctx = parsed["hookSpecificOutput"]["additionalContext"]
    assert "passed" in ctx.lower()
    assert "clawtfup evaluate --pretty" in ctx
    assert str(tmp_path.resolve()) in ctx


def test_hook_user_prompt_submit_shows_failures_without_block(tmp_path) -> None:
    from policy_eval.claude_hook_cmds import hook_user_prompt_submit_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "UserPromptSubmit"}
    out = io.StringIO()
    fake_report = {
        "allow": False,
        "findings": [{"code": "Z", "message": "nope", "severity": "error"}],
    }
    with patch(
        "policy_eval.claude_hook_cmds.run_evaluate_subprocess",
        return_value=(2, fake_report),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_user_prompt_submit_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert "decision" not in parsed
    ctx = parsed["hookSpecificOutput"]["additionalContext"]
    assert "[Z]" in ctx
    assert "nope" in ctx


def test_hook_user_prompt_submit_skips_without_policies_dir(tmp_path) -> None:
    from policy_eval.claude_hook_cmds import hook_user_prompt_submit_cmd

    event = {"cwd": str(tmp_path), "hook_event_name": "UserPromptSubmit"}
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_user_prompt_submit_cmd() == 0
    assert out.getvalue() == ""


def test_hook_post_tool_use_skips_without_policies_dir(tmp_path) -> None:
    from policy_eval.claude_hook_cmds import hook_post_tool_use_cmd

    event = {"cwd": str(tmp_path), "hook_event_name": "PostToolUse"}
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_post_tool_use_cmd() == 0
    assert out.getvalue() == ""


def test_codex_hook_post_tool_use_blocks_on_policy_fail(tmp_path) -> None:
    from policy_eval.codex_hook_cmds import hook_codex_post_tool_use_cmd

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
        assert hook_codex_post_tool_use_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert parsed["decision"] == "block"
    assert "suppressOutput" not in parsed
    assert parsed["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    ctx = parsed["hookSpecificOutput"]["additionalContext"]
    assert "[X]" in ctx
    assert "bad" in ctx


def test_codex_hook_post_tool_use_no_stdout_on_pass(tmp_path) -> None:
    from policy_eval.codex_hook_cmds import hook_codex_post_tool_use_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "PostToolUse"}
    out = io.StringIO()
    with patch(
        "policy_eval.codex_hook_cmds.run_evaluate_subprocess",
        return_value=(0, {"allow": True, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_codex_post_tool_use_cmd() == 0
    assert out.getvalue() == ""


def test_codex_hook_user_prompt_submit_injects_eval_instruction(tmp_path) -> None:
    from policy_eval.codex_hook_cmds import hook_codex_user_prompt_submit_cmd

    _mkdir_policies(tmp_path)
    event = {"cwd": str(tmp_path), "hook_event_name": "UserPromptSubmit"}
    out = io.StringIO()
    with patch(
        "policy_eval.codex_hook_cmds.run_evaluate_subprocess",
        return_value=(0, {"allow": True, "findings": []}),
    ), patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_codex_user_prompt_submit_cmd() == 0
    parsed = json.loads(out.getvalue())
    assert "decision" not in parsed
    assert parsed["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    ctx = parsed["hookSpecificOutput"]["additionalContext"]
    assert "passed" in ctx.lower()
    assert "clawtfup evaluate --pretty" in ctx


def test_codex_hook_user_prompt_submit_skips_without_policies_dir(tmp_path) -> None:
    from policy_eval.codex_hook_cmds import hook_codex_user_prompt_submit_cmd

    event = {"cwd": str(tmp_path), "hook_event_name": "UserPromptSubmit"}
    out = io.StringIO()
    with patch.object(sys, "stdin", io.StringIO(json.dumps(event))), patch.object(
        sys, "stdout", out
    ):
        assert hook_codex_user_prompt_submit_cmd() == 0
    assert out.getvalue() == ""



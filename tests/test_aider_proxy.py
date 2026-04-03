"""Tests for Aider CLI proxy."""

from __future__ import annotations

from policy_eval.agent_proxy_run import run_aider_proxy


def test_run_aider_proxy_requires_policies_dir(tmp_path) -> None:
    assert run_aider_proxy([], tmp_path) == 1

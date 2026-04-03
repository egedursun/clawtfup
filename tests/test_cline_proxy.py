"""Tests for Cline CLI proxy."""

from __future__ import annotations

from policy_eval.agent_proxy_run import run_cline_proxy


def test_run_cline_proxy_requires_policies_dir(tmp_path) -> None:
    assert run_cline_proxy([], tmp_path) == 1

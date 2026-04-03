"""Tests for Charm Crush CLI proxy."""

from __future__ import annotations

from policy_eval.agent_proxy_run import run_crush_proxy


def test_run_crush_proxy_requires_policies_dir(tmp_path) -> None:
    assert run_crush_proxy([], tmp_path) == 1

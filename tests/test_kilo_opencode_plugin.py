"""Sanity checks for the Kilocode / OpenCode clawtfup plugin file."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PLUGIN = _REPO_ROOT / ".opencode" / "plugins" / "clawtfup-policy.mjs"


def test_kilo_opencode_plugin_file_exists() -> None:
    assert _PLUGIN.is_file(), f"missing {_PLUGIN}"


def test_kilo_opencode_plugin_contains_tool_hook_and_spawn() -> None:
    text = _PLUGIN.read_text(encoding="utf-8")
    assert "tool.execute.after" in text
    assert "spawnSync" in text
    assert "ClawtfupPolicy" in text
    assert ".clawtfup" in text and "policies" in text

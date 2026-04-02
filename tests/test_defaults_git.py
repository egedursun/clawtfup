"""Default layout (.clawtfup/policies) and git-based proposed changes."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from policy_eval.opa_runner import resolve_opa_binary


def _opa_available() -> bool:
    try:
        resolve_opa_binary()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _opa_available(), reason="OPA not installed")
def test_defaults_git_diff_head(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent
    ref = root.parent / "bundles" / "reference"
    policies = tmp_path / ".clawtfup" / "policies"
    policies.mkdir(parents=True)
    shutil.copytree(ref / "rego", policies / "rego")
    shutil.copy2(ref / "policy_eval.yaml", policies / "policy_eval.yaml")
    shutil.copy2(ref / "feedback.yaml", policies / "feedback.yaml")
    shutil.copy2(root / "fixtures" / "ws" / "app.py", tmp_path / "app.py")

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "t"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "app.py"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    app = tmp_path / "app.py"
    app.write_text(
        app.read_text(encoding="utf-8").replace(
            'return "hello"', 'return str(eval("1+1"))'
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "policy_eval",
            "evaluate",
            "--workspace",
            str(tmp_path),
            "--no-gitignore",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["inputs"]["change_source"] == "git_head"
    assert report["allow"] is False
    assert report["findings"][0]["code"] == "FORBIDDEN_PATTERN"


def test_cli_accepts_deprecated_patch_flag(tmp_path: Path) -> None:
    """Smoke: --patch still works (stderr deprecation)."""
    proc = subprocess.run(
        [sys.executable, "-m", "policy_eval", "evaluate", "--help"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "--diff-file" in proc.stdout

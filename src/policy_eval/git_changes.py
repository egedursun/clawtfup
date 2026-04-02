"""Resolve **proposed changes** as a unified diff (typically `git diff HEAD`)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .exceptions import PolicyEvalError


def git_diff_head(workspace: Path) -> str:
    """
    Return the unified diff of the working tree vs ``HEAD`` (staged + unstaged changes).

    Used when the user does not pass a diff file: “what would change vs last commit.”
    """
    git = shutil.which("git")
    if not git:
        raise PolicyEvalError(
            "Git not found on PATH. Pass proposed changes explicitly: "
            "--diff-file <path> or --diff-file - (stdin)."
        )
    ws = str(workspace.resolve())
    chk = subprocess.run(
        [git, "-C", ws, "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )
    if chk.returncode != 0:
        raise PolicyEvalError(
            "No diff file given: expected a git repo here to run `git diff HEAD`, "
            "or pass --diff-file / stdin with a unified diff of your proposed edits."
        )
    # Exclude `.clawtfup/` — those paths are not in the workspace index (policies/feedback are separate).
    proc = subprocess.run(
        [git, "-C", ws, "diff", "HEAD", "--", ".", ":(exclude).clawtfup"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise PolicyEvalError(f"git diff HEAD failed: {err}")
    return proc.stdout

"""Convention paths under a workspace root."""

from __future__ import annotations

from pathlib import Path

CLAWTFUP = ".clawtfup"
# Workspace-root file; patterns use the same syntax as .gitignore (gitwildmatch).
CFUPIGNORE_NAME = ".cfupignore"


def default_policies_dir(workspace: Path) -> Path:
    return (workspace / CLAWTFUP / "policies").resolve()

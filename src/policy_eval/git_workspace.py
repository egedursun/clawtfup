"""Index workspace file contents at ``git HEAD`` plus untracked files (for ``git diff HEAD``)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .exceptions import PolicyEvalError
from .workspace import (
    IndexResult,
    _excluded_by_glob,
    _load_cfupignore_spec,
    _load_gitignore_spec,
    _skipped_by_ignore_rules,
)


def index_at_git_head(
    root: Path,
    *,
    max_files: int,
    max_file_bytes: int,
    exclude_globs: list[str],
    use_gitignore: bool,
    use_cfupignore: bool = True,
) -> IndexResult:
    """
    ``files`` = committed tree at ``HEAD`` for tracked paths, merged with untracked files on disk.

    Skips the same way as disk indexing: ``.git``, ``.clawtfup``, globs, gitignore, size/binary/UTF-8.
    """
    git = shutil.which("git")
    if not git:
        raise PolicyEvalError("Git not on PATH (needed to index at HEAD).")
    root = root.resolve()
    git_spec = _load_gitignore_spec(root) if use_gitignore else None
    cfup_spec = _load_cfupignore_spec(root) if use_cfupignore else None
    globs = list(exclude_globs or [])
    out = IndexResult()
    count = 0

    def consider(rel_posix: str, raw: bytes) -> None:
        nonlocal count
        if ".git" in rel_posix.split("/") or ".clawtfup" in rel_posix.split("/"):
            return
        if _skipped_by_ignore_rules(
            rel_posix,
            git_spec=git_spec,
            cfup_spec=cfup_spec,
            use_gitignore=use_gitignore,
            use_cfupignore=use_cfupignore,
        ) or _excluded_by_glob(rel_posix, globs):
            return
        if max_file_bytes > 0 and len(raw) > max_file_bytes:
            out.skipped_large.append(rel_posix)
            return
        if max_files > 0 and count >= max_files:
            out.skipped_cap.append(rel_posix)
            return
        if b"\x00" in raw[:8192]:
            out.skipped_binary.append(rel_posix)
            return
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            out.skipped_binary.append(rel_posix)
            return
        out.files[rel_posix] = text
        count += 1

    tree = subprocess.run(
        [git, "-C", str(root), "ls-tree", "-r", "-z", "--name-only", "HEAD"],
        capture_output=True,
        text=False,
    )
    if tree.returncode != 0:
        err = (tree.stderr or b"").decode("utf-8", errors="replace").strip()
        raise PolicyEvalError(f"git ls-tree HEAD failed: {err}")

    for rel_b in tree.stdout.split(b"\0"):
        if not rel_b:
            continue
        rel_posix = rel_b.decode("utf-8", errors="replace")
        show = subprocess.run(
            [git, "-C", str(root), "show", f"HEAD:{rel_posix}"],
            capture_output=True,
        )
        if show.returncode != 0:
            out.warnings.append(f"git show HEAD:{rel_posix} failed")
            continue
        consider(rel_posix, show.stdout)

    others = subprocess.run(
        [git, "-C", str(root), "ls-files", "-z", "--others", "--exclude-standard"],
        capture_output=True,
        text=False,
    )
    if others.returncode != 0:
        err = (others.stderr or b"").decode("utf-8", errors="replace").strip()
        raise PolicyEvalError(f"git ls-files --others failed: {err}")

    for rel_b in others.stdout.split(b"\0"):
        if not rel_b:
            continue
        rel_posix = rel_b.decode("utf-8", errors="replace")
        path = root / rel_posix
        if not path.is_file():
            continue
        try:
            raw = path.read_bytes()
        except OSError as e:
            out.warnings.append(f"read failed {rel_posix}: {e}")
            continue
        consider(rel_posix, raw)

    if out.skipped_cap:
        out.warnings.append(
            f"Stopped indexing after {max_files} files; skipped {len(out.skipped_cap)} additional paths."
        )
    return out

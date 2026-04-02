from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from pathspec import PathSpec
    from pathspec.patterns import GitWildMatchPattern
except ImportError:
    PathSpec = None  # type: ignore[misc, assignment]
    GitWildMatchPattern = None  # type: ignore[misc, assignment]


@dataclass
class IndexResult:
    files: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    skipped_binary: list[str] = field(default_factory=list)
    skipped_large: list[str] = field(default_factory=list)
    skipped_cap: list[str] = field(default_factory=list)


def _load_gitignore_spec(root: Path) -> Any | None:
    if PathSpec is None:
        return None
    gi = root / ".gitignore"
    if not gi.is_file():
        return None
    lines = gi.read_text(encoding="utf-8", errors="replace").splitlines()
    patterns = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    if not patterns:
        return None
    return PathSpec.from_lines(GitWildMatchPattern, patterns)


def _ignored(rel_posix: str, spec: Any | None) -> bool:
    if spec is None:
        return False
    return spec.match_file(rel_posix)


def _excluded_by_glob(rel_posix: str, globs: list[str]) -> bool:
    for g in globs:
        if fnmatch.fnmatch(rel_posix, g) or fnmatch.fnmatch(rel_posix, g.replace("\\", "/")):
            return True
    return False


def index_workspace(
    root: Path,
    *,
    max_files: int = 10_000,
    max_file_bytes: int = 512 * 1024,
    exclude_globs: list[str] | None = None,
    use_gitignore: bool = True,
) -> IndexResult:
    """Walk ``root`` and collect UTF-8 text files for OPA ``input``.

    ``max_files``: max indexed files, or ``0`` for no cap.
    ``max_file_bytes``: skip files larger than this, or ``0`` for no per-file cap.
    """
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)

    spec = _load_gitignore_spec(root) if use_gitignore else None
    globs = list(exclude_globs or [])
    out = IndexResult()
    count = 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        rel_posix = rel.as_posix()
        if ".git" in rel.parts or ".clawtfup" in rel.parts:
            continue
        if _ignored(rel_posix, spec) or _excluded_by_glob(rel_posix, globs):
            continue

        try:
            size = path.stat().st_size
        except OSError as e:
            out.warnings.append(f"stat failed {rel_posix}: {e}")
            continue

        if max_file_bytes > 0 and size > max_file_bytes:
            out.skipped_large.append(rel_posix)
            continue

        if max_files > 0 and count >= max_files:
            out.skipped_cap.append(rel_posix)
            continue

        try:
            raw = path.read_bytes()
        except OSError as e:
            out.warnings.append(f"read failed {rel_posix}: {e}")
            continue

        if b"\x00" in raw[:8192]:
            out.skipped_binary.append(rel_posix)
            continue

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            out.skipped_binary.append(rel_posix)
            continue

        out.files[rel_posix] = text
        count += 1

    if out.skipped_cap:
        out.warnings.append(
            f"Stopped indexing after {max_files} files; skipped {len(out.skipped_cap)} additional paths."
        )
    return out

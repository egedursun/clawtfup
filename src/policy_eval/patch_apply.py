from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from unidiff import PatchSet

from .exceptions import PatchApplyError


def apply_unified_diff(
    files_before: dict[str, str],
    diff_text: str,
) -> tuple[dict[str, str], list[str]]:
    """
    Apply a unified diff to files_before. Returns (files_after, changed_paths).
    Paths in diff must match keys in files_before (relative posix paths).
    """
    if not diff_text.strip():
        return dict(files_before), []

    try:
        patch = PatchSet(diff_text.splitlines(keepends=True))
    except Exception as e:
        raise PatchApplyError(f"Failed to parse unified diff: {e}") from e

    files_after = dict(files_before)
    changed: list[str] = []

    for patched in patch:
        target = _normalize_patch_path(patched.path)
        if patched.is_removed_file:
            if target in files_after:
                del files_after[target]
            changed.append(target)
            continue

        if patched.is_added_file:
            new_lines = _materialize_target(patched)
            files_after[target] = "".join(new_lines)
            changed.append(target)
            continue

        if target not in files_before:
            raise PatchApplyError(
                f"Patch references '{target}' but file is not in workspace index"
            )
        base_lines = files_before[target].splitlines(keepends=True)
        new_lines = _apply_hunks(base_lines, patched)
        files_after[target] = "".join(new_lines)
        changed.append(target)

    return files_after, sorted(set(changed))


def _normalize_patch_path(path: str) -> str:
    p = path.replace("\\", "/")
    for prefix in ("a/", "b/"):
        if p.startswith(prefix) and "/" in p[2:]:
            p = p[2:]
            break
    return PurePosixPath(p).as_posix()


def _materialize_target(patched: Any) -> list[str]:
    lines: list[str] = []
    for hunk in patched:
        for line in hunk:
            if line.is_added or line.is_context:
                lines.append(line.value)
    return lines


def _apply_hunks(
    base_lines: list[str],
    patched: Any,
) -> list[str]:
    out: list[str] = []
    src_idx = 0

    for hunk in patched:
        start = hunk.source_start - 1
        if start < 0:
            raise PatchApplyError("Invalid hunk source_start")
        while src_idx < start and src_idx < len(base_lines):
            out.append(base_lines[src_idx])
            src_idx += 1
        if src_idx != start:
            raise PatchApplyError(
                f"Hunk context mismatch at line {start + 1}: index {src_idx}"
            )

        for line in hunk:
            if line.is_context:
                if src_idx >= len(base_lines):
                    raise PatchApplyError("Unexpected end of file in context line")
                if base_lines[src_idx] != line.value:
                    raise PatchApplyError(
                        f"Context mismatch at source line {src_idx + 1}"
                    )
                out.append(base_lines[src_idx])
                src_idx += 1
            elif line.is_removed:
                if src_idx >= len(base_lines):
                    raise PatchApplyError("Unexpected end of file in removal")
                if base_lines[src_idx] != line.value:
                    raise PatchApplyError(
                        f"Remove mismatch at source line {src_idx + 1}"
                    )
                src_idx += 1
            elif line.is_added:
                out.append(line.value)

    while src_idx < len(base_lines):
        out.append(base_lines[src_idx])
        src_idx += 1

    return out


def combined_changed_content(files_after: dict[str, str], changed_paths: list[str]) -> str:
    parts: list[str] = []
    for p in sorted(changed_paths):
        if p in files_after:
            parts.append(f"--- FILE: {p} ---\n{files_after[p]}")
    return "\n\n".join(parts)

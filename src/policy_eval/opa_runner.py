from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .exceptions import OpaEngineError


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_opa_binary() -> str:
    bundled = package_root() / "tools" / "opa"
    if bundled.is_file() and os.access(bundled, os.X_OK):
        return str(bundled)
    import shutil

    w = shutil.which("opa")
    if w:
        return w
    raise OpaEngineError(
        "OPA binary not found. Install with `brew install opa` or place executable at tools/opa."
    )


def opa_version(opa: str) -> str | None:
    try:
        proc = subprocess.run(
            [opa, "version"], capture_output=True, text=True, check=False
        )
        if proc.returncode != 0:
            return None
        for line in (proc.stdout or "").splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
        return (proc.stdout or "").strip() or None
    except OSError:
        return None


def opa_eval_query(
    *,
    bundle_dir: Path,
    input_doc: dict[str, Any],
    query: str,
    opa_binary: str | None = None,
) -> Any:
    opa = opa_binary or resolve_opa_binary()
    if not bundle_dir.is_dir():
        raise OpaEngineError(f"Policy bundle not found: {bundle_dir}")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(input_doc, tmp)
        tmp_path = tmp.name

    try:
        cmd = [
            opa,
            "eval",
            "-d",
            str(bundle_dir),
            "-i",
            tmp_path,
            "-f",
            "json",
            query,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise OpaEngineError(
                f"opa eval failed (exit {proc.returncode}): "
                f"{proc.stderr.strip() or proc.stdout.strip()}"
            )
        return parse_opa_value(proc.stdout)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def parse_opa_value(stdout: str) -> Any:
    data = json.loads(stdout)
    results = data.get("result") or []
    if not results:
        raise OpaEngineError("opa eval returned no result")
    exprs = results[0].get("expressions") or []
    if not exprs:
        raise OpaEngineError("opa eval: missing expressions")
    return exprs[0].get("value")

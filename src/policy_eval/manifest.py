from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .exceptions import ManifestError

MANIFEST_NAMES = ("policy_eval.yaml", "policy_eval.yml")


def load_manifest(bundle_dir: Path) -> dict[str, Any]:
    for name in MANIFEST_NAMES:
        p = bundle_dir / name
        if p.is_file():
            try:
                data = yaml.safe_load(p.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                raise ManifestError(f"Invalid YAML in {p}: {e}") from e
            if data is None:
                return {}
            if not isinstance(data, dict):
                raise ManifestError(f"Manifest {p} must be a mapping at root")
            return data
    return {}


def manifest_queries(manifest: dict[str, Any]) -> list[str]:
    raw = manifest.get("queries")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(q) for q in raw]
    raise ManifestError("manifest 'queries' must be a string or list of strings")


def manifest_findings_query(manifest: dict[str, Any]) -> str | None:
    q = manifest.get("findings_query")
    return str(q) if q else None

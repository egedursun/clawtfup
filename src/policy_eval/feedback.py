"""
Optional LLM-oriented remediation strings.

Loads from:

1. Policy bundle root (``--policies``): optional ``feedback.yaml`` / ``.yml`` / ``.json``.
2. ``<workspace>/.clawtfup/feedback/``: all ``*.yaml`` / ``*.yml`` / ``*.json`` merged on top (sorted by name; later files override keys). **Same violation ``code`` → entry from here wins.**

Default layout: remediation under ``.clawtfup/feedback/`` only; bundle root = manifest + Rego.

OPA does not read these files.

See BUNDLE.md and bundles/reference/README.md.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .exceptions import PolicyEvalError


def _load_feedback_file(p: Path) -> dict[str, Any]:
    if p.suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
    else:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise PolicyEvalError(f"{p} root must be a mapping keyed by violation code")
    return data


def load_feedback_map(bundle_dir: Path) -> dict[str, Any]:
    for name in ("feedback.yaml", "feedback.yml", "feedback.json"):
        p = bundle_dir / name
        if p.is_file():
            return _load_feedback_file(p)
    return {}


def load_feedback_dir(feedback_dir: Path) -> dict[str, Any]:
    """Merge all ``*.yaml`` / ``*.yml`` / ``*.json`` in the directory (sorted by name; later overrides)."""
    if not feedback_dir.is_dir():
        return {}
    paths = sorted(
        p
        for p in feedback_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".yaml", ".yml", ".json")
    )
    merged: dict[str, Any] = {}
    for p in paths:
        merged.update(_load_feedback_file(p))
    return merged


def load_combined_feedback(bundle_root: Path, workspace: Path) -> dict[str, Any]:
    """Bundle ``feedback.*`` first, then ``<workspace>/.clawtfup/feedback/*`` (overrides on same code)."""
    fb = load_feedback_map(bundle_root)
    extra = workspace.resolve() / ".clawtfup" / "feedback"
    if extra.is_dir():
        fb = {**fb, **load_feedback_dir(extra)}
    return fb


def enrich_finding(
    finding: dict[str, Any], feedback_map: dict[str, Any]
) -> dict[str, Any]:
    code = finding.get("code")
    out = dict(finding)
    if code and isinstance(code, str) and code in feedback_map:
        fb = feedback_map[code]
        if isinstance(fb, dict):
            out["feedback"] = {
                "title": fb.get("title"),
                "remediation": fb.get("remediation"),
                "references": list(fb.get("references") or []),
            }
            if fb.get("severity") is not None and "severity" not in out:
                out["severity"] = fb["severity"]
    return out

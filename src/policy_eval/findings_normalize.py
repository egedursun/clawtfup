from __future__ import annotations

from typing import Any


def normalize_from_report_value(value: Any) -> tuple[bool | None, list[dict[str, Any]]]:
    """
    If value matches {allow: bool, violations: [...]}, return (allow, findings).
    Violations may be strings (legacy) or objects with code/message/path.
    Otherwise return (None, []).
    """
    if not isinstance(value, dict):
        return None, []
    if "allow" not in value and "violations" not in value:
        return None, []

    allow = value.get("allow")
    allow_bool: bool | None
    if isinstance(allow, bool):
        allow_bool = allow
    else:
        allow_bool = None

    raw_v = value.get("violations")
    findings: list[dict[str, Any]] = []
    if raw_v is None:
        return allow_bool, findings

    if isinstance(raw_v, list):
        for item in raw_v:
            if isinstance(item, str):
                findings.append(
                    {
                        "code": "POLICY_VIOLATION",
                        "message": item,
                        "severity": "error",
                    }
                )
            elif isinstance(item, dict):
                f: dict[str, Any] = {
                    "code": item.get("code") or "POLICY_VIOLATION",
                    "message": item.get("message") or str(item),
                    "severity": item.get("severity") or "error",
                }
                if item.get("path") is not None:
                    f["path"] = item["path"]
                if item.get("rule") is not None:
                    f["rule"] = item["rule"]
                findings.append(f)

    return allow_bool, findings


def summarize_severities(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in findings:
        sev = str(f.get("severity") or "error")
        counts[sev] = counts.get(sev, 0) + 1
    return counts

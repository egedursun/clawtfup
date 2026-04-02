from policy_eval.findings_normalize import normalize_from_report_value, summarize_severities


def test_normalize_report_dict():
    allow, findings = normalize_from_report_value(
        {
            "allow": False,
            "violations": [
                {"code": "X", "message": "m", "severity": "error", "path": "p.py"},
                "legacy string",
            ],
        }
    )
    assert allow is False
    assert len(findings) == 2
    assert findings[0]["code"] == "X"
    assert findings[1]["code"] == "POLICY_VIOLATION"


def test_summarize_severities():
    s = summarize_severities(
        [{"severity": "error"}, {"severity": "warning"}, {"severity": "error"}]
    )
    assert s == {"error": 2, "warning": 1}

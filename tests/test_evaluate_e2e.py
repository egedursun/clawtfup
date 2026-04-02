from pathlib import Path

import pytest

from policy_eval.evaluate import EvaluateOptions, evaluate
from policy_eval.opa_runner import resolve_opa_binary


def _opa_available() -> bool:
    try:
        resolve_opa_binary()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _opa_available(), reason="OPA not installed")
def test_evaluate_sample_project_detects_eval():
    root = Path(__file__).resolve().parent
    sample = root / "fixtures" / "sample_project"
    policies = sample / ".clawtfup" / "policies"
    patch = (root / "fixtures" / "patches" / "app_eval.patch").read_text(encoding="utf-8")
    opts = EvaluateOptions(
        workspace=sample,
        bundle_root=policies,
        patch_text=patch,
        use_gitignore=False,
        change_source="diff_file",
    )
    report = evaluate(opts)
    assert report["allow"] is False
    assert report["findings"]
    assert report["findings"][0]["code"] == "UNSAFE_EVAL"
    assert "feedback" in report["findings"][0]
    assert "sample_project" in report["inputs"]["policy_bundle"].replace("\\", "/")

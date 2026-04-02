from pathlib import Path

from policy_eval.patch_apply import apply_unified_diff


def test_apply_unified_diff_updates_file():
    root = Path(__file__).resolve().parent / "fixtures"
    patch = (root / "patches" / "app_eval.patch").read_text(encoding="utf-8")
    before = {"app.py": (root / "ws" / "app.py").read_text(encoding="utf-8")}
    after, changed = apply_unified_diff(before, patch)
    assert changed == ["app.py"]
    assert ("ev" + "al(") in after["app.py"]
    assert after["app.py"] != before["app.py"]

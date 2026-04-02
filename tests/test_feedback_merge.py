from pathlib import Path

from policy_eval.feedback import load_combined_feedback, load_feedback_dir


def test_load_feedback_dir_merges_sorted_files(tmp_path: Path) -> None:
    d = tmp_path / "fb"
    d.mkdir()
    (d / "a.yaml").write_text("X: {title: first}\n", encoding="utf-8")
    (d / "b.yaml").write_text("X: {title: second}\n", encoding="utf-8")
    m = load_feedback_dir(d)
    assert m["X"]["title"] == "second"


def test_load_combined_feedback_clawtfup_overrides_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "policies"
    bundle.mkdir()
    (bundle / "feedback.yaml").write_text(
        "CODE: {title: from_bundle}\n", encoding="utf-8"
    )
    claw = tmp_path / ".clawtfup" / "feedback"
    claw.mkdir(parents=True)
    (claw / "local.yaml").write_text("CODE: {title: from_claw}\n", encoding="utf-8")
    m = load_combined_feedback(bundle, tmp_path)
    assert m["CODE"]["title"] == "from_claw"

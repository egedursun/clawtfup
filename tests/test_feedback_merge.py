from pathlib import Path

from policy_eval.feedback import load_feedback_dir, load_workspace_feedback


def test_load_feedback_dir_merges_sorted_files(tmp_path: Path) -> None:
    d = tmp_path / "fb"
    d.mkdir()
    (d / "a.yaml").write_text("X: {title: first}\n", encoding="utf-8")
    (d / "b.yaml").write_text("X: {title: second}\n", encoding="utf-8")
    m = load_feedback_dir(d)
    assert m["X"]["title"] == "second"


def test_load_workspace_feedback_from_clawtfup(tmp_path: Path) -> None:
    claw = tmp_path / ".clawtfup" / "feedback"
    claw.mkdir(parents=True)
    (claw / "x.yaml").write_text("CODE: {title: from_workspace}\n", encoding="utf-8")
    m = load_workspace_feedback(tmp_path)
    assert m["CODE"]["title"] == "from_workspace"

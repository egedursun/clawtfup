from pathlib import Path

from policy_eval.workspace import index_workspace


def test_index_max_files_zero_no_cap(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    r = index_workspace(tmp_path, max_files=0, max_file_bytes=1024, use_gitignore=False)
    assert set(r.files) == {"a.txt", "b.txt"}
    assert not r.skipped_cap


def test_index_max_files_one_skips_rest(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    r = index_workspace(tmp_path, max_files=1, max_file_bytes=1024, use_gitignore=False)
    assert len(r.files) == 1
    assert len(r.skipped_cap) == 1


def test_index_max_file_bytes_zero_allows_large(tmp_path: Path) -> None:
    big = "x" * 20_000
    (tmp_path / "big.txt").write_text(big, encoding="utf-8")
    r = index_workspace(tmp_path, max_files=10, max_file_bytes=0, use_gitignore=False)
    assert r.files["big.txt"] == big
    assert not r.skipped_large


def test_cfupignore_excludes_paths(tmp_path: Path) -> None:
    (tmp_path / ".cfupignore").write_text("ignored.txt\n", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("k", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("i", encoding="utf-8")
    r = index_workspace(tmp_path, max_files=10, max_file_bytes=1024, use_cfupignore=True)
    assert "keep.txt" in r.files
    assert "ignored.txt" not in r.files

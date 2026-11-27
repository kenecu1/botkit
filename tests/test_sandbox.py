import re
import subprocess
from pathlib import Path

import pytest

from botkit.sandbox import export_patch, make_clone


def git(path, *args):
    return subprocess.run(
        ["git", "-C", str(path), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "repo"
    path.mkdir()
    git(path, "init", "-q")
    (path / "a.txt").write_text("hello\n")
    git(path, "add", "a.txt")
    git(path, "-c", "user.name=Test", "-c", "user.email=test@example.com",
        "commit", "-q", "-m", "base")
    return path


@pytest.fixture
def clone(repo, tmp_path):
    """A plain clone made without make_clone, so export tests don't depend on it."""
    path = tmp_path / "plain_clone"
    subprocess.run(["git", "clone", "-q", str(repo), str(path)], check=True)
    return path


def head(path):
    return git(path, "rev-parse", "HEAD")


# Example 1
def test_make_clone_returns_dest_with_no_origin_and_head_at_base(repo, tmp_path):
    base = head(repo)
    dest = str(tmp_path / "clone")

    result = make_clone(str(repo), base, dest)

    assert result == dest
    assert git(dest, "remote") == ""
    assert head(dest) == base
    detached = subprocess.run(["git", "-C", dest, "symbolic-ref", "-q", "HEAD"])
    assert detached.returncode != 0


# Spec: make_clone uses --no-hardlinks (question 3)
def test_make_clone_shares_no_object_files_with_original(repo, tmp_path):
    dest = make_clone(str(repo), head(repo), str(tmp_path / "clone"))

    object_files = [p for p in Path(dest, ".git", "objects").rglob("*") if p.is_file()]

    assert object_files
    assert all(p.stat().st_nlink == 1 for p in object_files)


# Example 2
def test_export_patch_after_edit_returns_staged_diff_as_string(repo, clone):
    base = head(repo)
    (clone / "a.txt").write_text("hello\nworld\n")

    patch = export_patch(str(clone), base)

    assert isinstance(patch, str)
    assert "diff --git a/a.txt b/a.txt" in patch
    assert "+world" in patch
    assert git(clone, "diff", "--cached", "--name-only") == "a.txt"


# Example 3
def test_export_patch_with_edit_and_new_file_contains_both(repo, clone):
    base = head(repo)
    (clone / "a.txt").write_text("changed\n")
    (clone / "b.txt").write_text("brand new\n")

    patch = export_patch(str(clone), base)

    assert "diff --git a/a.txt b/a.txt" in patch
    assert "+changed" in patch
    assert "diff --git a/b.txt b/b.txt" in patch
    assert "new file mode" in patch
    assert "+brand new" in patch


# Example 4
def test_export_patch_with_no_change_raises_value_error(repo, clone):
    base = head(repo)

    with pytest.raises(ValueError, match=r"(?i)no change"):
        export_patch(str(clone), base)


# Example 5
def test_make_clone_with_existing_dest_raises_file_exists_error(repo, tmp_path):
    dest = tmp_path / "clone"
    dest.mkdir()
    (dest / "keep.txt").write_text("mine")

    with pytest.raises(FileExistsError, match=re.escape(str(dest))):
        make_clone(str(repo), head(repo), str(dest))

    assert [p.name for p in dest.iterdir()] == ["keep.txt"]


# Example 5
def test_make_clone_with_missing_repo_path_raises_file_not_found_error(tmp_path):
    missing = tmp_path / "no_such_repo"
    dest = tmp_path / "clone"

    with pytest.raises(FileNotFoundError, match=re.escape(str(missing))):
        make_clone(str(missing), "0" * 40, str(dest))

    assert not dest.exists()


# Example 5
def test_make_clone_with_bad_base_raises_value_error_and_creates_nothing(repo, tmp_path):
    bad_base = "0" * 40
    dest = tmp_path / "clone"

    with pytest.raises(ValueError, match=bad_base):
        make_clone(str(repo), bad_base, str(dest))

    assert not dest.exists()


# Error case from the spec (question 5): a folder that exists but isn't a repo
def test_make_clone_with_empty_folder_as_repo_path_raises_file_not_found_error(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    dest = tmp_path / "clone"

    with pytest.raises(FileNotFoundError, match=re.escape(str(empty))):
        make_clone(str(empty), "0" * 40, str(dest))

    assert not dest.exists()

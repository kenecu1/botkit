from dataclasses import replace

import pytest

from botkit.guard import compare, _git, take_snapshot
from botkit.shapes import Snapshot

BASE = Snapshot("/repo", "abc", {"main": "abc"}, 7, "f00")

def make_repo(path):
    _git(path, ["init", "-q"])
    (path / "a.txt").write_text("hello")
    _git(path, ["add", "a.txt"])
    _git(path, ["-c", "user.name=Test", "-c", "user.email=test@example.com",
                "commit", "-q", "-m", "base"])


def test_identical_snapshots_have_no_violations():
    assert compare(BASE, BASE) == []


def test_head_moved_is_one_violation():
    after = replace(BASE, head="xyz")

    problems = compare(BASE, after)

    assert len(problems) == 1
    assert "HEAD" in problems[0]
    assert "abc" in problems[0]
    assert "xyz" in problems[0]


def test_reflog_change_one_violation():
    after = replace(BASE, reflog_len=9)

    problems = compare(BASE, after)

    assert len(problems) == 1
    assert "9" in problems[0]
    assert "7" in problems[0]
    assert "reflog_len" in problems[0]


def test_different_repos_raise_value_error():
    after = replace(BASE, repo="/other_repo")

    with pytest.raises(ValueError, match="other_repo"):
        compare(BASE, after)


def test_ref_changed_one_violation():
    after = replace(BASE, refs={"main": "xyz"})

    problems = compare(BASE, after)

    assert len(problems) == 1
    assert "refs" in problems[0]


def test_config_hash_changed_one_violation():
    after = replace(BASE, config_hash="s01")

    problems = compare(BASE, after)

    assert len(problems) == 1
    assert "config_hash" in problems[0]


def test_three_changes_are_three_violations():
    after = replace(BASE, head="lll", refs={"main": "iop"}, reflog_len="7")

    problems = compare(BASE, after)

    assert len(problems) == 3


def test_no_violations(tmp_path):
    make_repo(tmp_path)
    before = take_snapshot(str(tmp_path))

    after = take_snapshot(str(tmp_path))
    problems = compare(before, after)

    assert problems == []


def test_new_commit_is_caught(tmp_path):
    make_repo(tmp_path)
    before = take_snapshot(str(tmp_path))

    (tmp_path / "a.txt").write_text("changed")
    _git(tmp_path, ["-c", "user.name=Test", "-c", "user.email=test@example.com",
                "commit", "-q", "-am", "change"])
    
    after = take_snapshot(str(tmp_path))
    problems = compare(before, after)

    assert len(problems) == 3
    assert any("HEAD" in p for p in problems)


def test_commit_reset_is_caught(tmp_path):
    make_repo(tmp_path)
    before = take_snapshot(str(tmp_path))

    (tmp_path / "a.txt").write_text("changed")
    _git(tmp_path, ["-c", "user.name=Test", "-c", "user.email=test@example.com",
                "commit", "-q", "-am", "change"])
    _git(tmp_path, ["reset", "-q", "--hard", "HEAD~1"])

    after = take_snapshot(str(tmp_path))
    problems = compare(before, after)

    assert len(problems) == 1
    assert "reflog" in problems[0]


def test_remote_to_config_is_caught(tmp_path):
    make_repo(tmp_path)
    before = take_snapshot(str(tmp_path))

    _git(tmp_path, ["remote", "add", "origin", "https://example.com/x.git"])
    
    after = take_snapshot(str(tmp_path))
    problems = compare(before, after)

    assert len(problems) == 1
    assert "config" in problems[0]

    




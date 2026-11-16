from dataclasses import replace

import pytest

from botkit.guard import compare
from botkit.shapes import Snapshot

BASE = Snapshot("/repo", "abc", {"main": "abc"}, 7, "f00")


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



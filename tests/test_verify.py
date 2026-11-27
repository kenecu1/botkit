import shlex
import subprocess
import sys

import pytest

from botkit.verify import verify

# The real pytest, run in a throwaway repo. No model, no network.
TEST_CMD = f"{shlex.quote(sys.executable)} -m pytest -q -p no:cacheprovider"
TEST_DIRS = ("tests",)
PASSING_TEST = "def test_ok():\n    assert True\n"
FAILING_TEST = "def test_ok():\n    assert False\n"


def git(path, *args):
    return subprocess.run(
        ["git", "-C", str(path), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def head(path):
    return git(path, "rev-parse", "HEAD")


def bot_writes(clone, files):
    """Stands in for the builder, then stages like sandbox.export_patch does."""
    for name, text in files.items():
        path = clone / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git(clone, "add", "-A")


def header(args):
    return "$ " + shlex.join(args)


@pytest.fixture
def clone(tmp_path):
    path = tmp_path / "clone"
    (path / "tests").mkdir(parents=True)
    git(path, "init", "-q")
    (path / ".gitignore").write_text("__pycache__/\n")
    (path / "app.py").write_text("VALUE = 1\n")
    (path / "tests" / "test_a.py").write_text(PASSING_TEST)
    (path / "tests" / "test_empty.py").write_text("# no tests yet\n")
    git(path, "add", "-A")
    git(path, "-c", "user.name=Test", "-c", "user.email=test@example.com",
        "commit", "-q", "-m", "base")
    return path


# Example 1
def test_untouched_passing_tests_return_true_no_changes_and_output(clone):
    acceptance = ("tests/test_a.py",)

    passed, changed, output = verify(str(clone), head(clone), TEST_DIRS, acceptance, TEST_CMD)

    assert passed is True
    assert changed == ()
    assert isinstance(output, str)
    assert "1 passed" in output
    lines = output.splitlines()
    acceptance_header = header(shlex.split(TEST_CMD) + list(acceptance))
    full_header = header(shlex.split(TEST_CMD))
    assert lines.index(acceptance_header) < lines.index(full_header)


# Example 2
def test_bot_edited_test_is_rolled_back_to_base_and_listed(clone):
    base = head(clone)
    bot_writes(clone, {"tests/test_a.py": FAILING_TEST, "app.py": "VALUE = 2\n"})

    passed, changed, _ = verify(str(clone), base, TEST_DIRS, ("tests/test_a.py",), TEST_CMD)

    assert changed == ("tests/test_a.py",)
    assert (clone / "tests" / "test_a.py").read_text() == PASSING_TEST
    assert git(clone, "status", "--porcelain", "--", "tests") == ""
    assert passed is True
    assert (clone / "app.py").read_text() == "VALUE = 2\n"  # non-test file untouched


# Example 3
def test_zero_acceptance_tests_collected_returns_false(clone):
    acceptance = ("tests/test_empty.py",)

    passed, changed, output = verify(str(clone), head(clone), TEST_DIRS, acceptance, TEST_CMD)

    assert passed is False
    assert changed == ()
    assert header(shlex.split(TEST_CMD)) in output.splitlines()  # full run still ran
    assert "1 passed" in output


# Example 4
def test_missing_base_raises_value_error_and_changes_nothing(clone):
    bad_base = "0" * 40
    bot_writes(clone, {"tests/test_a.py": FAILING_TEST})

    with pytest.raises(ValueError, match="does not exist") as err:
        verify(str(clone), bad_base, TEST_DIRS, ("tests/test_a.py",), TEST_CMD)

    assert bad_base in str(err.value)
    assert (clone / "tests" / "test_a.py").read_text() == FAILING_TEST


# From the brief's Outputs and question 2: a new test file is deleted and listed
def test_bot_new_test_file_is_deleted_and_listed(clone):
    base = head(clone)
    bot_writes(clone, {"tests/test_bot.py": FAILING_TEST})

    passed, changed, _ = verify(str(clone), base, TEST_DIRS, ("tests/test_a.py",), TEST_CMD)

    assert changed == ("tests/test_bot.py",)
    assert not (clone / "tests" / "test_bot.py").exists()
    assert git(clone, "status", "--porcelain", "--", "tests") == ""
    assert passed is True


# Spec edge case: a base test file the bot deleted is restored and listed
def test_bot_deleted_test_file_is_restored_and_listed(clone):
    base = head(clone)
    (clone / "tests" / "test_a.py").unlink()
    git(clone, "add", "-A")

    passed, changed, _ = verify(str(clone), base, TEST_DIRS, ("tests/test_a.py",), TEST_CMD)

    assert changed == ("tests/test_a.py",)
    assert (clone / "tests" / "test_a.py").read_text() == PASSING_TEST
    assert git(clone, "status", "--porcelain", "--", "tests") == ""
    assert passed is True


# Spec edge case (question 5): ignored files are not listed and not deleted
def test_ignored_file_under_tests_is_kept_and_not_listed(clone):
    base = head(clone)
    cache = clone / "tests" / "__pycache__" / "x.pyc"
    cache.parent.mkdir()
    cache.write_bytes(b"cache")

    passed, changed, _ = verify(str(clone), base, TEST_DIRS, ("tests/test_a.py",), TEST_CMD)

    assert changed == ()
    assert cache.read_bytes() == b"cache"
    assert passed is True

import pytest

from botkit.shapes import Ticket
from botkit.ticket import read_ticket

FULL_TOML = """\
base = "abc123"
test_cmd = "pytest -q"
acceptance = ["tests/test_a.py", "tests/test_b.py"]
touches = ["src/botkit/a.py"]
by_hand = false
"""


def make_ticket_folder(path, toml_text):
    path.mkdir(parents=True)
    (path / "brief.md").write_text("the brief text\n")
    (path / "spec.md").write_text("the spec text\n")
    if toml_text is not None:
        (path / "ticket.toml").write_text(toml_text)
    return path


# Example 1
def test_full_folder_gives_ticket_with_every_value_and_tuples(tmp_path):
    folder = make_ticket_folder(tmp_path / "repo" / "tickets" / "T009-thing", FULL_TOML)

    ticket = read_ticket(str(folder))

    assert ticket == Ticket(
        repo_path=str(tmp_path / "repo"),
        ticket_name="T009-thing",
        brief="the brief text\n",
        spec="the spec text\n",
        base="abc123",
        test_cmd="pytest -q",
        acceptance=("tests/test_a.py", "tests/test_b.py"),
        touches=("src/botkit/a.py",),
        by_hand=False,
    )
    assert isinstance(ticket.acceptance, tuple)
    assert isinstance(ticket.touches, tuple)


# Example 2
def test_name_is_folder_name_and_repo_path_is_two_folders_up(tmp_path):
    folder = make_ticket_folder(tmp_path / "botkit" / "tickets" / "T001-ticket", FULL_TOML)

    ticket = read_ticket(str(folder))

    assert ticket.ticket_name == "T001-ticket"
    assert ticket.repo_path == str(tmp_path / "botkit")


# Example 3
def test_by_hand_true_and_three_touches_are_read_normally(tmp_path):
    toml_text = """\
base = "abc123"
test_cmd = "pytest"
acceptance = ["tests/test_a.py"]
touches = ["src/botkit/a.py", "src/botkit/b.py", "src/botkit/c.py"]
by_hand = true
"""
    folder = make_ticket_folder(tmp_path / "repo" / "tickets" / "T010-hand", toml_text)

    ticket = read_ticket(str(folder))

    assert ticket.by_hand is True
    assert ticket.touches == ("src/botkit/a.py", "src/botkit/b.py", "src/botkit/c.py")


# Example 4
def test_missing_ticket_toml_raises_file_not_found_naming_it(tmp_path):
    folder = make_ticket_folder(tmp_path / "repo" / "tickets" / "T011-broken", None)

    with pytest.raises(FileNotFoundError) as error:
        read_ticket(str(folder))

    assert "ticket.toml" in str(error.value)


# Proposed 1, approved
def test_missing_key_in_ticket_toml_raises_key_error_naming_it(tmp_path):
    toml_text = FULL_TOML.replace('test_cmd = "pytest -q"\n', "")
    folder = make_ticket_folder(tmp_path / "repo" / "tickets" / "T012-nokey", toml_text)

    with pytest.raises(KeyError) as error:
        read_ticket(str(folder))

    assert "test_cmd" in str(error.value)


# Proposed 2, approved
def test_relative_path_gives_absolute_repo_path(tmp_path, monkeypatch):
    make_ticket_folder(tmp_path / "repo" / "tickets" / "T013-rel", FULL_TOML)
    monkeypatch.chdir(tmp_path)

    ticket = read_ticket("repo/tickets/T013-rel")

    assert ticket.repo_path == str(tmp_path / "repo")
    assert ticket.ticket_name == "T013-rel"


# Proposed 3, approved
def test_trailing_slash_gives_same_ticket(tmp_path):
    folder = make_ticket_folder(tmp_path / "repo" / "tickets" / "T014-slash", FULL_TOML)

    assert read_ticket(str(folder) + "/") == read_ticket(str(folder))


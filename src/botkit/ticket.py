"""Read one ticket folder and turn it into a Ticket record."""

import os
import tomllib

from botkit.shapes import Ticket


def read_ticket(ticket_folder_path: str) -> Ticket:
    """Read brief.md, spec.md and ticket.toml from a ticket folder into a Ticket."""

    folder = os.path.abspath(ticket_folder_path)
    ticket_name = os.path.basename(folder)
    repo_path = os.path.dirname(os.path.dirname(folder))

    toml_path = os.path.join(folder, "ticket.toml")
    if not os.path.isfile(toml_path):
        raise FileNotFoundError(f"ticket.toml not found: {toml_path}")

    with open(toml_path, "rb") as toml_file:
        settings = tomllib.load(toml_file)

    base = _get_string(settings, "base")
    test_cmd = _get_string(settings, "test_cmd")
    acceptance = _get_string_list(settings, "acceptance")
    touches = _get_string_list(settings, "touches")
    by_hand = _get_bool(settings, "by_hand")

    brief = _read_text(os.path.join(folder, "brief.md"))
    spec = _read_text(os.path.join(folder, "spec.md"))

    return Ticket(
        repo_path=repo_path,
        ticket_name=ticket_name,
        brief=brief,
        spec=spec,
        base=base,
        test_cmd=test_cmd,
        acceptance=acceptance,
        touches=touches,
        by_hand=by_hand,
    )


def _read_text(path: str) -> str:
    """Return the full text of a file."""
    with open(path, encoding="utf-8") as text_file:
        return text_file.read()


def _get_value(settings: dict, key: str):
    """Return settings[key], or raise KeyError naming the key if it is missing."""
    if key not in settings:
        raise KeyError(f"ticket.toml is missing key: {key}")
    return settings[key]


def _get_string(settings: dict, key: str) -> str:
    """Return a string value from settings, checking its type."""
    value = _get_value(settings, key)
    if not isinstance(value, str):
        raise TypeError(f"ticket.toml key {key} must be a string")
    return value


def _get_bool(settings: dict, key: str) -> bool:
    """Return a boolean value from settings, checking its type."""
    value = _get_value(settings, key)
    if not isinstance(value, bool):
        raise TypeError(f"ticket.toml key {key} must be a boolean")
    return value


def _get_string_list(settings: dict, key: str) -> tuple[str, ...]:
    """Return a list of strings from settings as a tuple, checking every item."""
    value = _get_value(settings, key)
    if not isinstance(value, list):
        raise TypeError(f"ticket.toml key {key} must be a list of strings")
    for item in value:
        if not isinstance(item, str):
            raise TypeError(f"ticket.toml key {key} must hold only strings")
    return tuple(value)

"""Exit codes and the errors that carry them.

Ticket: BK-1   Tier: A
Design: docs/design.md
"""

from enum import IntEnum


class ExitCode(IntEnum):
    pass  # TODO: OK=0, INVALID_SPEC=2 ... SAFETY_VIOLATION=11


class BotkitError(Exception):
    """TODO: hold an ExitCode and a message."""

"""The state machine: which status may follow which.

Ticket: BK-1   Tier: A
Design: docs/design.md
"""

# TODO: ALLOWED = {TicketStatus.X: {TicketStatus.Y, ...}, ...}


def can_move(current, new) -> bool:
    raise NotImplementedError


def check_move(current, new) -> None:
    """Raise BotkitError if the move is not allowed."""
    raise NotImplementedError

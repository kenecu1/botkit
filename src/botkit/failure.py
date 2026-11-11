"""Decide: retry, wait, or give up. Recover after a crash.

Ticket: BK-9   Tier: B
Design: docs/design.md
"""

class CappedBackoff:
    def next_delay(self, attempt, exit_code):
        """Seconds to wait, or None to stop retrying."""
        raise NotImplementedError


def recover(store, scheduler):
    """At startup: restart any ticket stuck in BUILDING, TESTING, REVIEWING."""
    raise NotImplementedError


def install_shutdown_handler(on_stop):
    raise NotImplementedError

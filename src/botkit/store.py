"""Save and read tickets, runs, events, findings in SQLite.

Ticket: BK-2   Tier: B
Design: docs/design.md
"""

class SqliteStore:
    """TODO: tables tickets, runs, events, findings, questions, dead_letters."""

    def __init__(self, db_path):  # path comes from config: <home>/botkit.db
        raise NotImplementedError

    def create_ticket(self, ticket):
        """Same ticket id twice returns the existing ticket."""
        raise NotImplementedError

    def get(self, ticket_id):
        raise NotImplementedError

    def transition(self, ticket_id, expected_from, to, detail=""):
        """Only move if the ticket is still in expected_from. Write an event."""
        raise NotImplementedError

    def record_run(self, run):
        raise NotImplementedError

    def record_findings(self, ticket_id, findings):
        raise NotImplementedError

    def list_by_status(self, status):
        raise NotImplementedError

    def history(self, ticket_id):
        raise NotImplementedError


class MemoryStore:
    """Same methods, kept in a dict. For tests."""

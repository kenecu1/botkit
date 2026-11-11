"""One Git worktree per ticket.

Ticket: BK-6   Tier: B
Design: docs/design.md
"""

class GitWorktreeWorkspace:
    def ensure(self, ticket):
        """Create ~/.botkit/worktrees/<id> on branch botkit/<id> only if missing. Return its path."""
        raise NotImplementedError

    def diff(self, ticket):
        """Stage everything (git add -A, never commit). Return the staged diff vs the base commit."""
        raise NotImplementedError

    def head_commit(self, ticket):
        """Latest commit on the ticket branch. Used by the safety check."""
        raise NotImplementedError

    def remove(self, ticket):
        raise NotImplementedError

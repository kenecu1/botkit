"""Run the project's test, build, and lint commands.

Ticket: BK-4   Tier: C
Design: docs/design.md
"""

class SubprocessTestRunner:
    def run(self, workdir, commands):
        """Return a TestResult. Keep only the tail of the output."""
        raise NotImplementedError

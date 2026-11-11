"""Call Claude Code in headless mode (claude -p, prompt on stdin).

Find the program with shutil.which. On timeout, stop the whole process tree.

Ticket: BK-7   Tier: B
Design: docs/design.md
"""

class ClaudeRunner:
    def run(self, role, prompt, workdir, timeout_s):
        """Return an AgentResult with duration, tokens, cost, model name."""
        raise NotImplementedError

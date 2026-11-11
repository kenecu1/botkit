"""Call ChatGPT through Codex in headless mode (codex exec - reads the prompt from stdin).

Find the program with shutil.which. On timeout, stop the whole process tree.

Ticket: BK-7   Tier: B
Design: docs/design.md
"""

class CodexRunner:
    def run(self, role, prompt, workdir, timeout_s):
        raise NotImplementedError


def parse_review(output_text):
    """JSON text -> ReviewReport. Bad JSON raises AGENT_ERROR."""
    raise NotImplementedError

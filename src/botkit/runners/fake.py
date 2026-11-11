"""Pretend runners with scripted answers, so tests never call a real model.

Ticket: BK-4   Tier: C
Design: docs/design.md
"""

class FakeRunner:
    def __init__(self, scripted_results):
        raise NotImplementedError

    def run(self, role, prompt, workdir, timeout_s):
        raise NotImplementedError


class FakeTestRunner:
    def __init__(self, scripted_results):
        raise NotImplementedError

    def run(self, workdir, commands):
        raise NotImplementedError

"""Drive one ticket through the state machine, step by step.

Ticket: BK-5   Tier: A
Design: docs/design.md
"""

class Scheduler:
    def __init__(self, store, workspace, builder, reviewer, tests, retry, notifier, config):
        raise NotImplementedError

    def run_ticket(self, ticket):
        """VALIDATED -> BUILDING -> TESTING -> REVIEWING -> AWAITING_HUMAN.
        Fail at tests or review -> RETRYING -> BUILDING, cap from config.
        Cap reached: tests failing -> FAILED; tests pass but review FAIL -> AWAITING_HUMAN (review unresolved).
        Same diff or same failing output as the last attempt -> treat as cap reached.
        Existing test files touched -> tests_changed in the handoff.
        After each build: commit changed -> SAFETY_VIOLATION. Queue cap -> QUEUE_FULL."""
        raise NotImplementedError

    def review_only(self, ticket):
        """Tier A path: no build. VALIDATED -> TESTING -> REVIEWING -> AWAITING_HUMAN. No retries."""
        raise NotImplementedError

    def build_reviewer_prompt(self, ticket, diff):
        """Spec and diff only. Never the builder's output text."""
        raise NotImplementedError

    # Phase 3: run_queue(), queue cap, parallel builders, BLOCKED questions


def apply_verdict_rule(report, max_findings):
    """FAIL counts only with a HIGH BUG or SPEC_MISMATCH finding. Keep the top findings by severity."""
    raise NotImplementedError

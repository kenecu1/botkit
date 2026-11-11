"""All fixed lists of values.

Ticket: BK-1   Tier: A
Design: docs/design.md
"""

from enum import Enum


class TicketStatus(Enum):
    pass  # TODO: 12 values, design section 7


class Tier(Enum):
    pass  # TODO: A, B, C


class Role(Enum):
    pass  # TODO: BUILDER, REVIEWER, QUIZ


class Severity(Enum):
    pass  # TODO: HIGH, MEDIUM, LOW


class Verdict(Enum):
    pass  # TODO: PASS, FAIL


class FindingCategory(Enum):
    pass  # TODO: SPEC_MISMATCH, BUG, QUALITY


class Setup(Enum):
    pass  # TODO: TESTS_ONLY, CLAUDE_REVIEW, CHATGPT_REVIEW

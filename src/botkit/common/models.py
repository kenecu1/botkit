"""Data shapes passed between modules.

Ticket: BK-1   Tier: A
Design: docs/design.md
"""

from dataclasses import dataclass  # noqa: F401  (remove when BK-1 uses it)

# TODO: one @dataclass each, fields listed in design section 3:
# Ticket, AgentResult, TestResult, Finding, ReviewReport,
# Run, Event, Question, HandoffSummary

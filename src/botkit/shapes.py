"""Records shared by every Botkit module"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen = True)
class Snapshot:
    """Snapshot of each original and copy repo at one moment for comparison start and finish"""
    
    repo: str
    head: str
    refs: dict[str, str]
    reflog_len: int
    config_hash: str


@dataclass(frozen = True)
class Ticket:
    """Record that holds spec, brief, ticket.toml settings, ticket name and repo path"""

    repo_path: str
    ticket_name: str
    brief: str
    spec: str
    base: str
    test_cmd: str
    acceptance: tuple[str, ...]
    touches: tuple[str, ...]
    by_hand: bool


@dataclass(frozen = True)
class AgentResult:
    """Record that holds information from one agent call (build or review)"""

    role: str
    model: str
    final_text: str | None
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    turns: int | None
    seconds: float
    exit_code: int
    raw_path: str


@dataclass(frozen = True)
class Finding:
    """Record of one finding from a review"""

    file: str
    line_start: int
    line_end: int
    severity: str
    claim: str
    evidence: str


@dataclass(frozen = True)
class Review:
    """Record that holds output information from one review agent """

    summary: str
    findings: tuple[Finding, ...]
    bug_count: int


@dataclass(frozen = True)
class Verdict:
    """Record that holds results of one pipeline run"""

    ticket_name: str
    outcome: Literal["PASS", "FAIL", "VIOLATION", "ERROR"]
    reason: str | None
    guard_problems: tuple[str, ...]
    tests_changed: tuple[str, ...]
    tests_passed: bool | None
    review: Review | None
    seconds: float

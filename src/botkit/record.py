"""Write the files of one run into its run folder."""

import json
import os
import shutil
from dataclasses import asdict
from typing import Literal

from botkit.shapes import AgentResult, Snapshot, Verdict

SEVERITY_ORDER = {"bug": 0, "risk": 1, "nit": 2}
MAX_FINDINGS = 5


def _new_path(run_path, name):
    """Create the run folder if needed and return the path for name, raising if it already exists."""
    os.makedirs(run_path, exist_ok=True)
    path = os.path.join(run_path, name)
    if os.path.exists(path):
        raise FileExistsError(f"{path} already exists")
    return path


def _write_text(path, text):
    """Write text to path as UTF-8."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _write_json(path, value):
    """Write value to path as indented UTF-8 JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=2)


def add_step(run_path: str, step: str, event: Literal["start", "end"], time: str) -> str:
    """Append one step event as a JSON line to steps.jsonl and return its path."""
    os.makedirs(run_path, exist_ok=True)
    path = os.path.join(run_path, "steps.jsonl")
    line = json.dumps({"step": step, "event": event, "time": time})
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return path


def copy_ticket(run_path: str, ticket_path: str) -> str:
    """Copy the whole ticket folder into the run folder as ticket/ and return its path."""
    path = _new_path(run_path, "ticket")
    shutil.copytree(ticket_path, path)
    return path


def write_guard(run_path: str,
                clone_before: Snapshot, clone_after: Snapshot,
                real_before: Snapshot, real_after: Snapshot,
                problems: list[str]) -> str:
    """Write the four snapshots and the problems list to guard.json and return its path."""
    path = _new_path(run_path, "guard.json")
    data = {
        "clone_before": asdict(clone_before),
        "clone_after": asdict(clone_after),
        "real_before": asdict(real_before),
        "real_after": asdict(real_after),
        "problems": problems,
    }
    _write_json(path, data)
    return path


def write_build(run_path: str, result: AgentResult) -> str:
    """Write the build agent result to build.json and return its path."""
    path = _new_path(run_path, "build.json")
    _write_json(path, asdict(result))
    return path


def write_patch(run_path: str, patch: str) -> str:
    """Write the patch text to change.patch and return its path."""
    path = _new_path(run_path, "change.patch")
    _write_text(path, patch)
    return path


def write_tests(run_path: str, output: str) -> str:
    """Write the test output to tests.txt and return its path."""
    path = _new_path(run_path, "tests.txt")
    _write_text(path, output)
    return path


def _bullet_lines(items):
    """Return one "- item" line per item, or ["None"] when there are none."""
    if not items:
        return ["None"]
    return [f"- {item}" for item in items]


def _passed_text(tests_passed):
    """Return "yes", "no" or "not run" for the tests_passed value."""
    if tests_passed is None:
        return "not run"
    if tests_passed:
        return "yes"
    return "no"


def _severity_rank(finding):
    """Return the sort position of a finding's severity, unknown severities last."""
    return SEVERITY_ORDER.get(finding.severity, len(SEVERITY_ORDER))


def _finding_lines(review):
    """Return the findings heading and up to five finding lines, worst severity first."""
    findings = []
    if review is not None:
        findings = list(review.findings)
    shown = sorted(findings, key=_severity_rank)[:MAX_FINDINGS]
    lines = [f"## Findings ({len(shown)} of {len(findings)})"]
    if not shown:
        lines.append("None")
    for f in shown:
        lines.append(f"- [{f.severity}] {f.file}:{f.line_start}-{f.line_end} {f.claim}")
    return lines


def _report_text(verdict, outside_touches):
    """Build the readable report.md text from the verdict and the outside touches list."""
    tests_changed = ", ".join(verdict.tests_changed) or "None"
    lines = [
        f"# {verdict.ticket_name}: {verdict.outcome}",
        "",
        f"Reason: {verdict.reason or 'None'}",
        "",
        "## Tests",
        f"Passed: {_passed_text(verdict.tests_passed)}",
        f"Tests changed: {tests_changed}",
        "",
        "## Guard problems",
    ]
    lines += _bullet_lines(verdict.guard_problems)
    lines += ["", "## Outside touches"]
    if outside_touches:
        lines.append("WARNING: patch changed files outside touches:")
    lines += _bullet_lines(outside_touches)
    lines.append("")
    lines += _finding_lines(verdict.review)
    return "\n".join(lines) + "\n"


def write_verdict(run_path: str, verdict: Verdict,
                  outside_touches: list[str]) -> tuple[str, str]:
    """Write report.md then verdict.json, and return both paths with verdict.json first."""
    report_path = _new_path(run_path, "report.md")
    verdict_path = _new_path(run_path, "verdict.json")
    _write_text(report_path, _report_text(verdict, outside_touches))
    _write_json(verdict_path, asdict(verdict))
    return verdict_path, report_path

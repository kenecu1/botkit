import json
import os
from dataclasses import asdict

import pytest

from botkit.record import (
    add_step,
    copy_ticket,
    write_build,
    write_guard,
    write_patch,
    write_tests,
    write_verdict,
)
from botkit.shapes import AgentResult, Finding, Review, Snapshot, Verdict


def make_snapshot(repo, head):
    return Snapshot(
        repo=repo,
        head=head,
        refs={"refs/heads/main": head},
        reflog_len=3,
        config_hash="c0ffee",
    )


SNAPSHOTS = {
    "clone_before": make_snapshot("/tmp/clone", "aaa111"),
    "clone_after": make_snapshot("/tmp/clone", "bbb222"),
    "real_before": make_snapshot("/home/me/repo", "ccc333"),
    "real_after": make_snapshot("/home/me/repo", "ccc333"),
}
PROBLEMS = ["HEAD changed from aaa111 to bbb222"]

AGENT_RESULT = AgentResult(
    role="build",
    model="claude-opus-5-5",
    final_text="done",
    input_tokens=1200,
    cached_input_tokens=800,
    output_tokens=300,
    turns=7,
    seconds=42.5,
    exit_code=0,
    raw_path="/runs/T005-record/20261123T100000Z/build_raw.json",
)

PATCH = "diff --git a/src/botkit/record.py b/src/botkit/record.py\n+print('hi')\n"
TESTS_OUTPUT = "===== 3 passed in 0.12s =====\n"


def make_finding(severity, claim, line):
    return Finding(
        file="src/botkit/a.py",
        line_start=line,
        line_end=line + 2,
        severity=severity,
        claim=claim,
        evidence="evidence for " + claim,
    )


def make_verdict(findings):
    return Verdict(
        ticket_name="T005-record",
        outcome="FAIL",
        reason="tests/test_record.py::test_x failed",
        guard_problems=(),
        tests_changed=("tests/test_record.py",),
        tests_passed=False,
        review=Review(
            summary="one summary",
            findings=tuple(findings),
            bug_count=sum(f.severity == "bug" for f in findings),
        ),
        seconds=99.0,
    )


def as_json(value):
    """What a value looks like after a JSON round trip (tuples become lists)."""
    return json.loads(json.dumps(value))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# Example 1
def test_each_writer_creates_its_file_in_run_folder_and_returns_its_path_with_same_values(tmp_path):
    run_path = str(tmp_path / "runs" / "T005-record" / "20261123T100000Z")  # does not exist yet
    verdict = make_verdict([make_finding("bug", "off by one", 10)])

    guard_path = write_guard(run_path, **SNAPSHOTS, problems=PROBLEMS)
    build_path = write_build(run_path, AGENT_RESULT)
    patch_path = write_patch(run_path, PATCH)
    tests_path = write_tests(run_path, TESTS_OUTPUT)
    verdict_path, report_path = write_verdict(run_path, verdict, [])

    assert guard_path == os.path.join(run_path, "guard.json")
    assert build_path == os.path.join(run_path, "build.json")
    assert patch_path == os.path.join(run_path, "change.patch")
    assert tests_path == os.path.join(run_path, "tests.txt")
    assert verdict_path == os.path.join(run_path, "verdict.json")
    assert report_path == os.path.join(run_path, "report.md")

    expected_guard = {name: asdict(snap) for name, snap in SNAPSHOTS.items()}
    expected_guard["problems"] = PROBLEMS
    assert load_json(guard_path) == as_json(expected_guard)
    assert load_json(build_path) == as_json(asdict(AGENT_RESULT))
    assert read_text(patch_path) == PATCH
    assert read_text(tests_path) == TESTS_OUTPUT
    assert load_json(verdict_path) == as_json(asdict(verdict))
    assert os.path.isfile(report_path)


# Example 2
def test_copy_ticket_copies_folder_and_leaves_source_unchanged(tmp_path):
    source = tmp_path / "repo" / "tickets" / "T005-record"
    (source / "notes").mkdir(parents=True)
    (source / "brief.md").write_text("the brief\n")
    (source / "spec.md").write_text("the spec\n")
    (source / "ticket.toml").write_text('base = "abc123"\n')
    (source / "notes" / "extra.md").write_text("extra\n")

    def contents(folder):
        return {
            os.path.relpath(os.path.join(dirpath, name), folder): open(os.path.join(dirpath, name), "rb").read()
            for dirpath, _, names in os.walk(folder)
            for name in names
        }

    def stats(folder):
        return {
            os.path.relpath(os.path.join(dirpath, name), folder): os.stat(os.path.join(dirpath, name)).st_mtime_ns
            for dirpath, dirs, names in os.walk(folder)
            for name in dirs + names
        }

    contents_before = contents(source)
    stats_before = stats(source)
    run_path = str(tmp_path / "run")  # does not exist yet

    copied = copy_ticket(run_path, str(source))

    assert copied == os.path.join(run_path, "ticket")
    assert contents(copied) == contents_before
    assert contents(source) == contents_before
    assert stats(source) == stats_before


# Example 3
def test_seven_findings_report_lists_only_five_worst_with_bug_before_risk(tmp_path):
    findings = [
        make_finding("nit", "nit one", 10),
        make_finding("risk", "risk one", 20),
        make_finding("bug", "bug one", 30),
        make_finding("nit", "nit two", 40),
        make_finding("risk", "risk two", 50),
        make_finding("bug", "bug two", 60),
        make_finding("risk", "risk three", 70),
    ]

    _, report_path = write_verdict(str(tmp_path / "run"), make_verdict(findings), [])

    finding_lines = [line for line in read_text(report_path).splitlines() if line.startswith("- [")]
    assert finding_lines == [
        "- [bug] src/botkit/a.py:30-32 bug one",
        "- [bug] src/botkit/a.py:60-62 bug two",
        "- [risk] src/botkit/a.py:20-22 risk one",
        "- [risk] src/botkit/a.py:50-52 risk two",
        "- [risk] src/botkit/a.py:70-72 risk three",
    ]


# Example 4
def test_add_step_appends_a_new_line_each_call_instead_of_raising(tmp_path):
    run_path = str(tmp_path / "run")  # does not exist yet
    calls = [
        ("build", "start", "2026-11-23T10:00:00Z"),
        ("build", "end", "2026-11-23T10:04:12Z"),
        ("verify", "start", "2026-11-23T10:04:13Z"),
    ]

    paths = [add_step(run_path, step, event, time) for step, event, time in calls]

    steps_path = os.path.join(run_path, "steps.jsonl")
    assert paths == [steps_path] * 3
    lines = read_text(steps_path).splitlines()
    assert [json.loads(line) for line in lines] == [
        {"step": step, "event": event, "time": time} for step, event, time in calls
    ]


# Example 5
WRITERS = {
    "guard.json": lambda run: write_guard(run, **SNAPSHOTS, problems=PROBLEMS),
    "build.json": lambda run: write_build(run, AGENT_RESULT),
    "change.patch": lambda run: write_patch(run, PATCH),
    "tests.txt": lambda run: write_tests(run, TESTS_OUTPUT),
    "verdict.json": lambda run: write_verdict(run, make_verdict([]), []),
    "report.md": lambda run: write_verdict(run, make_verdict([]), []),
}


@pytest.mark.parametrize("name", list(WRITERS))
def test_existing_file_raises_file_exists_error_saying_it_already_exists(tmp_path, name):
    run = tmp_path / "run"
    run.mkdir()
    (run / name).write_text("old")

    with pytest.raises(FileExistsError, match="already exists") as err:
        WRITERS[name](str(run))

    assert os.path.join(str(run), name) in str(err.value)
    assert (run / name).read_text() == "old"
    assert os.listdir(run) == [name]  # nothing else written, not even the other verdict file


# FileExistsError for the ticket folder
def test_existing_ticket_folder_raises_file_exists_error_saying_it_already_exists(tmp_path):
    source = tmp_path / "repo" / "tickets" / "T005-record"
    source.mkdir(parents=True)
    (source / "brief.md").write_text("the brief\n")
    run = tmp_path / "run"
    (run / "ticket").mkdir(parents=True)
    (run / "ticket" / "old.md").write_text("old")

    with pytest.raises(FileExistsError, match="already exists") as err:
        copy_ticket(str(run), str(source))

    assert os.path.join(str(run), "ticket") in str(err.value)
    assert os.listdir(run / "ticket") == ["old.md"]


# Outside-touches warning (Proposed item 1, approved)
def test_report_warns_when_patch_touched_files_outside_touches(tmp_path):
    _, with_files = write_verdict(str(tmp_path / "a"), make_verdict([]), ["src/botkit/other.py"])
    _, empty = write_verdict(str(tmp_path / "b"), make_verdict([]), [])

    assert "WARNING" in read_text(with_files)
    assert "src/botkit/other.py" in read_text(with_files)
    assert "WARNING" not in read_text(empty)

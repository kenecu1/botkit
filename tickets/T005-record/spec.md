# Spec: record.py

## Goal
Record gets everything from pipeline as function arguments, the run folder path plus the data to save, and writes files into that run folder.

## Signatures
File: `src/botkit/record.py` (new)

```python
from typing import Literal
from botkit.shapes import AgentResult, Snapshot, Verdict

def add_step(run_path: str, step: str, event: Literal["start", "end"], time: str) -> str: ...
def copy_ticket(run_path: str, ticket_path: str) -> str: ...
def write_guard(run_path: str,
                clone_before: Snapshot, clone_after: Snapshot,
                real_before: Snapshot, real_after: Snapshot,
                problems: list[str]) -> str: ...
def write_build(run_path: str, result: AgentResult) -> str: ...
def write_patch(run_path: str, patch: str) -> str: ...
def write_tests(run_path: str, output: str) -> str: ...
def write_verdict(run_path: str, verdict: Verdict,
                  outside_touches: list[str]) -> tuple[str, str]: ...
```

## Inputs and outputs

Every function:
- Takes `run_path` (`str`) from pipeline. record never builds it.
- Creates `run_path`, including parent folders, if it does not exist.
- Returns `os.path.join(run_path, <name>)` for what it wrote. `write_verdict` returns `(verdict.json path, report.md path)`.
- Writes text as UTF-8.

| Function | Writes | Content |
|---|---|---|
| `add_step` | `steps.jsonl` | Appends one line: `{"step": step, "event": event, "time": time}` as JSON. `time` is stored exactly as given. Never raises `FileExistsError`. |
| `copy_ticket` | `ticket/` | A copy of the whole folder at `ticket_path`, subfolders included. Only reads `ticket_path`. |
| `write_guard` | `guard.json` | One object: keys `clone_before`, `clone_after`, `real_before`, `real_after` (each `dataclasses.asdict` of the Snapshot) and `problems` (the list as given). |
| `write_build` | `build.json` | `dataclasses.asdict(result)`. |
| `write_patch` | `change.patch` | `patch`, exactly as given. |
| `write_tests` | `tests.txt` | `output`, exactly as given. |
| `write_verdict` | `report.md`, then `verdict.json` | `verdict.json` is `dataclasses.asdict(verdict)`. `report.md` is described below. `verdict.json` is written last. |

JSON files are written with `json.dump(..., indent=2)`. Tuples become lists. Nested records (`Review`, `Finding`) become nested objects.

### report.md
Built only from `verdict` and `outside_touches`. Layout, in this order:

```
# {ticket_name}: {outcome}

Reason: {reason, or "None"}

## Tests
Passed: {"yes" | "no" | "not run" when tests_passed is None}
Tests changed: {tests_changed joined with ", ", or "None"}

## Guard problems
- {one line per problem, or "None"}

## Outside touches
WARNING: patch changed files outside touches:
- {one line per file}
(or just "None" when outside_touches is empty)

## Findings ({shown} of {total})
- [{severity}] {file}:{line_start}-{line_end} {claim}
(or "None" when there are no findings or review is None)
```

Findings:
- At most 5 are shown.
- Order: `bug`, then `risk`, then `nit`. Findings with the same severity keep their order from `verdict.review.findings`.
- Each finding line is exactly `- [{severity}] {file}:{line_start}-{line_end} {claim}`.

`outside_touches` is computed by the caller. record does not compute it.

### Errors
- The target file (or the `ticket/` folder) already exists: raise `FileExistsError` whose message contains the full path and the words `already exists`. Nothing is written or changed.
- `write_verdict` checks both `report.md` and `verdict.json` before writing either. If one exists, it raises as above and writes neither.

## Examples
1. Normal: receive a record correctly → creates the file in that location and returns the correct file path. Check that the values are the same.
2. Only reads and stores: record doesn't change any code, so the ticket folder it copies from stays the same.
3. Worked out: 7 findings → report.md lists only the 5 worst, highest severity first. highest severity first means bug before risk
4. Unusual: steps.jsonl adds a new line each time instead of raising, because steps would be added to continuously.
5. Broken: file already there → `FileExistsError` saying it already exists.

## Edge cases
- `run_path` does not exist: created, with parents, by whichever function runs first.
- `add_step` on an existing `steps.jsonl`: appends a line and never raises.
- `add_step` does not check `event` or the format of `time`.
- Empty `patch` or empty test output: writes an empty file.
- Empty `problems`: `"problems": []` in guard.json.
- `review` is `None`, or it has 0 findings: report shows `## Findings (0 of 0)` and `None`.
- 5 or fewer findings: all are shown, sorted by severity.
- Equal severities: keep their order from the Review.
- `tests_passed` is `None`: report says `Passed: not run`.
- Only one of `report.md` and `verdict.json` exists: `FileExistsError` naming that file, and neither is written.
- `ticket/` already exists in the run folder: `FileExistsError` naming it. The existing folder is left untouched.

## Acceptance tests
All in `tests/test_record.py`:

| Test | Covers |
|---|---|
| `test_each_writer_creates_its_file_in_run_folder_and_returns_its_path_with_same_values` | Example 1, and a missing run folder is created |
| `test_copy_ticket_copies_folder_and_leaves_source_unchanged` | Example 2 |
| `test_seven_findings_report_lists_only_five_worst_with_bug_before_risk` | Example 3 |
| `test_add_step_appends_a_new_line_each_call_instead_of_raising` | Example 4 |
| `test_existing_file_raises_file_exists_error_saying_it_already_exists` (one case per file, both verdict files included) | Example 5, and the both-files check |
| `test_existing_ticket_folder_raises_file_exists_error_saying_it_already_exists` | `FileExistsError` for `ticket/` |
| `test_report_warns_when_patch_touched_files_outside_touches` | Outside-touches warning shown only when there are files |

## Out of scope
- It doesn't call guard, verify or agents, and it doesn't read their files. The one exception is copying the ticket folder, where it reads from the path it was given.
- Doesn't write explain.md, I write it.
- Doesn't write review.json, agents has already written it.
- Doesn't commit, doesn't delete folders, doesn't decide outcome.
- Agents saves the raw output as build_raw.json; record never writes that file.

## Proposed
Not covered by the acceptance tests. Approve, change or drop each one.

1. Not tested: the report.md wording besides the finding lines and the outside-touches warning, as you chose. That covers the header, reason, the tests section, guard problems, `None` and `not run`.
2. Not tested: review `None`, 0 findings, and 5 or fewer findings in report.md.
3. Assumption: a severity other than `bug`, `risk` or `nit` sorts after `nit` and keeps its order. The design allows only these three, so this shouldn't happen.
4. Assumption: if `ticket_path` does not exist, `copy_ticket` lets the standard library's error (`FileNotFoundError`) through unchanged. The brief doesn't cover this. It is not tested and not listed as an error case.
5. Assumption: the JSON uses `indent=2` and UTF-8. Tests compare loaded values, not file bytes.
6. Not handled: two processes writing `steps.jsonl` at the same time. There is no locking. Pipeline runs steps one after another.
7. Note: design §5 says the experiment imports "the writer from record". This spec doesn't say which function that is. The experiment may need one that writes a review result, which is not in this brief.

# Brief: record.py

## Goal
Record gets everything from pipeline as function arguments: the run folder path plus the data to save. It writes files into that run folder.

## Inputs
- `run_path` (`str`): must be passed in, record never builds it.
- Multiple functions, one for each step:
  - `steps.jsonl`: step name (`str`), start or end, and the time given by pipeline.
  - `ticket/`: the ticket folder path.
  - `guard.json`: the four Snapshots (clone and real repo, before and after) and the problems list from compare.
  - `build.json`: the AgentResult from build.
  - `change.patch`: patch text (`str`).
  - `tests.txt`: pytest output (`str`).
  - `verdict.json` and `report.md`: the Verdict.

## Outputs
- Each should return the path (`str`) so we know where it was made.
- If run path doesn't exist, create the run path folder.
- Don't overwrite. If the file is already there, raise `FileExistsError` saying it already exists.
- report.md is the one file in the run folder written for you to read. It's built from the Verdict, the same record that becomes verdict.json, just turned into readable text. That's why both are written together at the end. It shows:
  - The outcome and reason, for example PASS, or FAIL with the failing test.
  - The tests: passed or not, and any test files the bot changed (tests_changed).
  - Guard problems, if any.
  - A warning if the patch touched files outside touches. The report function receives the list of changed files outside touches as its own argument. record doesn't compute it.
  - At most 5 review findings, highest severity first.

## Examples
1. Normal: receive a record correctly → creates the file in that location and returns the correct file path. Check that the values are the same.
2. Only reads and stores: record doesn't change any code, so the ticket folder it copies from stays the same.
3. Worked out: 7 findings → report.md lists only the 5 worst, highest severity first. highest severity first means bug before risk
4. Unusual: steps.jsonl adds a new line each time instead of raising, because steps would be added to continuously.
5. Broken: file already there → `FileExistsError` saying it already exists.

## Out of scope
- It doesn't call guard, verify or agents, and it doesn't read their files. The one exception is copying the ticket folder, where it reads from the path it was given.
- Doesn't write explain.md, I write it.
- Doesn't write review.json, agents has already written it.
- Doesn't commit, doesn't delete folders, doesn't decide outcome.
- Agents saves the raw output as build_raw.json; record never writes that file.

## Touches
- src/botkit/record.py (new file; no existing files change)

# Brief: verify.py

## Goal
This code restores tests, run them, returns pass or fail.

## Inputs
- `clone_path` (`str`): runs in clone path.
- `base` (`str`): it restores from base.
- test folders (`tuple[str, ...]`): passed in, tuple so they shouldn't be changed.
- acceptance paths (`tuple[str, ...]`): passed in, tuple so they shouldn't be changed.
- `test_cmd` (`str`): run test_cmd.
- No runner.

## Outputs
- A tuple: (did the test pass?, did any tests change?, output text of pytest).
- Tests passed is True or False once verify is called. None only comes from pipeline, when verify never ran.
- Tests changed is a tuple of file names.
- Run acceptance paths first, then the full test_cmd. The full test_cmd still runs if they fail, because we want that info saved.
- A new test file the bot creates that wasn't in base gets listed in tests changed.
- `base` doesn't exist: raise `ValueError`.

## Examples
1. Normal: bot didn't touch the tests and they pass → passed is True, tests changed is empty (0), output is the pytest string.
2. Worked out: bot edits a test file → it gets rolled back and added to tests changed for sure, and the file is checked to be the same as base.
3. Unusual: zero acceptance tests ran (exit code 5) → passed is False.
4. Broken: `base` isn't real → `ValueError` saying base doesn't exist.

## Out of scope
- Only test files get rolled back. Don't change non test files, only rolls back the tests and makes sure they are the same.
- Don't write tests.txt, record does. Verify returns the output instead.
- Don't commit.
- If something fails we don't try to restart.
- If outcome fails, keep patch and clone and skip review is pipeline's job, not verify's.

## Touches
- src/botkit/verify.py (new file; no existing files change)

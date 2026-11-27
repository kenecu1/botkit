# Spec: verify.py

## Goal
Restore the tests from `base`, run them, and return pass or fail.

## Signatures
File: `src/botkit/verify.py` (new)

```python
def verify(clone_path: str, base: str, test_dirs: tuple[str, ...],
           acceptance: tuple[str, ...], test_cmd: str) -> tuple[bool, tuple[str, ...], str]:
    """Returns (passed, tests_changed, output)."""
```

## Inputs and outputs

### Inputs
- `clone_path` (`str`): the clone, after `sandbox.export_patch` has staged everything. All work happens here.
- `base` (`str`): the base commit SHA.
- `test_dirs` (`tuple[str, ...]`): test folders, relative to `clone_path`, for example `("tests",)`. Not changed.
- `acceptance` (`tuple[str, ...]`): acceptance test paths, relative to `clone_path`. Not changed.
- `test_cmd` (`str`): the test command, for example `"pytest"`.

### Steps
1. **Check `base`.** `git -C <clone_path> rev-parse --verify --quiet <base>^{commit}` must succeed. If not, it raises `ValueError`. The message contains `does not exist` and `base` as given. Nothing is restored or run.
2. **Find changed tests.** The guarded paths are `test_dirs + acceptance`. A file under a guarded path is changed if git sees it differ from `base`: it was edited, deleted, or added (staged or untracked). Files that `.gitignore` covers are never changed.
3. **Restore.** Under every guarded path:
   - every file that exists in `base` gets `base`'s content back (`git checkout <base> -- <path>`), and
   - every file that is not in `base` and not ignored is deleted, from both the working tree and the index.
   Afterwards the working tree and the index under the guarded paths match `base`. Ignored files are left alone. Files outside the guarded paths are never touched.
4. **Acceptance run.** Runs `shlex.split(test_cmd) + list(acceptance)` with `cwd=clone_path`, stdout and stderr captured together as text, and no shell.
5. **Full run.** Runs `shlex.split(test_cmd)` the same way. It always runs, even if the acceptance run failed.
6. **Return** `(passed, tests_changed, output)`.

### Outputs
- `passed` (`bool`): `True` only if **both** runs exit with code 0. Any other code, including 5 (no tests collected), gives `False`. Never `None`.
- `tests_changed` (`tuple[str, ...]`): the changed files from step 2, as paths relative to `clone_path` with `/` separators, sorted, with no duplicates. Empty if nothing changed.
- `output` (`str`): one block per run, acceptance first, then full. A block is the header line `"$ " + shlex.join(args)` followed by that run's output. If the output doesn't end with `"\n"`, a `"\n"` is added.

## Examples
1. Normal: bot didn't touch the tests and they pass → passed is True, tests changed is empty (0), output is the pytest string.
2. Worked out: bot edits a test file → it gets rolled back and added to tests changed for sure, and the file is checked to be the same as base.
3. Unusual: zero acceptance tests ran (exit code 5) → passed is False.
4. Broken: `base` isn't real → `ValueError` saying base doesn't exist.

## Edge cases
- The bot adds a new test file → it is deleted and listed in `tests_changed`.
- The bot deletes a test file that was in `base` → it is restored and listed.
- An acceptance path outside `test_dirs` → it is guarded and restored too.
- A guarded path that doesn't exist in `base` → nothing to restore there. Any new files in it are deleted and listed.
- Ignored files, such as `__pycache__` → not listed and not deleted.
- The acceptance run fails → the full run still runs, and `passed` is `False`.
- The acceptance run passes but the full run fails → `passed` is `False`.
- A test that was already failing at `base` → it still makes `passed` `False`.
- Non-test files the bot changed → left as they are.

## Out of scope
- Only test files get rolled back. Don't change non test files, only rolls back the tests and makes sure they are the same.
- Don't write tests.txt, record does. Verify returns the output instead.
- Don't commit.
- If something fails we don't try to restart.
- If outcome fails, keep patch and clone and skip review is pipeline's job, not verify's.

## Proposed
**Assumptions**
1. **"Passes the tests from base"** means both runs exit 0. After the restore, only `base`'s tests are left, so both runs run only those.
2. **There's no timeout** (question 4). A hanging test hangs `verify` and the pipeline. Consider a `timeout` argument in a later ticket.
3. **If `test_cmd` can't be started** (the program isn't found), the `subprocess` error propagates. It is not turned into `passed = False`.
4. **The index is restored too**, not just the working tree, so `git status` under the guarded paths is clean afterwards.
5. **`base` is checked in `clone_path`**, which is a clone of the repo at `base`.

**Extra tests to consider**
6. The acceptance run passes and the full run fails → `passed` is `False`.
7. An acceptance path outside `test_dirs` that the bot edited → restored and listed.
8. The `output` blocks for a run whose output doesn't end with a newline.

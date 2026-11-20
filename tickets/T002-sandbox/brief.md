# Brief: sandbox.py

## Goal
Clone repo at base commit in ticket.toml into throwaway folder, deletes origin from clone so bot can't push, after its built, stage everything with git add -A and export the diff against base.

## Inputs
- Function 1 (make clone): `repo_path` (`str`), `base` (`str`), `dest` (`str`, the /clone folder for each run). It creates the git clone at dest, so the /clone folder is made by the clone itself.
- Function 2 (export patch): `clone_path` (`str`, which is /clone) and `base` (`str`). Runs git add -A, and git diff with --cached and --binary.

## Outputs
- Function 1 returns a `str` that is the clone path.
- Function 2 returns the patch text as a `str`.
- `dest` already exists: raise `FileExistsError`.
- `repo_path` is not a real repo path: raise `FileNotFoundError`.
- `base` is not a real base: raise `ValueError`.
- Nothing was changed: raise `ValueError`.

## Examples
1. Normal (make clone): input repo, base and dest. It returns dest, the clone has no origin (origin is gone), and the clone's HEAD is equal to base.
2. Normal (export): function 2 receives the clone path and base, makes sure files are added, then runs git diff to output what changed, as a string.
3. Edit and new file: bot edits one file and creates a new one, the patch should contain both.
4. Unusual: nothing was changed, so raise `ValueError` saying that no patch was outputted because no change was made, because there should be something changed and otherwise verify can't run.
5. Broken: raise `FileExistsError` saying dest already exists, `FileNotFoundError` saying repo_path cannot be found, `ValueError` saying base isn't a real commit. One test for each.

## Out of scope
- It shouldn't take snapshots (`guard`), run a builder (`agents`), or restore or run tests (`verify`).
- Only things it should do is make a clone, and export a patch.
- It shouldn't write change.patch because `record` does.
- It doesn't delete the clone. The clone is kept on ERROR.

## Touches
- src/botkit/sandbox.py (new file; no existing files change)

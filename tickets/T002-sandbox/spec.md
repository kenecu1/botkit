# Spec: sandbox.py

## Goal
Clone the repo at the ticket's base commit into a throwaway folder and remove `origin` so the bot can't push. After the build, stage everything with `git add -A` and export the diff against base.

## Signatures
File: `src/botkit/sandbox.py` (new)

```python
def make_clone(repo_path: str, base: str, dest: str) -> str: ...
def export_patch(clone_path: str, base: str) -> str: ...
```

## Inputs and outputs

### make_clone
- `repo_path` (`str`): the original repo.
- `base` (`str`): the commit SHA from `ticket.toml`.
- `dest` (`str`): the clone folder for this run. It must not exist yet. `git clone` creates it.

It checks these in order, before anything is created:
1. **`repo_path` is a git repo.** It must exist, and it must be the top of a git work tree: `git -C <repo_path> rev-parse --show-toplevel` succeeds and resolves to the same folder as `repo_path`. If not, it raises `FileNotFoundError`. The message contains `repo_path` as given. This covers a missing path and a folder that exists but is not a git repo, such as an empty folder.
2. **`base` is a commit in `repo_path`.** `git -C <repo_path> rev-parse --verify --quiet <base>^{commit}` succeeds. If not, it raises `ValueError`. The message contains `base` as given. `dest` is not created.
3. **`dest` does not exist.** If it does, it raises `FileExistsError`. The message contains `dest` as given and says it already exists. `dest` is left untouched.

Then it:
1. Runs `git clone --no-hardlinks --no-checkout -q <repo_path> <dest>`. The clone has its own copy of every object and shares no files with the original: every file under `<dest>/.git/objects` has a link count (`st_nlink`) of 1.
2. Runs `git -C <dest> checkout -q --detach <base>`. HEAD is detached at `base`.
3. Runs `git -C <dest> remote remove origin`. The clone has no remotes.
4. Returns `dest`, exactly as given.

Every git call uses an argument list, never `shell=True`.

### export_patch
- `clone_path` (`str`): the clone made by `make_clone`, after the builder has run.
- `base` (`str`): the same base commit.

It:
1. Runs `git -C <clone_path> add -A`. All new, changed and deleted files are staged, and `.gitignore` is respected.
2. Runs `git -C <clone_path> diff --cached --binary <base>`.
3. If that output is empty, it raises `ValueError`. The message contains `no change`, for example `"no patch exported: no change was made in <clone_path>"`.
4. Otherwise it returns the output exactly as given, as `str`.

It does not commit, and does not write any file.

## Examples
1. Normal (make clone): input repo, base and dest. It returns dest, the clone has no origin (origin is gone), and the clone's HEAD is equal to base.
2. Normal (export): function 2 receives the clone path and base, makes sure files are added, then runs git diff to output what changed, as a string.
3. Edit and new file: bot edits one file and creates a new one, the patch should contain both.
4. Unusual: nothing was changed, so raise `ValueError` saying that no patch was outputted because no change was made, because there should be something changed and otherwise verify can't run.
5. Broken: raise `FileExistsError` saying dest already exists, `FileNotFoundError` saying repo_path cannot be found, `ValueError` saying base isn't a real commit. One test for each.

## Edge cases
- `repo_path` exists but is not a git repo (an empty folder): `FileNotFoundError`, and `dest` is not created.
- `base` is a valid-looking SHA that isn't in the repo: `ValueError`, and `dest` is not created.
- `dest` already exists, even as an empty folder: `FileExistsError`, and its contents are left untouched.
- More than one input is bad: the first failed check, in the order above, decides the error.
- The builder made no change, or only changed ignored files: `export_patch` raises `ValueError` (`no change`).
- The builder deleted a file: the deletion is staged and appears in the patch.
- Binary files: included, because of `--binary`.

## Out of scope
- It shouldn't take snapshots (`guard`), run a builder (`agents`), or restore or run tests (`verify`).
- Only things it should do is make a clone, and export a patch.
- It shouldn't write change.patch because `record` does.
- It doesn't delete the clone. The clone is kept on ERROR.

## Proposed
**Assumptions**
1. **Check order** is `repo_path` → `base` → `dest`. The brief doesn't give an order. Each test triggers only one error, so the order isn't tested.
2. **`base`** is the latest commit's SHA, from `ticket.toml`. Anything that resolves to a commit is accepted. The tests use the full SHA.
3. **A git repo** means the top of a work tree. A subfolder of a repo, or a bare repo, counts as not a repo.
4. **The clone only gets branches and tags.** A `base` that is only reachable from something else (a stash, or a detached commit no ref points to) passes check 2 but fails at checkout. `git` raises an error there, and it is not turned into `ValueError`.

**Extra tests to consider**
5. An older base: a repo with two commits and `base` set to the first. HEAD is the first commit, and the second commit's file isn't in the work tree.
6. A deleted file appears in the patch as `deleted file mode`.
7. A binary file appears in the patch as `GIT binary patch`.
8. The patch applies: `git apply --check` on a fresh checkout of `base` succeeds.
9. `export_patch` doesn't commit: HEAD is still `base` afterwards.
10. Ignored files are not in the patch.

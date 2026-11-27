# T002 sandbox explain

Tier: B (bootstrap ticket, interface level explain)

## src/botkit/sandbox.py
- Starts up clone for builder to run in, removes remote so bot can't push into real repo, and then exports the diff or changes from base commit to see what changed including new files.

## Interface
- `make_clone(repo_path, base, dest) -> str`: clones at base, detached, origin removed, returns dest.
- `export_patch(clone_path, base) -> str`: git add -A, then git diff --cached --binary against base, returns the patch text.
- Errors: dest exists -> FileExistsError; repo_path missing -> FileNotFoundError; base not a commit or nothing changed -> ValueError.
- Does not write change.patch (record does) and does not delete the clone (kept on ERROR).

## Compared with the bot's summary
- Missed: any git failure after the input checks raises RuntimeError with git's error text. The pipeline will need to treat that as ERROR.
- Missed: the clone uses --no-hardlinks, so it copies git's files instead of sharing them, and the bot can't reach the real repo through shared files.
- Missed: all three checks run before anything is created, so a bad input never leaves a half made folder.
- Untested: deleted files and binary files in the patch. Worth a test in a later ticket.

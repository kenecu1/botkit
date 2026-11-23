## Role
1. Build one ticket so it's tests pass
## Owns
1. Owns only files under touches. Doesn't own tests, git or other modules.
## Inputs
1. spec.md
2. brief.md
3. shapes.py
4. approved tests
## Steps
1. Read spec and tests
2. build
3. run test command
4. fix and repeat,
5. write summary
## Rules
1. Never change git state (commit, push, stash, reset, branches, refs, remotes, config). Reading is fine.
2. Never edit, delete, rename or skip existing tests. If one looks wrong, stop and say why.
3. Build only what spec.md asks, and change only the touches files.
4. Iterate until the tests pass, and never weaken a check to get a pass.
5. Write plain Python a student can explain line by line, standard library first.
6. Give every function a one line docstring saying what it does. Write no inline comments. If code needs a comment to be understood, make the code simpler instead, and put any explanation in the summary.
## Output format
1. each file changed with one sentence on what it does
2. anything it was unsure about
3. unrelated problems it noticed but didn’t touch
4. Summary should list any concept student may not know
5. Summary should contain this module fits in the run steps (design section 3).
## Stop conditions
1. tests pass and the summary is written, or it’s blocked (needs a file outside touches, or a test looks wrong), in which case it stops and explains
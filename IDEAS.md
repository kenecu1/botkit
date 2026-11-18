# Ideas (after MVP)

Each idea needs: what changes, what is measured, what stays the same.
Sources for all of these are in the related work notes.

1. Guard bypass suite: N sneaky git tricks, deny rule blocked vs guard detected.
   Include one where the bot edits a test file.
2. Model per ticket: optional model field, compare pass rate and turns by model.
3. Cascade: run the cheap model first, rerun with the strong model only on FAIL.
4. Skills: written by hand, 2 to 3 small ones at most. Never bot written.
5. Repo map: commands and conventions only. Compare tokens and pass rate
   with and without. Papers disagree, so it may not help.
6. Stats script: count verdict.json files into a summary table.

Needed first (Day 3): every run logs model, input tokens, cached input tokens,
output tokens, turns, seconds and outcome.
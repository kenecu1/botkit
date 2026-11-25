# T005 record explain

Tier: B (bootstrap ticket, interface level explain)

## What it does
- Record gets data and run path from pipeline into function arguments. Then writes files into the run folder. 

## Interface
- 7 writers: add_step, copy_ticket, write_guard, write_build, write_patch, write_tests, write_verdict
- In: run_path plus the data from pipeline. Out: the path of the file it wrote

## Check questions
- How does it refuse to overwrite a file?
  - Raises a FileExistsError
- Why does steps.jsonl append instead of raising?
  - Appends because we edit it more than once throughout the pipeline, so it would
  already exist
- How does write_verdict pick the 5 findings for report.md?
  - Picks based on highest severity to least, same severity keep review order

## Compared with the bot's summary
- Missed: write_verdict writes report.md first and verdict.json last, so a run folder without verdict.json means the run didn't finish.
- Missed: copy_ticket uses shutil.copytree and lets FileNotFoundError through if the ticket folder is missing.
- Bot's own gap: it couldn't check the report layout by eye. You already closed that gap last night when you printed a sample report and it looked right, so write that down.
- Bot's own gap: it still ranks a nit severity that your schema doesn't have. That traces back to the stale design line, and tonight's docs PR fixes the source.

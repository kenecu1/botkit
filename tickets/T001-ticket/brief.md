# Brief: ticket.py

## Goal
Read a ticket folder and output a filled-in Ticket record.

## Inputs
- `ticket_folder_path` (`str`): the path to the ticket folder.

## Outputs
- A filled-in `Ticket` record from `shapes.py`.
- On failure, raises `FileNotFoundError` whose message names the missing file.

## Examples
1. Normal: a folder with brief.md, spec.md and a full ticket.toml gives a Ticket with every value copied over. `acceptance` and `touches` come back as tuples, even though ticket.toml writes them as lists.
2. Worked out: for `/home/kenecu/dev/botkit/tickets/T001-ticket`, `ticket_name` is `"T001-ticket"` and `repo_path` is `"/home/kenecu/dev/botkit"` (two folders up).
3. Unusual but allowed: `by_hand = true` and `touches` with three files. Both are read normally into the Ticket.
4. Broken: the folder has no ticket.toml. Raise `FileNotFoundError` with a message that names `ticket.toml`.

## Out of scope
- It should only ever read a ticket folder and output a Ticket record.
- It does not refuse `by_hand` tickets. `pipeline` does that.
- It does not check that `base` is a real commit. `sandbox` finds out when it clones.

## Touches
- src/botkit/ticket.py (new file; no existing files change)
